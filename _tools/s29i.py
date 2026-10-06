# -*- coding: utf-8 -*-
"""SEO v29-I: add <lastmod> to sitemap.xml from file mtimes (ISO 8601)."""
import os, re, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'sitemap.xml')
with open(p, encoding='utf-8') as f: t = f.read()
def lastmod(m):
    rel = m.group(1).replace('https://elmasria.aidy.site/', '').replace('https://elmasria.aidy.site', '')
    fp = os.path.join(ROOT, rel.replace('/', os.sep))
    if rel in ('', '/'): fp = os.path.join(ROOT, 'index.html')
    if rel.endswith('/'): fp = os.path.join(ROOT, rel, 'index.html')
    if not os.path.exists(fp): return m.group(0)
    ts = datetime.datetime.utcfromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d')
    return '<loc>' + m.group(1) + '</loc><lastmod>' + ts + '</lastmod>'
t2 = re.sub(r'<loc>([^<]+)</loc>(?!<lastmod>)', lastmod, t)
if t2 != t:
    with open(p, 'w', encoding='utf-8', newline='\r\n') as f: f.write(t2)
    print('I-DONE lastmod added, urls=' + str(t2.count('<lastmod>')))
else:
    print('I-DONE unchanged')
