"""The chart must retain evidence and distinguish target/browser/physical scopes."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_chart_is_current_and_uses_tested_engines():
    spec = importlib.util.spec_from_file_location('chart', ROOT / 'scripts/build-compatibility-chart.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (ROOT / 'docs/images/compatibility.svg').read_text() == module.generate()
    data = json.loads((ROOT / 'docs/compatibility.json').read_text())
    assert data['previewVersion'] == json.loads((ROOT / 'package.json').read_text())['version']
    engines = json.loads((ROOT / 'scripts/test-browsers.json').read_text())
    assert {str(row['chromium']) for row in data['versions']} == set(engines)


def test_physical_evidence_is_specific_and_not_promoted_from_preview():
    data = json.loads((ROOT / 'docs/compatibility.json').read_text())
    for item in data['hardware'] + data['communityReports']:
        assert item['model'] and item['firmware'] and item['appVersion'] and item['evidence']
        assert item['tizen'] in {row['tizen'] for row in data['versions']}
    chart = (ROOT / 'docs/images/compatibility.svg').read_text()
    assert '1.3.9' in chart and 'browser-tested' in chart
