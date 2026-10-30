"""Validate widget identity, resources and the Q60B privilege boundary offline."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as XML

root = Path(__file__).resolve().parents[1]
app = root / 'app'
ns = {'w': 'http://www.w3.org/ns/widgets', 't': 'http://tizen.org/ns/widgets'}
manifest = XML.parse(app / 'config.xml').getroot()
identity = manifest.find('t:application', ns)
assert identity.attrib == {'id': 'D5Q60BHome.CleanHome', 'package': 'D5Q60BHome', 'required_version': '5.0'}
assert manifest.find("t:metadata[@key='http://samsung.com/tv/metadata/devel.api.version']", ns).get('value') == identity.get('required_version')
assert manifest.get('version') == json.loads((root / 'package.json').read_text())['version']
assert '<meta name="clean-home-version" content="' + manifest.get('version') + '">' in (app / 'index.html').read_text()
assert manifest.find('t:setting', ns).get('background-support') == 'disable'
assert manifest.find("t:metadata[@key='http://samsung.com/tv/metadata/multitasking.support']", ns).get('value') == 'true'
assert not manifest.findall('t:background-category', ns)
privileges = {e.get('name') for e in manifest.findall('t:privilege', ns)}
assert privileges == {'http://tizen.org/privilege/' + x for x in ['application.launch', 'application.info', 'tv.inputdevice', 'tv.window', 'system', 'fullscreen', 'internet']} | {'http://developer.samsung.com/privilege/productinfo'}
for node in manifest.findall('w:access', ns):
    assert node.get('origin') in ['https://api.open-meteo.com', 'https://www.bing.com']
for tag in ['content', 'icon']:
    assert (app / manifest.find('w:' + tag, ns).get('src')).is_file()
for reference in re.findall(r'(?:src|href)=[\"\']([^\"\']+)', (app / 'index.html').read_text()):
    if reference.startswith('$WEBAPIS/'):
        continue
    assert (app / reference).is_file(), reference
for css in app.rglob('*.css'):
    for reference in re.findall(r'url\([\"\']?([^\)\"\']+)', css.read_text()):
        if ':' not in reference:
            assert (css.parent / reference.split('?')[0]).is_file(), reference
for wall in json.loads((app / 'assets/wallpapers/SOURCES.json').read_text()):
    for field in ['src', 'thumb']:
        assert (app / wall[field]).is_file()
    assert (app / 'assets/wallpapers' / (wall['id'] + '-lens.jpg')).is_file()
source = '\n'.join((app / name).read_text() for name in ['main.js', 'device.js', 'index.html'])
for forbidden in ['vconf', 'SYS_BASES', 'sysExecOutput', 'useAsHome', 'maybeHandOffHome', 'coldBoot', 'KsHome0001', '192.168.', '/exec', '/remap', 'CH_DEBUG_URL +']:
    assert forbidden not in source, 'Forbidden legacy integration: ' + forbidden
assert not re.search(r'(?<![A-Za-z-])inset\s*:', (app / 'style.css').read_text()), 'Chromium 85 does not support CSS inset'
assert not re.search(r'(backdrop-filter|filter)\s*:\s*blur', (app / 'style.css').read_text())
assert not (root / 'scripts/native-home').exists()
for notice in ['LICENSE', 'docs/THIRD_PARTY_NOTICES.md', 'vendor/aerotizen/LICENSE']:
    assert (root / notice).is_file()
print('Q60B manifest, assets, notices and integration boundary passed.')
