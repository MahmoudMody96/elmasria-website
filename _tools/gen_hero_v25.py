"""Generate the v25 contact-page hero image set.

New hero photo is 1672x941 (16:9), so 480/960/1440 variants are all true downscales
(1440 < 1672) -- no upscaling. A NEW filename is used deliberately: the old file was
served with a 7-day cache, so reusing the name would show stale pixels to returning
visitors.

Follows the repo convention (quality=78, method=6, LANCZOS) and archives the untouched
original in _tools/_photo-src/ (gitignored).
"""
import os
import shutil
import sys
from PIL import Image

ROOT = r"D:/MAHMOUD/projects/موقع شركة المصرية للسلامة والصحة المهنية"
PHOTOS = os.path.join(ROOT, "assets/img/photos")
ARCHIVE = os.path.join(ROOT, "_tools/_photo-src")
SRC = r"C:/Users/M_abd/.workbuddy-ai/clipboard-images/clipboard-2026-09-30T12-57-45-230Z-42ef56cb.jpg"
NAME = "safety-supervisor"
WIDTHS = [480, 960, 1440]

im = Image.open(SRC)
if im.size != (1672, 941):
    print(f"FAIL unexpected source size {im.size} (expected (1672, 941))")
    sys.exit(1)
im = im.convert("RGB")
src_bytes = os.path.getsize(SRC)

dst_src = os.path.join(ARCHIVE, NAME + ".jpg")
if not os.path.isfile(dst_src):
    shutil.copy2(SRC, dst_src)
assert os.path.getsize(dst_src) == src_bytes, "archive copy differs from source"

fail = 0
for w in WIDTHS:
    h = round(im.height * w / im.width)
    out = os.path.join(PHOTOS, f"{NAME}-{w}.webp")
    im.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=78, method=6)
    back = Image.open(out)
    if back.size != (w, h) or back.format != "WEBP":
        print(f"FAIL {NAME}-{w}: wrote {back.size} {back.format}")
        fail += 1
        continue
    ob = os.path.getsize(out)
    if ob >= src_bytes:
        print(f"FAIL {NAME}-{w}: {ob} B not smaller than source")
        fail += 1
        continue
    print(f"{NAME}-{w}.webp".ljust(30) + f"{w}x{h}  {ob:>8,} B")

print("\nfailures:", fail)
sys.exit(1 if fail else 0)
