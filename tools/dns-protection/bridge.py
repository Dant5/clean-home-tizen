"""TV/soundbar-only, bounded AdGuard Home adapter. No DNS implementation or generic proxy."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timedelta, timezone
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import re
import socket
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler, Request
from zoneinfo import ZoneInfo

MAX_RECORDS = 20000
PAGE = 500
BLOCK_REASONS = {
    'FilteredBlackList': 'Blocklist', 'FilteredSafeBrowsing': 'Malware protection',
    'FilteredParental': 'Parental filter', 'FilteredBlockedService': 'Blocked service',
    'FilteredInvalid': 'Invalid request', 'FilteredSafeSearch': 'Safe search',
}
DOMAIN = re.compile(r'(?=.{1,253}\Z)[a-z0-9_](?:[a-z0-9_.-]*[a-z0-9_])?\Z', re.I)


class Unavailable(Exception):
    """Fail closed for controls, without leaking upstream details."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Unavailable('Redirect refused')


def stamp(value):
    if not isinstance(value, str):
        raise ValueError('Missing timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp lacks timezone')
    return parsed.astimezone(timezone.utc)


def load_config(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
        raise ValueError('Use a regular owner-only configuration file (0600)')
    cfg = json.loads(path.read_text())
    for key in ('tv_ip', 'bind', 'agh_url', 'agh_user', 'agh_password', 'tv_token', 'timezone'):
        if not isinstance(cfg.get(key), str) or not cfg[key]:
            raise ValueError('Missing configuration field: ' + key)
    for key in ('tv_ip', 'bind') + (('soundbar_ip',) if cfg.get('soundbar_ip') else ()):
        addr = ipaddress.ip_address(cfg[key])
        if addr.version != 4 or not (addr.is_private or addr.is_loopback) or addr.is_unspecified:
            raise ValueError('Use explicit private IPv4 addresses')
    if cfg.get('soundbar_ip') == cfg['tv_ip']:
        raise ValueError('TV and soundbar must have distinct identities')
    parsed = urlsplit(cfg['agh_url'])
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('AdGuard administration must be on IPv4 loopback, without a path')
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,128}', cfg['tv_token']):
        raise ValueError('Use a separate random TV capability token')
    ZoneInfo(cfg['timezone'])
    cfg['port'] = int(cfg.get('port', 8768))
    if not 1024 <= cfg['port'] <= 65535:
        raise ValueError('Invalid unprivileged port')
    return cfg


class AdGuard:
    def __init__(self, cfg):
        self.base = cfg['agh_url'] + '/control'
        credential = (cfg['agh_user'] + ':' + cfg['agh_password']).encode()
        self.auth = 'Basic ' + base64.b64encode(credential).decode()
        self.opener = build_opener(NoRedirect(), ProxyHandler({}))

    def call(self, path, data=None):
        # Paths are constants chosen below, never provided by an HTTP caller.
        request = Request(self.base + path, data=None if data is None else json.dumps(data).encode(),
                          headers={'Authorization': self.auth, 'Content-Type': 'application/json'})
        try:
            with self.opener.open(request, timeout=4) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise Unavailable('Response too large')
                value = {} if data is not None else json.loads(raw) if raw.strip() else {}
                if not isinstance(value, dict):
                    raise Unavailable('Invalid resolver response')
                return value
        except (OSError, ValueError, HTTPError) as exc:
            raise Unavailable('Resolver unavailable') from exc


def aggregate(records, client_ips, now, tz, filters, complete, names=None):
    """Derive local calendar-day counts; never label rolling 24h as 'today'."""
    allowed = {client_ips} if isinstance(client_ips, str) else set(client_ips)
    names = names or {}
    today = now.astimezone(tz).date()
    days = [{'date': (today - timedelta(days=6-i)).isoformat(), 'queries': 0, 'blocked': 0} for i in range(7)]
    buckets = {d['date']: d for d in days}
    domains = Counter()
    domains_today = Counter()
    recent = []
    protocols = Counter()
    upstreams = Counter()
    invalid = 0
    newest = None
    for item in records:
        if not isinstance(item, dict):
            invalid += 1
            continue
        if item.get('client') not in allowed:
            continue
        try:
            at = stamp(item['time'])
            if at > now + timedelta(minutes=1):
                raise ValueError('Future timestamp')
        except (KeyError, ValueError, TypeError, OverflowError):
            invalid += 1
            continue
        key = at.astimezone(tz).date().isoformat()
        if key not in buckets:
            continue
        newest = max(newest, at) if newest else at
        day = buckets[key]
        day['queries'] += 1
        protocols[str(item.get('client_proto', ''))] += 1
        upstream = item.get('upstream', '')
        if isinstance(upstream, str) and upstream:
            upstreams['Encrypted' if upstream.startswith(('https://', 'tls://', 'quic://')) else 'Plain DNS'] += 1
        reason = item.get('reason')
        if reason not in BLOCK_REASONS:
            continue
        day['blocked'] += 1
        domain = item.get('question', {}).get('name', '').rstrip('.').lower()
        if not DOMAIN.fullmatch(domain):
            domain = '(domain unavailable)'
        domains[domain] += 1
        if key == today.isoformat():
            domains_today[domain] += 1
        sources = []
        for rule in item.get('rules', [])[:5]:
            name = filters.get(rule.get('filter_list_id'))
            if name and name not in sources:
                sources.append(name)
        recent.append({'device': names.get(item['client'], 'TV'), 'domain': domain, 'time': at.isoformat(), 'reason': BLOCK_REASONS[reason],
                       'source': ', '.join(sources) or 'AdGuard Home', 'category': 'Not provided by list'})
    recent.sort(key=lambda row: row['time'], reverse=True)
    count, blocked = days[-1]['queries'], days[-1]['blocked']
    return {'today': {'queries': count, 'blocked': blocked, 'percent': round(100 * blocked / count, 1) if count else 0},
            'days': days, 'top': [{'domain': domain, 'count': count} for domain, count in domains.most_common(5)],
            'topToday': [{'domain': domain, 'count': count} for domain, count in domains_today.most_common(3)],
            'recent': recent[:12], 'complete': complete and not invalid, 'invalidRecords': invalid,
            'lastQueryAt': newest.isoformat() if newest else None,
            'observedClientProtocols': dict(protocols), 'observedUpstreamTransport': dict(upstreams)}


