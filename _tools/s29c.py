import glob, os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    if 'BreadcrumbList' in t: continue
    canon = re.search(r'rel="canonical" href="([^"]*)"', t)
    url = canon.group(1) if canon else ''
    org = url.rsplit('/services/', 1)[0] if '/services/' in url else ''
    crumbs = re.findall(r'<nav class="crumb"[^>]*>(.*?)</nav>', t, re.S)
    items = []
    if crumbs:
        links = re.findall(r'<a href="([^"]*)"[^>]*>(.*?)</a>', crumbs[0], re.S)
        spans = re.findall(r'<span>(.*?)</span>', crumbs[0], re.S)
        pos = 1
        for href, txt in links:
            txt = re.sub(r'<[^>]+>', '', txt).strip()
            if not txt: continue
            ahref = href
            if href.startswith('../'): ahref = org + '/' + href[3:]
            elif href.startswith('./'): ahref = org + '/services/' + href[2:]
            items.append({'@type': 'ListItem', 'position': pos, 'name': txt, 'item': ahref})
            pos += 1
        for s in spans:
            s = re.sub(r'<[^>]+>', '', s).strip()
            if not s or s in ('\u2039', '<', '>', '/', '|'): continue
            items.append({'@type': 'ListItem', 'position': pos, 'name': s, 'item': url})
            pos += 1
    if not items:
        mh = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
        h1 = re.sub(r'<[^>]+>', '', mh.group(1)).strip() if mh else name
        items = [{'@type': 'ListItem', 'position': 1, 'name': h1, 'item': url}]
    bl = json.dumps({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': items}, ensure_ascii=False)
    t = t.replace('</script>', '</script>\n<script type="application/ld+json">' + bl + '</script>', 1)
    wr(path, t); n += 1; print('C-fixed ' + sub)
print('C-DONE ' + str(n))
