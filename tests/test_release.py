"""A public artifact must reject owner profiles, signing data and unsafe archives."""
import importlib.util
from pathlib import Path
import zipfile
import sys
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))

def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

release = load('prepare-release')
engine = load('install-test-browser')

def widget(tmp_path, extra=None, config='window.CleanHomeConfig = {};'):
    target = tmp_path / 'test.wgt'
    with zipfile.ZipFile(target, 'w') as package:
        for name, text in {'LICENSE':'MIT', 'THIRD_PARTY_NOTICES.md':'Notices', 'config.xml':'manifest', 'device-config.js':config, **(extra or {})}.items():
            package.writestr(name, text)
    return target

def test_generic_widget_allowed(tmp_path):
    release.validate_widget(widget(tmp_path))

@pytest.mark.parametrize('name', ['author-signature.xml','signature1.xml','keys/author.p12','../secret','/absolute','assets/private-fonts/secret.ttf'])
def test_release_rejects_private_or_unsafe_members(tmp_path, name):
    with pytest.raises(ValueError):
        release.validate_widget(widget(tmp_path, {name:'fake fixture'}))

@pytest.mark.parametrize('config', ['window.CleanHomeConfig.verifiedAppIds = {};', 'window.CleanHomeConfig.host="203.0.113.20";'])
def test_release_rejects_personal_profile(tmp_path, config):
    with pytest.raises(ValueError):
        release.validate_widget(widget(tmp_path, config=config))

def test_browser_download_must_match_pinned_digest(tmp_path):
    path = tmp_path / 'wrong.zip'
    path.write_bytes(b'not the verified browser')
    with pytest.raises(ValueError, match='checksum'):
        engine.install(path, tmp_path / 'engine')
    assert not (tmp_path / 'engine').exists()


@pytest.mark.parametrize('suffix', ['.pfx', '.crt', '.cer', '.der', '.jks', '.keystore'])
def test_release_rejects_certificate_exports_and_signing_stores(tmp_path, suffix):
    with pytest.raises(ValueError):
        release.validate_widget(widget(tmp_path, {'hidden/owner' + suffix:'fake fixture'}))


def test_release_rejects_private_data_outside_the_device_profile(tmp_path):
    host = '.'.join(map(str, [10, 25, 30, 40]))
    with pytest.raises(ValueError):
        release.validate_widget(widget(tmp_path, {'helper.js': 'var host="' + host + '";'}))
