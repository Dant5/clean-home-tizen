"""The combined download must preserve validated app/tool bytes and identity."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import zipfile
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('complete_setup_release', ROOT / 'scripts/prepare-release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def inputs(folder, *, appid='D5Q60BHome.CleanHome', package='D5Q60BHome', version='1.4.2', signed=False, platform='Windows'):
    widget = folder / 'app.wgt'
    xml = '<widget xmlns:tizen="http://tizen.org/ns/widgets" version="'+version+'"><tizen:application id="'+appid+'" package="'+package+'"/></widget>'
    with zipfile.ZipFile(widget, 'w') as archive:
        for name, data in {'config.xml': xml, 'LICENSE': 'MIT', 'THIRD_PARTY_NOTICES.md': 'Notices', 'device-config.js': 'window.CleanHomeConfig = {};'}.items():
            archive.writestr(name, data)
        if signed: archive.writestr('author-signature.xml', 'OWNER SIGNATURE FIXTURE')
    companion = folder / 'companion.zip'
    with zipfile.ZipFile(companion, 'w') as archive:
        archive.writestr('LICENSE', 'MIT')
        archive.writestr('CleanHome-Home-Setup.exe' if platform == 'Windows' else 'START-LINUX.sh', 'PACKAGING FIXTURE')
    return widget, companion


def test_bundle_preserves_tool_app_notices_and_checksums(tmp_path):
    widget, companion = inputs(tmp_path)
    result = release.build_setup_bundle(widget, companion, tmp_path, 'Windows', '1.4.2')
    with zipfile.ZipFile(result) as archive:
        assert archive.read('CleanHome-Tizen-1.4.2-unsigned.wgt') == widget.read_bytes()
        assert archive.read('home-setup/CleanHome-Home-Setup.exe') == b'PACKAGING FIXTURE'
        assert archive.read('home-setup/LICENSE') == b'MIT'
        guide = archive.read('START-HERE.html').decode()
        assert '__WIDGET__' not in guide and '__START_TOOL__' not in guide
        assert 'QA55Q60BAWXXY / T-NKLBUABC-1720.7 only' in guide
        assert 'Undo setup' in guide and 'Apps2Samsung' in guide
        for line in archive.read('SETUP-CHECKSUMS.txt').decode().splitlines():
            digest, name = line.split('  ', 1)
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest


@pytest.mark.parametrize('field,value', [('appid','Other.App'), ('package','OtherPackage'), ('version','9.9.9')])
def test_bundle_refuses_wrong_app_identity_or_version(tmp_path, field, value):
    widget, companion = inputs(tmp_path, **{field:value})
    with pytest.raises(ValueError, match='matching Clean Home'):
        release.build_setup_bundle(widget, companion, tmp_path, 'Windows', '1.4.2')
    assert not list(tmp_path.glob('CleanHome-Setup-*'))


def test_bundle_refuses_owner_signed_widget(tmp_path):
    widget, companion = inputs(tmp_path, signed=True)
    with pytest.raises(ValueError, match='signed widget'):
        release.build_setup_bundle(widget, companion, tmp_path, 'Windows', '1.4.2')


def test_bundle_refuses_wrong_host_tool(tmp_path):
    widget, companion = inputs(tmp_path, platform='Python')
    with pytest.raises(ValueError, match='entry point'):
        release.build_setup_bundle(widget, companion, tmp_path, 'Windows', '1.4.2')
