#!/usr/bin/env python3
"""Embed pinned browser assets in a new fastp report; never change analysis data."""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import tempfile

ASSETS = Path('/usr/local/share/fastp/report-assets')
SINGLE = "<script src='https://opengene.org/plotly-1.2.0.min.js'></script>"
FALLBACK = "    window.Plotly || document.write('<script src=\"https://cdn.plot.ly/plotly-1.2.0.min.js\"><\\/script>')"
BATCH = {
    '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>': 'chart.umd.min.js',
    '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>': 'plotly-1.58.5.min.js',
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/modern-normalize/2.0.0/modern-normalize.min.css">': 'normalize.min.css',
}

class RuntimeRefs(HTMLParser):
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ('src', 'href'):
            if tag in ('script', 'link', 'iframe', 'img') and a.get(key, '').startswith(('http:', 'https:', '//')):
                raise ValueError('unrecognized external runtime reference: ' + a[key])

def convert(source, target):
    text = source.read_text(encoding='utf-8')
    if target.exists() or target.is_symlink():
        raise ValueError('output already exists; choose a new output path')
    if '</body>' not in text or 'taffish-fastp-offline-assets' in text:
        raise ValueError('expected an original fastp HTML report, not an already converted file')
    lock = (ASSETS / 'report-assets.lock').read_text()
    assets = {}
    for line in lock.splitlines():
        digest, name, url = line.split()
        data = (ASSETS / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('asset checksum mismatch: ' + name)
        assets[name] = data.decode('utf-8')
    def inline(name):
        data = assets[name]
        data = re.sub(r'^//# sourceMappingURL=.*$', '', data, flags=re.M)
        data = re.sub(r'</script', r'<\\/script', data, flags=re.I)
        return '<style>' + data + '</style>' if name.endswith('.css') else '<script>' + data + '</script>'
    if text.count(SINGLE) == 1 and text.count(FALLBACK) == 1:
        # Keep upstream data/layout; use the pinned legacy Plotly version whose
        # PNG export is compatible with current browsers (1.2.0 export fails).
        text = text.replace(SINGLE, inline('plotly-1.58.5.min.js')).replace(FALLBACK, '')
    elif all(text.count(marker) == 1 for marker in BATCH):
        for marker, name in BATCH.items():
            text = text.replace(marker, inline(name))
    else:
        raise ValueError('unsupported report template; use fastp 1.4.0 or parallel.py to generate the input')
    RuntimeRefs().feed(text)
    notices = '\n\n'.join(name + '\n' + value for name, value in assets.items() if name.endswith('LICENSE'))
    appendix = '<details id="taffish-fastp-offline-assets"><summary>Offline report assets and licenses</summary><pre>'
    appendix += html.escape(lock + '\n' + notices) + '</pre></details>\n'
    text = text.replace('</body>', appendix + '</body>', 1)
    # Atomic, no-clobber publication on the same filesystem; source remains unchanged.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent,
                                     prefix='.fastp-report-', delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
            os.link(temporary, target)
        finally:
            temporary.unlink()
    print('Offline report: ' + str(target))

def main():
    p = argparse.ArgumentParser(description='Make a new, self-contained offline fastp HTML report (input is never overwritten).')
    p.add_argument('input', type=Path, help='original fastp or parallel.py HTML report')
    p.add_argument('output', type=Path, help='new HTML path; parent directory must exist')
    a = p.parse_args()
    try:
        convert(a.input, a.output)
    except (OSError, ValueError) as error:
        p.exit(1, 'fastp-report-offline: ' + str(error) + '\n')

if __name__ == '__main__':
    main()
