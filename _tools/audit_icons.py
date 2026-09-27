# -*- coding: utf-8 -*-
"""
Audit: report every ad-hoc unicode emoji / glyph character used in the HTML pages,
grouped by the markup context it sits in (so we know which CSS hooks are needed).

Usage (from repo root):  python _tools/audit_icons.py
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT_PAGES = ["index.html", "about.html", "contact.html", "projects.html"]
SERVICE_PAGES = [
    "civil-defense.html", "cleaning.html", "clinic.html", "construction.html",
    "environmental.html", "football-fields.html", "index.html", "iso.html",
    "landscape.html", "manpower.html", "pest-control.html", "safety.html",
]
PAGES = ROOT_PAGES + ["services/" + p for p in SERVICE_PAGES]

VS16 = "\ufe0f"

# emoji / glyph + optional variation selector-16
TARGET = re.compile(
    "["
    "\U0001F000-\U0001FAFF"
    "\u2600-\u27BF"
    "\u25BE\u2713\u2715\u2630\u2190\u2709"
    "\ufe0f"
    "]"
)


def scan(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    contexts = defaultdict(lambda: defaultdict(int))
    attrs = defaultdict(int)
    total = defaultdict(int)

    for m in TARGET.finditer(text):
        ch = m.group()
        if ch == VS16:
            continue
        total[ch] += 1

        # attribute detection: nearest unclosed quote before the match
        before = text[max(0, m.start() - 400):m.start()]
        open_q = max(before.rfind('"'), before.rfind("'"))
        close_q = max(before.rfind('"'), before.rfind("'"))
        tag_open = before.rfind("<")
        tag_close = before.rfind(">")
        if tag_open > tag_close and before.count('"') % 2 == 1:
            attrs[ch] += 1
            continue

        # context = last class="..." and the tag it belongs to
        classes = re.findall(r'class="([^"]{0,80})"', before)
        tags = re.findall(r"<([a-zA-Z0-9]+)[^<>]*$", before)
        key = (tags[-1] if tags else "?", classes[-1] if classes else "-")
        contexts[key][ch] += 1

    return total, contexts, attrs


def main() -> int:
    grand = defaultdict(int)
    all_ctx = defaultdict(lambda: defaultdict(int))
    all_attrs = defaultdict(int)

    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        total, contexts, attrs = scan(path)
        for ch, n in total.items():
            grand[ch] += n
        for key, counters in contexts.items():
            for ch, n in counters.items():
                all_ctx[key][ch] += n
        for ch, n in attrs.items():
            all_attrs[ch] += n
        print(f"{rel}: {sum(total.values())} occurrences")

    print("\n=== totals per character ===")
    for ch, n in sorted(grand.items(), key=lambda kv: -kv[1]):
        print(f"  {ch} (U+{ord(ch):04X}) x{n}")

    print("\n=== occurrences inside HTML attributes (cannot become inline SVG) ===")
    if not all_attrs:
        print("  none")
    for ch, n in sorted(all_attrs.items(), key=lambda kv: -kv[1]):
        print(f"  {ch} (U+{ord(ch):04X}) x{n}")

    print("\n=== markup contexts ===")
    for key, counters in sorted(all_ctx.items(), key=lambda kv: -sum(kv[1].values())):
        parts = ", ".join(f"{ch}x{n}" for ch, n in sorted(counters.items(), key=lambda kv: -kv[1]))
        print(f"  <{key[0]}> .{key[1]} => {parts}")

    print(f"\nTOTAL: {sum(grand.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
