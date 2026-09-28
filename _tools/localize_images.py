# -*- coding: utf-8 -*-
"""
Bring every photo the site uses *in-house* (no third-party CDN) and serve it at
the right pixel size, then rewrite the markup to the local WebP ladder.

Why: the pages hot-linked images.unsplash.com (an external dependency that can
change or block) and always declared sizes="(max-width:640px) 100vw, 1200px",
so a 350px related-card image downloaded the 1440w file (measured: 334 KB for a
599x280 slot on index.html).

Migration note: two of the old hot-linked photos are dead on Unsplash (HTTP 404
— they were broken images on the live site). They are replaced by free-licence
Pexels photos (Pexels licence: free for commercial use, no attribution needed);
see SWAPS / SOURCE_OVERRIDES below. Once the pages point at the local WebP files
the mappings are migration records only — the default run then has nothing to do
and --check is the useful mode.

What it does
    1. analyse  — read all pages, collect every images.unsplash.com photo id and
                  the layout context that uses it,
    2. fetch    — download each photo once into _tools/_photo-src/ (gitignored),
    3. build    — write assets/img/photos/<slug>-<w>.webp (480/960/1440 ladder),
    4. rewrite  — replace src/srcset/sizes in every page with the local files and
                  the sizes value that matches the CSS for that context.

Usage (from repo root):
    python _tools/localize_images.py              # fetch (if needed) + build + rewrite
    python _tools/localize_images.py --fetch      # download the sources only
    python _tools/localize_images.py --build      # rebuild webp from cached sources
    python _tools/localize_images.py --rewire     # only rewrite the markup
    python _tools/localize_images.py --refresh    # re-download even if cached
    python _tools/localize_images.py --check      # 0 remote refs + all files present
"""
from __future__ import annotations

import os
import re
import sys
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "_tools", "_photo-src")
OUTDIR = os.path.join(ROOT, "assets", "img", "photos")

PAGES = [
    "index.html", "about.html", "contact.html", "projects.html",
    "services/civil-defense.html", "services/cleaning.html", "services/clinic.html",
    "services/construction.html", "services/environmental.html",
    "services/football-fields.html", "services/index.html", "services/iso.html",
    "services/landscape.html", "services/manpower.html", "services/pest-control.html",
    "services/safety.html",
]

# Unsplash photo id -> local slug (semantic, stable, safe for URLs)
SLUGS = {
    "1504328345606-18bbc8c9d7d1": "industrial-plant",
    "1541888946425-d81bb19240f5": "safety-team",
    "1466611653911-95081537e5b7": "coastal-tourism",
    "1503387762-592deb58ef4e": "construction-site",
    "1581091226825-a6a2a5aee158": "engineering-review",
    "1581092160607-ee22621dd758": "industrial-facility",
    "1416879595882-3373a0480b5b": "green-landscape",
    "1521737604893-d14cc237f11d": "workforce-team",
    "1528740561666-dc2479dc08ab": "cleaning-service",
    "1454165804606-c3d57bc86b40": "iso-audit",
    "1581094794329-c8112a89af12": "environment-lab",
    "1579154204601-01588f351e67": "clinic-care",
    "1584820927498-cfe5211fd8bf": "pest-control",
    "1473341304170-971dccb5ac1e": "clean-energy",
}

# Unsplash ids that went dead (HTTP 404, verified 2026-09-28) and their replacement.
# The live site showed broken images for both before this tool ran.
SWAPS = {
    "1529904029598-3820d84bce03": "football-pitch",
    "1565043589221-1a6fd9ae45d7": "fire-safety",
}

# slug -> source URL template for photos that do not come from Unsplash
SOURCE_OVERRIDES = {
    "football-pitch":
        "https://images.pexels.com/photos/5467303/pexels-photo-5467303.jpeg"
        "?auto=compress&cs=tinysrgb&w={w}",
    "fire-safety":
        "https://images.pexels.com/photos/189474/pexels-photo-189474.jpeg"
        "?auto=compress&cs=tinysrgb&w={w}",
}

