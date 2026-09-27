# -*- coding: utf-8 -*-
"""
Migrate ad-hoc unicode emoji / glyph characters in the EL MASRIA static site
to references of the shared SVG sprite (assets/img/icons.svg).

Every replaced character becomes:
    <svg class="ic" aria-hidden="true" focusable="false">
      <use href="assets/img/icons.svg#i-xxx"></use>
    </svg>
(root pages) or the same with a "../" prefix for services/*.html.

Usage (from repo root):
    python _tools/migrate_icons.py --check   # dry run, report only
    python _tools/migrate_icons.py           # rewrite the HTML files
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT_PAGES = ["index.html", "about.html", "contact.html", "projects.html"]
SERVICE_PAGES = [
    "civil-defense.html", "cleaning.html", "clinic.html", "construction.html",
    "environmental.html", "football-fields.html", "index.html", "iso.html",
    "landscape.html", "manpower.html", "pest-control.html", "safety.html",
]
PAGES = [(p, "") for p in ROOT_PAGES] + [("services/" + p, "../") for p in SERVICE_PAGES]

VS16 = "\ufe0f"

# ad-hoc character -> sprite symbol id
ICONS = {
    # UI / structural
    "\u2630": "i-menu",            # ☰ hamburger
    "\u2715": "i-x",               # ✕ drawer close
    "\u2713": "i-check",           # ✓ checklist tick
    "\u25be": "i-chevron-down",    # ▾ menu caret
    "\u2190": "i-arrow-left",      # ← link arrow
    # services
    "\U0001F9BA": "i-vest",        # 🦺 safety & health
    "\U0001F9EF": "i-extinguisher",  # 🧯 civil defense / fire
    "\U0001F6E1": "i-bug",         # 🛡️ pest control
    "\U0001F33F": "i-leaf",        # 🌿 environmental studies
    "\U0001F4CB": "i-clipboard",   # 📋 ISO
    "\U0001F477": "i-hat",         # 👷 manpower
    "\U0001F3D7": "i-crane",       # 🏗️ construction
    "\u2728": "i-sparkles",        # ✨ cleaning
    "\U0001F333": "i-tree",        # 🌳 landscape
    "\u26D1": "i-cross",           # ⛑️ clinic
    "\u26BD": "i-ball",            # ⚽ football fields
    # contact
    "\U0001F4DE": "i-phone",       # 📞
    "\u2709": "i-mail",            # ✉️
    "\U0001F4CD": "i-pin",         # 📍
    # about / values
    "\U0001F3AF": "i-crosshair",   # 🎯 vision & goals
    "\u2705": "i-check-circle",    # ✅ quality
    "\U0001F91D": "i-handshake",   # 🤝 principle
    "\U0001F465": "i-users",       # 👥 team
    "\U0001F50D": "i-search",      # 🔍 supervision & quality
    "\U0001F4C8": "i-trending",    # 📈 efficiency
    "\u267E": "i-infinity",        # ♾️ continuity
    # why / projects
    "\U0001F4DC": "i-file",        # 📜 legal commitment
    "\U0001F3ED": "i-factory",     # 🏭 consulting + execution
    "\u2699": "i-tool",            # ⚙️ operation contracts
}

EMO_ALT = "|".join(re.escape(ch) for ch in sorted(ICONS, key=len, reverse=True))
EMO_ANY = re.compile("(?:" + EMO_ALT + ")\ufe0f?")


def build_svg(symbol: str, base: str, cls: str = "ic") -> str:
    return (
        f'<svg class="{cls}" aria-hidden="true" focusable="false">'
        f'<use href="{base}assets/img/icons.svg#{symbol}"></use></svg>'
    )



def convert(text: str, base: str):
    """Return (converted_text, {char: replacement_count})."""
    counts: dict[str, int] = {}

    def svg_of(ch: str, cls: str = "ic") -> str:
        return build_svg(ICONS[ch], base, cls)

    def hit(ch: str) -> None:
        counts[ch] = counts.get(ch, 0) + 1

    # 1) dropdown menu icon tiles: <span class="di">🦺</span> / <span class="di o">☰</span>
    def _di(m: re.Match) -> str:
        hit(m.group("e"))
        return f'{m.group(1)}{svg_of(m.group("e"))}{m.group(3)}'

    text = re.sub(
        r'(<span class="di(?: o)?">)\s*(?P<e>' + EMO_ALT + r')\ufe0f?\s*(</span>)', _di, text)

    # 2) service card corner badge: <span class="svc-ico">🦺</span>
    def _svc(m: re.Match) -> str:
        hit(m.group("e"))
        return f'{m.group(1)}{svg_of(m.group("e"))}{m.group(3)}'

    text = re.sub(
        r'(<span class="svc-ico">)\s*(?P<e>' + EMO_ALT + r')\ufe0f?\s*(</span>)', _svc, text)

    # 3) checklist tick: <span class="ck">✓</span>
    def _ck(m: re.Match) -> str:
        hit(m.group("e"))
        return f'{m.group(1)}{svg_of(m.group("e"))}{m.group(3)}'

    text = re.sub(
        r'(<span class="ck">)\s*(?P<e>' + EMO_ALT + r')\ufe0f?\s*(</span>)', _ck, text)

    # 4) page / section headings: <h1>🦺 نص</h1>, <h3 style="…">✉️ نص</h3>
    def _head(m: re.Match) -> str:
        ch = m.group("e")
        hit(ch)
        cls = "ic ic-h" if m.group("lv") == "1" else "ic"
        return f'{m.group(1)}{svg_of(ch, cls)} '

    text = re.sub(
        r'(<h(?P<lv>[1-6])(?:\s[^>]*)?>)\s*(?P<e>' + EMO_ALT + r')\ufe0f?\s*', _head, text)

    # 5) hamburger button: <button class="burger" …>☰</button>
    def _burger(m: re.Match) -> str:
        hit(m.group("e"))
        return f'{m.group(1)}{svg_of(m.group("e"))}{m.group(3)}'

    text = re.sub(
        r'(aria-label="فتح القائمة">)\s*(?P<e>' + EMO_ALT + r')\ufe0f?\s*(</button>)',
        _burger, text)

    # 6) drawer close button: <button data-close …>✕</button>
    def _close(m: re.Match) -> str:
        hit(m.group("e"))
        return f'{m.group(1)}{svg_of(m.group("e"))}{m.group(3)}'

    text = re.sub(
        r'(aria-label="إغلاق">)\s*(?P<e>' + EMO_ALT + r')\ufe0f?\s*(</button>)',
        _close, text)

    # 7) services caret in the top navigation: خدماتنا ▾
    def _caret(m: re.Match) -> str:
        hit(m.group("e"))
        return svg_of(m.group("e"))

    text = re.sub(r'(?P<e>\u25be)\ufe0f?', _caret, text)

    # 8) footer contact rows: <li>📞 <span>…, <li>✉️ <a>…, <li>📍 <span>…
    def _li(m: re.Match) -> str:
        hit(m.group("e"))
        return f'{m.group(1)}{svg_of(m.group("e"))} '

    text = re.sub(r'(<li>)\s*(?P<e>' + EMO_ALT + r')\ufe0f?\s+', _li, text)

    # 9) leading icon inside links / buttons with text: >📞 01096087999</a>
    def _lead(m: re.Match) -> str:
        hit(m.group("e"))
        return f'>{svg_of(m.group("e"))} '

    text = re.sub(r'>(?P<e>' + EMO_ALT + r')\ufe0f?\s+', _lead, text)

    # 10) link arrows: "تفاصيل الخدمة ←</a>" and side-list "<span>←</span>"
    def _arrow(m: re.Match) -> str:
        hit("\u2190")
        return f' {svg_of("\u2190")}{m.group(1)}'

    text = re.sub(r'\s*\u2190\s*(</a>)', _arrow, text)

    def _arrow_span(m: re.Match) -> str:
        hit("\u2190")
        return f'<span>{svg_of("\u2190")}</span>'

    text = re.sub(r'<span>\s*\u2190\s*</span>', _arrow_span, text)

    # 11) catch-all for anything left (an emoji used inline in prose)
    def _any(m: re.Match) -> str:
        hit(m.group("e"))
        return svg_of(m.group("e"))

    text = re.sub(r'(?P<e>' + EMO_ALT + r')\ufe0f?', _any, text)

    return text, counts


EMO_SCAN = re.compile("["
                      "\U0001F000-\U0001FAFF"
                      "\u2600-\u27BF"
                      "\u25BE\u2713\u2715\u2630\u2190\u2709"
                      "\ufe0f"
                      "]")


def leftovers(text: str) -> list[str]:
    """Return the ad-hoc characters still present in the given markup."""
    found = sorted({ch for ch in text if EMO_SCAN.match(ch)})
    return [f"{ch} (U+{ord(ch):04X})" for ch in found]


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    grand: dict[str, int] = {}
    failures: list[str] = []

    for rel, base in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        with open(path, "r", encoding="utf-8", newline="") as fh:
            original = fh.read()
        newline = "\r\n" if "\r\n" in original else "\n"

        converted, counts = convert(original, base)
        # keep the newline convention the file shipped with (the repo uses CRLF in HTML)
        converted = converted.replace("\r\n", "\n").replace("\n", newline)
        left = leftovers(converted)

        for ch, n in counts.items():
            grand[ch] = grand.get(ch, 0) + n

        status = "OK" if not left else "LEFT: " + ", ".join(left)
        if left:
            failures.append(f"{rel}: {status}")
        print(f"{rel:<32} replaced {sum(counts.values()):>3} icons   {status}")

        if not check_only and converted != original:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(converted)

    print(f"\nTOTAL replaced: {sum(grand.values())} across {len(PAGES)} pages")
    for ch, n in sorted(grand.items(), key=lambda kv: -kv[1]):
        print(f"  {ch} (U+{ord(ch):04X}) x{n} -> {ICONS[ch]}")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

