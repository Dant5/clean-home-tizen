"""Fetch a checksum-pinned TV-generation test engine, never a normal browsing profile."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/782078/chrome-linux.zip'
SHA256 = '3013c06ee25c60c952e4b63938271d7380c3f5c7b889fec67fa28da58e93e5de'


def install(archive, destination, digest=SHA256, directory="chrome-linux"):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
        raise ValueError('Chromium archive checksum mismatch')
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            path = Path(info.filename)
            if path.is_absolute() or '..' in path.parts or path.parts[0] != directory or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unexpected Chromium archive path')
        package.extractall(destination)
        for info in package.infolist():
            if not info.is_dir() and (info.external_attr >> 16) & 0o111:
                (destination / info.filename).chmod(0o755)
    return destination / directory / 'chrome'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', choices=list(json.loads((ROOT / 'scripts/test-browsers.json').read_text())), default='85')
    parser.add_argument('--archive', type=Path, help='Existing pinned archive; otherwise download over HTTPS')
    args = parser.parse_args()
    record = json.loads((ROOT / 'scripts/test-browsers.json').read_text())[args.engine]
    with tempfile.TemporaryDirectory(prefix='clean-home-browser-') as folder:
        archive = args.archive or Path(folder) / 'chromium85.zip'
        if not args.archive:
            with urlopen(record['url'], timeout=60) as response, archive.open('wb') as target:
                shutil.copyfileobj(response, target)
        print(install(archive, ROOT / ('.local/chromium' + args.engine), record['sha256'], record.get('directory', 'chrome-linux')))


if __name__ == '__main__':
    main()
