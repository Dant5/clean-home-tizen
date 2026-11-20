"""Counter export is optional and never merges packet counters with DNS totals."""
from datetime import datetime, timezone, timedelta
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('router_counters', Path(__file__).resolve().parents[1]/'tools/dns-protection/router_counters.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
IP = '192.0.2.25'
RULES = '\n'.join('[%s:240] -A FORWARD -s %s/32 -i br0 -o eth0 -p %s -m %s --dport 53 -j DROP' % (n, IP, proto, proto) for proto, n in [('udp', 7), ('tcp', 4)])


def test_exact_rule_counts_and_no_raw_data(tmp_path):
    value = m.parse_counters(RULES, IP)
    assert value['udpPackets'] == 7 and value['tcpPackets'] == 4
    assert IP not in json.dumps(value) and 'DROP' not in json.dumps(value)
    p = tmp_path/'counters.json'; p.write_text(json.dumps(value)); p.chmod(0o644)
    assert m.read_snapshot(p) == value


@pytest.mark.parametrize('raw', [RULES.splitlines()[0], RULES+'\n'+RULES, RULES.replace('--dport 53', '--dport 853'), RULES.replace(IP, '192.0.2.26'), RULES.replace('DROP', 'ACCEPT'), RULES.replace('-o eth0', '-o eth1')])
def test_missing_duplicate_changed_scope_is_unknown(raw):
    with pytest.raises(ValueError): m.parse_counters(raw, IP)


@pytest.mark.parametrize('change', ['stale', 'future', 'negative', 'boolean', 'extra', 'writable', 'symlink'])
def test_untrusted_snapshots_refused(tmp_path, change):
    value = m.parse_counters(RULES, IP)
    now = datetime.now(timezone.utc)
    if change in ('stale','future'): value['sampledAt'] = (now+timedelta(seconds=-361 if change=='stale' else 6)).isoformat()
    if change == 'negative': value['udpPackets'] = -1
    if change == 'boolean': value['tcpPackets'] = True
    if change == 'extra': value['raw'] = 'private data'
    p = tmp_path/'counters';p.write_text(json.dumps(value));p.chmod(0o666 if change=='writable' else 0o644)
    if change == 'symlink': q=tmp_path/'link';q.symlink_to(p);p=q
    with pytest.raises(ValueError): m.read_snapshot(p, now)
