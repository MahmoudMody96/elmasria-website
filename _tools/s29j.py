# -*- coding: utf-8 -*-
"""SEO v29-J: keep twitter:title/description in sync with og: on every page."""
import glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rd(p):
    with open(p, encoding='utf-8') as f: return f.read()
def wr(p, t):
    with open(p, 'w', encoding='utf-8', newline='\r\n') as f: f.write(t)
n = 0
files = sorted(glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, 'services', '*.html')))
for path in files:
    sub = os.path.relpath(path, ROOT).replace(os.sep, '/')
    t0 = rd(path); t = t0
    ogt = re.search(r'<meta property="og:title" content="([^"]*)"', t)
    ogd = re.search(r'<meta property="og:description" content="([^"]*)"', t)
    if ogt:
        t = re.sub(r'(<meta name="twitter:title" content=")[^"]*(")', lambda m: m.group(1) + ogt.group(1) + m.group(2), t, count=1)
    if ogd:
        t = re.sub(r'(<meta name="twitter:description" content=")[^"]*(")', lambda m: m.group(1) + ogd.group(1) + m.group(2), t, count=1)
    if t != t0: wr(path, t); n += 1; print('J-fixed ' + sub)
print('J-DONE ' + str(n))
