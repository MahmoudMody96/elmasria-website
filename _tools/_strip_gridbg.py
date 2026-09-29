#!/usr/bin/env python3
"""شيل `grid-bg` و `grid-bg-d` من كلاسات الـHTML (الأنماط اتشالت من CSS).

بيشيل الرمز من الـclass attribute، ولو الخاصية فضيت بيشيل الخاصية نفسها.
بيتحقق من كل ملف ويبلّغ — وميفشلش بصمت.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = ("grid-bg", "grid-bg-d")

files = []
for pat in ("*.html", "*/*.html"):
    files.extend(glob.glob(os.path.join(ROOT, pat)))
files = sorted(f for f in set(files)
               if ".workbuddy-ai" not in f and "_tools" not in f)

total = 0
changed_files = []
for path in files:
    text = open(path, encoding="utf-8").read()
    before = text.count("grid-bg")
    if not before:
        continue

    def fix_class(m):
        raw = m.group(1)
        tokens = raw.split()
        kept = [t for t in tokens if t not in TARGETS]
        if not kept:
            return ""                      # الخاصية فضيت — نشيلها بالكامل
        return 'class="' + " ".join(kept) + '"'

    new = re.sub(r'class="([^"]*)"', fix_class, text)
    after = new.count("grid-bg")
    if after:
        print(f"FAIL  {os.path.relpath(path, ROOT)}: فاضل {after} بعد التنظيف")
        sys.exit(1)
    open(path, "w", encoding="utf-8", newline="").write(new)
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    changed_files.append(rel)
    total += before
    print(f"OK    {rel:28s} شال {before}")

print(f"\nاتعدّل {len(changed_files)} ملف — اتشال {total} رمز")

# تحقق أخير: مفيش grid-bg في أي HTML
leftover = []
for path in files:
    if "grid-bg" in open(path, encoding="utf-8").read():
        leftover.append(os.path.relpath(path, ROOT))
print("باقي في HTML:", leftover if leftover else "صفر ✓")
sys.exit(1 if leftover else 0)
