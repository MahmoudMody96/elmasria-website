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
    mh = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
    h1 = re.sub(r'<[^>]+>', '', mh.group(1)).strip() if mh else ''
    h1 = re.sub(r'\s+', ' ', h1)[:80]
    t = re.sub(r'(<div class="ph-bg"><img[^>]*?)alt=""', lambda m: m.group(1) + 'alt="' + h1 + '"', t, count=1)
    t = re.sub(r'(<div class="hero-media"[^>]*>\s*<img[^>]*?)alt=""', lambda m: m.group(1) + 'alt="' + h1 + '"', t, count=1)
    ogt = re.search(r'property="og:title" content="([^"]*)"', t)
    ogd = re.search(r'property="og:description" content="([^"]*)"', t)
    add = ''
    if ogt and 'twitter:title' not in t: add += '\n<meta name="twitter:title" content="' + ogt.group(1) + '">'
    if ogd and 'twitter:description' not in t: add += '\n<meta name="twitter:description" content="' + ogd.group(1) + '">'
    if add: t = t.replace('content="summary_large_image">', 'content="summary_large_image">' + add, 1)
    if t != t0: wr(path, t); n += 1; print('A-fixed ' + sub)
print('A-DONE ' + str(n))
