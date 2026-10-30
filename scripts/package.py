"""Offline public-font build; optional signing with the owner's external certificates."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as XML
from font_assets import ROOT, write_widget_archive, archive_member


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cert-dir', type=Path, help='External owner-only directory containing author.p12, distributor.p12, password.txt')
    parser.add_argument('--bindings-json', type=Path, help='Private, inventory-verified mapping of the four favourite names to IDs')
    args = parser.parse_args()
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    target = out / 'CleanHome-Q60B-unsigned.wgt'
    overlay = None
    bindings = None
    if args.bindings_json:
        bindings = json.loads(args.bindings_json.read_text())
        brands = ['youtube', 'nuvio', 'spotify', 'moonlight']
        if set(bindings) != set(brands) or not all(isinstance(v, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,160}', v) for v in bindings.values()):
            parser.error('Bindings must contain only the four favourite names and valid application IDs.')
        base = (ROOT / 'app/device-config.js').read_text()
        overlay = {'device-config.js': (base + '\nwindow.CleanHomeConfig.verifiedAppIds = ' + json.dumps(bindings, sort_keys=True) + ';\n').encode()}
    write_widget_archive(target, include_private=False, runtime_overlay=overlay)
    with zipfile.ZipFile(target, 'a', zipfile.ZIP_DEFLATED) as package:
        for source, name in [('LICENSE', 'LICENSE'), ('docs/THIRD_PARTY_NOTICES.md', 'THIRD_PARTY_NOTICES.md'), ('vendor/aerotizen/LICENSE', 'AeroTizen-LICENSE')]:
            package.writestr(archive_member(name), (ROOT / source).read_bytes())
    if args.cert_dir:
        folder = args.cert_dir.resolve()
        if folder.is_relative_to(ROOT):
            parser.error('Keep signing credentials outside the repository.')
        if os.name == 'posix':
            if folder.stat().st_mode & 0o077:
                parser.error('Certificate directory must be owner-only (0700).')
            for name in ['author.p12', 'distributor.p12', 'password.txt']:
                path = folder / name
                if path.is_symlink() or path.stat().st_mode & 0o077:
                    parser.error('Certificate files must be regular owner-only files (0600).')
        sys.path.insert(0, str(ROOT))
        from vendor.aerotizen.signer import sign_wgt
        signed = out / 'CleanHome-Q60B.wgt'
        try:
            sign_wgt(str(target), str(signed), str(folder))
        except Exception:
            raise SystemExit('Signing failed. Check the external certificate files and password; no credential values logged.')
        target = signed
    with zipfile.ZipFile(target) as package:
        assert package.testzip() is None
        assert len(package.namelist()) == len(set(package.namelist()))
        identity = XML.fromstring(package.read('config.xml')).find('{http://tizen.org/ns/widgets}application')
    report = {'file': target.name, 'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'signed': bool(args.cert_dir), 'application_id': identity.get('id'), 'minimum_tizen': identity.get('required_version'), 'tv_contacted': False, 'verified_favourite_ids': bindings}
    (out / (target.stem + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    (out / (target.name + '.sha256')).write_text(report['sha256'] + '  ' + target.name + '\n')
    print(json.dumps(report, indent=2))
    if not args.cert_dir:
        print('Awaiting owner Samsung certificates: unsigned widget cannot be installed directly.')


if __name__ == '__main__':
    main()
