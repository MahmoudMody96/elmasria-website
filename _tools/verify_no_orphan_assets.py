#!/usr/bin/env python3
"""حارس الأصول اليتيمة — أي ملف تحت `assets/` محدش بيشير إليه = يتيم.

السبب: في v25 اتكشفت 39 صورة يتيمة، وفي جلسة التنظيف (v27) الحارس القديم
(`cleanup_orphan_photos_v25.py`) شاف `chairman.png` و`logo.png` و`logo-emblem.png`
**يتامى** وكان هيحذفهم — مع إن:
  · `BRAND.md` بيعتبر `logo.png` **المصدر الوحيد للألوان**،
  · و`optimize_brand_assets.py` بيوصّف `logo.png`/`logo-emblem.png` بأنهم
    **المasters — «never modified — the source of truth»** وأي حذف ليهم بيكسر
    القدرة على توليد كل المشتقات،
  · و`chairman.png` هو **الأصل الوحيد لصورة الرئيس** في المستودع (قرار المستخدم).

الفخ الحقيقي: الحارس القديم كان بيفحص `.html/.css/.js` بس **وبيتخطّى `_tools`**.
يعني أي أصل بيُستشهد بيه من `*.md` أو من سكربت أدوات بيطلع «يتيم» غلط.
الحارس ده بيفحص **كل ملفات النص في المستودع** (html · css · js · xml · txt ·
md · py · sh · json · yml) عشان يقفل الفجوة دي.

⚠️ فرق مهم بين الحارسين:
  · `verify_asset_refs.py`  = «كل مرجع → الملف موجود» (ناقص = عطل).
  · `verify_no_orphan_assets.py` = «كل ملف → له مرجع» (يتيم = دَين).
  الاتنين مش بديلين لبعض.

قائمة الإعفاءات (ALLOW) لازم كل بند فيها **موجود فعلًا على القرص**، وإلا الحارس
بيفشل ويقولك إن الإعفاء بايت (stale) — عشان القائمة ما تكبرش للأبد بنسيان.

الاستخدام:
    python _tools/verify_no_orphan_assets.py            # تقرير + exit 1 لو فيه يتيم
    python _tools/verify_no_orphan_assets.py --list     # اطبع المراجع والمفحوص كمان
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ملفات النص اللي ممكن تشير لأصل. أي نوع جديد لازم يتضاف هنا.
REF_EXT = (".html", ".css", ".js", ".xml", ".txt", ".md", ".py", ".sh",
           ".json", ".yml", ".yaml", ".webmanifest", ".svg")

SKIP_DIRS = {".git", ".workbuddy-ai", "__pycache__", "node_modules", "_site"}

# أصول **مقصودة** بلا مرجع من أي صفحة: masters بتُولَّد منها المشتقات،
# وأصول مصدر مفردة المستودع هو آخر نسخة منها.
ALLOW = {
    "logo.png":
        "master logo — مصدر الألوان الوحيد في BRAND.md ومدخل optimize_brand_assets.py",
    "logo-emblem.png":
        "master emblem — الأصل اللي كل مشتقات الهيدر/الفوتر بتتولّد منه",
    "chairman.png":
        "الأصل الوحيد لصورة الرئيس في المستودع (قرار المستخدم: يفضل)",
}


def walk_files():
    """كل ملفات النص المرجعية + كل ملفات assets."""
    ref_files, asset_files = [], []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            if fn.endswith(REF_EXT):
                ref_files.append((rel, full))
            if rel.startswith("assets/"):
                asset_files.append(rel)
    return ref_files, asset_files


def main() -> int:
    verbose = "--list" in sys.argv

    ref_files, asset_files = walk_files()

    # نجمع كل نصوص الملفات المرجعية في كتلة واحدة → أسرع وأبسط من فحص ملف ملف.
    blob = []
    for rel, full in ref_files:
        try:
            blob.append(open(full, encoding="utf-8", errors="replace").read())
        except OSError:
            pass
    blob = "\n".join(blob)

    orphans = []
    for rel in sorted(asset_files):
        base = os.path.basename(rel)
        if base in ALLOW:
            continue
        if base not in blob:
            orphans.append(rel)

    # --- حارس الإعفاءات البايتة: كل بند في ALLOW لازم يكون موجود على القرص ---
    stale = [n for n in ALLOW if not os.path.isfile(os.path.join(ROOT, "assets", "img", n))]

    print(f"ملفات مرجعية مفحوصة : {len(ref_files)}")
    print(f"أصول مفحوصة        : {len(asset_files)}")
    print(f"إعفاءات معتمدة     : {len(ALLOW)}")
    if verbose:
        for n in sorted(ALLOW):
            print(f"   معفى: {n} — {ALLOW[n]}")

    rc = 0

    if stale:
        print(f"\nFAIL — {len(stale)} إعفاء بايت (الملف مش موجود على القرص):")
        for n in stale:
            print(f"  {n}")
        rc = 1

    if orphans:
        print(f"\nFAIL — {len(orphans)} أصل يتيم (محدش بيشير إليه):")
        for rel in orphans:
            size = os.path.getsize(os.path.join(ROOT, rel))
            print(f"  {rel}  ({size / 1024:.1f} KB)")
        print("\n  القرار: يا إما يتحذف، يا إما يُستخدم، يا إما يتضاف لـALLOW بسبب موثّق.")
        rc = 1

    if rc == 0:
        print("\nOK  مفيش أصل يتيم — كل ملف تحت assets/ له مرجع، وكل إعفاء لسه صالح.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
