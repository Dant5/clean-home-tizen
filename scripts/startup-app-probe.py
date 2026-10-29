"""Bounded read-only app preflight for HA. Config is base64 JSON, never shell text.

No daemon, TV launch/control, credentials or private app-data access. Parallel
metadata reads keep the last check close to the actual launch decision.
"""
import base64
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import json
import re
import os
import signal
import sys
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

HOME_ID = 'D5Q60BHome.CleanHome'


def probe(host, app_id, opener=urlopen):
    url = 'http://' + host + ':8001/api/v2/applications/' + quote(app_id, safe='')
    try:
        with opener(url, timeout=2) as response:
            data = json.loads(response.read(65537))
        if not isinstance(data, dict) or not isinstance(data.get('visible'), bool):
            return None
        return data['visible']
    except HTTPError as error:
        return False if error.code == 404 and app_id != HOME_ID else None
    except (OSError, ValueError, TypeError):
        return None


def assess(config, reader=probe):
    address = ipaddress.IPv4Address(config['host'])
    if not address.is_private or address.is_unspecified or address.is_multicast:
        raise ValueError('Use the TV local IPv4 address')
    app_ids = config['protected_app_ids']
    if not isinstance(app_ids, list) or not 1 <= len(app_ids) <= 32:
        raise ValueError('Provide 1..32 verified consumer REST IDs')
    if any(not isinstance(i, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', i) or i == HOME_ID for i in app_ids):
        raise ValueError('Invalid protected application ID')
    parallel_home = config.get('parallel_home_check', False)
    if not isinstance(parallel_home, bool):
        raise ValueError('parallel_home_check must be a boolean')
    app_ids = list(dict.fromkeys(app_ids))
    started = time.monotonic()
    if parallel_home:
        # Opt-in startup experiment: overlap our status read with the
        # consumer reads. All requests share the same eight-worker budget.
        with ThreadPoolExecutor(max_workers=min(8, len(app_ids) + 1)) as pool:
            statuses = list(pool.map(lambda app: reader(str(address), app), [HOME_ID] + app_ids))
        home, values = statuses[0], statuses[1:]
    else:
        home = reader(str(address), HOME_ID)
        if home is True:
            values = []
        elif home is False:
            with ThreadPoolExecutor(max_workers=min(8, len(app_ids))) as pool:
                values = list(pool.map(lambda app: reader(str(address), app), app_ids))
        else:
            values = [None]
    return {'home_visible': home is True,
            'safe_to_launch': home is False and all(v is False for v in values),
            'protected_visible': any(v is True for v in values),
            'visible_app_ids': [app for app, visible in zip(app_ids, values) if visible is True],
            'unknown_status': home is None or any(v is None for v in values),
            'checked_apps': len(values), 'elapsed_ms': round((time.monotonic() - started) * 1000)}


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2 or len(sys.argv[1]) > 16384:
            raise ValueError('Expected one bounded base64 JSON argument')
        if hasattr(signal, 'SIGALRM'):
            def deadline(signum, frame):
                print(json.dumps({'safe_to_launch': False, 'unknown_status': True}));sys.stdout.flush();os._exit(1)
            signal.signal(signal.SIGALRM, deadline)
            signal.alarm(12)
        config = json.loads(base64.b64decode(sys.argv[1], validate=True))
        print(json.dumps(assess(config)))
    except (ValueError, KeyError, TypeError, TimeoutError):
        print(json.dumps({'safe_to_launch': False, 'unknown_status': True}))
        sys.exit(1)
