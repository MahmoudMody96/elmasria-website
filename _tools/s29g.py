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
    m = re.search(r'<div class="info-card reveal">\s*<h3>(.*?)</h3>', t, re.S)
    if m: t = t.replace(m.group(0), '<div class="info-card reveal">\n<h2 class="card-h">' + m.group(1) + '</h2>')
    for mm in set(re.findall(r'<h3 style="margin-top:22px">(.*?)</h3>', t, re.S)):
        t = t.replace('<h3 style="margin-top:22px">' + mm + '</h3>', '<h2 class="card-h" style="margin-top:22px">' + mm + '</h2>')
    m = re.search(r'<div class="form-card reveal">\s*<h3 style="font-size:20px">(.*?)</h3>', t, re.S)
    if m: t = t.replace(m.group(0), '<div class="form-card reveal">\n<h2 class="card-h" style="font-size:20px">' + m.group(1) + '</h2>')
    m = re.search(r'<div><h4>(.*?)</h4>\s*<ul class="foot-contact">', t, re.S)
    if m: t = t.replace(m.group(0), '<div><h2 class="foot-h">' + m.group(1) + '</h2>\n<ul class="foot-contact">')
    if t != t0: wr(path, t); n += 1; print('G-fixed ' + sub)
print('G-DONE ' + str(n))
