"""Prepare a private, TV/soundbar AdGuard profile. Does not deploy or route DNS."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
from zoneinfo import ZoneInfo

IMAGE = 'adguard/adguardhome:v0.107.80@sha256:e2e1b48c832f7705be915873f95de0d5114de573736441d7f2923a8a6293027c'
LISTS = [
    {'id': 1, 'enabled': True, 'name': 'HaGeZi Light', 'url': 'https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/light.txt'},
    {'id': 2, 'enabled': True, 'name': 'HaGeZi Samsung', 'url': 'https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/native.samsung.txt'},
]
# Narrow exceptions preserve update, clock, connectivity, certificate and account paths.
# These are compatibility precautions, not a complete discovered endpoint inventory.
PRESERVE = [
    'samsungqbe.com', 'samsungqbe.cn', 'samsungapps.com',
    'account.samsung.com', 'samsungosp.com', 'smartthings.com', 'samsungiotcloud.com', 'samsungotn.net',
    'netflix.com', 'nflxvideo.net', 'nflxso.net', 'nflxext.com',
    'youtube.com', 'googlevideo.com', 'ytimg.com', 'spotify.com', 'scdn.co',
]


def configuration(tv_ip, server_ip, admin_hash, test=False, soundbar_ip=None):
    addresses = [tv_ip] + ([soundbar_ip] if soundbar_ip else [])
    if len(set(addresses)) != len(addresses):
        raise ValueError('Devices must have distinct identities')
    for value in addresses + [server_ip]:
        addr = ipaddress.ip_address(value)
        if addr.version != 4 or not addr.is_private or addr.is_unspecified:
            raise ValueError('Explicit private IPv4 addresses required')
    if not re.fullmatch(r'\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}', admin_hash):
        raise ValueError('Expected bcrypt administrator password hash')
    # Use the separate native list for Samsung ACR/advertising. No blanket Samsung parent blocks.
    rules = ['@@||' + domain + '^' for domain in PRESERVE]
    rules += ['@@||' + d + '^' for d in ['cdn.samsungcloudsolution.com', 'cdn.samsungcloudsolution.net',
              'time.samsungcloudsolution.com', 'time.samsungcloudsolution.net',
              'sas.samsungcloudsolution.com', 'sas.samsungcloudsolution.net']]
    return {
        'http': {'address': '127.0.0.1:13080', 'session_ttl': '24h'},
        'users': [{'name': 'cleanhome-admin', 'password': admin_hash}],
        'auth_attempts': 5, 'block_auth_min': 15,
        'dns': {'bind_hosts': [server_ip], 'port': 15353 if test else 53, 'ratelimit': 50,
                'allowed_clients': addresses, 'disallowed_clients': [],
                'upstream_dns': ['https://dns.quad9.net/dns-query'], 'bootstrap_dns': ['9.9.9.9', '149.112.112.112'],
                'fallback_dns': [], 'cache_size': 4194304, 'anonymize_client_ip': False,
                'use_private_ptr_resolvers': False, 'resolve_clients': False, 'hostsfile_enabled': False},
        'filtering': {'protection_enabled': True, 'filtering_enabled': True, 'blocking_mode': 'nxdomain',
                      'blocked_response_ttl': 10, 'filters_update_interval': 24,
                      'safebrowsing_enabled': False, 'parental_enabled': False, 'safe_search': {'enabled': False}},
        'filters': LISTS, 'whitelist_filters': [], 'user_rules': rules,
        'querylog': {'enabled': True, 'file_enabled': True, 'interval': '168h', 'size_memory': 1000},
        'statistics': {'enabled': True, 'interval': '168h'},
        'dhcp': {'enabled': False},
        'clients': {'persistent': [{'name': 'TV' if i == 0 else 'Soundbar', 'ids': [address], 'use_global_settings': True,
                                    'filtering_enabled': True, 'ignore_querylog': False, 'ignore_statistics': False} for i, address in enumerate(addresses)],
                    'runtime_sources': {'whois': False, 'arp': False, 'rdns': False, 'dhcp': False, 'hosts': False}},
        'log': {'enabled': True, 'verbose': False, 'file': ''}, 'schema_version': 34,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tv-ip', required=True)
    p.add_argument('--server-ip', required=True)
    p.add_argument('--soundbar-ip', help='Separately verified soundbar address; never infer it from TV pairing')
    p.add_argument('--admin-hash-file', type=Path, required=True)
    p.add_argument('--admin-password-file', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--timezone', default='UTC', help='IANA timezone for calendar-day statistics')
    p.add_argument('--test', action='store_true', help='Loopback only, alternate DNS port, no live routing')
    a = p.parse_args()
    if a.test and not all(ipaddress.ip_address(ip).is_loopback for ip in [a.tv_ip, a.server_ip] + ([a.soundbar_ip] if a.soundbar_ip else [])):
        p.error('Tests must stay on loopback')
    ZoneInfo(a.timezone)
    out = a.output.resolve()
    if out.exists():
        p.error('Output already exists; preserve the existing private profile')
    for f in (a.admin_hash_file, a.admin_password_file):
        if f.is_symlink() or f.stat().st_mode & 0o077:
            p.error('Secret inputs must be owner-only regular files')
    config = configuration(a.tv_ip, a.server_ip, a.admin_hash_file.read_text().strip(), a.test, a.soundbar_ip)
    out.mkdir(parents=True, mode=0o700)
    os.chmod(out, 0o700)
    for name in ['conf', 'work']:
        (out / name).mkdir(mode=0o700)
    token = secrets.token_urlsafe(32)
    values = {
        'conf/AdGuardHome.yaml': json.dumps(config, indent=2),
        'bridge.json': json.dumps({'tv_ip': a.tv_ip, 'soundbar_ip': a.soundbar_ip, 'bind': a.server_ip, 'port': 8768,
                                  'timezone': a.timezone, 'agh_url': 'http://127.0.0.1:13080',
                                  'agh_user': 'cleanhome-admin', 'agh_password': a.admin_password_file.read_text().strip(),
                                  'tv_token': token}, indent=2),
        'widget.json': json.dumps({'endpoint': 'http://' + a.server_ip + ':8768', 'token': token}, indent=2),
        'profile.env': 'ADGUARD_IMAGE=' + IMAGE + '\nPROFILE_DIR=' + str(out) + '\nPROFILE_UID=' + str(os.getuid()) + '\nPROFILE_GID=' + str(os.getgid()) + '\n',
    }
    for name, text in values.items():
        path = out / name
        path.write_text(text + '\n')
        path.chmod(0o600)
    print('Private profile prepared. Nothing deployed; no DNS routing changed.')


if __name__ == '__main__':
    main()
