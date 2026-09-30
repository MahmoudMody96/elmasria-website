# -*- coding: utf-8 -*-
"""
Normalize the shared chrome and the social metadata of every page — idempotent,
so it can be re-run any time (and used as a checker).

What it fixes
  1. mobile drawer  : drop the hard-coded aria-hidden="true" (it hid the whole menu
                      from screen readers even while open) and give the panel
                      role="dialog" + an accessible name,
  2. burger button  : add aria-expanded="false" / aria-controls="drawer" (main.js
                      keeps aria-expanded in sync),
  3. dropdown       : remove role="menu" (its children are plain links, so the ARIA
                      pattern was invalid),
  4. services hub   : link the canonical /services/ URL instead of /services/index.html
                      (two URLs for one page),
  5. footer year    : wrap it in <span id="yy"> and let main.js refresh it on every
                      page instead of a hard-coded "© 2026" (plus the inline script
                      that only index.html had),
  6. social meta    : og:image → the 1200x630 og-cover.png with its dimensions,
                      and fill in og:site_name / og:description / twitter:card on
                      every page that lacks them.

Usage (from repo root):
    python _tools/normalize_pages.py            # apply
    python _tools/normalize_pages.py --check    # verify only (exit 1 on drift)
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    "index.html", "about.html", "contact.html", "projects.html", "404.html",
    "services/civil-defense.html", "services/cleaning.html", "services/clinic.html",
    "services/construction.html", "services/environmental.html",
    "services/football-fields.html", "services/index.html", "services/iso.html",
    "services/landscape.html", "services/manpower.html", "services/pest-control.html",
    "services/safety.html",
]
# 404 is noindex: it keeps the icon + footer wiring but gets no share card
SOCIAL_PAGES = [p for p in PAGES if p != "404.html"]

SITE_NAME = "EL MASRIA — المصرية للسلامة والصحة المهنية"

# النطاق بيُقرأ من مصدر الحقيقة الوحيد (`_tools/site_origin.txt`) — ممنوع يتكتب هنا.
# القيمة المكتوبة يدويًا كانت بتقدِم: فضلت على النطاق القديم بعد ما الصفحات اتحدّثت،
# فأي إعادة تشغيل كانت هترجّع `og:image` للنطاق القديم في ١٦ صفحة.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from set_origin import read_origin  # noqa: E402

COVER = read_origin() + "/assets/img/og-cover.png"
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
BURGER = '<button class="burger" id="burger" aria-label="فتح القائمة">'
BURGER_FIXED = ('<button class="burger" id="burger" aria-label="فتح القائمة" '
                'aria-expanded="false" aria-controls="drawer">')


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def chrome(text: str, rel: str) -> tuple[str, int]:
    """aria + links + footer year; returns (text, change count)."""
    hits = 0

    text, n = re.subn(r'<div class="drawer" id="drawer" aria-hidden="true">',
                      '<div class="drawer" id="drawer">', text)
    hits += n

    text, n = re.subn(r'<aside class="panel">',
                      '<aside class="panel" role="dialog" aria-label="قائمة التنقل">', text)
    hits += n

    if BURGER in text:
        text = text.replace(BURGER, BURGER_FIXED)
        hits += 1

    text, n = re.subn(r'<div class="drop" role="menu">', '<div class="drop">', text)
    hits += n

    if rel.startswith("services/"):
        text, n = re.subn(r'href="index\.html"', 'href="./"', text)
    else:
        text, n = re.subn(r'href="(\.\./|/)?services/index\.html"',
                          r'href="\1services/"', text)
    hits += n

    text, n = re.subn(r'© 2026 ', '© <span id="yy">2026</span> ', text)
    hits += n

    text, n = re.subn(r'\s*<script>document\.getElementById\(\'yy\'\)\.textContent = '
                      r'new Date\(\)\.getFullYear\(\);</script>', '', text)
    hits += n
    return text, hits


def social(text: str) -> tuple[str, int]:
    """Complete the share card on pages that can be shared."""
    hits = 0
    desc = DESC_RE.search(text)
    desc = desc.group(1) if desc else ""

    # one cover image for every platform, at the right aspect ratio
    if COVER not in text:
        text, n = re.subn(r'(<meta property="og:image" content=")[^"]*(">)',
                          r'\1' + COVER + r'\2', text)
        hits += n
        text, n = re.subn(r'(<meta name="twitter:image" content=")[^"]*(">)',
                          r'\1' + COVER + r'\2', text)
        hits += n

    if 'property="og:image:width"' not in text:
        text, n = re.subn(r'(\n?)(<meta property="og:image" content="[^"]*">)',
                          r'\1\2\n<meta property="og:image:width" content="1200">'
                          r'\n<meta property="og:image:height" content="630">', text)
        hits += n

    if 'property="og:site_name"' not in text:
        text, n = re.subn(r'(<meta property="og:locale" content="[^"]*">)',
                          r'\1\n<meta property="og:site_name" content="' + SITE_NAME + r'">',
                          text)
        hits += n

    if 'property="og:description"' not in text and desc:
        text, n = re.subn(r'(<meta property="og:title" content="[^"]*">)',
                          r'\1\n<meta property="og:description" content="' + desc + r'">',
                          text)
        hits += n

    if 'name="twitter:card"' not in text:
        text, n = re.subn(r'(<meta name="twitter:image")',
                          r'<meta name="twitter:card" content="summary_large_image">\n\1',
                          text)
        hits += n
    return text, hits


def check() -> int:
    problems: list[str] = []
    for rel in PAGES:
        text = read(os.path.join(ROOT, rel.replace("/", os.sep)))
        if 'id="drawer" aria-hidden="true"' in text:
            problems.append(f"{rel}: mobile drawer is still hidden from assistive tech")
        if BURGER in text:
            problems.append(f"{rel}: burger button has no aria-expanded/aria-controls")
        if 'role="menu"' in text:
            problems.append(f"{rel}: dropdown still claims role=\"menu\" without menuitems")
        if 'services/index.html' in text:
            problems.append(f"{rel}: still links services/index.html (use services/)")
        if '<span id="yy">' not in text:
            problems.append(f"{rel}: footer year is hard-coded (needs #yy)")
        if rel in SOCIAL_PAGES:
            for needle, why in (
                (COVER, "share card is not the 1200x630 og-cover.png"),
                ('property="og:image:width"', "missing og:image:width/height"),
                ('property="og:site_name"', "missing og:site_name"),
                ('property="og:description"', "missing og:description"),
                ('name="twitter:card"', "missing twitter:card"),
            ):
                if needle not in text:
                    problems.append(f"{rel}: {why}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  - " + p)
        return 1
    print(f"page chrome OK: aria wiring, canonical hub links, live footer year and "
          f"complete share cards on {len(SOCIAL_PAGES)} pages")
    return 0


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return check()

    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        text = read(path)
        new, n1 = chrome(text, rel)
        new, n2 = social(new) if rel in SOCIAL_PAGES else (new, 0)
        if new != text:
            write(path, new)
            print(f"  {rel:<34} {n1} chrome + {n2} social fixes")
    return check()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
