"""Persistent since-enrolment counts survive restarts without double counting."""
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('lifetime', Path(__file__).resolve().parents[1]/'tools/dns-protection/lifetime.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
IDS = {'tv': '192.0.2.1', 'soundbar': '192.0.2.2'}
NOW = datetime(2026, 11, 20, 3, tzinfo=timezone.utc)

def row(at, client='tv'):
    return {'client': IDS[client], 'time': at.isoformat(), 'reason': 'FilteredBlackList'}

def test_enrol_restart_attribution_and_no_double_count(tmp_path):
    p = tmp_path/'state'
    assert m.update(p, [row(NOW-timedelta(seconds=1))], IDS, NOW, True)['blocked'] == 0
    rows = [row(NOW+timedelta(seconds=1)), row(NOW+timedelta(seconds=2), 'soundbar')]
    out = m.update(p, rows, IDS, NOW+timedelta(seconds=3), True)
    assert out['blocked'] == 2 and out['devices'] == {'tv': 1, 'soundbar': 1}
    before = p.stat().st_mtime_ns
    assert m.update(p, rows, IDS, NOW+timedelta(seconds=4), True) == out
    assert p.stat().st_mtime_ns == before, 'Unchanged refresh does not rewrite the counter'
    assert not p.stat().st_mode & 0o077

@pytest.mark.parametrize('gap', ['partial', 'long', 'reset'])
def test_gaps_are_persistent_lower_bounds(tmp_path, gap):
    p = tmp_path/'state';m.update(p, [], IDS, NOW, True)
    rows = [row(NOW+timedelta(seconds=1))]
    m.update(p, rows, IDS, NOW+timedelta(seconds=2), True)
    out = m.update(p, [] if gap=='reset' else rows, IDS, NOW+timedelta(days=6) if gap=='long' else NOW+timedelta(seconds=3), gap!='partial')
    assert out['blocked'] == 1 and out['complete'] is False
    assert m.update(p, rows, IDS, NOW+timedelta(days=7), True)['complete'] is False

def test_identity_change_or_corrupt_state_refused(tmp_path):
    p = tmp_path/'state';m.update(p, [], IDS, NOW, True)
    with pytest.raises(ValueError):m.update(p, [], dict(IDS, tv='192.0.2.3'), NOW, True)
    p.write_text('{}')
    with pytest.raises(KeyError):m.update(p, [], IDS, NOW, True)

def test_expired_day_counts_never_added_twice(tmp_path):
    p = tmp_path/'state';m.update(p, [], IDS, NOW, True)
    rows=[row(NOW+timedelta(seconds=1))]
    assert m.update(p, rows, IDS, NOW+timedelta(days=1), True)['blocked']==1
    assert m.update(p, rows, IDS, NOW+timedelta(days=8), True)['blocked']==1
    assert m.update(p, rows, IDS, NOW+timedelta(days=9), True)['blocked']==1


def test_log_reset_with_same_count_is_not_claimed_complete(tmp_path):
    p = tmp_path/'state';m.update(p, [], IDS, NOW, True)
    m.update(p, [row(NOW+timedelta(seconds=1))], IDS, NOW+timedelta(seconds=2), True)
    out=m.update(p, [row(NOW+timedelta(seconds=3))], IDS, NOW+timedelta(seconds=4), True)
    assert out['blocked']==1 and out['complete'] is False
