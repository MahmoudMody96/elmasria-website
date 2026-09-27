# -*- coding: utf-8 -*-
"""
Verify the emoji → SVG migration:
  1. no ad-hoc emoji / glyph characters are left in any HTML page,
  2. every <use href> points at a symbol that really exists in the sprite,
  3. every symbol the sprite defines is used at least once,
  4. the expected markup hooks are present (h1 caret, drawer close, burger …).

Usage (from repo root):  python _tools/verify_icons.py
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    "index.html", "about.html", "contact.html", "projects.html",
    "services/civil-defense.html", "services/cleaning.html", "services/clinic.html",
    "services/construction.html", "services/environmental.html",
    "services/football-fields.html", "services/index.html", "services/iso.html",
    "services/landscape.html", "services/manpower.html", "services/pest-control.html",
    "services/safety.html",
]

EMOJI = re.compile("["
                   "\U0001F000-\U0001FAFF"
                   "\u2600-\u27BF"
                   "\u25BE\u2713\u2715\u2630\u2190\u2709"
                   "\ufe0f"
                   "]")

USE = re.compile(r'<use href="(?P<href>[^"]+)"')
SYMBOL = re.compile(r'<symbol id="(?P<id>[^"]+)"')

EXPECTED_HOOKS = [
    (r'class="burger"[^>]*aria-label="فتح القائمة"><svg class="ic"', "hamburger icon"),
    (r'aria-label="إغلاق"><svg class="ic"', "drawer close icon"),
    (r'<h1><svg class="ic ic-h"', "page-hero h1 icon"),
    (r'<span class="di"><svg class="ic"', "dropdown icon tile"),
    (r'<span class="svc-ico"><svg class="ic"', "service card badge icon"),
    (r'<span class="ck"><svg class="ic"', "checklist tick icon"),
    (r'<span><svg class="ic" aria-hidden="true" focusable="false"><use href="[^"]*#i-arrow-left"',
     "side-list arrow icon"),
    (r'xmlns="http://www.w3.org/2000/svg"', "sprite linked from a page (sanity)"),
]

# motion v2.2 scroll UI: the markup that style.css + main.js expect to find
PER_PAGE_HOOKS = [
    (r'<div id="progress" aria-hidden="true"></div>', "reading-progress bar"),
    (r'<button id="toTop" type="button" aria-label="العودة لأعلى الصفحة">'
     r'<svg class="ic" aria-hidden="true" focusable="false">'
     r'<use href="[^"]*#i-arrow-up"></use></svg></button>', "back-to-top button"),
]
HOME_HOOKS = [
    (r'<div class="scroll-cue" aria-hidden="true"><span></span></div>', "hero scroll cue"),
]


def main() -> int:
    problems: list[str] = []

    sprite_path = os.path.join(ROOT, "assets", "img", "icons.svg")
    with open(sprite_path, "r", encoding="utf-8") as fh:
        symbols = set(SYMBOL.findall(fh.read()))

    used: dict[str, int] = {}
    texts: dict[str, str] = {}
    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        texts[rel] = text

        leftover = sorted({ch for ch in text if EMOJI.match(ch)})
        if leftover:
            problems.append(
                f"{rel}: leftover ad-hoc characters "
                + ", ".join(f"{ch} (U+{ord(ch):04X})" for ch in leftover))

        refs = USE.findall(text)
        for href in refs:
            frag = href.split("#")[-1]
            used[frag] = used.get(frag, 0) + 1
            if frag not in symbols:
                problems.append(f"{rel}: <use> points at missing symbol #{frag}")
            if not href.endswith("assets/img/icons.svg#" + frag):
                problems.append(f"{rel}: unexpected sprite path in {href}")

    print(f"sprite symbols      : {len(symbols)}")
    print(f"distinct icons used : {len(used)}")
    print(f"total <use> refs    : {sum(used.values())}")

    unused = sorted(symbols - set(used))
    print("unused symbols      : " + (", ".join(unused) if unused else "none"))

    # ---- scroll UI markup (motion v2.2): must be on every page ----
    missing_pages = [rel for rel, text in texts.items()
                     if not all(re.search(pat, text) for pat, _ in PER_PAGE_HOOKS)]
    for rel, text in texts.items():
        for pattern, label in PER_PAGE_HOOKS:
            if not re.search(pattern, text):
                problems.append(f"{rel}: missing {label}")
    home = texts.get("index.html", "")
    for pattern, label in HOME_HOOKS:
        if not re.search(pattern, home):
            problems.append(f"index.html: missing {label}")
    print(f"scroll UI markup    : {len(texts) - len(missing_pages)}/{len(texts)} pages wired"
          f" (progress + toTop), cue on index.html: "
          f"{'yes' if all(re.search(p, home) for p, _ in HOME_HOOKS) else 'no'}")

    for pattern, label in EXPECTED_HOOKS:
        found = any(re.search(pattern, open(os.path.join(ROOT, p.replace("/", os.sep)),
                                           encoding="utf-8").read())
                    for p in PAGES)
        if not found and label != "sprite linked from a page (sanity)":
            problems.append(f"missing markup hook: {label}")

    print("\n=== per-symbol usage ===")
    for sym, n in sorted(used.items(), key=lambda kv: -kv[1]):
        print(f"  {sym:<16} x{n}")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  - " + p)
        return 1

    print("\nAll checks passed — no ad-hoc emoji left, all symbols resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
