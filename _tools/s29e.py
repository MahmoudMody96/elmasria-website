import glob, os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN = 'https://elmasria.aidy.site'
def rd(p):
    with open(p, encoding='utf-8') as f: return f.read()
def wr(p, t):
    with open(p, 'w', encoding='utf-8', newline='\r\n') as f: f.write(t)
n = 0
for path in sorted(glob.glob(os.path.join(ROOT, 'services', '*.html'))):
    sub = os.path.relpath(path, ROOT).replace(os.sep, '/')
    name = os.path.basename(path)
    if name == 'index.html': continue
    t0 = rd(path); t = t0
    md = re.search(r'<meta name="description" content="([^"]*)">', t)
    desc = md.group(1) if md else ''
    def repl(m):
        b = m.group(0)
        if '"description"' not in b:
            b = b.replace('"provider":', '"description":' + json.dumps(desc, ensure_ascii=False) + ',"provider":', 1)
        if '"foundingDate":"1999"' in b and ORIGIN not in b.split('"provider"')[1][:200]:
            b = b.replace('"foundingDate":"1999"', '"url":"' + ORIGIN + '/","foundingDate":"1999"', 1)
        return b
    t = re.sub(r'<script type="application/ld\+json">\{"@context":"https://schema\.org","@type":"Service".*?\}</script>', repl, t, count=1)
    if t != t0: wr(path, t); n += 1; print('E-fixed ' + sub)
print('E-DONE ' + str(n))
