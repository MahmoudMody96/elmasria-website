# -*- coding: utf-8 -*-
"""
Normalize the line endings of the site's HTML pages back to CRLF (the convention
the repository ships with). Run from repo root:

    python _tools/normalize_eol.py          # convert to CRLF
    python _tools/normalize_eol.py --check  # report only
"""
from __future__ import annotations

import os
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
    check_only = "--check" in argv
    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print(f"{rel:<34} missing — skipped")
            continue
        with open(path, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
        crlf = text.count("\r\n")
        lf_only = text.count("\n") - crlf
        if lf_only == 0:
            print(f"{rel:<34} already CRLF")
            continue
        if check_only:
            print(f"{rel:<34} {lf_only} LF-only lines (needs CRLF)")
            continue
        fixed = text.replace("\r\n", "\n").replace("\n", "\r\n")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(fixed)
        print(f"{rel:<34} converted {lf_only} LF → CRLF")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
