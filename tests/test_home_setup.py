"""The companion's host/HTTP recovery boundaries; all TVs are fake."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import struct
import sys
import threading
import urllib.error
import urllib.request
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/home-setup'))
import core
spec = importlib.util.spec_from_file_location('home_companion_setup', ROOT / 'tools/home-setup/setup.py')
wizard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wizard)


def original():
    return {'Main': core.SAMSUNG, 'Strings': dict(zip(core.KEYS, [core.SAMSUNG, 'org.tizen.tv-viewer', 'example.Previous', core.SAMSUNG])), 'AutoStart': 0}


def query(home=None, last=1):
    home = home or original()
    item = lambda x: {'ok': True, 'value': x}
    return {'readOnly': True, 'uid': 901, 'target': core.TARGET, 'firmware': core.FIRMWARE, 'homeOperation': item(home['Main']), 'keys': {k: item(v) for k, v in home['Strings'].items()}, 'autostart': item(home['AutoStart']), 'lastApp': item(last), 'bootSupported': item(1)}


class TV:
    def __init__(self):
        self.home, self.last, self.actions, self.binding = original(), 1, [], hashlib.sha256(b'EXAMPLE_DUID').hexdigest()
        self.fail = None
    def transport(self, host, files): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def run(self, action, saved=None):
        self.actions.append(action)
        if action == 'query': return query(self.home, self.last)
        if action == 'apply-all':
            self.home['Main'] = core.TARGET
            self.home['Strings'][core.KEYS[0]] = core.TARGET
            self.home['AutoStart'], self.last = 1, 0
        if action == 'restore-all': self.home, self.last = copy.deepcopy(saved['home']), saved['lastApp']
        if self.fail == action: raise core.DeviceSessionError('Lost completion')
        return {'Success': True}


@pytest.fixture
def setup(tmp_path):
    store, tv = core.Store(tmp_path / 'recovery'), TV()
    return core.Companion(store, {}, tv.transport), store, tv


@pytest.mark.parametrize('address', ['127.0.0.1', '8.8.8.8', '0.0.0.0', '::1', 'https://example.com', '198.51.100.3', 'not an IP', None])
def test_refuse_non_lan_addresses(address):
    with pytest.raises(ValueError): core.private_ipv4(address)


def test_snapshot_requires_exact_profile_and_all_reads():
    for field, value in [('uid', 0), ('firmware', 'Version=UNVERIFIED;'), ('readOnly', False), ('target', 'Other.App'), ('lastApp', {'ok': False})]:
        q = query()
        q[field] = value
        with pytest.raises(ValueError): core.snapshot(q)
    q = query()
    del q['keys'][core.KEYS[-1]]
    with pytest.raises(ValueError): core.snapshot(q)


def test_identity_is_normalized_without_storing_the_duid():
    sample = 'EXAMPLE_DUID_0123456789'
    assert core.device_binding(sample) == core.device_binding('duid: '+sample+'\n')
    assert core.device_binding(sample) == hashlib.sha256(sample.encode()).hexdigest()


@pytest.mark.parametrize('output', ['', 'Unknown command', 'getduid is not supported', 'EXAMPLE_DUID_0123456789\nOTHER_DUID_9876543210'])
def test_ambiguous_or_failed_identity_refused(output):
    with pytest.raises(ValueError): core.device_binding(output)


def test_check_is_getter_only_and_does_not_save_original(setup):
    companion, store, tv = setup
    from unittest.mock import patch
    with patch.object(core, 'private_ipv4', return_value='TV_FIXTURE'):
        result = companion.perform('TV_FIXTURE', 'inspect')
    assert result['canApply'] and not result['canUndo']
    assert tv.actions == ['query'] and store.original(tv.binding) is None


def perform(companion, action):
    from unittest.mock import patch
    with patch.object(core, 'private_ipv4', return_value='TV_FIXTURE'):
        return companion.perform('TV_FIXTURE', action)


def test_apply_saves_original_before_write_and_undo_is_exact(setup):
    companion, store, tv = setup
    prior = copy.deepcopy(tv.home)
    perform(companion, 'apply')
    assert store.original(tv.binding)['home'] == prior
    assert tv.actions == ['query', 'apply-all', 'query']
    assert tv.home['Main'] == core.TARGET and tv.last == 0
    assert store.status(tv.binding)['phase'] == 'active'
    raw = store.path(tv.binding, '.original.json').read_bytes()
    assert perform(companion, 'apply')['success']
    assert tv.actions.count('apply-all') == 1
    perform(companion, 'undo')
    assert tv.home == prior and tv.last == 1
    assert store.path(tv.binding, '.original.json').read_bytes() == raw


def test_unknown_outcome_never_blindly_reapplies(setup):
    companion, store, tv = setup
    tv.fail = 'apply-all'
    with pytest.raises(core.DeviceSessionError): perform(companion, 'apply')
    assert store.status(tv.binding)['phase'] == 'unknown'
    # A full read can recognize an already-active state, but never executes again.
    perform(companion, 'apply')
    assert tv.actions.count('apply-all') == 1
    tv.home = original()
    with pytest.raises(ValueError, match='interrupted'): perform(companion, 'apply')
    tv.fail = None
    perform(companion, 'undo')
    assert store.status(tv.binding)['phase'] == 'original'


def test_no_undo_without_this_tvs_original(setup):
    companion, store, tv = setup
    with pytest.raises(ValueError, match='No original'): perform(companion, 'undo')
    assert tv.actions == ['query']


def test_already_assigned_tv_without_baseline_is_refused(setup):
    companion, store, tv = setup
    tv.home['Main'] = core.TARGET
    tv.home['Strings'][core.KEYS[0]] = core.TARGET
    with pytest.raises(ValueError): perform(companion, 'apply')
    assert store.original(tv.binding) is None and tv.actions == ['query']


def test_tampered_original_and_changed_device_are_refused(setup):
    companion, store, tv = setup
    perform(companion, 'apply')
    assert store.original(hashlib.sha256(b'OTHER_TV').hexdigest()) is None
    path = store.path(tv.binding, '.original.json')
    data = json.loads(path.read_text())
    data['original']['lastApp'] = 0
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='corrupt'): perform(companion, 'undo')
    assert 'restore-all' not in tv.actions


def test_original_is_exclusive_and_repo_storage_refused(setup):
    _, store, tv = setup
    store.save_original(tv.binding, tv.home, 1)
    with pytest.raises(FileExistsError): store.save_original(tv.binding, tv.home, 0)
    with pytest.raises(ValueError): core.Store(ROOT / '.local/unsafe-recovery')


def test_second_companion_process_lock_refused(tmp_path):
    with wizard.ProcessLock(tmp_path):
        with pytest.raises(ValueError, match='already running'):
            with wizard.ProcessLock(tmp_path): pass


def test_sdk_script_is_one_time_uid_guarded_checked_and_cleaned():
    from vendor.aerotizen import sdk
    script, command, stage, paths = sdk.build_script({'helper.dll': b'MIT test payload'}, 'helper.dll', ('--query',), '127.0.0.1', 12345, 'abcdef123456')
    assert 'test "$(id -u)" = 901' in script and 'sha256sum -c' in script
    assert 'trap ' in script and sdk.CLEANUP_MARKER in script and sdk.EXIT_PREFIX in script
    assert len(command.encode()) <= 400 and stage.endswith('.s')
    assert sdk.parse_output('{}\n'+sdk.CLEANUP_MARKER+'\n'+sdk.EXIT_PREFIX+'0\n')['staging_cleaned']
    for output in ['{}', sdk.CLEANUP_MARKER+'\n', sdk.CLEANUP_MARKER+'\n'+sdk.EXIT_PREFIX+'0\n'+sdk.EXIT_PREFIX+'0']:
        with pytest.raises(core.DeviceSessionError): sdk.parse_output(output)


def test_bounded_transport_rejects_large_frames_and_bad_checksums():
    from vendor.aerotizen.sdb import MAX_DATA, WRTE
    for payload, size, checksum in [(b'', MAX_DATA+1, 0), (b'abc', 3, 0)]:
        client = core.BoundedSdb('unused')
        left, right = socket.socketpair()
        client.sock = left
        try:
            right.sendall(struct.pack('<6I', WRTE, 1, 1, size, checksum, WRTE ^ 0xFFFFFFFF)+payload)
            with pytest.raises(core.DeviceSessionError): client._recv()
        finally: left.close(); right.close()


def test_bounded_sdb_roundtrip_upload_and_shell_share_one_session(fake_tv):
    tv = fake_tv({'0 getduid': 'EXAMPLE_DUID_0123456789'})
    client = core.BoundedSdb('127.0.0.1')
    client.port = tv.port
    with client.connect(attempts=1):
        data = b'helper-checksum-fixture' * 5000
        client.push(data, '/home/owner/share/tmp/sdk_tools/test-fixture.dll')
        assert client.shell_bounded('0 getduid', 2) == 'EXAMPLE_DUID_0123456789'
    assert tv.uploads['/home/owner/share/tmp/sdk_tools/test-fixture.dll'] == data


@pytest.mark.parametrize('clean', [True, False])
def test_sdk_callback_roundtrip_requires_confirmed_cleanup(clean):
    from vendor.aerotizen import sdk
    import re
    class Session:
        host = '127.0.0.1'
        uploads = {}
        def push(self, data, path): self.uploads[path] = data
        def shell_bounded(self, command, seconds, limit):
            script = next(data.decode() for path, data in self.uploads.items() if path.endswith('.s'))
            match = re.search(r'exec 3<>/dev/tcp/([^/]+)/([0-9]+)', script)
            output = '{"readOnly":true}\n'
            if clean: output += sdk.CLEANUP_MARKER+'\n'+sdk.EXIT_PREFIX+'0\n'
            with socket.create_connection((match[1], int(match[2])), timeout=2) as connection:
                connection.sendall(output.encode())
            return ''
    session = Session()
    if clean:
        result = sdk.run(session, {'query.dll': b'test payload'}, 'query.dll', ('--query',))
        assert result['exit_code'] == 0 and result['staging_cleaned']
    else:
        with pytest.raises(core.DeviceSessionError, match='cleanup'):
            sdk.run(session, {'query.dll': b'test payload'}, 'query.dll', ('--query',))


def test_local_wizard_requires_token_origin_and_explicit_confirmation():
    class FakeCompanion:
        calls = []
        error = None
        def perform(self, host, action):
            self.calls.append((host, action))
            if self.error: raise self.error
            return {'success': True}
    fake = FakeCompanion()
    server = wizard.create_server(fake)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = 'http://127.0.0.1:'+str(server.server_port)
    try:
        html = urllib.request.urlopen(url).read().decode()
        assert 'Network Status → IP Settings' in html and 'TV’s local IP' in html
        import re
        token = re.search(r'nonce="([a-f0-9]+)"', html)[1]
        for headers, confirmed in [({}, True), ({'X-Clean-Home': token, 'Origin': 'https://example.com'}, True), ({'X-Clean-Home': token}, False)]:
            body = json.dumps({'host': 'TV_FIXTURE', 'action': 'apply', 'confirmed': confirmed}).encode()
            request = urllib.request.Request(url+'/action', data=body, headers={'Content-Type': 'application/json', **headers})
            with pytest.raises(urllib.error.HTTPError): urllib.request.urlopen(request)
        assert not fake.calls
        request = urllib.request.Request(url+'/action', data=json.dumps({'host': 'TV_FIXTURE', 'action': 'inspect', 'confirmed': False}).encode(), headers={'Content-Type':'application/json','X-Clean-Home':token})
        assert json.load(urllib.request.urlopen(request))['success']
        assert fake.calls == [('TV_FIXTURE','inspect')]
        # Base SDB errors include refused handshakes/transfers and must not leak
        # native output or leave the operation lock held after returning JSON.
        from vendor.aerotizen.sdb import SdbError
        for error_type in (SdbError, core.DeviceSessionError):
            fake.error = error_type('PRIVATE_NATIVE_OUTPUT')
            with pytest.raises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request)
            assert caught.value.code == 400
            message = json.load(caught.value)['error']
            assert 'PRIVATE_NATIVE_OUTPUT' not in message
            assert 'Keep the recovery folder' in message and 'Host PC address' in message
        fake.error = None
        assert json.load(urllib.request.urlopen(request))['success']
    finally: server.shutdown(); server.server_close(); thread.join(2)
