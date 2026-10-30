"""Generate the README chart from reviewed compatibility evidence, not guesses."""
from pathlib import Path
from html import escape
import json

ROOT = Path(__file__).resolve().parents[1]


def generate():
    data = json.loads((ROOT / 'docs/compatibility.json').read_text())
    rows = data['versions']
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 920" role="img" aria-labelledby="title desc">',
           '<title id="title">Clean Home TV compatibility</title>',
           '<desc id="desc">Tizen 5.0 to 10.0 are preview targets with passing browser checks. Only the Q60B on Tizen 6.5 has real-TV reference evidence, running Clean Home 1.3.9. Other models await confirmation. Tizen 4.0 and earlier are outside the target.</desc>',
           '<rect width="1120" height="920" rx="20" fill="#101a28"/>',
           '<g font-family="system-ui,Segoe UI,Arial,sans-serif" fill="#f4f7fb">']

    def text(x, y, label, size=21, color='#f4f7fb', weight=400):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(str(label))}</text>')

    text(36, 57, 'Will Clean Home work on my TV?', 34, weight=700)
    text(36, 94, 'Made for Tizen 5.0–10.0. Most TV models still need testing.', 21, '#b9c9dc')
    for x, label in [(36, 'Tizen OS'), (194, 'Typical year*'), (360, 'App target'), (571, 'Browser check'), (814, 'Actual TV')]:
        text(x, 151, label, 19, '#b9c9dc', 600)
    for i, row in enumerate(rows):
        y = 174 + i * 66
        if i % 2 == 0:
            svg.append(f'<rect x="22" y="{y}" width="1076" height="64" rx="6" fill="#19283a"/>')
        text(36, y + 40, row['tizen'], 25, weight=600)
        text(194, y + 40, row['year'])
        text(360, y + 40, 'Preview target', 20, '#b5d2ff')
        text(571, y + 40, 'Passed', 20, '#88e0b4')
        evidence = [h for h in data['hardware'] if h['tizen'] == row['tizen']]
        community = [h for h in data['communityReports'] if h['tizen'] == row['tizen']]
        status = 'Tested: ' + evidence[0]['name'] + '**' if len(evidence) == 1 else str(len(evidence)) + ' reference TVs' if evidence else str(len(community)) + ' community reports' if community else 'Unconfirmed'
        text(814, y + 40, status, 20, '#88e0b4' if evidence else '#b5d2ff' if community else '#f0ca85')
    y = 174 + len(rows) * 66
    text(36, y + 40, '4.0 or older', 22)
    text(194, y + 40, '2018 or older', 19)
    text(360, y + 40, 'Outside target', 20, '#b9c9dc')
    text(571, y + 40, 'Not covered', 20, '#b9c9dc')
    text(814, y + 40, 'Unconfirmed', 20, '#b9c9dc')
    text(36, 809, '* Model-year guide. Your TV may have received a newer OS.', 18, '#b9c9dc')
    text(36, 840, '** Reference TV runs 1.3.9; the ' + data['previewVersion'] + ' preview is browser-tested.', 18, '#b9c9dc')
    text(36, 871, 'Passing browser checks does not guarantee that every TV will work.', 18, '#b9c9dc')
    svg.append('</g></svg>')
    return '\n'.join(svg) + '\n'


if __name__ == '__main__':
    (ROOT / 'docs/images/compatibility.svg').write_text(generate())
