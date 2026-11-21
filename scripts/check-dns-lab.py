"""Opt-in integration test against the loopback-only AdGuard lab, never a TV."""
import argparse
import importlib.util
import json
from pathlib import Path
import socket
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dns_bridge', ROOT / 'tools/dns-protection/bridge.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def query(domain, source='127.0.0.2', tcp=False, port=15353):
    name = b''.join(bytes([len(part)]) + part.encode('ascii') for part in domain.split('.')) + b'\0'
    packet = struct.pack('!6H', 0x2345, 0x0100, 1, 0, 0, 0) + name + struct.pack('!2H', 1, 1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM if tcp else socket.SOCK_DGRAM) as sock:
        sock.settimeout(8); sock.bind((source, 0))
        try:
            if tcp:
                sock.connect(('127.0.0.1', port)); sock.sendall(struct.pack('!H', len(packet)) + packet)
                length = sock.recv(2)
                if len(length) != 2: return None
                data = sock.recv(struct.unpack('!H', length)[0])
            else:
                sock.sendto(packet, ('127.0.0.1', port)); data, _ = sock.recvfrom(4096)
        except (TimeoutError, ConnectionResetError):
            return None
    if len(data) < 12: return None
    ident, flags, questions, answers, _, _ = struct.unpack('!6H', data[:12])
    assert ident == 0x2345 and flags & 0x8000
    return {'rcode': flags & 15, 'answers': answers}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', type=Path, required=True)
    a = p.parse_args(); cfg = m.load_config(a.profile / 'bridge.json')
    if cfg['tv_ip'] != '127.0.0.2' or cfg['bind'] != '127.0.0.1':
        raise SystemExit('Refusing a non-lab profile')
    api = m.AdGuard(cfg); protection = m.Protection(cfg, api)
    checks = []
    def check(name, result):
        assert result, name
        checks.append(name); print('PASS', name)
    for attempt in range(60):
        try:
            protection.guard(); break
        except m.Unavailable:
            time.sleep(1)
    else: raise AssertionError('Resolver/lists did not become ready')
    check('Dedicated client scope and lists loaded', bool(protection.guard()))
    normal = query('example.org')
    check('Real upstream resolution over UDP', normal and normal['rcode'] == 0 and normal['answers'] > 0)
    blocked = query('rtb-config.samsungads.com')
    check('Samsung advertising domain blocked', blocked and blocked['rcode'] == 3)
    check('TCP DNS filtering', query('acr-au-prd.samsungcloud.tv', tcp=True)['rcode'] == 3)
    check('Unapproved loopback client denied', query('example.org', source='127.0.0.4') in (None, {'rcode': 5, 'answers': 0}))
    # Check resolver policy, not availability of legacy/region-specific endpoints.
    preserve = ['sas.samsungcloudsolution.com', 'cdn.samsungcloudsolution.com', 'time.samsungcloudsolution.com',
                'svdca.samsungqbe.com', 'account.samsung.com', 'www.netflix.com', 'www.youtube.com', 'www.spotify.com', 'api.smartthings.com', 'samsungotn.net']
    from urllib.parse import urlencode
    for domain in preserve:
        result = api.call('/filtering/check_host?' + urlencode({'name': domain, 'client': cfg['tv_ip']}))
        check('Preserve policy: ' + domain, not result['reason'].startswith('Filtered'))
    if cfg.get('soundbar_ip'):
        check('Independent soundbar test-client resolution', query('example.org', source=cfg['soundbar_ip'])['answers'] > 0)
        check('Independent soundbar test-client blocking', query('acr-au-prd.samsungcloud.tv', source=cfg['soundbar_ip'])['rcode'] == 3)
    try:
        protection.change('pause15')
        check('Pause has a real resolver expiry', bool(api.call('/dns_info').get('protection_disabled_until')))
        result = query('rtb-config.samsungads.com')
        check('Paused query no longer blocked by filter', result and result['rcode'] != 3)
    finally:
        protection.last_action = 0; protection.change('enable')
    check('Resume restores blocking', query('rtb-config.samsungads.com')['rcode'] == 3)
    data = protection.snapshot(force=True)
    check('Real log has only attributed test client totals', data['today']['queries'] >= 5 and data['today']['blocked'] >= 3)
    check('Observed encrypted upstream replies', data['observedUpstreamTransport'].get('Encrypted', 0) > 0)
    if cfg.get('soundbar_ip'):
        tv, soundbar = data['devices']
        check('Separate real log totals sum to combined total', tv['today']['queries'] + soundbar['today']['queries'] == data['today']['queries'])
        check('Soundbar has separately attributed requests', soundbar['today']['queries'] >= 2 and soundbar['today']['blocked'] >= 1)
    # Shortened native timer exercises expiry without waiting for the UI's 15 min pause.
    api.call('/protection', {'enabled': False, 'duration': 1000})
    time.sleep(2)
    check('Native pause expires without the widget running', api.call('/dns_info')['protection_enabled'] is True)
    check('No claim of full DNS coverage', 'not been ruled out' in data['coverage'])
    report = {'scope': 'Real loopback AdGuard integration with synthetic DNS requests; NOT TV traffic or physical streaming validation',
              'checks': checks, 'snapshot': data, 'version': api.call('/status')['version']}
    (a.profile / 'test-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(len(checks), 'real resolver integration checks passed')


if __name__ == '__main__': main()
