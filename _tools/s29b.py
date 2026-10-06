import glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN = 'https://elmasria.aidy.site'
def rd(p):
    with open(p, encoding='utf-8') as f: return f.read()
def wr(p, t):
    with open(p, 'w', encoding='utf-8', newline='\r\n') as f: f.write(t)
n = 0
files = sorted(glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, 'services', '*.html')))
for path in files:
    sub = os.path.relpath(path, ROOT).replace(os.sep, '/')
    name = os.path.basename(path)
    t0 = rd(path); t = t0
    if sub == 'index.html':
        t = t.replace('"telephone":"+20-109-608-7999"', '"telephone":"+20-100-010-1040"')
        if '"logo"' not in t:
            t = t.replace('"url":"' + ORIGIN + '/",', '"url":"' + ORIGIN + '/","logo":"' + ORIGIN + '/assets/img/logo-emblem-192.png",', 1)
    if sub == 'about.html' and '"logo"' not in t:
        t = t.replace('"foundingDate":"1999"', '"url":"' + ORIGIN + '/","logo":"' + ORIGIN + '/assets/img/logo-emblem-192.png","foundingDate":"1999"', 1)
    if sub == 'contact.html' and '"openingHours"' not in t:
        t = t.replace('"address":{"@type":"PostalAddress"', '"openingHours":"Mo-Sa 09:00-18:00","address":{"@type":"PostalAddress"', 1)
    if sub == 'projects.html' and 'BreadcrumbList' not in t:
        if sub == 'index.html': url = ORIGIN + '/'
        elif sub == 'services/index.html': url = ORIGIN + '/services/'
        else: url = ORIGIN + '/' + sub
        bl = '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[]}'
        t = t.replace('</head>', '<script type="application/ld+json">' + bl + '</script>\n</head>', 1)
    if t != t0: wr(path, t); n += 1; print('B-fixed ' + sub)
print('B-DONE ' + str(n))
