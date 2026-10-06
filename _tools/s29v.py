import glob, os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = 0
okn = 0
files = sorted(glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, 'services', '*.html')))
for path in files:
    sub = os.path.relpath(path, ROOT).replace(os.sep, '/')
    t = open(path, encoding='utf-8').read()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
    for b in blocks:
        try:
            json.loads(b); okn += 1
        except Exception as e:
            bad += 1; print('BAD ' + sub + ' err=' + str(e)[:80])
print('JSON-OK blocks=' + str(okn) + ' bad=' + str(bad))
