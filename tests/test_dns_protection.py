"""Resolver adapter boundary: attributed data, exact scope and bounded controls."""
import copy
from datetime import datetime, timezone
import http.client
import importlib.util
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dns_bridge', ROOT / 'tools/dns-protection/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

TV = '127.0.0.1'
CFG = dict(tv_ip=TV, bind=TV, port=0, timezone='Australia/Perth', tv_token='x' * 40)


class API:
    def __init__(self):
        self.responses = {
            '/status': {'running': True},
            '/access/list': {'allowed_clients': [TV], 'disallowed_clients': []},
            '/clients': {'clients': [{'ids': [TV], 'use_global_settings': True}]},
            '/dns_info': {'protection_enabled': True, 'protection_disabled_until': None},
            '/filtering/status': {'enabled': True, 'filters': [{'id': 1, 'name': 'Fixture list', 'enabled': True, 'rules_count': 1}]},
            '/querylog/config': {'enabled': True, 'anonymize_client_ip': False},
            '/querylog': {'data': []},
        }
        self.writes = []

    def call(self, path, data=None):
        if data is not None:
            self.writes.append((path, data))
            self.responses['/dns_info']['protection_enabled'] = data['enabled']
            return {}
        return copy.deepcopy(self.responses[urlsplit(path).path])


def entry(client=TV, at='2026-11-18T16:01:00Z', reason='FilteredBlackList', domain='track.example.org'):
    return {'client': client, 'time': at, 'question': {'name': domain}, 'reason': reason,
            'rules': [{'filter_list_id': 1}], 'client_proto': '', 'upstream': 'https://dns.example.org/dns-query'}


def test_local_midnight_and_attribution():
    now = datetime(2026, 11, 19, 4, tzinfo=timezone.utc)
    records = [entry(), entry(at='2026-11-18T15:59:00Z'), entry(client='127.0.0.2'),
               entry(reason='NotFilteredWhiteList'), entry(at='invalid'), entry(at='2026-11-20T00:00:00Z')]
    out = bridge.aggregate(records, TV, now, ZoneInfo('Australia/Perth'), {1: 'Fixture'}, True)
    assert out['today'] == {'queries': 2, 'blocked': 1, 'percent': 50.0}
    assert out['days'][-2]['blocked'] == 1
    assert out['topToday'] == [{'domain': 'track.example.org', 'count': 1}]
    assert out['recent'][0]['source'] == 'Fixture'
    assert out['recent'][0]['category'] == 'Not provided by list'
    assert not out['complete']
    assert out['invalidRecords'] == 2
    assert 'client' not in json.dumps(out)


def test_empty_and_bad_domain_are_honest():
    now = datetime(2026, 11, 19, 4, tzinfo=timezone.utc)
    out = bridge.aggregate([], TV, now, ZoneInfo('UTC'), {}, True)
    assert out['lastQueryAt'] is None and out['today']['percent'] == 0
    out = bridge.aggregate([entry(domain='<script>')], TV, now, ZoneInfo('UTC'), {}, True)
    assert out['recent'][0]['domain'] == '(domain unavailable)'


@pytest.mark.parametrize('path,key,value', [
    ('/status', 'running', False),
    ('/access/list', 'allowed_clients', []),
    ('/access/list', 'allowed_clients', [TV, '127.0.0.2']),
    ('/access/list', 'allowed_clients', ['127.0.0.0/8']),
    ('/clients', 'clients', [{'ids': [TV], 'use_global_settings': False}]),
    ('/querylog/config', 'enabled', False),
    ('/querylog/config', 'anonymize_client_ip', True),
    ('/filtering/status', 'enabled', False),
    ('/filtering/status', 'filters', []),
])
def test_scope_or_attribution_drift_locks_controls(path, key, value):
    api = API(); api.responses[path][key] = value
    with pytest.raises(bridge.Unavailable):
        bridge.Protection(CFG, api).change('disable')
    assert api.writes == []


def test_pause_is_native_and_readback_checked():
    api = API(); p = bridge.Protection(CFG, api)
    assert p.change('pause15') == {'accepted': True}
    assert api.writes == [('/protection', {'enabled': False, 'duration': 900000})]
    with pytest.raises(bridge.Unavailable): p.change('enable')
    p.last_action = 0
    p.change('enable')
    assert api.responses['/dns_info']['protection_enabled']
    with pytest.raises(ValueError): p.change('install')


