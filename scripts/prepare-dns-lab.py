"""Generate loopback test secrets without exposing them in arguments or logs."""
import os
from pathlib import Path
import secrets
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
folder = root / '.local/dns-protection'
folder.mkdir(parents=True, exist_ok=True, mode=0o700)
os.chmod(folder, 0o700)
password = secrets.token_urlsafe(30)
# Established system bcrypt utility, test-time only. No password on its command line.
result = subprocess.run(['htpasswd', '-niBC', '12', 'cleanhome-admin'], input=password + '\n', text=True, capture_output=True, check=True)
hashed = result.stdout.strip().split(':', 1)[1]
for name, value in [('lab-password', password), ('lab-hash', hashed)]:
    path = folder / name
    if path.exists():
        raise SystemExit('Refusing to replace existing lab secrets')
    path.write_text(value); path.chmod(0o600)
subprocess.run([sys.executable, str(root / 'tools/dns-protection/prepare.py'),
                '--tv-ip', '127.0.0.2', '--soundbar-ip', '127.0.0.3', '--server-ip', '127.0.0.1',
                '--admin-password-file', str(folder / 'lab-password'), '--admin-hash-file', str(folder / 'lab-hash'),
                '--output', str(folder / 'lab'), '--test'], check=True)
