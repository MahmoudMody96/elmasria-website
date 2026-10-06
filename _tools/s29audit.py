# -*- coding: utf-8 -*-
"""SEO audit v29: titles/desc/heads/alt/jumps check (ASCII output only)."""
import glob, os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = sorted(glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, 'services', '*.html')))
issues = 0
for path in files:
    sub = os.path.relpath(path, ROOT).replace(os.sep, '/')
    is404 = os.path.basename(path) == '404.html'
    t = open(path, encoding='utf-8').read()
    prob = []
    ti = re.search(r'<title>(.*?)</title>', t, re.S)
    title = re.sub(r'\s+', ' ', ti.group(1)).strip() if ti else 'MISSING'
    if not ti or len(title) < 25: prob.append('title-len=' + str(len(title)))
    md = re.search(r'<meta name="description" content="([^"]*)"', t)
    d = md.group(1) if md else ''
    if not d: prob.append('desc-missing')
    elif not is404 and len(d) > 170: prob.append('desc-long=' + str(len(d)))
    elif not is404 and len(d) < 110: prob.append('desc-short=' + str(len(d)))
    if 'rel="canonical"' not in t and not is404: prob.append('no-canonical')
    if 'twitter:title' not in t and not is404: prob.append('no-tw-title')
    h1s = re.findall(r'<h1[^>]*>', t)
    if len(h1s) != 1: prob.append('h1-count=' + str(len(h1s)))
    for im in re.findall(r'<img[^>]*>', t):
        if 'alt=' not in im: prob.append('img-no-alt')
    heads = [int(h[1]) for h in re.findall(r'<(h[1-6])[^>]*>', t)]
    for i in range(1, len(heads)):
        if heads[i] - heads[i-1] > 1: prob.append('jump h' + str(heads[i-1]) + '-h' + str(heads[i])); break
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try: json.loads(b)
        except Exception: prob.append('bad-jsonld')
    if prob:
        issues += 1
        print('ISSUE ' + sub + ' :: ' + ','.join(sorted(set(prob))))
print('AUDIT issues=' + str(issues) + ' pages=' + str(len(files)))