def test_readback_failure_does_not_claim_success():
    api = API()
    original = api.call
    def call(path, data=None):
        result = original(path, data)
        api.responses['/dns_info']['protection_enabled'] = True
        return result
    api.call = call
    with pytest.raises(bridge.Unavailable): bridge.Protection(CFG, api).change('disable')


def test_snapshot_cache_and_scope_refresh_before_write():
    api = API(); p = bridge.Protection(CFG, api)
    p.snapshot(); api.responses['/access/list']['allowed_clients'] = []
    assert p.snapshot()['scope'] == 'Dedicated TV / soundbar resolver'
    with pytest.raises(bridge.Unavailable): p.change('disable')
    assert not api.writes


def test_log_pagination_caps_and_partial_counts():
    api = API()
    api.responses['/querylog'] = {'data': [entry(at=datetime.now(timezone.utc).isoformat())] * bridge.PAGE}
    p = bridge.Protection(CFG, api)
    data = p.snapshot()
    assert not data['complete']
    assert data['today']['queries'] <= bridge.MAX_RECORDS


@pytest.fixture
def http_server():
    api = API(); server = bridge.Server(CFG, bridge.Protection(CFG, api))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    yield server, api
    server.shutdown(); server.server_close(); thread.join()


def call(server, method, path, data=None, headers=None):
    c = http.client.HTTPConnection(*server.server_address, timeout=5)
    all_headers = {'Authorization': 'Bearer ' + CFG['tv_token'], 'Origin': 'null', 'Content-Type': 'application/json'}
    all_headers.update(headers or {})
    c.request(method, path, body=data, headers=all_headers)
    r = c.getresponse(); out = (r.status, dict(r.getheaders()), r.read()); c.close(); return out


def test_http_auth_origin_host_and_no_generic_proxy(http_server):
    server, api = http_server
    assert call(server, 'GET', '/v1/status')[0] == 200
    assert call(server, 'GET', '/v1/status', headers={'Authorization': 'Bearer wrong'})[0] == 403
    assert call(server, 'GET', '/v1/status', headers={'Origin': 'https://evil.example.org'})[0] == 403
    assert call(server, 'GET', '/v1/status', headers={'Host': 'evil.example.org'})[0] == 403
    assert call(server, 'GET', '/control/dns_info')[0] == 404
    assert call(server, 'GET', '/v1/status?client=anyone')[0] == 404
    assert call(server, 'POST', '/v1/protection', '{"action":"install"}')[0] == 400
    assert call(server, 'POST', '/v1/protection', '{"action":"disable","client":"other"}')[0] == 400
    assert call(server, 'POST', '/v1/protection', '{"action":"disable"}', {'Content-Type': 'text/plain'})[0] == 400
    assert not api.writes
    status, headers, data = call(server, 'POST', '/v1/protection', '{"action":"pause15"}')
    assert status == 200 and json.loads(data)['accepted']
    assert headers['Cache-Control'] == 'no-store'
    assert api.writes == [('/protection', {'enabled': False, 'duration': 900000})]


def test_http_wrong_source_denied(http_server):
    server, api = http_server
    server.cfg = dict(CFG, tv_ip='127.0.0.2')
    assert call(server, 'GET', '/v1/status')[0] == 403
    assert not api.writes


def test_profile_permissions_and_upstream_credentials_stay_private(tmp_path):
    cfg = dict(CFG, port=8768, agh_url='http://127.0.0.1:13080', agh_user='admin', agh_password='private')
    path = tmp_path / 'bridge.json'; path.write_text(json.dumps(cfg)); path.chmod(0o600)
    assert bridge.load_config(path)['tv_ip'] == TV
    path.chmod(0o644)
    with pytest.raises(ValueError): bridge.load_config(path)
    path.chmod(0o600); cfg['agh_url'] = 'http://evil.example.org'; path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError): bridge.load_config(path)


def test_health_for_existing_monitor_fails_on_scope_drift(http_server):
    server, api = http_server
    status, _, body = call(server, 'GET', '/health', headers={'Authorization': ''})
    assert status == 200 and json.loads(body) == {'status': 'UP'}
    api.responses['/access/list']['allowed_clients'] = []
    status, _, body = call(server, 'GET', '/health')
    assert status == 503 and json.loads(body) == {'status': 'DOWN'}


