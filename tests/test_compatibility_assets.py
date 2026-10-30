"""Prevent stale older-engine spacing after changing original layout rules."""
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_generated_older_engine_spacing_is_current():
    spec = importlib.util.spec_from_file_location('compatibility_css', ROOT / 'scripts/build-compatibility-css.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (ROOT / 'app/compatibility.css').read_text() == module.generate()
