"""Create generic unsigned release assets from the reviewed Git source only."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from font_assets import ROOT, archive_member
from privacy_rules import content_findings

ALLOWED_ROOTS = {'app', 'docs', 'scripts', 'tests', 'tools', 'vendor', '.github'}
ALLOWED_FILES = {'README.md', 'INSTALL.md', 'AGENTS.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'SECURITY.md', 'PRIVACY.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'package.json', 'package-lock.json', 'requirements-build.txt', '.gitignore'}


def validate_widget(path):
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        if len(names) != len(set(names)) or package.testzip():
            raise ValueError('Invalid widget archive')
        for name in names:
            part = Path(name)
            if part.is_absolute() or '..' in part.parts or part.suffix.lower() in {'.p12', '.pfx', '.pem', '.key', '.csr', '.crt', '.cer', '.der', '.jks', '.keystore'} or (name == 'author-signature.xml' or re.fullmatch(r'signature\d+\.xml', name) or part.name in {'password.txt', 'profiles.xml', 'session.json'}) or name.startswith('assets/private-fonts/'):
                raise ValueError('Private or signed widget member: ' + name)
        for name in names:
            if Path(name).suffix.lower() in {'.js', '.css', '.xml', '.json', '.html', '.md', '.txt', '.svg'}:
                try:
                    content = package.read(name).decode()
                except UnicodeError:
                    continue
                if content_findings(name, content, device_config=name == 'device-config.js'):
                    raise ValueError('Private data pattern in widget member: ' + name)
        config = package.read('device-config.js').decode()
        if re.search(r'verifiedAppIds\s*=', config) or content_findings('device-config.js', config, device_config=True):
            raise ValueError('Personal device profile in release widget')
        if not all(name in names for name in ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'config.xml']):
            raise ValueError('Missing release notices or manifest')


def source_names():
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    result = []
    for name in filter(None, names):
        path = Path(name)
        if path.parts[0] not in ALLOWED_ROOTS and name not in ALLOWED_FILES:
            raise ValueError('Unexpected tracked release path: ' + name)
        if (ROOT / path).is_symlink() or path.suffix.lower() in {'.wgt', '.p12', '.pfx', '.pem', '.key', '.csr', '.crt', '.cer', '.der', '.jks', '.keystore', '.pyc'}:
            raise ValueError('Unsafe source member: ' + name)
        try:
            text = (ROOT / path).read_text()
        except UnicodeError:
            text = ''
        if content_findings(name, text):
            raise ValueError('Private data pattern in source member: ' + name)
        result.append(name)
    if not result:
        raise ValueError('Stage and review the source before preparing a release')
    return sorted(result)


def main():
    version = json.loads((ROOT / 'package.json').read_text())['version']
    subprocess.run([sys.executable, 'scripts/package.py'], cwd=ROOT, check=True)
    widget = ROOT / 'dist/CleanHome-Q60B-unsigned.wgt'
    validate_widget(widget)
    folder = ROOT / 'dist/release'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / ('CleanHome-Tizen-' + version + '-unsigned.wgt')
    target.write_bytes(widget.read_bytes())
    source = folder / ('CleanHome-Tizen-' + version + '-source.zip')
    with zipfile.ZipFile(source, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name in source_names():
            info = archive_member('clean-home-tizen-' + version + '/' + name)
            if (ROOT / name).stat().st_mode & 0o111:
                info.external_attr = 0o100755 << 16
            package.writestr(info, (ROOT / name).read_bytes())
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))
    def describe(p):
        return {'name': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    manifest = {'version': version, 'source_commit': commit, 'working_tree_dirty': dirty, 'signed': False, 'tv_contacted': False, 'personal_profile': False, 'assets': [describe(target), describe(source)], 'compatibility': 'Core tested on Q60B / Tizen 6.5. First-run picker browser-tested; other hardware unverified.'}
    record = folder / 'release-manifest.json'
    record.write_text(json.dumps(manifest, indent=2) + '\n')
    (folder / 'SHA256SUMS').write_text(''.join(describe(p)['sha256'] + '  ' + p.name + '\n' for p in [target, source, record]))
    print('Unsigned generic release assets: ' + str(folder.relative_to(ROOT)))
    if dirty:
        print('Working tree is dirty: commit reviewed changes and regenerate before uploading.')


if __name__ == '__main__':
    main()
