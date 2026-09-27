# -*- coding: utf-8 -*-
"""
Answer one question with data: are the CSS colour tokens really the logo identity?

It reads assets/img/logo.png, extracts the dominant colours from the actual
pixels (transparent ones excluded) and compares them, both ways, with the
:root tokens of assets/css/style.css and the hex values claimed in BRAND.md.

Usage (from repo root):
    python _tools/logo_palette.py            # top colours + token comparison
    python _tools/logo_palette.py --top 20   # show more dominant colours
"""
from __future__ import annotations

import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "assets", "img", "logo.png")
CSS = os.path.join(ROOT, "assets", "css", "style.css")
BRAND = os.path.join(ROOT, "BRAND.md")

HEX = re.compile(r"#([0-9a-fA-F]{6})\b")
TOKEN = re.compile(r"--([a-z0-9-]+)\s*:\s*#([0-9a-fA-F]{6})\b")


def rgb(hexstr: str) -> tuple[int, int, int]:
    h = hexstr.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hexstr(c: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % c


def distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Redmean colour distance — a cheap perceptual approximation."""
    r1, g1, b1, r2, g2, b2 = *a, *b
    rm = (r1 + r2) / 2
    return ((2 + rm / 256) * (r1 - r2) ** 2
            + 4 * (g1 - g2) ** 2
            + (2 + (255 - rm) / 256) * (b1 - b2) ** 2) ** 0.5


def exact_histogram(path: str, alpha_min: int = 200) -> tuple["Counter", int, tuple[int, int]]:
    """Exact RGB histogram of the opaque pixels (no quantisation artefacts)."""
    from collections import Counter

    img = Image.open(path).convert("RGBA")
    data = img.tobytes()
    pixels: Counter = Counter()
    for r, g, b, a in zip(data[0::4], data[1::4], data[2::4], data[3::4]):
        if a >= alpha_min:
            pixels[(r, g, b)] += 1
    return pixels, sum(pixels.values()), img.size


def cluster(pixels: "Counter", tolerance: float = 14.0, limit: int = 40) -> list[tuple[tuple[int, int, int], int]]:
    """Merge antialias shades into their parent colour (greedy, by frequency)."""
    clusters: list[list] = []           # [colour, count, exact_hits]
    for colour, n in pixels.most_common():
        for c in clusters:
            if distance(colour, c[0]) < tolerance:
                # keep the most frequent exact value as the cluster colour
                c[1] += n
                if n > c[2]:
                    c[0], c[2] = colour, n
                break
        else:
            clusters.append([colour, n, n])
        if len(clusters) >= limit:
            break
    clusters.sort(key=lambda c: -c[1])
    return [(tuple(c[0]), c[1]) for c in clusters]


def dominant_colours(path: str, count: int = 14) -> tuple[list[tuple[tuple[int, int, int], float]], int, tuple[int, int]]:
    pixels, total, size = exact_histogram(path)
    merged = cluster(pixels)
    top = [(colour, n / total) for colour, n in merged[:count]]
    return top, total, size


def main(argv: list[str]) -> int:
    top = 14
    if "--top" in argv:
        i = argv.index("--top")
        top = int(argv[i + 1]) if len(argv) > i + 1 else 14

    pixels, opaque, size = exact_histogram(LOGO)
    merged = cluster(pixels)
    colours = [(colour, n / opaque) for colour, n in merged[:top]]
    print(f"logo      : assets/img/logo.png  {size[0]}x{size[1]}  "
          f"opaque pixels: {opaque:,} of {size[0] * size[1]:,}")

    print("\n=== most frequent EXACT pixel values (proof, no quantiser) ===")
    for colour, n in pixels.most_common(8):
        print(f"  {hexstr(colour):<9} {n:>7,} px  {n / opaque * 100:5.2f}%")

    css = open(CSS, encoding="utf-8").read()
    tokens = [(name, rgb(h)) for name, h in TOKEN.findall(css)]
    claimed = [(f"BRAND.md #{h}", rgb(h)) for h in dict.fromkeys(HEX.findall(open(BRAND, encoding="utf-8").read()))]

    print(f"\ncss       : {len(tokens)} --tokens compared")
    print("=== dominant colours in the logo (antialias shades merged) ===")
    for colour, share in colours:
        nearest = min(tokens, key=lambda t: distance(colour, t[1]))
        d = distance(colour, nearest[1])
        tag = f"= --{nearest[0]} ({hexstr(nearest[1])})" if d < 2 else (
            f"≈ --{nearest[0]} ({hexstr(nearest[1])}) Δ={d:.0f}" if d < 40 else "no token nearby")
        print(f"  {hexstr(colour):<9} {share * 100:5.1f}%   {tag}")

    print("\n=== is every token a logo colour? ===")
    exact = near = absent = 0
    for name, value in tokens:
        best, best_d = min(((c, distance(value, c)) for c, _ in colours), key=lambda cd: cd[1])
        if best_d < 1:
            exact += 1
            verdict = "exact logo colour"
        elif best_d < 26:
            near += 1
            verdict = f"close to logo {hexstr(best)} (Δ={best_d:.0f})"
        else:
            absent += 1
            verdict = f"NOT in the logo — nearest {hexstr(best)} (Δ={best_d:.0f})"
        print(f"  --{name:<8} {hexstr(value):<9} {verdict}")
    print(f"\nsummary   : {exact} exact · {near} near (derived) · {absent} not present in the logo")

    print("\n=== exact pixel count of every token value in the logo ===")
    literal = 0
    for name, value in tokens:
        n = pixels.get(value, 0)
        literal += 1 if n else 0
        print(f"  --{name:<8} {hexstr(value):<9} {n:>7,} px  {n / opaque * 100:5.2f}%"
              + ("" if n else "   ← value absent from the logo"))
    print(f"tokens found pixel-for-pixel in the logo: {literal}/{len(tokens)}")

    print("\n=== hex values claimed in BRAND.md vs the logo ===")
    for label, value in claimed:
        best, best_d = min(((c, distance(value, c)) for c, _ in colours), key=lambda cd: cd[1])
        verdict = ("exact" if best_d < 1 else
                   f"nearest logo colour {hexstr(best)} (Δ={best_d:.0f})" if best_d < 40 else
                   f"not in the logo (nearest {hexstr(best)}, Δ={best_d:.0f})")
        print(f"  {label:<18} {hexstr(value):<9} {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
