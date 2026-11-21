"""Inject an optional private DNS capability into a local-only widget build."""
import ipaddress
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def runtime_overlay(profile_path, existing=None):
    path = Path(profile_path)
    if path.is_symlink() or not path.is_file() or (os.name == 'posix' and path.stat().st_mode & 0o077):
        raise ValueError('DNS profile must be a regular owner-only file (0600).')
    try:
        profile = json.loads(path.read_text())
        if not isinstance(profile, dict) or set(profile) != {'endpoint', 'token'}:
            raise ValueError('Unexpected profile fields')
        endpoint = urlsplit(profile['endpoint'])
        address = ipaddress.ip_address(endpoint.hostname or '')
        valid = (address.version == 4 and address.is_private and not address.is_unspecified
                 and endpoint.port is not None and 1024 <= endpoint.port <= 65535
                 and endpoint.scheme == 'http' and not endpoint.username
                 and not endpoint.path and not endpoint.query and not endpoint.fragment
                 and re.fullmatch(r'[A-Za-z0-9_-]{32,128}', profile['token']))
    except (ValueError, TypeError, KeyError):
        valid = False
    if not valid:
        raise ValueError('Expected only a private IPv4 HTTP endpoint and limited TV capability token.')
    overlay = dict(existing or {})
    base = overlay.get('device-config.js', (ROOT / 'app/device-config.js').read_bytes())
    overlay['device-config.js'] = base + ('\nwindow.CleanHomeConfig.dnsProtection = ' + json.dumps(profile, sort_keys=True) + ';\n').encode()
    manifest = (ROOT / 'app/config.xml').read_text()
    overlay['config.xml'] = manifest.replace('</widget>', '  <access origin="' + profile['endpoint'] + '" subdomains="false"/>\n</widget>').encode()
    return overlay
