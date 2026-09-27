# -*- coding: utf-8 -*-
"""
Split the brand logo into its two parts.

assets/img/logo.png is a 1500x1500 square: the emblem (circle + worker) sits on
top and the Arabic wordmark sits under it. Rendered at ~54px in the header the
wordmark turns into mush, so the header/footer use a tightly cropped emblem
instead and let the HTML text (`.brand-name`) carry the name — crisper at any
DPI, selectable and searchable.

The tool measures the transparent gap between the two bands, writes a square
`assets/img/logo-emblem.png` (transparent, small margin) and prints the numbers
needed to size it in CSS.

Usage (from repo root):
    python _tools/crop_emblem.py           # write assets/img/logo-emblem.png
    python _tools/crop_emblem.py --check   # measure only
"""
from __future__ import annotations

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "img", "logo.png")
OUT = os.path.join(ROOT, "assets", "img", "logo-emblem.png")

STEP = 10          # rows per probe
ALPHA = 128        # considered opaque


def row_profile(im: Image.Image) -> list[tuple[int, bool]]:
    """[(row index, has pixels?)] probed every STEP rows."""
    w, h = im.size
    alpha = im.getchannel("A")
    out = []
    for y in range(0, h, STEP):
        band = alpha.crop((0, y, w, min(y + STEP, h)))
        out.append((y, band.getbbox() is not None))
    return out


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    profile = row_profile(im)

    # the emblem is everything from the first opaque row to the row before the
    # transparent gap that separates it from the wordmark
    first = next(y for y, filled in profile if filled)
    gap_start = None
    for i, (y, filled) in enumerate(profile):
        if i and filled and not profile[i - 1][1]:
            gap_start = y            # a gap precedes this band -> previous band ended
    # find the empty run that starts after `first`
    end = h
    seen_filled = False
    for y, filled in profile:
        if filled:
            seen_filled = True
        elif seen_filled and y > first:
            end = y
            break

    alpha = im.getchannel("A")
    box = alpha.crop((0, first, w, end)).getbbox()      # tight bbox of the emblem
    if not box:
        print("no emblem found — is the logo the expected 1500x1500 square?")
        return 1
    x0, y0, x1, y1 = box
    ew, eh = x1 - x0, y1 - y0

    print(f"logo        : {w}x{h}")
    print(f"emblem band : rows {first}..{end}   gap rows {end}..{min(end + 40, h)}..")
    print(f"emblem bbox : x {x0}..{x1} · y {y0}..{y1}  -> {ew}x{eh}  "
          f"(aspect {ew / eh:.3f}, {ew / w * 100:.0f}% of width, {eh / h * 100:.0f}% of height)")
    if gap_start:
        print(f"wordmark    : starts around row {gap_start}")
    print(f"at height:54px the emblem would need width {54 * ew / eh:.0f}px; "
          f"the full logo at 54px renders its wordmark at {54 * (h - end) / h:.0f}px tall")

    if check_only:
        return 0

    # square crop with a small transparent margin so circles do not touch the edge
    side = max(ew, eh)
    pad = max(8, side // 22)
    side += pad * 2
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im.crop((cx - side // 2, cy - side // 2,
                          cx - side // 2 + side, cy - side // 2 + side)),
                 (0, 0), None)
    canvas.save(OUT)
    print(f"wrote       : assets/img/logo-emblem.png  {side}x{side}  "
          f"({os.path.getsize(OUT):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
