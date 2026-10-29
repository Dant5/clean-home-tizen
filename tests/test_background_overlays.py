"""The cached shading must cover the gallery and match its reviewed source inputs."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'app/assets/background-overlays'


def test_shading_cache_matches_source_and_gallery():
    manifest = json.loads((FOLDER / 'manifest.json').read_text())
    assert manifest['engine'].startswith('85.')
    for name, expected in manifest['sourceHashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, 'Regenerate shading after changing ' + name
    gallery = json.loads((ROOT / 'app/assets/wallpapers/catalog.js').read_text().split(' = ', 1)[1].strip().removesuffix(';'))
    expected = {(wall['id'], layout) for wall in gallery for layout in ('dock', 'list')}
    entries = manifest['entries']
    assert {(entry['wall'], entry['layout']) for entry in entries} == expected
    assert len(entries) == len(expected)
    css = (FOLDER / 'overlays.css').read_text()
    assert 'assets/background-overlays/overlays.css' in (ROOT / 'app/index.html').read_text()
    for entry in entries:
        file = entry['file']
        assert file == hashlib.sha256((FOLDER / file).read_bytes()).hexdigest()[:16] + '.png'
        with Image.open(FOLDER / file) as image:
            assert image.mode == 'RGBA' and image.size == (1920, 1080)
        assert '.stage.bg-photo.l-' + entry['layout'] + '[data-wall="' + entry['wall'] + '"]' in css
        assert 'url("' + file + '")' in css
    assert {path.name for path in FOLDER.glob('*.png')} == {entry['file'] for entry in entries}
