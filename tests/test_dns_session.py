"""Real HTTP session boundary: avoid password hashing per read, never replay writes."""
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dns_session_bridge', ROOT / 'tools/dns-protection/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


@pytest.fixture
def api():
    state = {'logins': 0, 'calls': [], 'session': '', 'fail_login': False,
             'redirect': False, 'no_cookie': False, 'reject_write': False, 'oversized': False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, body=b'', headers=None):
            self.send_response(code)
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            state['calls'].append(('POST', self.path, self.headers.get('Authorization')))
            if self.path == '/control/login':
                assert json.loads(body) == {'name': 'fixture-admin', 'password': 'test-only-password'}
                state['logins'] += 1
                if state['fail_login']:
                    self.reply(403)
                elif state['redirect']:
                    self.reply(302, headers={'Location': '/leak'})
                else:
                    state['session'] = 'session-' + str(state['logins'])
                    headers = {} if state['no_cookie'] else {'Set-Cookie': 'agh_session=' + state['session'] + '; Path=/; HttpOnly'}
                    self.reply(200, headers=headers)
            elif state['reject_write']:
                self.reply(401)
            else:
                assert self.headers.get('Cookie') == 'agh_session=' + state['session']
                self.reply(200)

        def do_GET(self):
            state['calls'].append(('GET', self.path, self.headers.get('Authorization')))
            if self.headers.get('Cookie') != 'agh_session=' + state['session']:
                self.reply(401)
            else:
                self.reply(200, b'x' * 2_000_001 if state['oversized'] else b'{"running":true}')

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = bridge.AdGuard({'agh_url': 'http://127.0.0.1:' + str(server.server_port),
                            'agh_user': 'fixture-admin', 'agh_password': 'test-only-password'})
    try:
        yield client, state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_repeated_reads_and_write_share_native_session_without_basic_auth(api):
    client, state = api
    for _ in range(6):
        assert client.call('/status')['running']
    assert client.call('/protection', {'enabled': True}) == {}
    assert state['logins'] == 1
    assert all(auth is None for _, _, auth in state['calls'])
    assert len(state['calls']) == 8


def test_expired_server_session_reauthenticates_one_read(api):
    client, state = api
    assert client.call('/status')['running']
    state['session'] = 'expired'
    assert client.call('/status')['running']
    assert state['logins'] == 2
    assert sum(path == '/control/status' for _, path, _ in state['calls']) == 3


def test_unauthorized_setter_is_never_replayed(api):
    client, state = api
    client.call('/status')
    state['reject_write'] = True
    with pytest.raises(bridge.Unavailable, match='Resolver unavailable'):
        client.call('/protection', {'enabled': False})
    assert state['logins'] == 1
    assert sum(path == '/control/protection' for _, path, _ in state['calls']) == 1


@pytest.mark.parametrize('failure', ['fail_login', 'redirect', 'no_cookie'])
def test_login_failure_missing_cookie_and_redirect_fail_closed(api, failure):
    client, state = api
    state[failure] = True
    with pytest.raises(bridge.Unavailable) as error:
        client.call('/status')
    assert 'fixture-admin' not in str(error.value) and 'test-only-password' not in str(error.value)
    assert state['logins'] == 1
    assert all(path == '/control/login' for _, path, _ in state['calls'])


def test_simultaneous_first_reads_authenticate_once(api):
    client, state = api
    with ThreadPoolExecutor(max_workers=6) as pool:
        assert all(pool.map(lambda _: client.call('/status')['running'], range(6)))
    assert state['logins'] == 1


def test_session_responses_keep_existing_size_bound(api):
    client, state = api
    state['oversized'] = True
    with pytest.raises(bridge.Unavailable, match='Response too large'):
        client.call('/status')
