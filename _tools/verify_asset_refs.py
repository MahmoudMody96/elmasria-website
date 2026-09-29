#!/usr/bin/env python3
"""حارس مراجع الأصول — كل ملف يشير إليه الوسم أو CSS لازم يكون موجودًا فعلًا.

السبب: في v23 اتكشفت 45 صورة محذوفة من `assets/img/photos/` (حذف خارج git،
بلا أي كوميت بيسجّله). تسعة منها كانت مستخدمة فعليًا في `index.html` و`contact.html`
— يعني الموقع كان هيعرض صورًا مكسورة بمجرد أي `git add -A`. الحارس ده بيمنع تكرارها.

بيغطّي:
  · `src` و`srcset` في كل ملفات HTML (بما فيها قوائم srcset بفواصل)
  · `href` للروابط المحلية (صفحات، CSS، أيقونة، manifest…)
  · `url(...)` في `assets/css/style.css`

الاستثناءات: http/https، `//`، `data:`، `mailto:`، `tel:`، `#`، والفراغ.
المسار اللي يبدأ بـ`/` بيتفسّر من جذر الموقع مش من مجلد الصفحة.

الاستخدام:
    python _tools/verify_asset_refs.py          # تقرير + exit 1 لو فيه ناقص
"""
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"_tools", ".git", ".workbuddy-ai"}
SKIP_SCHEMES = ("http://", "https://", "//", "data:", "mailto:", "tel:", "javascript:")

# src / srcset / href  (نتجاهل href داخل <use> لأن مرجع الـsprite بيفحصه verify_icons.py)
ATTR = re.compile(r'\b(?:src|srcset|href)\s*=\s*"([^"]*)"', re.I)
CSS_URL = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', re.I)


def is_skippable(url: str) -> bool:
    u = url.strip()
    if not u:
        return True
    low = u.lower()
    return low.startswith(SKIP_SCHEMES) or u.startswith("#")


def candidates(raw: str):
    """يرجّع روابط فردية من قيمة src/srcset."""
    if "," in raw:
        for part in raw.split(","):
            part = part.strip()
            if part:
                yield part.split()[0]
    else:
        yield raw.strip()


def resolve(page_dir: str, url: str):
    """يرجّع المسار النسبي للجذر، أو None لو الرابط مش مرجع ملف (فراغ/مرساة).

    بيتعامل مع الروابط المجلدية: `services/` و`./` بتتحوّل لـ`index.html`
    جوه المجلد — وهي مراجع سليمة مش ناقصة.
    """
    u = url.split("?")[0].split("#")[0].strip()
    if not u:
        return None
    is_dir_ref = u.endswith("/") or u.endswith(os.sep)
    if u.startswith("/"):
        target = os.path.normpath(u.lstrip("/")) if u.lstrip("/") else "."
    else:
        target = os.path.normpath(os.path.join(page_dir, u))
    return target, is_dir_ref


def exists(target: str, is_dir_ref: bool) -> bool:
    full = os.path.join(ROOT, target)
    if os.path.isfile(full):
        return True
    # مرجع مجلد → index.html جواه
    if is_dir_ref or os.path.isdir(full):
        if os.path.isfile(os.path.join(full, "index.html")):
            return True
    return False


def main() -> int:
    pages = [
        p for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
        if not any(seg in SKIP_DIRS for seg in p.replace(ROOT, "").split(os.sep))
    ]
    missing = []
    checked = 0

    for page in pages:
        rel_page = os.path.relpath(page, ROOT).replace("\\", "/")
        page_dir = os.path.dirname(rel_page)
        text = open(page, encoding="utf-8").read()
        for m in ATTR.finditer(text):
            for url in candidates(m.group(1)):
                if is_skippable(url):
                    continue
                resolved = resolve(page_dir, url)
                if resolved is None:
                    continue
                target, is_dir_ref = resolved
                checked += 1
                if not exists(target, is_dir_ref):
                    missing.append((rel_page, url))

    css = os.path.join(ROOT, "assets", "css", "style.css")
    if os.path.isfile(css):
        text = open(css, encoding="utf-8").read()
        for m in CSS_URL.finditer(text):
            url = m.group(1).strip()
            if is_skippable(url):
                continue
            resolved = resolve("assets/css", url)
            if resolved is None:
                continue
            target, is_dir_ref = resolved
            checked += 1
            if not exists(target, is_dir_ref):
                missing.append(("assets/css/style.css", url))

    print(f"صفحات HTML مفحوصة: {len(pages)}")
    print(f"مراجع أصول مفحوصة: {checked}")
    if missing:
        print(f"\nFAIL — {len(missing)} مرجع يشير إلى ملف غير موجود:")
        for page, url in missing:
            print(f"  {page}  ->  {url}")
        return 1
    print("\nOK  كل مراجع الأصول (صور · srcset · روابط · url() في CSS) موجودة على القرص.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
