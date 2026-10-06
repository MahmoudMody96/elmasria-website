import glob, os, re, json
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
    if 'FAQPage' in t: continue
    faqs = re.findall(r'<details class="faq"><summary>(.*?)</summary><p>(.*?)</p></details>', t, re.S)
    if not faqs: continue
    ents = [{'@type': 'Question', 'name': re.sub(r'<[^>]+>', '', q).strip(), 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'<[^>]+>', '', a).strip()}} for q, a in faqs]
    fl = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': ents}, ensure_ascii=False)
    t = t.replace('</script>', '</script>\n<script type="application/ld+json">' + fl + '</script>', 1)
    wr(path, t); n += 1; print('D-fixed ' + sub + ' q=' + str(len(ents)))
print('D-DONE ' + str(n))