class Protection:
    def __init__(self, cfg, api=None):
        self.cfg = cfg
        self.api = api or AdGuard(cfg)
        self.lock = threading.Lock()
        self.cached = None
        self.cache_at = 0.0
        self.last_action = 0.0

    def guard(self):
        if self.api.call('/status').get('running') is not True:
            raise Unavailable('DNS listener is not running')
        access = self.api.call('/access/list')
        expected = {self.cfg['tv_ip']}
        if self.cfg.get('soundbar_ip'):
            expected.add(self.cfg['soundbar_ip'])
        if set(access.get('allowed_clients', [])) != expected or access.get('disallowed_clients'):
            raise Unavailable('TV/soundbar scope is not configured; controls locked')
        clients = self.api.call('/clients')
        persistent = clients.get('clients', [])
        # Per-client exceptions could contradict the protection switch.
        if not isinstance(persistent, list) or any(not isinstance(c, dict) or not isinstance(c.get('ids'), list) or len(c['ids']) != 1 or c['ids'][0] not in expected or not c.get('use_global_settings', True) or c.get('ignore_querylog') for c in persistent):
            raise Unavailable('Unexpected client settings; controls locked')
        dns = self.api.call('/dns_info')
        filtering = self.api.call('/filtering/status')
        log = self.api.call('/querylog/config')
        if not log.get('enabled') or log.get('anonymize_client_ip') or log.get('ignored'):
            raise Unavailable('TV-attributed query logging is unavailable')
        if not filtering.get('enabled') or not any(f.get('enabled') and f.get('rules_count', 0) for f in filtering.get('filters', [])):
            raise Unavailable('No active blocklist; controls locked')
        return dns, filtering

    def snapshot(self, force=False):
        with self.lock:
            if not force and self.cached and time.monotonic() - self.cache_at < 30:
                return self.cached
            dns, filtering = self.guard()
            now = datetime.now(timezone.utc)
            tz = ZoneInfo(self.cfg['timezone'])
            start = datetime.combine(now.astimezone(tz).date() - timedelta(days=6), datetime.min.time(), tzinfo=tz)
            rows, cursor, complete = [], '', True
            deadline = time.monotonic() + 12
            while len(rows) < MAX_RECORDS and time.monotonic() < deadline:
                query = {'limit': PAGE}
                if cursor:
                    query['older_than'] = cursor
                page = self.api.call('/querylog?' + urlencode(query)).get('data', [])
                if not isinstance(page, list):
                    raise Unavailable('Invalid query log')
                rows.extend(page)
                if not page or len(page) < PAGE:
                    break
                try:
                    oldest = stamp(page[-1]['time'])
                except (KeyError, ValueError, TypeError):
                    complete = False
                    break
                if oldest < start:
                    break
                next_cursor = page[-1]['time']
                if next_cursor == cursor:
                    complete = False
                    break
                cursor = next_cursor
            else:
                complete = False
            filters = {f['id']: str(f.get('name', 'Blocklist'))[:80] for f in filtering.get('filters', [])}
            identities = {'tv': self.cfg['tv_ip']}
            if self.cfg.get('soundbar_ip'):
                identities['soundbar'] = self.cfg['soundbar_ip']
            names = {value: 'TV' if key == 'tv' else 'Soundbar' for key, value in identities.items()}
            result = aggregate(rows, list(identities.values()), now, tz, filters, complete, names)
            result['devices'] = []
            for key, label in [('tv', 'TV'), ('soundbar', 'Soundbar')]:
                if key in identities:
                    stats = aggregate(rows, identities[key], now, tz, filters, complete, names)
                    result['devices'].append({'id': key, 'label': label, 'configured': True, **stats})
                else:
                    result['devices'].append({'id': key, 'label': label, 'configured': False})
            # Log retention and start-of-service are not proof of seven complete days.
            result.update({'schema': 1, 'sampledAt': now.isoformat(), 'timezone': self.cfg['timezone'],
                           'protectionEnabled': dns.get('protection_enabled') is True,
                           'pausedUntil': dns.get('protection_disabled_until'),
                           'scope': 'Dedicated TV / soundbar resolver', 'coverage': 'Other DNS paths have not been ruled out',
                           'history': 'Available query log only; missing history is not zero activity',
                           'resolver': 'AdGuard Home', 'filters': list(filters.values()),
                           'listsUpdatedAt': [f.get('last_updated') for f in filtering.get('filters', []) if f.get('enabled')]})
            self.cached, self.cache_at = result, time.monotonic()
            return result

    def change(self, action):
        choices = {'enable': {'enabled': True}, 'disable': {'enabled': False},
                   'pause15': {'enabled': False, 'duration': 900000}, 'pause60': {'enabled': False, 'duration': 3600000}}
        if action not in choices:
            raise ValueError('Unsupported action')
        with self.lock:
            if self.last_action and time.monotonic() - self.last_action < 2:
                raise Unavailable('Please wait before changing protection again')
            self.guard()  # Fresh scope check immediately before every setter.
            self.api.call('/protection', choices[action])
            self.cached = None
            self.last_action = time.monotonic()
            readback = self.api.call('/dns_info')
            if readback.get('protection_enabled') is not choices[action]['enabled']:
                raise Unavailable('Protection change could not be confirmed')
        return {'accepted': True}


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, cfg, protection):
        self.cfg, self.protection = cfg, protection
        self.slots = threading.BoundedSemaphore(8)
        super().__init__((cfg['bind'], cfg['port']), Handler)

    def handle_error(self, request, client_address):
        pass  # Avoid default traceback logs containing client addresses or private data.

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        super().process_request(request, address)

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    server_version = 'CleanHomePrivacy'

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format, *args):
        pass  # Do not write client addresses, tokens or queried domains to HTTP logs.

    def reply(self, code, value=None):
        data = json.dumps(value or {}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if self.headers.get('Origin') == 'null':
            self.send_header('Access-Control-Allow-Origin', 'null')
            self.send_header('Vary', 'Origin')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(data)

    def permitted(self, token=True):
        cfg = self.server.cfg
        host = f"{cfg['bind']}:{self.server.server_address[1]}"
        if self.client_address[0] != cfg['tv_ip'] or self.headers.get('Host') != host:
            return False
        if self.headers.get('Origin') not in (None, 'null'):
            return False
        return not token or hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + cfg['tv_token'])

    def do_OPTIONS(self):
        if self.path not in ('/v1/status', '/v1/protection') or not self.permitted(token=False):
            self.reply(403)
            return
        if self.headers.get('Access-Control-Request-Method') not in ('GET', 'POST'):
            self.reply(403)
            return
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', 'null')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'authorization, content-type')
        self.send_header('Access-Control-Max-Age', '300')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health' and self.client_address[0] in ('127.0.0.1', self.server.cfg['bind']):
            try:
                self.server.protection.guard()
                self.reply(200, {'status': 'UP'})
            except Unavailable:
                self.reply(503, {'status': 'DOWN'})
            return
        if not self.permitted():
            self.reply(403)
            return
        if self.path != '/v1/status':
            self.reply(404)
            return
        try:
            self.reply(200, self.server.protection.snapshot())
        except (Unavailable, ValueError, KeyError, TypeError):
            self.reply(503, {'error': 'Protection cannot be verified. Check the local resolver.'})

    def do_POST(self):
        if not self.permitted():
            self.reply(403)
            return
        if self.path != '/v1/protection':
            self.reply(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 128 or self.headers.get('Content-Type') != 'application/json' or self.headers.get('Transfer-Encoding'):
                raise ValueError('Invalid body')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict) or set(body) != {'action'} or not isinstance(body['action'], str):
                raise ValueError('Invalid command')
            self.reply(200, self.server.protection.change(body['action']))
        except (ValueError, TypeError):
            self.reply(400)
        except (Unavailable, socket.timeout):
            self.reply(503, {'error': 'Change not confirmed. Refresh before trying again.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--action', choices=['status', 'enable', 'disable', 'pause15', 'pause60'],
                        help='Owner-local recovery control; never starts an HTTP listener')
    args = parser.parse_args()
    cfg = load_config(args.config)
    protection = Protection(cfg)
    if args.action:
        try:
            if args.action == 'status':
                result = protection.snapshot(force=True)
                print(json.dumps({key: result[key] for key in ('protectionEnabled', 'pausedUntil', 'today', 'coverage')}))
            else:
                print(json.dumps(protection.change(args.action)))
        except Unavailable:
            print(json.dumps({'error': 'Protection could not be verified. No confirmed change.'}))
            raise SystemExit(1)
        return
    Server(cfg, protection).serve_forever(poll_interval=0.5)


if __name__ == '__main__':
    main()
