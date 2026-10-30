"""Package the optional Windows executable with its redistribution notices."""
import argparse
from importlib.metadata import distribution
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    args = parser.parse_args()
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if not python_license.is_file(): raise SystemExit('Python redistribution licence missing')
    installer = distribution('pyinstaller')
    candidates = [path for path in installer.files if path.name == 'COPYING.txt']
    if len(candidates) != 1: raise SystemExit('PyInstaller redistribution licence missing or ambiguous')
    notices = {
        'CleanHome-Home-Setup.exe': args.executable.read_bytes(),
        'LICENSE.txt': (ROOT / 'LICENSE').read_bytes(),
        'licenses/AeroTizen-MIT.txt': (ROOT / 'vendor/aerotizen/LICENSE').read_bytes(),
        'licenses/Python.txt': python_license.read_bytes(),
        'licenses/PyInstaller.txt': Path(installer.locate_file(candidates[0])).read_bytes(),
        'README.txt': b'Clean Home optional Home setup (experimental)\r\n\r\nExtract this folder, then open CleanHome-Home-Setup.exe.\r\nPython is included. No installation or administrator account is needed.\r\nFirst install/open the TV widget using your own Samsung certificates.\r\nUse Check TV, confirmation and Use Clean Home. Keep the recovery folder.\r\nAlways Undo before uninstalling the TV widget.\r\nOnly QA55Q60BAWXXY / T-NKLBUABC-1720.7 is accepted.\r\nThe underlying method worked on that TV; this new companion is experimental.\r\nhttps://github.com/Dant5/clean-home-tizen/blob/main/docs/NATIVE-HOME.md\r\n'
    }
    output = ROOT / 'dist/companion/CleanHome-Home-Setup-Windows-experimental.zip'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in notices.items(): archive.writestr(name, data)
    print(output.name)


if __name__ == '__main__': main()