def test_upstream_failure_is_sanitized(http_server):
    server, api = http_server
    def fail(*args, **kwargs): raise bridge.Unavailable('private internal failure with credentials')
    api.call = fail
    status, _, body = call(server, 'GET', '/v1/status')
    assert status == 503 and b'private internal' not in body


def test_prepared_resolver_has_no_dhcp_or_global_listener():
    spec = importlib.util.spec_from_file_location('dns_prepare', ROOT / 'tools/dns-protection/prepare.py')
    prepare = importlib.util.module_from_spec(spec); spec.loader.exec_module(prepare)
    cfg = prepare.configuration('127.0.0.2', '127.0.0.1', '$2b$12$' + 'x'*53, True)
    assert cfg['dns']['allowed_clients'] == ['127.0.0.2']
    assert cfg['dns']['bind_hosts'] == ['127.0.0.1'] and cfg['dns']['port'] == 15353
    assert not cfg['dhcp']['enabled']
    assert cfg['http']['address'].startswith('127.0.0.1:')
    assert cfg['dns']['fallback_dns'] == []
    assert not cfg['filtering']['parental_enabled'] and not cfg['filtering']['safe_search']['enabled']
    assert {item['name'] for item in cfg['filters']} == {'HaGeZi Light', 'HaGeZi Samsung'}
    assert all(rule.startswith('@@||') for rule in cfg['user_rules'])
    assert not any(rule == '||samsung.com^' for rule in cfg['user_rules'])
    assert 'samsungqbe.com' in ' '.join(cfg['user_rules'])


def test_new_private_widget_connection_cannot_be_released(tmp_path):
    import zipfile
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from dns_profile import runtime_overlay
    profile = tmp_path / 'widget.json'
    profile.write_text(json.dumps({'endpoint': 'http://127.0.0.1:8768', 'token': 'x' * 40}))
    profile.chmod(0o600)
    overlay = runtime_overlay(profile, {'device-config.js': b'var preservedBinding = true;\n'})
    assert overlay['device-config.js'].startswith(b'var preservedBinding = true;')
    assert b'http://127.0.0.1:8768' in overlay['config.xml']
    release_spec = importlib.util.spec_from_file_location('release_for_dns', ROOT / 'scripts/prepare-release.py')
    release = importlib.util.module_from_spec(release_spec); release_spec.loader.exec_module(release)
    widget = tmp_path / 'private.wgt'
    with zipfile.ZipFile(widget, 'w') as z:
        for name, content in {'LICENSE': b'MIT', 'THIRD_PARTY_NOTICES.md': b'Notices', **overlay}.items():
            z.writestr(name, content)
    with pytest.raises(ValueError): release.validate_widget(widget)


@pytest.mark.parametrize('overrides', [
    {'endpoint': 'https://evil.example.org'}, {'endpoint': 'http://127.0.0.1:8768/path'},
    {'endpoint': 'http://user:pass@127.0.0.1:8768'}, {'token': 'short'},
    {'agh_password': 'REDACTED'},
])
def test_widget_profile_rejects_extra_power_and_bad_endpoints(tmp_path, overrides):
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from dns_profile import runtime_overlay
    profile = tmp_path / 'widget.json'
    profile.write_text(json.dumps({'endpoint': 'http://127.0.0.1:8768', 'token': 'x' * 40, **overrides}))
    profile.chmod(0o600)
    with pytest.raises(ValueError): runtime_overlay(profile)


def test_two_devices_have_distinct_counts_and_no_third_device_leak():
    api = API(); cfg = dict(CFG, soundbar_ip='127.0.0.2')
    api.responses['/access/list']['allowed_clients'] = [TV, cfg['soundbar_ip']]
    api.responses['/clients']['clients'].append({'ids': [cfg['soundbar_ip']], 'use_global_settings': True})
    now = datetime.now(timezone.utc).isoformat()
    api.responses['/querylog']['data'] = [entry(at=now), entry(at=now, reason='NotFilteredWhiteList'),
                                        entry(client=cfg['soundbar_ip'], at=now), entry(client='127.0.0.3', at=now)]
    p = bridge.Protection(cfg, api); data = p.snapshot()
    assert data['today'] == {'queries': 3, 'blocked': 2, 'percent': 66.7}
    tv, soundbar = data['devices']
    assert tv['id'] == 'tv' and tv['today']['queries'] == 2 and tv['today']['percent'] == 50
    assert soundbar['id'] == 'soundbar' and soundbar['today']['queries'] == 1 and soundbar['today']['percent'] == 100
    assert {r['device'] for r in data['recent']} == {'TV', 'Soundbar'}
    assert '127.0.0.' not in json.dumps(data)
    p.change('pause15')
    assert api.writes == [('/protection', {'enabled': False, 'duration': 900000})]
    api.responses['/access/list']['allowed_clients'].append('127.0.0.3'); p.last_action = 0
    with pytest.raises(bridge.Unavailable): p.change('enable')


