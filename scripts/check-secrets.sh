#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
command -v gitleaks >/dev/null || { echo 'Install official Gitleaks before publishing.' >&2; exit 1; }
# Scan only publishable source files; ignored browsers, credentials and build output stay local.
python3 - <<'PY'
from pathlib import Path
import shutil
import subprocess
import tempfile
root = Path.cwd()
names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().split('\0')
with tempfile.TemporaryDirectory(prefix='clean-home-source-scan-') as temp:
    dest = Path(temp)
    for name in names:
        if not name:
            continue
        source = root / name
        if not source.is_file() or source.is_symlink():
            continue
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    subprocess.run(['gitleaks', 'dir', str(dest), '--redact', '--no-banner'], check=True)
PY
gitleaks git . --redact --no-banner --log-opts="--all"
