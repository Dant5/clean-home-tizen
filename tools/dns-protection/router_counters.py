"""On-demand, read-only export of audited ASUS port-53 DROP counters.

Run as the owner with existing router-admin access, never as the TV adapter.
Only the sanitised snapshot is shared with the unprivileged dashboard service.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def parse_counters(raw, tv_ip, lan='br0', wan='eth0'):
    ip = str(ipaddress.IPv4Address(tv_ip))
    if any(not re.fullmatch(r'[A-Za-z0-9_.-]{1,16}', name) for name in (lan, wan)):
        raise ValueError('Invalid interface')
    found = {}
    # Exact audited rule shape only. Missing, duplicate or altered rules are unknown.
    pattern = (r'\[(\d+):(\d+)\] -A FORWARD -s ' + re.escape(ip)
               + r'/32 -i ' + re.escape(lan) + ' -o ' + re.escape(wan)
               + r' -p (udp|tcp) -m \3 --dport 53 -j DROP')
    for line in raw.splitlines():
        match = re.fullmatch(pattern, line)
        if match:
            proto = match[3]
            if proto in found:
                raise ValueError('Ambiguous duplicate rule')
            found[proto] = int(match[1])
    if set(found) != {'udp', 'tcp'}:
        raise ValueError('Both audited rules are required')
    return {'schema': 1, 'sampledAt': datetime.now(timezone.utc).isoformat(),
            'device': 'tv', 'ruleStatus': 'present', 'udpPackets': found['udp'],
            'tcpPackets': found['tcp'], 'period': 'current-router-counters'}


def read_snapshot(path, now=None):
    """Refuse stale/future/untrusted shapes; never return raw firewall data."""
    now = now or datetime.now(timezone.utc)
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > 2048 or p.stat().st_mode & 0o022:
        raise ValueError('Unsafe counter snapshot')
    data = json.loads(p.read_text())
    required = {'schema', 'sampledAt', 'device', 'ruleStatus', 'udpPackets', 'tcpPackets', 'period'}
    if set(data) != required or data['schema'] != 1 or data['device'] != 'tv' or data['ruleStatus'] != 'present' or data['period'] != 'current-router-counters':
        raise ValueError('Invalid counter snapshot')
    at = datetime.fromisoformat(data['sampledAt'])
    if at.tzinfo is None or not -5 <= (now-at).total_seconds() <= 120:
        raise ValueError('Counter snapshot is stale or future-dated')
    if any(type(data[k]) is not int or not 0 <= data[k] <= 2**64-1 for k in ('udpPackets', 'tcpPackets')):
        raise ValueError('Invalid packet counts')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tv-ip', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    ipaddress.IPv4Address(args.tv_ip)
    # No caller-supplied command, shell, remote action or management endpoint.
    result = subprocess.run([str(Path.home()/'.local/bin/router-admin'), 'firewall'],
                            capture_output=True, text=True, timeout=25, check=True)
    if len(result.stdout) > 2_000_000:
        raise ValueError('Router response too large')
    value = parse_counters(result.stdout, args.tv_ip)
    # Parent is owner-managed; publish atomically, no key/profile in this file.
    parent = args.output.parent
    if parent.is_symlink() or parent.stat().st_mode & 0o022:
        raise ValueError('Output directory must not be group/world writable')
    fd, temporary = tempfile.mkstemp(prefix='.router-counters-', dir=parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream)
        os.chmod(temporary, 0o644)
        os.replace(temporary, args.output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == '__main__':
    main()
