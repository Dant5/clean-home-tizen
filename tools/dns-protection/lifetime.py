"""Small durable counter since enrolment; gaps remain explicit lower bounds.

Updated by the existing adapter and dashboard reads. No domain log copy.
"""
from datetime import datetime, timedelta, timezone
import json
import fcntl
import os
from pathlib import Path
import tempfile


BLOCKED_REASONS = {'FilteredBlackList', 'FilteredSafeBrowsing', 'FilteredParental', 'FilteredBlockedService', 'FilteredInvalid', 'FilteredSafeSearch'}

def update(path, rows, identities, now, complete):
    p = Path(path)
    if p.parent.is_symlink() or p.parent.stat().st_mode & 0o022:
        raise ValueError('Unsafe lifetime directory')
    fd = os.open(p.with_suffix('.lock'), os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _update(path, rows, identities, now, complete)


def _update(path, rows, identities, now, complete):
    p = Path(path)
    if p.is_symlink() or p.parent.is_symlink() or p.parent.stat().st_mode & 0o022:
        raise ValueError('Unsafe lifetime storage')
    original = None
    if p.exists():
        if p.stat().st_mode & 0o077 or p.stat().st_size > 32768:
            raise ValueError('Unsafe lifetime state')
        original = p.read_text()
        state = json.loads(original)
        if state['schema'] != 1 or state['identities'] != identities:
            raise ValueError('Counter identity changed')
        if set(state['totals']) != set(identities) or any(type(v) is not int or v < 0 for v in state['totals'].values()) or type(state['complete']) is not bool:
            raise ValueError('Invalid totals')
        if not isinstance(state['days'], dict) or len(state['days']) > 7:
            raise ValueError('Invalid day counters')
        for day, counts in state['days'].items():
            datetime.fromisoformat(day)
            if set(counts) != set(identities) or any(type(v) is not int or not 0 <= v <= state['totals'][k] for k, v in counts.items()):
                raise ValueError('Invalid day count')
        since = datetime.fromisoformat(state['since'])
        previous = datetime.fromisoformat(state['checkedAt'])
        if since.tzinfo is None or previous.tzinfo is None or not since <= previous <= now:
            raise ValueError('Invalid counter time')
        if now-previous > timedelta(days=5):
            state['complete'] = False  # Cannot prove expired/missing log history.
    else:
        state = {'schema': 1, 'since': now.isoformat(), 'checkedAt': now.isoformat(),
                 'lastBlockedAt': None, 'identities': identities, 'totals': {k: 0 for k in identities}, 'days': {}, 'complete': True}
        since = now
    state['complete'] = state['complete'] and complete
    buckets = {}
    reverse = {v: k for k, v in identities.items()}
    for row in rows:
        device = reverse.get(row.get('client'))
        if not device or row.get('reason') not in BLOCKED_REASONS:
            continue
        at = datetime.fromisoformat(row['time'].replace('Z', '+00:00'))
        if not since <= at <= now:
            continue
        day = at.astimezone(timezone.utc).date().isoformat()
        values = buckets.setdefault(day, {k: 0 for k in identities})
        values[device] += 1
    blocked_times = [row['time'] for row in rows if row.get('client') in reverse and row.get('reason') in BLOCKED_REASONS and since <= datetime.fromisoformat(row['time'].replace('Z', '+00:00')) <= now]
    marker = state.get('lastBlockedAt')
    if marker and marker not in blocked_times:
        state['complete'] = False  # Detect a reset even if the replacement log has the same count.
    if blocked_times:
        state['lastBlockedAt'] = max(blocked_times, key=lambda at: datetime.fromisoformat(at.replace('Z', '+00:00')))
    cutoff = (now.date()-timedelta(days=6)).isoformat()
    for day, values in state['days'].items():
        if day >= cutoff and day not in buckets and any(values.values()):
            state['complete'] = False
    for day, values in buckets.items():
        if day < cutoff:
            continue
        old = state['days'].get(day, {k: 0 for k in identities})
        for key, count in values.items():
            if count < old[key]:
                state['complete'] = False
            state['totals'][key] += max(0, count-old[key])
            values[key] = max(count, old[key])
        state['days'][day] = values
    state['days'] = {k: v for k, v in state['days'].items() if k >= cutoff}
    state['checkedAt'] = now.isoformat()
    answer = {'since': state['since'], 'complete': state['complete'], 'blocked': sum(state['totals'].values()),
              'devices': dict(state['totals'])}
    # No write for an unchanged refresh; checkpoint an idle counter at most hourly.
    if original:
        old = json.loads(original)
        last_check = datetime.fromisoformat(old['checkedAt'])
        old['checkedAt'] = state['checkedAt']
        if old == state and now-last_check < timedelta(hours=1):
            return answer
    fd, temp = tempfile.mkstemp(prefix='.lifetime-', dir=p.parent)
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(state, out)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, p)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return answer
