#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بوابة تغطية الأصناف: تقارن الأصناف المستخدمة في HTML مع المُعرَّفة في CSS.

الاتجاهان مهمّان:
  1) صنف مستخدم في HTML وغير معرّف في CSS  -> خطأ (يصدر exit 1) لأنه يعني عنصرًا بلا تنسيق.
  2) صنف معرّف في CSS وغير مستخدم في HTML  -> تحذير فقط (كود ميت محتمل)،
     مع قائمة إعفاء للأصناف التي يضيفها JS وقت التشغيل.

الفحص يمرّ على كل ملفات HTML في المستودع (وليس ملفًا واحدًا) لأن أي تقسيم
أو إعادة هيكلة تنقل الأصناف بين الملفات وتكسر حارسًا يقرأ ملفًا واحدًا.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "assets", "css", "style.css")

# أصناف تُضاف/تُزال من JS فقط، فلا يجوز اعتبارها كودًا ميتًا.
JS_APPLIED = {
    "in", "active", "open", "is-open", "show", "hidden", "on",
    "reveal-in", "drop-open", "loading", "loaded", "scrolled",
}

CLASS_ATTR = re.compile(r'class\s*=\s*"([^"]*)"')
CSS_CLASS = re.compile(r'\.(-?[_a-zA-Z][\w-]*)')


def html_files():
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "_tools", ".workbuddy-ai"}]
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.join(base, f))
    return sorted(out)


def used_classes():
    used = {}
    for path in html_files():
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for m in CLASS_ATTR.finditer(text):
            for tok in m.group(1).split():
                used.setdefault(tok, set()).add(os.path.relpath(path, ROOT).replace("\\", "/"))
    return used


def defined_classes():
    text = io.open(CSS, encoding="utf-8", errors="replace").read()
    # اشطب التعليقات حتى لا تُحسب أصناف مذكورة في شرح
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return set(CSS_CLASS.findall(text))


def main():
    used = used_classes()
    defined = defined_classes()

    missing = sorted(c for c in used if c not in defined)
    dead = sorted(c for c in defined if c not in used and c not in JS_APPLIED)

    print("ملفات HTML المفحوصة : %d" % len(html_files()))
    print("أصناف في HTML        : %d" % len(used))
    print("أصناف في CSS         : %d" % len(defined))
    print()

    if missing:
        print("!! أصناف مستخدمة في HTML وغير معرّفة في CSS (%d):" % len(missing))
        for c in missing:
            where = ", ".join(sorted(used[c])[:4])
            print("   .%-26s %s" % (c, where))
    else:
        print("OK  لا يوجد صنف مستخدم في HTML بدون تعريف في CSS.")

    if dead:
        print()
        print("~~ أصناف معرّفة في CSS وغير مستخدمة في HTML (%d) — كود ميت محتمل:" % len(dead))
        for c in dead:
            print("   .%s" % c)

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
