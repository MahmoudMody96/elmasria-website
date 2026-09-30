#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حارس سياسة البريد الإلكتروني — EL MASRIA
=========================================

السياسة (قرار المالك، 2026-09-30):

  الموقع **لا يعرض بريدًا إلكترونيًا إطلاقًا**. قناة التواصل الرسمية هي
  **الواتساب** (wa.me/201000101040) والهاتف (tel:)، ونموذج التواصل في
  `contact.html` يبني رسالة واتساب جاهزة عبر `main.js`.

  قبل قرار 2026-09-30 كان `info@elmasria-eg.com` يُعرض في الشريط العلوي
  والفوتر وصفحة التواصل ويُستخدم كهدف `mailto:` للنموذج. أُلغي بالكامل لأن
  البريد كان هدفًا شبه ميت (لا أحد يراقبه) بينما الواتساب قناة حيّة.

ما يمنعه هذا الحارس:
  1. **أي بريد إلكتروني** يظهر في `mailto:` أو نص العرض في أي صفحة أو JS.
     (يكشف أي بريد، لا `elmasria-eg.com` بعينه — لأن السياسة «صفر بريد للعرض».)
  2. أي `mailto:` متبقٍّ في الوسم أو الـJS.
  3. الرمز `i-mail` وهو غير مستخدم في الـsprite ولا في أي صفحة
     (إن أُضيف رمز البريد مستقبلًا فهذا يعني نقضًا للسياسة).
  4. الرمز `#waSend` أو الزر القديم «إرسال عبر البريد الرسمي» في `contact.html`.

التغطية:
  * يُكتشف الملفات بـglob: `*.html` + `services/*.html` + `assets/js/*.js`
    + `assets/css/*.css` — فأي صفحة جديدة تُغطّى تلقائيًا بلا تعديل هنا.
  * يُستثنى من الفحص: كل مجلد `.git` و`_tools/` (توثيق وتقارير داخلية لا تُنشر)
    وملفات `*.md` (قد تذكر البريد في التوثيق التاريخي).

الاستخدام:
    python _tools/verify_mail_policy.py          # فحص (exit 1 عند أي خرق)
    python _tools/verify_mail_policy.py --list   # يعرض كل قواعد الفحص
"""

import re
import sys
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ملفات/مجلدات مستثناة (توثيق داخلي لا يُنشر)
SKIP_DIRS = {".git", "_tools", "_backup_review", "node_modules", "__pycache__"}
SKIP_SUFFIX = (".md",)

# أنماط الخرق: (اسم القاعدة، regex، وصف)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
MAILTO_RE = re.compile(r"mailto:", re.IGNORECASE)
OLD_SUBMIT_RE = re.compile(r"waSend|إرسال عبر البريد")
I_MAIL_RE = re.compile(r"#i-mail\b")

RULES = [
    ("EMAIL", EMAIL_RE, "بريد إلكتروني ظاهر (السياسة: صفر بريد معروض — القناة واتساب)"),
    ("MAILTO", MAILTO_RE, "هدف mailto: متبقٍّ (لازم يتحوّل لواتساب/هاتف)"),
    ("OLDFORM", OLD_SUBMIT_RE, "بقايا الزر القديم (waSend / إرسال عبر البريد)"),
    ("IMAIL", I_MAIL_RE, "مرجع للرمز i-mail (أُزيل في v28 — لو رجع يبقى نقض القرار)"),
]


def iter_files():
    pats = [
        os.path.join(ROOT, "*.html"),
        os.path.join(ROOT, "services", "*.html"),
        os.path.join(ROOT, "assets", "js", "*.js"),
        os.path.join(ROOT, "assets", "css", "*.css"),
    ]
    for p in pats:
        for f in sorted(glob.glob(p)):
            rel = os.path.relpath(f, ROOT).replace("\\", "/")
            if any(part in SKIP_DIRS for part in rel.split("/")):
                continue
            if rel.endswith(SKIP_SUFFIX):
                continue
            yield f, rel


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def main():
    if "--list" in sys.argv:
        print("قواعد الفحص:")
        for name, _, desc in RULES:
            print(f"  {name:8} — {desc}")
        return 0

    violations = []
    files = list(iter_files())
    for path, rel in files:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for name, rx, desc in RULES:
            for m in rx.finditer(text):
                ln = line_of(text, m.start())
                snippet = text[m.start():m.start() + 60].splitlines()[0]
                violations.append((rel, ln, name, snippet, desc))

    print(f"ملفات مفحوصة : {len(files)}")
    print(f"القناة المعتمدة: الواتساب wa.me/201000101040 + الهاتف tel:")

    if violations:
        print(f"\n❌ FAIL — {len(violations)} خرق لسياسة البريد:\n")
        for rel, ln, name, snip, desc in violations:
            print(f"  [{name}] {rel}:{ln}")
            print(f"         {desc}")
            print(f"         → {snip}")
        return 1

    print("\nOK  صفر بريد معروض · صفر mailto: · صفر بقايا النموذج القديم.")
    print("    القناة الوحيدة للتواصل هي الواتساب والهاتف — كما في BRAND.md/README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
