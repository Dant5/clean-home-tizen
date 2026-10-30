"""Generate margin equivalents for the original flex gaps on older TV engines."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = {'.caption', '.dock-empty', '.settings-group-copy', '.setting-copy', '.setting-options'}


def generate():
    rules = ['/* Generated from style.css by build-compatibility-css.py. Only used when flex gap is absent. */']
    for selectors, body in re.findall(r'([^{}]+)\{([^{}]*)\}', (ROOT / 'app/style.css').read_text()):
        match = re.search(r'(?:^|;)gap:([0-9.]+(?:px)?)(?:;|$)', body)
        if not match:
            continue
        selectors = re.sub(r'/\*.*?\*/', '', selectors, flags=re.S).strip()
        for selector in selectors.split(','):
            selector = selector.strip()
            gap = match.group(1)
            column = selector in COLUMNS or selector.startswith('.l-list .quiet-utils') and '.u' not in selector.replace('.quiet-utils', '')
            if selector == '.is-horizontal .setting-options':
                column = False
            reverse = selector.startswith('.l-list ') and selector.endswith('.u-content')
            left, top, right = ('0', gap, '0') if column else ('0', '0', gap) if reverse else (gap, '0', '0')
            rules.append('.no-flex-gap ' + selector + '{gap:0!important}')
            rules.append('.no-flex-gap ' + selector + '> * + *{margin-left:' + left + ';margin-top:' + top + ';margin-right:' + right + '}')
    rules.append('.no-flex-gap .quiet-utils.is-text .u-content>.u-label{margin-left:0!important;margin-right:0!important}')
    rules.append('.no-flex-gap .setting-name,.no-flex-gap .setting-description,.no-flex-gap .setting-reason{overflow-wrap:break-word;word-wrap:break-word}')
    rules.append('.no-flex-gap .er-text,.no-flex-gap .eo-text{margin-right:20px!important}')
    rules.append('.no-flex-gap .setting-choice.has-forward .setting-copy{margin-right:16px}')
    rules.append('.no-flex-gap .er-move,.no-flex-gap .eo-verb,.no-flex-gap .setting-forward{margin-left:auto!important}')
    rules.append('.no-flex-gap .caption .weather{row-gap:0!important}')
    rules.append('.no-flex-gap .caption .wx-place{margin-left:0;margin-top:4px}')
    return '\n'.join(rules) + '\n'


if __name__ == '__main__':
    (ROOT / 'app/compatibility.css').write_text(generate())
