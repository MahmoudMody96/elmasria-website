"""Rebuild the 12 page-hero images from high-resolution originals.

Why this exists: `assets/img/pack/*.jpg` are 384x170 / 512x188 / 980x235 -- shown at
100vw they are upscaled up to 3.3x at a 1280px viewport (and the Ken Burns animation
zooms a further 1.1x), so they look soft. The content is right (each image is
purpose-shot for its service and carries the company logo) but the resolution is not.
No higher-resolution original exists in the repo, so the originals have to be supplied.

Usage:
    put the originals in INCOMING (any name), then map them in SOURCES and run.
    python _tools/gen_pack_heroes_v25.py            # generate
    python _tools/gen_pack_heroes_v25.py --check    # only report what is ready

Guard: refuses any source narrower than MIN_W, because generating from a small source
would silently produce an upscaled image that looks no better than today's.
"""
import os
import sys
from PIL import Image

ROOT = r"D:/MAHMOUD/projects/موقع شركة المصرية للسلامة والصحة المهنية"
OUT_DIR = os.path.join(ROOT, "assets/img/pack")
INCOMING = os.path.join(ROOT, "elmasria_website_images_pack")   # where originals are dropped
WIDTHS = [480, 960, 1440]
MIN_W = 1200          # below this, the 1440 variant would be upscaled -> refuse

# slot -> (source filename expected in INCOMING, pages it serves)
SLOTS = [
    ("01-hero-company",          ["about.html", "services/index.html"]),
    ("02-occupational-safety",   ["projects.html", "services/safety.html"]),
    ("03-civil-defense",         ["services/civil-defense.html"]),
    ("04-environmental-studies", ["services/environmental.html"]),
    ("05-pest-control",          ["services/pest-control.html"]),
    ("06-iso-management",        ["services/iso.html"]),
    ("07-manpower",              ["services/manpower.html"]),
    ("08-construction",          ["services/construction.html"]),
    ("09-cleaning",              ["services/cleaning.html"]),
    ("10-landscape",             ["services/landscape.html"]),
    ("11-occupational-clinic",   ["services/clinic.html"]),
    ("12-sports-fields",         ["services/football-fields.html"]),
]

check_only = "--check" in sys.argv
ready, blocked = [], []

for slot, pages in SLOTS:
    # accept the original under its slot name, with any of the usual extensions
    src = None
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        cand = os.path.join(INCOMING, slot + ext)
        if os.path.isfile(cand):
            src = cand
            break
    if not src:
        blocked.append((slot, "no source file in elmasria_website_images_pack/"))
        continue
    im = Image.open(src)
    if im.width < MIN_W:
        blocked.append((slot, f"source is {im.size[0]}x{im.size[1]} -- need >= {MIN_W}px wide "
                              f"(1440 variant would be upscaled {1440/im.width:.1f}x)"))
        continue
    ready.append((slot, src, im))

print(f"{'slot':28s} {'status'}")
print("-" * 96)
for slot, src, im in ready:
    print(f"{slot:28s} READY   {im.size[0]}x{im.size[1]}  {os.path.basename(src)}")
for slot, why in blocked:
    print(f"{slot:28s} BLOCKED {why}")

print(f"\nready: {len(ready)}/{len(SLOTS)}   blocked: {len(blocked)}")

if check_only:
    sys.exit(0)

if blocked:
    print("\nNothing generated -- resolve the blocked slots first.")
    sys.exit(1)

for slot, src, im in ready:
    im = im.convert("RGB")
    for w in WIDTHS:
        h = round(im.height * w / im.width)
        out = os.path.join(OUT_DIR, f"{slot}-{w}.webp")
        im.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=78, method=6)
        back = Image.open(out)
        assert back.size == (w, h), f"{slot}-{w}: wrote {back.size}"
        assert back.format == "WEBP"
        print(f"{slot}-{w}.webp".ljust(34) + f"{w}x{h}  {os.path.getsize(out):>8,} B")

print("\ndone. Now update the 13 page references to use srcset, and re-run the guards.")
