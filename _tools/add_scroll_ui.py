# -*- coding: utf-8 -*-
"""
Wire the scroll UI that style.css already styles (motion v2.2 rules):

  #progress   fixed reading-progress bar      → first element inside <body>
  #toTop      back-to-top button (i-arrow-up) → right before the main.js <script>
  .scroll-cue hero "scroll down" indicator    → inside the home hero only

CSS, JS and the sprite already existed; only the markup was missing.
The tool is idempotent (re-running it changes nothing) and keeps the CRLF
line endings the pages ship with.

Usage (from repo root):
    python _tools/add_scroll_ui.py --check   # dry run, report only
    python _tools/add_scroll_ui.py           # rewrite the HTML files
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT_PAGES = ["index.html", "about.html", "contact.html", "projects.html", "404.html"]
SERVICE_PAGES = [
    "civil-defense.html", "cleaning.html", "clinic.html", "construction.html",
    "environmental.html", "football-fields.html", "index.html", "iso.html",
    "landscape.html", "manpower.html", "pest-control.html", "safety.html",
]
PAGES = [(p, "") for p in ROOT_PAGES] + [("services/" + p, "../") for p in SERVICE_PAGES]

PROGRESS = '<div id="progress" aria-hidden="true"></div>'


def totop(base: str) -> str:
    return ('<button id="toTop" type="button" aria-label="العودة لأعلى الصفحة">'
            '<svg class="ic" aria-hidden="true" focusable="false">'
            f'<use href="{base}assets/img/icons.svg#i-arrow-up"></use></svg></button>')


CUE = '<div class="scroll-cue" aria-hidden="true"><span></span></div>'


def insert_after_body(text: str) -> tuple[str, bool]:
    """Put the progress bar as the first element inside <body>."""
    m = re.search(r"<body[^>]*>\r?\n", text)
    if not m:
        return text, False
    return text[:m.end()] + PROGRESS + "\n" + text[m.end():], True


def insert_before_script(text: str, markup: str, needle: str) -> tuple[str, bool]:
    """Insert `markup` on its own line just before the line holding `needle`."""
    at = text.find(needle)
    if at < 0:
        return text, False
    line_start = text.rfind("\n", 0, at) + 1
    return text[:line_start] + markup + "\n" + text[line_start:], True


def insert_before_line(text: str, markup: str, needle: str, indent: str = "") -> tuple[str, bool]:
    """Insert `markup` (with indentation) just before the line holding `needle`."""
    at = text.find(needle)
    if at < 0:
        return text, False
    line_start = text.rfind("\n", 0, at) + 1
    return text[:line_start] + indent + markup + "\n" + text[line_start:], True


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    problems: list[str] = []

    for rel, base in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print(f"{rel:<32} missing — skipped")
            continue

        with open(path, "r", encoding="utf-8", newline="") as fh:
            original = fh.read()
        newline = "\r\n" if "\r\n" in original else "\n"
        text = original
        added: list[str] = []

        if 'id="progress"' not in text:
            text, ok = insert_after_body(text)
            if ok:
                added.append("progress")
            else:
                problems.append(f"{rel}: no <body> tag found")

        if 'id="toTop"' not in text:
            text, ok = insert_before_script(text, totop(base), f'{base}assets/js/main.js')
            if ok:
                added.append("toTop")
            else:
                problems.append(f"{rel}: main.js <script> tag not found")

        if 'class="scroll-cue"' not in text and re.search(r'class="[^"]*\bhero-inner\b', text):
            text, ok = insert_before_line(text, CUE, '<div class="hero-diagonal"', "  ")
            if ok:
                added.append("scroll-cue")
            else:
                problems.append(f"{rel}: hero found but no hero-diagonal anchor")

        text = text.replace("\r\n", "\n").replace("\n", newline)
        print(f"{rel:<32} {'added: ' + ', '.join(added) if added else 'already wired'}")

        if not check_only and text != original:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  - " + p)
        return 1

    print("\nScroll UI markup is in place on every page."
          + ("  (dry run — nothing written)" if check_only else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
