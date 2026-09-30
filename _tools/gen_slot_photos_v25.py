"""Generate the two replacement photo sets for v25.

NEW-A (worker with a checklist in front of SAFETY FIRST signage) -> safety-inspection-*
NEW-B (four engineers reviewing a drawing)                        -> team-blueprint-*

Sources are 1024x1536 portrait, so only 480w and 960w variants are emitted.
A 1440w variant would be pure upscaling from a 1024px source -- deliberately omitted.

Follows the repo's existing encoding convention (quality=78, method=6, LANCZOS) and
archives the untouched originals into _tools/_photo-src/ (gitignored).
"""
import os
import shutil
import sys
from PIL import Image

ROOT = r"D:/MAHMOUD/projects/موقع شركة المصرية للسلامة والصحة المهنية"
PHOTOS = os.path.join(ROOT, "assets/img/photos")
ARCHIVE = os.path.join(ROOT, "_tools/_photo-src")
CLIP = r"C:/Users/M_abd/.workbuddy-ai/clipboard-images"

JOBS = [
    ("safety-inspection", os.path.join(CLIP, "clipboard-2026-09-30T12-13-58-360Z-66d91af4.jpg")),
    ("team-blueprint",    os.path.join(CLIP, "clipboard-2026-09-30T12-13-58-361Z-1ca2c87f.jpg")),
]
WIDTHS = [480, 960]

fail = 0
for name, src in JOBS:
    if not os.path.isfile(src):
        print(f"FAIL  source missing: {src}")
        fail += 1
        continue
    im = Image.open(src)
    if im.size != (1024, 1536):
        print(f"FAIL  {name}: unexpected source size {im.size} (expected 1024x1536)")
        fail += 1
        continue
    im = im.convert("RGB")
    src_bytes = os.path.getsize(src)

    # archive the untouched original
    dst_src = os.path.join(ARCHIVE, name + ".jpg")
    if not os.path.isfile(dst_src):
        shutil.copy2(src, dst_src)
    assert os.path.getsize(dst_src) == src_bytes, "archive copy differs from source"

    for w in WIDTHS:
        h = round(im.height * w / im.width)
        out = os.path.join(PHOTOS, f"{name}-{w}.webp")
        im.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=78, method=6)
        # verify by reading back
        back = Image.open(out)
        assert back.size == (w, h), f"{name}-{w}: wrote {back.size}, expected {(w, h)}"
        assert back.format == "WEBP", f"{name}-{w}: format is {back.format}"
        ob = os.path.getsize(out)
        assert ob < src_bytes, f"{name}-{w}: {ob} B is not smaller than source {src_bytes} B"
        print(f"{name}-{w}.webp".ljust(28) + f"{w}x{h}  {ob:>8,} B")

print("\nfailures:", fail)
sys.exit(1 if fail else 0)
