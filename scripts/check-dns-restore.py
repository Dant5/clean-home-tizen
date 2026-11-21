"""Cold-copy/restore rehearsal for the disposable loopback lab, not production."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--profile', type=Path, default=ROOT / '.local/dns-protection/lab')
args = parser.parse_args()
LAB = args.profile.resolve()
if LAB.parent != (ROOT / '.local/dns-protection').resolve() or LAB.name not in ('lab', 'dual-lab'):
    raise SystemExit('Only the named disposable loopback labs can be restored')
RESTORE = LAB.parent / ('restore-lab' if LAB.name == 'lab' else 'dual-lab-restore')
BACKUP = LAB.parent / ('cold-copy' if LAB.name == 'lab' else 'dual-lab-cold-copy')
project = 'cleanhome-dns-' + LAB.name
restore_project = 'cleanhome-dns-restore-lab' if LAB.name == 'lab' else 'cleanhome-dns-dual-lab-restore'
for name, path in [('bridge', ROOT / 'tools/dns-protection/bridge.py'), ('dns_lab', ROOT / 'scripts/check-dns-lab.py')]:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    globals()[name] = module
assert bridge.load_config(LAB / 'bridge.json')['tv_ip'] == '127.0.0.2'
if RESTORE.exists() or BACKUP.exists():
    raise SystemExit('Preserve the existing restore evidence; choose a fresh lab for another rehearsal')
base = ['docker', 'compose', '--project-name', project, '--env-file', str(LAB / 'profile.env'), '-f', str(ROOT / 'tools/dns-protection/compose.yaml')]
subprocess.run(base + ['stop'], check=True, capture_output=True)
try:
    shutil.copytree(LAB, BACKUP)
finally:
    subprocess.run(base + ['start'], check=True, capture_output=True)
files = [p for p in LAB.rglob('*') if p.is_file() and p.relative_to(LAB).parts[0] in ('conf', 'work')]
# Compare the stopped snapshot to itself after copying into an isolated restore path.
shutil.copytree(BACKUP, RESTORE)
for p in BACKUP.rglob('*'):
    if p.is_file():
        assert hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256((RESTORE / p.relative_to(BACKUP)).read_bytes()).digest()
conf = RESTORE / 'conf/AdGuardHome.yaml'
text = conf.read_text().replace('address: 127.0.0.1:13080', 'address: 127.0.0.1:13081').replace('port: 15353', 'port: 15354')
assert text != conf.read_text(); conf.write_text(text)
profile = json.loads((RESTORE / 'bridge.json').read_text()); profile['agh_url'] = 'http://127.0.0.1:13081'
(RESTORE / 'bridge.json').write_text(json.dumps(profile)); (RESTORE / 'bridge.json').chmod(0o600)
env = (RESTORE / 'profile.env').read_text().replace(str(LAB), str(RESTORE)); (RESTORE / 'profile.env').write_text(env)
base = ['docker', 'compose', '--project-name', restore_project, '--env-file', str(RESTORE / 'profile.env'), '-f', str(ROOT / 'tools/dns-protection/compose.yaml')]
subprocess.run(base + ['up', '-d'], check=True, capture_output=True)
try:
    p = bridge.Protection(profile)
    for i in range(10):
        try:
            snapshot = p.snapshot(force=True); break
        except bridge.Unavailable:
            time.sleep(0.5)
    else: raise AssertionError('Restored resolver unavailable')
    assert snapshot['today']['queries'] > 0 and snapshot['today']['blocked'] > 0
    if profile.get('soundbar_ip'):
        assert snapshot['devices'][0]['today']['queries'] > 0 and snapshot['devices'][1]['today']['queries'] > 0
    assert dns_lab.query('rtb-config.samsungads.com', port=15354)['rcode'] == 3
    assert dns_lab.query('example.org', port=15354)['answers'] > 0
    report = {'scope': 'Isolated cold-copy restore, not an encrypted off-machine backup verification',
              'restoredFilesHashVerified': len([p for p in BACKUP.rglob('*') if p.is_file()]),
              'authenticatedApi': True, 'statisticsRetained': True, 'filteringWorks': True, 'normalResolutionWorks': True}
    (LAB.parent / ('restore-results.json' if LAB.name == 'lab' else 'dual-restore-results.json')).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
finally:
    subprocess.run(base + ['stop'], check=True, capture_output=True)
