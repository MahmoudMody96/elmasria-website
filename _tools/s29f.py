import glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAV1 = '<nav aria-label="NAVQUICK"><h4>'
NAV2 = '<nav aria-label="NAVSVC"><h4>'
def rd(p):
    with open(p, encoding='utf-8') as f: return f.read()
def wr(p, t):
    with open(p, 'w', encoding='utf-8', newline='\r\n') as f: f.write(t)
q1 = q2 = None
n = 0
files = sorted(glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, 'services', '*.html')))
for path in files:
    sub = os.path.relpath(path, ROOT).replace(os.sep, '/')
    name = os.path.basename(path)
    t0 = rd(path); t = t0
    if q1 is None:
        m1 = re.search(r'<nav aria-label="([^"]*)"><h4>', t)
        if m1: q1 = m1.group(1)
        m2s = re.findall(r'<nav aria-label="([^"]*)"><h4>', t)
        if len(m2s) > 1: q2 = m2s[1]
    if q1: t = t.replace('<nav aria-label="' + q1 + '"><h4>', '<nav aria-label="' + q1 + '"><h2 class="foot-h">')
    if q2: t = t.replace('<nav aria-label="' + q2 + '"><h4>', '<nav aria-label="' + q2 + '"><h2 class="foot-h">')
    if sub.startswith('services/') and name != 'index.html':
        m = re.search(r'<div class="side-card dark"><h3>(.*?)</h3>', t)
        if m: t = t.replace(m.group(0), '<div class="side-card dark"><h2 class="side-h">' + m.group(1) + '</h2>')
        m = re.search(r'<div class="side-card"><h3>(.*?)</h3>', t)
        if m: t = t.replace(m.group(0), '<div class="side-card"><h2 class="side-h">' + m.group(1) + '</h2>')
    if sub == 'projects.html':
        t = t.replace('<div class="why-card reveal"><h3>', '<div class="why-card reveal"><h2 class="why-h">')
        t = t.replace('<div class="why-card o reveal"><h3>', '<div class="why-card o reveal"><h2 class="why-h">')
    if sub == 'services/index.html':
        ms = re.findall(r'<div><h3>(.*?)</h3></div>', t)
        for mm in set(ms):
            t = t.replace('<div><h3>' + mm + '</h3></div>', '<div><h2 class="cluster-h">' + mm + '</h2></div>')
        ms2 = re.findall(r'<div class="cf-body"><h4>(<a href=.*?</a>)</h4>', t, re.S)
        for mm in set(ms2):
            t = t.replace('<div class="cf-body"><h4>' + mm + '</h4>', '<div class="cf-body"><h3 class="cf-h">' + mm + '</h3>')
    if t != t0: wr(path, t); n += 1; print('F-fixed ' + sub)
print('F-DONE ' + str(n))