# layout context token -> (sizes attribute, whether the slot is full-bleed)
CONTEXTS: dict[str, tuple[str, bool]] = {
    "hero-media": ("100vw", True),
    "ph-bg": ("100vw", True),
    "main": ("(max-width:1020px) 92vw, 540px", True),
    "cf-img": ("(max-width:760px) 92vw, 600px", False),
    "sector": ("(max-width:640px) 92vw, (max-width:1020px) 46vw, 280px", False),
    "rel-card": ("(max-width:640px) 92vw, (max-width:1020px) 46vw, 350px", False),
    "hero-photo-card": ("(max-width:640px) 92vw, (max-width:1020px) 45vw, 360px", False),
}
CONTEXT_ORDER = ["hero-media", "ph-bg", "cf-img", "sector", "rel-card",
                 "hero-photo-card", "main"]
DEFAULT_CONTEXT = "cf-img"

FULL_LADDER = (480, 960, 1440)
CARD_LADDER = (480, 960)

REMOTE = re.compile(
    r"https://images\.unsplash\.com/photo-(?P<id>[0-9a-f\-]+)\?[^\"\s]*")
IMG_TAG = re.compile(r"<img\b[^>]*>")


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def detect_context(text: str, tag_start: int) -> str:
    """Which layout slot owns this <img>? own class first, then the nearest ancestor."""
    classes: list[str] = []
    own = re.search(r'class="([^"]*)"', text[tag_start:tag_start + 300])
    if own:
        classes += own.group(1).split()
    back = re.findall(r'class="([^"]*)"', text[max(0, tag_start - 400):tag_start])
    if back:
        classes += back[-1].split()
    for token in CONTEXT_ORDER:
        if token in classes:
            return token
    return DEFAULT_CONTEXT


def slug_of(pid: str) -> str:
    slug = SLUGS.get(pid) or SWAPS.get(pid)
    if not slug:
        raise SystemExit(f"unknown photo id {pid} — add it to SLUGS/SWAPS in {__file__}")
    return slug


def analyse() -> dict[str, dict]:
    """slug -> {contexts, pages} for every remote image still referenced."""
    plan: dict[str, dict] = {}
    for rel in PAGES:
        text = read(os.path.join(ROOT, rel.replace("/", os.sep)))
        for tag in IMG_TAG.finditer(text):
            m = REMOTE.search(tag.group(0))
            if not m:
                continue
            entry = plan.setdefault(slug_of(m.group("id")),
                                    {"contexts": set(), "pages": set()})
            entry["contexts"].add(detect_context(text, tag.start()))
            entry["pages"].add(rel)
    return plan


def ladder_for(plan_entry: dict) -> tuple[int, ...]:
    full = any(CONTEXTS[c][1] for c in plan_entry["contexts"])
    return FULL_LADDER if full else CARD_LADDER


def source_url(slug: str, width: int) -> str:
    if slug in SOURCE_OVERRIDES:
        return SOURCE_OVERRIDES[slug].format(w=width)
    pid = next(pid for pid, s in SLUGS.items() if s == slug)
    return f"https://images.unsplash.com/photo-{pid}?fm=jpg&q=78&w={width}"


