"""Keep moved user/developer guides reachable from repository Markdown."""
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def test_local_markdown_links_resolve():
    files = list(ROOT.glob('*.md'))
    for folder in ['docs', '.github', 'tools']:
        files.extend((ROOT / folder).rglob('*.md'))
    for file in files:
        for link in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)\)', file.read_text()):
            if link.startswith(('http:', 'https:', 'mailto:', '#')):
                continue
            path = unquote(link.split('#', 1)[0])
            assert (file.parent / path).exists(), f'{file.relative_to(ROOT)}: {path}'