def test_unconfigured_soundbar_is_not_reported_as_zero():
    data = bridge.Protection(CFG, API()).snapshot()
    assert data['devices'][1] == {'id': 'soundbar', 'label': 'Soundbar', 'configured': False}


def test_owner_cli_uses_fixed_control_without_http_listener(monkeypatch, capsys):
    api = API()
    protection = bridge.Protection(CFG, api)
    monkeypatch.setattr(bridge, 'load_config', lambda path: CFG)
    monkeypatch.setattr(bridge, 'Protection', lambda cfg: protection)
    monkeypatch.setattr(bridge, 'Server', lambda *args: pytest.fail('CLI must not expose a listener'))
    monkeypatch.setattr('sys.argv', ['bridge.py', '--config', 'private.json', '--action', 'pause15'])
    bridge.main()
    assert json.loads(capsys.readouterr().out) == {'accepted': True}
    assert api.writes == [('/protection', {'enabled': False, 'duration': 900000})]


def test_owner_cli_reports_fixed_unknown_without_upstream_details(monkeypatch, capsys):
    class Failed:
        def snapshot(self, **kwargs):
            raise bridge.Unavailable('private upstream details')
    monkeypatch.setattr(bridge, 'load_config', lambda path: CFG)
    monkeypatch.setattr(bridge, 'Protection', lambda cfg: Failed())
    monkeypatch.setattr('sys.argv', ['bridge.py', '--config', 'private.json', '--action', 'status'])
    with pytest.raises(SystemExit) as error:
        bridge.main()
    assert error.value.code == 1
    output = capsys.readouterr().out
    assert 'private upstream details' not in output
    assert json.loads(output)['error'].startswith('Protection could not be verified')


def test_enforcement_optional_and_authenticated(http_server):
    server, api = http_server
    assert json.loads(call(server, 'GET', '/v1/enforcement')[2]) == {'schema': 1, 'ruleStatus': 'unknown'}
    assert call(server, 'GET', '/v1/enforcement', headers={'Authorization': 'Bearer wrong'})[0] == 403
    assert call(server, 'GET', '/v1/enforcement?command=anything')[0] == 404
    assert call(server, 'POST', '/v1/enforcement', '{}')[0] == 404
    assert not api.writes


def test_enforcement_stale_file_does_not_break_resolver(tmp_path):
    path = tmp_path/'counter.json';path.write_text('{}');path.chmod(0o644)
    p = bridge.Protection(dict(CFG, router_counter_file=str(path)), API())
    assert p.enforcement() == {'schema': 1, 'ruleStatus': 'unknown'}
    assert p.snapshot()['resolver'] == 'AdGuard Home'


def test_lifetime_collection_reuses_server_when_dashboard_closed(monkeypatch):
    class CounterProtection:
        def __init__(self): self.calls = 0
        def snapshot(self, force=False):
            assert force
            self.calls += 1
    clock = [1000.0]
    monkeypatch.setattr(bridge.time, 'monotonic', lambda: clock[0])
    protection = CounterProtection()
    server = bridge.Server(dict(CFG, lifetime_file='/not-accessed-by-fixture'), protection)
    try:
        server.service_actions();server.counter_worker.join(timeout=2)
        assert protection.calls == 1
        server.service_actions();assert protection.calls == 1
        clock[0] += 300
        server.service_actions();server.counter_worker.join(timeout=2)
        assert protection.calls == 2
    finally: server.server_close()
    server = bridge.Server(CFG, protection)
    try:
        server.service_actions()
        assert server.counter_worker is None and protection.calls == 2
    finally: server.server_close()
