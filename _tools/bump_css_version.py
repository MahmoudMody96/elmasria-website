# -*- coding: utf-8 -*-
"""
Bump the style.css cache-buster (?v=N) in every page.

The stylesheet gained the v2.3 icon-context rules, so returning visitors must not
keep the cached copy. Run from repo root:

    python _tools/bump_css_version.py          # 3 -> 4
    python _tools/bump_css_version.py 3 5      # 3 -> 5
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


def main(argv: list[str]) -> int:
    old = argv[0] if argv else "3"
    new = argv[1] if len(argv) > 1 else str(int(old) + 1)
    pattern = re.compile(r"(assets/css/style\.css\?v=)" + re.escape(old) + r"\b")
    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print(f"{rel:<34} missing — skipped")
            continue
        with open(path, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
        updated, n = pattern.subn(r"\g<1>" + new, text)
        if not n:
            print(f"{rel:<34} no change")
            continue
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(updated)
        print(f"{rel:<34} style.css?v={old} → v={new} ({n})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
