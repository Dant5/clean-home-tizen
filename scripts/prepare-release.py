"""Create generic unsigned release assets from the reviewed Git source only."""
import hashlib
from html import escape
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as XML
from font_assets import ROOT, archive_member
from privacy_rules import content_findings

ALLOWED_ROOTS = {'app', 'docs', 'scripts', 'tests', 'tools', 'vendor', '.github'}
ALLOWED_FILES = {'README.md', 'AGENTS.md', 'LICENSE', 'package.json', 'package-lock.json', '.gitignore'}


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


def validate_companion(path):
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or archive.testzip():
            raise ValueError('Invalid companion archive')
        if sum(info.file_size for info in archive.infolist())>128*1024*1024:
            raise ValueError('Companion archive too large')
        for info in archive.infolist():
            name=info.filename
            member=Path(name)
            if member.is_absolute() or '..' in member.parts or '\\' in name or (info.external_attr>>16)&0o170000==0o120000:
                raise ValueError('Unsafe companion path: '+name)
            if member.suffix.lower() in {'.wgt','.p12','.pfx','.pem','.key','.csr','.crt','.cer','.der','.jks','.keystore'} or member.name.lower() in {'originalhome.json','original-home.json','profiles.xml','password.txt','session.json'} or '.original.json' in name or '.status.json' in name:
                raise ValueError('Private companion member: '+name)
            if member.suffix.lower() in {'.py','.json','.txt','.html','.cmd','.sh'}:
                if content_findings('tools/'+name,archive.read(name).decode('utf-8')):
                    raise ValueError('Private data pattern in companion: '+name)
        if not any(Path(name).name in {'LICENSE','LICENSE.txt'} for name in names):
            raise ValueError('Companion licence missing')


def build_setup_bundle(widget, companion, folder, platform, version):
    """One reviewed download: app, existing Home tool and an offline install guide."""
    validate_widget(widget)
    validate_companion(companion)
    with zipfile.ZipFile(widget) as package:
        manifest = XML.fromstring(package.read('config.xml'))
        identity = manifest.find('{http://tizen.org/ns/widgets}application')
        if identity is None or identity.get('id') != 'D5Q60BHome.CleanHome' or identity.get('package') != 'D5Q60BHome' or manifest.get('version') != version:
            raise ValueError('Setup bundle requires the matching Clean Home widget')
    if platform not in {'Windows', 'Python'} or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Invalid setup bundle platform/version')
    widget_name = 'CleanHome-Tizen-' + version + '-unsigned.wgt'
    start = 'CleanHome-Home-Setup.exe' if platform == 'Windows' else 'START-LINUX.sh'
    with zipfile.ZipFile(companion) as archive:
        if start not in archive.namelist():
            raise ValueError('Setup bundle is missing its Home tool entry point')
        files = {'home-setup/' + name: archive.read(name) for name in archive.namelist() if not name.endswith('/')}
        executable = {'home-setup/' + item.filename for item in archive.infolist() if (item.external_attr >> 16) & 0o111}
    guide = (ROOT / 'tools/setup-bundle/START-HERE.html').read_text(encoding='utf-8')
    for key, value in {'__PLATFORM__': platform, '__WIDGET__': widget_name, '__START_TOOL__': 'home-setup/' + start,
                       '__RUNTIME__': ' (Python is included)' if platform == 'Windows' else ' with Python 3.11 or newer; on Windows with Python, use START-WINDOWS.cmd instead'}.items():
        guide = guide.replace(key, escape(value))
    files.update({'START-HERE.html': guide.encode('utf-8'), widget_name: widget.read_bytes(),
                  'home-preview.jpg': (ROOT / 'docs/images/home-example.jpg').read_bytes(),
                  'LICENSE': (ROOT / 'LICENSE').read_bytes(),
                  'README.txt': b'Clean Home Setup (community preview)\n\nExtract the whole ZIP, then open START-HERE.html.\nFollow Install the TV app, then Make it your Home screen.\nHome replacement accepts QA55Q60BAWXXY / T-NKLBUABC-1720.7 only.\nOther Samsung models: use Check TV, then Send compatibility report.\nKeep the recovery folder and Undo before removing the TV app.\nYour own Samsung sign-in/certificates are handled by Apps2Samsung.\n'})
    files['SETUP-CHECKSUMS.txt'] = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in sorted(files.items())).encode()
    output = folder / ('CleanHome-Setup-' + platform + '-preview.zip')
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = archive_member(name)
            if name in executable: info.external_attr = 0o100755 << 16
            archive.writestr(info, data)
    return output


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
    assets=[target,source]
    for extra in [ROOT/'dist/CleanHome-Home-Setup-experimental.zip',ROOT/'dist/companion/CleanHome-Home-Setup-Windows-experimental.zip']:
        if extra.is_file():
            validate_companion(extra)
            destination=folder/extra.name
            destination.write_bytes(extra.read_bytes())
            assets.append(destination)
            platform = 'Windows' if 'Windows' in extra.name else 'Python'
            assets.append(build_setup_bundle(widget, extra, folder, platform, version))
    manifest = {'version': version, 'source_commit': commit, 'working_tree_dirty': dirty, 'signed': False, 'tv_contacted': False, 'personal_profile': False, 'assets': [describe(p) for p in assets], 'compatibility': 'Tizen 5.0+ target; browser checks span Chromium 63-130. Reference hardware: Q60B / Tizen 6.5; other TVs unverified.', 'native_setup': 'Home writes: QA55Q60BAWXXY / T-NKLBUABC-1720.7 only. Settings-read-only compatibility diagnostics and opt-in reports are available for other identified Samsung TVs. New guided installer/Undo and cross-model probes need physical-TV validation; underlying native Home mechanism has reference-device evidence.'}
    record = folder / 'release-manifest.json'
    record.write_text(json.dumps(manifest, indent=2) + '\n')
    (folder / 'SHA256SUMS').write_text(''.join(describe(p)['sha256'] + '  ' + p.name + '\n' for p in assets+[record]))
    print('Unsigned generic release assets: ' + str(folder.relative_to(ROOT)))
    if dirty:
        print('Working tree is dirty: commit reviewed changes and regenerate before uploading.')


if __name__ == '__main__':
    main()