def fetch(plan: dict[str, dict], refresh: bool = False) -> int:
    os.makedirs(CACHE, exist_ok=True)
    got = 0
    for slug, entry in plan.items():
        dest = os.path.join(CACHE, slug + ".jpg")
        if os.path.exists(dest) and not refresh:
            print(f"  {slug:<22} cached ({os.path.getsize(dest) / 1024:6.1f} KB)")
            continue
        width = max(ladder_for(entry))
        req = urllib.request.Request(source_url(slug, width),
                                     headers={"User-Agent": "Mozilla/5.0 (elmasria build)"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(dest, "wb") as fh:
            fh.write(data)
        print(f"  {slug:<22} fetched {width}px  {len(data) / 1024:6.1f} KB")
        got += 1
    return got


def rewire(rel: str, text: str, plan: dict[str, dict]) -> tuple[str, int]:
    prefix = "../assets/img/photos/" if rel.startswith("services/") else "assets/img/photos/"
    hits = 0

    def replace(m: re.Match) -> str:
        nonlocal hits
        tag = m.group(0)
        remote = REMOTE.search(tag)
        if not remote:
            return tag
        slug = slug_of(remote.group("id"))
        entry = plan[slug]
        ladder = ladder_for(entry)
        sizes = CONTEXTS[detect_context(text, m.start())][0]
        src = f"{prefix}{slug}-{max(ladder)}.webp"
        srcset = ", ".join(f"{prefix}{slug}-{w}.webp {w}w" for w in ladder)

        tag, n1 = re.subn(r'src="[^"]*"', f'src="{src}"', tag, count=1)
        tag, n2 = re.subn(r'srcset="[^"]*"', f'srcset="{srcset}"', tag, count=1)
        tag, n3 = re.subn(r'sizes="[^"]*"', f'sizes="{sizes}"', tag, count=1)
        if (n1, n2, n3) != (1, 1, 1):
            raise SystemExit(f"{rel}: unexpected <img> shape (src/srcset/sizes) — {tag[:90]}")
        hits += 1
        return tag

    return IMG_TAG.sub(replace, text), hits


def check() -> int:
    problems: list[str] = []
    referenced: set[str] = set()
    for rel in PAGES:
        text = read(os.path.join(ROOT, rel.replace("/", os.sep)))
        for m in REMOTE.finditer(text):
            line = text[:m.start()].count("\n") + 1
            problems.append(f"{rel}:{line} still hot-links {m.group(0)[:70]}")
        for m in re.finditer(r'((?:\.\./)?)assets/img/photos/([\w\-]+\.webp)', text):
            referenced.add(m.group(2))
            full = os.path.join(ROOT, "assets", "img", "photos", m.group(2))
            if not os.path.exists(full):
                line = text[:m.start()].count("\n") + 1
                problems.append(f"{rel}:{line} references missing photos/{m.group(2)}")
    if os.path.isdir(OUTDIR):
        on_disk = {f for f in os.listdir(OUTDIR) if f.endswith(".webp")}
        for orphan in sorted(on_disk - referenced):
            problems.append(f"assets/img/photos/{orphan} is never referenced")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  - " + p)
        return 1
    print(f"image localisation OK: 0 remote references, {len(referenced)} local WebP "
          f"files referenced and all present")
    return 0


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return check()

    plan = analyse()
    if not plan:
        print("nothing to localise — no images.unsplash.com reference left")
        return check()

    print(f"remote photos referenced: {len(plan)}")
    for slug, entry in sorted(plan.items()):
        ladder = ladder_for(entry)
        ctx = ",".join(sorted(entry["contexts"]))
        source = "pexels" if slug in SOURCE_OVERRIDES else "unsplash"
        print(f"  {slug:<22} {str(ladder):<20} {source:<9} {ctx}")

    if "--rewire" not in argv:
        print("\nfetching sources into _tools/_photo-src/ …")
        fetch(plan, refresh="--refresh" in argv)
        if "--fetch" in argv:
            return 0
        print("\nbuilding assets/img/photos/*.webp …")
        build(plan)
        if "--build" in argv:
            return 0

    print("\nrewiring the markup …")
    total = 0
    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        text = read(path)
        new, hits = rewire(rel, text, plan)
        if new != text:
            write(path, new)
            print(f"  {rel:<34} {hits} images localised")
        total += hits
    print(f"localised {total} <img> references across {len(PAGES)} pages")
    return 0


def build(plan: dict[str, dict]) -> int:
    os.makedirs(OUTDIR, exist_ok=True)
    total = 0
    for slug, entry in plan.items():
        src = os.path.join(CACHE, slug + ".jpg")
        if not os.path.exists(src):
            raise SystemExit(f"missing source {src} — run with --fetch first")
        for width in ladder_for(entry):
            with Image.open(src) as im:
                im = im.convert("RGB")
                if im.width != width:
                    height = round(im.height * width / im.width)
                    im = im.resize((width, height), Image.LANCZOS)
                dest = os.path.join(OUTDIR, f"{slug}-{width}.webp")
                im.save(dest, "WEBP", quality=78, method=6)
            size = os.path.getsize(dest)
            total += size
            print(f"  photos/{slug}-{width}.webp"
                  f"{' ' * max(1, 24 - len(slug))}{size / 1024:6.1f} KB")
    print(f"  {len(plan)} photos · {total / 1024:.0f} KB of local WebP")
    return total


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
