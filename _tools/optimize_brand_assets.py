# -*- coding: utf-8 -*-
"""
Derive the small, web-sized brand assets from the master logo files and rewire
every page to the derivatives.

Masters (never modified — the source of truth):
    assets/img/logo.png         1500x1500  full lock-up (emblem + wordmark)
    assets/img/logo-emblem.png  1255x1255  circular emblem only

Derived (what the site actually downloads):
    assets/img/favicon-32.png        32x32     browser tab icon
    assets/img/favicon-180.png      180x180    apple-touch-icon
    assets/img/logo-emblem-128.png  128x128    header / footer / drawer (<=56px @2x)
    assets/img/logo-emblem-192.png  192x192    hero identity card, 1x candidate
    assets/img/logo-emblem-384.png  384x384    hero identity card, 2x candidate
    assets/img/og-cover.png        1200x630    social share card (og:image)

Before this tool the site shipped 446 KB (logo.png as favicon) + 435 KB
(emblem at 1255px shown at 52px) on *every* first load — ~880 KB per visitor
for two images that need ~25 KB in total.

Usage (from repo root):
    python _tools/optimize_brand_assets.py            # build derivatives + rewire pages
    python _tools/optimize_brand_assets.py --build     # rebuild derivatives only
    python _tools/optimize_brand_assets.py --rewire    # only rewire the pages
    python _tools/optimize_brand_assets.py --check     # verify wiring/sizes (exit 1 on drift)
"""
from __future__ import annotations

import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    "index.html", "about.html", "contact.html", "projects.html", "404.html",
    "services/civil-defense.html", "services/cleaning.html", "services/clinic.html",
    "services/construction.html", "services/environmental.html",
    "services/football-fields.html", "services/index.html", "services/iso.html",
    "services/landscape.html", "services/manpower.html", "services/pest-control.html",
    "services/safety.html",
]

LOGO = os.path.join(ROOT, "assets", "img", "logo.png")
EMBLEM = os.path.join(ROOT, "assets", "img", "logo-emblem.png")

# name -> (source, side, max bytes) — max bytes is the drift guard for --check
DERIVED = {
    "favicon-32.png": (EMBLEM, 32, 6_000),
    "favicon-180.png": (EMBLEM, 180, 30_000),
    "logo-emblem-128.png": (EMBLEM, 128, 25_000),
    "logo-emblem-192.png": (EMBLEM, 192, 45_000),
    "logo-emblem-384.png": (EMBLEM, 384, 130_000),
}

COVER = "og-cover.png"
COVER_SIZE = (1200, 630)
G950 = (6, 36, 51)
G700 = (26, 155, 215)
ORG = (242, 101, 34)
MUT = (159, 179, 189)
W = (255, 255, 255)

FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\segoeui.ttf"),
    (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for bold_path, path in FONT_CANDIDATES:
        chosen = bold_path if bold else path
        if os.path.exists(chosen):
            return ImageFont.truetype(chosen, size)
    raise SystemExit("no usable TTF font found for og-cover.png (install DejaVu/Segoe UI)")


def _resize(src: str, side: int) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    return im.resize((side, side), Image.LANCZOS)


def build_one(name: str, source: str, side: int) -> int:
    out = os.path.join(ROOT, "assets", "img", name)
    _resize(source, side).save(out, "PNG", optimize=True)
    return os.path.getsize(out)


def build_cover() -> int:
    """1200x630 social card: brand dark field + emblem + Latin lock-up.

    Latin only on purpose: PIL cannot shape Arabic script, and the Arabic name
    travels in og:title / og:description where the platform renders it correctly.
    """
    card = Image.new("RGB", COVER_SIZE, G950)
    draw = ImageDraw.Draw(card, "RGBA")

    # the site's diagonal signature band
    draw.polygon([(0, 0), (0, COVER_SIZE[1]), (220, COVER_SIZE[1]), (120, 0)], fill=ORG + (38,))
    draw.polygon([(0, 0), (0, 150), (330, 0)], fill=G700 + (30,))
    draw.rectangle([0, COVER_SIZE[1] - 10, COVER_SIZE[0], COVER_SIZE[1]], fill=ORG)

    emblem_side = 300
    emblem = _resize(EMBLEM, emblem_side)
    card.paste(emblem, ((COVER_SIZE[0] - emblem_side) // 2, 58), emblem)

    draw.text((COVER_SIZE[0] // 2, 470), "EL MASRIA", font=_font(76, bold=True),
              fill=W, anchor="mm")
    draw.line([(COVER_SIZE[0] // 2 - 90, 528), (COVER_SIZE[0] // 2 + 90, 528)],
              fill=ORG, width=5)
    draw.text((COVER_SIZE[0] // 2, 566),
              "SINCE 1999  ·  SAFETY  ·  ENGINEERING  ·  ENVIRONMENT",
              font=_font(24), fill=MUT, anchor="mm")

    out = os.path.join(ROOT, "assets", "img", COVER)
    card.save(out, "PNG", optimize=True)
    return os.path.getsize(out)


def build() -> None:
    total_master = os.path.getsize(LOGO) + os.path.getsize(EMBLEM)
    total_derived = 0
    for name, (source, side, _cap) in DERIVED.items():
        size = build_one(name, source, side)
        total_derived += size
        print(f"  assets/img/{name:<24} {side:>4}px  {size / 1024:7.1f} KB")
    cover_size = build_cover()
    total_derived += cover_size
    print(f"  assets/img/{COVER:<24} 1200x630 {cover_size / 1024:7.1f} KB")
    print(f"  masters kept: {total_master / 1024:.1f} KB (no longer downloaded by pages)")
    print(f"  derivatives : {total_derived / 1024:.1f} KB")


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def rewire(text: str) -> tuple[str, int]:
    hits = 0

    # header / footer brand tile + mobile drawer logo -> the 128px emblem
    for cls in ("brand-logo", "drawer-logo"):
        pattern = r'(class="' + cls + r'" src=")((?:\.\./)?assets/img/)logo-emblem\.png'
        text, n = re.subn(pattern, r"\1\2logo-emblem-128.png", text)
        hits += n

    # hero identity card -> srcset (192w for 1x, 384w for 2x of a 190px box)
    pattern = (r'<img src="((?:\.\./)?assets/img/)logo-emblem\.png" '
               r'(alt="[^"]*" fetchpriority="high")')
    text, n = re.subn(
        pattern,
        r'<img src="\1logo-emblem-384.png" srcset="\1logo-emblem-192.png 192w, '
        r'\1logo-emblem-384.png 384w" sizes="190px" \2',
        text)
    hits += n

    # favicon + apple-touch-icon -> the real small icons
    text, n = re.subn(
        r'(<link rel="icon" type="image/png" href=")((?:\.\./)?|/)assets/img/logo\.png(">)',
        r'\1\2assets/img/favicon-32.png\3', text)
    hits += n
    text, n = re.subn(
        r'(<link rel="apple-touch-icon" href=")((?:\.\./)?|/)assets/img/logo\.png(">)',
        r'\1\2assets/img/favicon-180.png\3', text)
    hits += n
    return text, hits


def check() -> int:
    problems: list[str] = []
    for name, (_source, side, cap) in DERIVED.items():
        path = os.path.join(ROOT, "assets", "img", name)
        if not os.path.exists(path):
            problems.append(f"missing derivative assets/img/{name}")
            continue
        with Image.open(path) as im:
            if im.size != (side, side):
                problems.append(f"{name}: {im.size} != {(side, side)}")
        size = os.path.getsize(path)
        if size > cap:
            problems.append(f"{name}: {size / 1024:.1f} KB exceeds the {cap / 1024:.0f} KB budget")
    cover = os.path.join(ROOT, "assets", "img", COVER)
    if not os.path.exists(cover):
        problems.append(f"missing assets/img/{COVER}")
    else:
        with Image.open(cover) as im:
            if im.size != COVER_SIZE:
                problems.append(f"{COVER}: {im.size} != {COVER_SIZE}")

    for rel in PAGES:
        text = read(os.path.join(ROOT, rel.replace("/", os.sep)))
        for needle, why in (('logo-emblem.png', "unoptimized emblem"),
                            ('logo.png', "unoptimized logo")):
            for m in re.finditer(re.escape(needle), text):
                line = text[:m.start()].count("\n") + 1
                fragment = text[m.start():m.start() + 80].replace("\n", " ")
                problems.append(f"{rel}:{line} {why} still referenced — {fragment}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  - " + p)
        return 1
    print("brand assets OK: every derivative exists at the right size and no page "
          "downloads logo.png / logo-emblem.png any more")
    return 0


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return check()

    if "--rewire" not in argv:
        print("building brand derivatives …")
        build()
        if "--build" in argv:
            return 0

    total = 0
    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        text = read(path)
        new, hits = rewire(text)
        if new != text:
            write(path, new)
            print(f"  {rel:<34} {hits} rewired")
        total += hits
    print(f"rewired {total} references across {len(PAGES)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
