# -*- coding: utf-8 -*-
"""v30 — استضافة الخطوط محليًا + width/height للصور + og:image:alt (أداة لمرة واحدة).

ثلاثة تعديلات على كل صفحات HTML (الجذر + services/ + 404):
  1) إزالة سطور Google Fonts الثلاثة (preconnect ×2 + stylesheet) وإدراج بدلها:
     preload لملفي الخط العربي الحرجين (Cairo variable + IBM Plex 400) + fonts.css محلي.
  2) إضافة width/height لكل <img> محلي يفتقدهما (من أبعاد الملف الفعلية عبر PIL).
  3) إدراج <meta property="og:image:alt"> (نفس محتوى og:title) بعد og:image:height.

الاستخدام:
  python _tools/v30_seo.py            # معاينة (لا كتابة)
  python _tools/v30_seo.py --apply    # كتابة فعلية
"""
import re
import sys
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
APPLY = '--apply' in sys.argv

CAIRO_AR = '93eb7989.woff2'   # Cairo variable — arabic subset (كل الأوزان 600-900)
PLEX400_AR = '00b30da7.woff2'  # IBM Plex Sans Arabic 400 — arabic subset

# التحقق من وجود ملفي الخط قبل أي شيء
for f in (CAIRO_AR, PLEX400_AR):
    p = ROOT / 'assets/fonts' / f
    assert p.exists() and p.stat().st_size > 1000, f'missing font file: {p}'

pages = sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('services/*.html'))
assert len(pages) == 17, f'expected 17 pages, got {len(pages)}'

RE_STYLESHEET = re.compile(
    r'<link href="https://fonts\.googleapis\.com/css2\?family=[^"]+" rel="stylesheet">')
RE_IMG = re.compile(r'<img\b[^>]*>')
RE_SRC = re.compile(r'\bsrc="([^"]+)"')

stats = {'fonts': 0, 'dims': 0, 'ogalt': 0, 'skip_dims': 0}
for page in pages:
    rel = page.relative_to(ROOT).as_posix()
    prefix = '/' if rel == '404.html' else ('../' if '/' in rel else '')
    with open(page, encoding='utf-8', newline='') as fh: text = fh.read()
    orig = text

    # -- 1) الخطوط ------------------------------------------------------------
    n_pre = text.count('<link rel="preconnect" href="https://fonts.googleapis.com">')
    n_pre2 = text.count('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    assert n_pre == 1 and n_pre2 == 1, f'{rel}: preconnect x{n_pre}/{n_pre2}'
    m = RE_STYLESHEET.search(text)
    assert m, f'{rel}: no google fonts stylesheet'
    block = (
        f'<link rel="preload" as="font" type="font/woff2" crossorigin href="{prefix}assets/fonts/{CAIRO_AR}">'
        f'<link rel="preload" as="font" type="font/woff2" crossorigin href="{prefix}assets/fonts/{PLEX400_AR}">'
        f'<link rel="stylesheet" href="{prefix}assets/css/fonts.css?v=29">'
    )
    # سطور الـpreconnect الثلاثة متتالية على سطر واحد أو ثلاثة أسطر — نشيل كل واحد
    # مع الـCRLF الذي يسبقه (أو يليه) حتى لا نبقي أسطرًا فارغة.
    text = re.sub(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\r?\n?', '', text)
    text = re.sub(r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\r?\n?', '', text)
    text = RE_STYLESHEET.sub(block, text, count=1)
    stats['fonts'] += 1

    # -- 2) width/height ------------------------------------------------------
    def add_dims(mo):
        tag = mo.group(0)
        if 'width=' in tag or 'height=' in tag:
            stats['skip_dims'] += 1
            return tag
        sm = RE_SRC.search(tag)
        if not sm or sm.group(1).startswith(('http', '/', 'data:')):
            stats['skip_dims'] += 1
            return tag
        f = (page.parent / sm.group(1)).resolve()
        if not f.exists():
            stats['skip_dims'] += 1
            return tag
        w, h = Image.open(f).size
        stats['dims'] += 1
        return tag.replace('<img ', f'<img width="{w}" height="{h}" ', 1)
    text = RE_IMG.sub(add_dims, text)

    # -- 3) og:image:alt ------------------------------------------------------
    if 'og:image:alt' not in text and 'og:image:height' in text:
        tm = re.search(r'<meta property="og:title" content="([^"]+)">', text)
        hm = re.search(r'(<meta property="og:image:height" content="\d+">)', text)
        assert tm and hm, f'{rel}: og:title/og:image:height not found'
        text = text.replace(hm.group(1), hm.group(1) + f'\r\n<meta property="og:image:alt" content="{tm.group(1)}">', 1)
        stats['ogalt'] += 1

    if text != orig:
        print(f'{rel}: changed')
        if APPLY:
            with open(page, 'w', encoding='utf-8', newline='') as fh: fh.write(text)

print('SUMMARY', stats, 'APPLY' if APPLY else 'DRY-RUN')
