# -*- coding: utf-8 -*-
"""
Bump the cache-buster (?v=N) of the front-end assets in every page.

Both assets carry their own version query:
    <link href="assets/css/style.css?v=N" …>
    <script src="assets/js/main.js?v=N" …>

A new value forces returning visitors (the pages are cached for 7 days) to
fetch the updated file, so run this after touching CSS **or** JS.

Usage (from repo root):
    python _tools/bump_css_version.py --set 5    # deterministic: both assets -> ?v=5
    python _tools/bump_css_version.py            # auto: every asset N -> max(N)+1
    python _tools/bump_css_version.py 4 5        # manual: ?v=4 -> ?v=5 (both assets)

`--set` is the safe one to re-run: it is idempotent, while the auto mode bumps
again on every run (run it once per asset change).
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


ASSETS = ["assets/css/style.css?v=", "assets/js/main.js?v="]


def main(argv: list[str]) -> int:
    set_to = None
    if "--set" in argv:
        i = argv.index("--set")
        set_to = argv[i + 1] if len(argv) > i + 1 else ""
        if not set_to.isdigit():
            print("usage: python _tools/bump_css_version.py --set <N>")
            return 2

    old = argv[0] if argv and not argv[0].startswith("--") else None
    new = argv[1] if len(argv) > 1 else (str(int(old) + 1) if old is not None else None)

    pages: dict[str, str] = {}
    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print(f"{rel:<34} missing — skipped")
            continue
        with open(path, "r", encoding="utf-8", newline="") as fh:
            pages[rel] = fh.read()

    # auto mode (no arguments) looks at the whole site and picks max(N)+1 per asset
    targets: dict[str, str] = {}
    if old is None and set_to is None:
        for asset in ASSETS:
            pattern = re.compile(re.escape(asset) + r"(\d+)")
            seen = {int(m.group(1)) for text in pages.values() for m in pattern.finditer(text)}
            if seen:
                targets[asset] = str(max(seen) + 1)
        print("auto mode — bumping to the next version; "
              "use `--set <N>` when you need a deterministic value.\n")

    for rel, text in pages.items():
        updated, notes = text, []
        for asset in ASSETS:
            name = asset.split("?")[0].split("/")[-1]
            pattern = re.compile(re.escape(asset) + r"(\d+)")
            current = sorted({m.group(1) for m in pattern.finditer(updated)})

            if not current:
                notes.append(f"{name}: not linked")
                continue
            if set_to is not None:
                target = set_to
            elif old is None:
                target = targets[asset]
            else:
                strict = re.compile(re.escape(asset + old) + r"\b")
                updated, n = strict.subn(asset + new, updated)
                notes.append(f"{name}:v{old} → v{new} ({n})" if n
                             else f"{name}: no v={old}")
                continue

            if current == [target]:
                notes.append(f"{name}:v{target} unchanged")
                continue
            updated = pattern.sub(f"{asset}{target}", updated)
            notes.append(f"{name}:v{'/v'.join(current)} → v{target}")

        if updated != text:
            path = os.path.join(ROOT, rel.replace("/", os.sep))
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(updated)
        print(f"{rel:<34} " + " · ".join(notes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
