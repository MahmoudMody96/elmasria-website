"""Remove the orphaned photo assets agreed in v25, with assertions at every step.

⚠️ سكربت لمرة واحدة (v25) ومحصوز على `assets/img/photos/` وبيفحص `.html/.css/.js` بس
   **وبيتخطّى `_tools`**. الاستخدام العام بقى `_tools/verify_no_orphan_assets.py`،
   اللي بيفحص كل ملفات النص (بما فيها `*.md` والسكربتات) على كل `assets/`.
   سيب ده هنا كسجل تاريخي — ما تعمّمش منطقه على مجلدات تانية.


Safety model (why this is reversible):
  * every removed set has its untouched JPEG original in _tools/_photo-src/ (gitignored),
    so the WebP variants can be regenerated with _tools/gen_slot_photos_v25.py-style code;
  * `git rm` keeps the blobs in history, so `git checkout <commit> -- <path>` restores them.

Refuses to delete anything that is still referenced, untracked, or missing its archive
original -- a wrong deletion here is silent and would only surface as a broken image
on the live site.
"""
import os
import re
import subprocess
import sys

ROOT = r"D:/MAHMOUD/projects/موقع شركة المصرية للسلامة والصحة المهنية"
PHOTOS = "assets/img/photos"
ARCHIVE = "_tools/_photo-src"
# explicitly requested leftovers. chman.png was removed in the first run of this
# script; it is intentionally no longer listed so the script stays re-runnable
# (it now only reports whatever is orphaned at the moment it runs).
EXTRA = []

os.chdir(ROOT)


def tracked(path):
    r = subprocess.run(["git", "ls-files", "--error-unmatch", path],
                       capture_output=True, text=True)
    return r.returncode == 0


def scan_refs():
    refs = set()
    skip = {".git", "_tools", "node_modules", "_site"}
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            if not fn.endswith((".html", ".css", ".js")):
                continue
            p = os.path.join(dirpath, fn)
            t = open(p, encoding="utf-8", errors="replace").read()
            for m in re.findall(r"photos/([A-Za-z0-9_-]+?)(?:-[0-9]+)?\.webp", t):
                refs.add(m)
    return refs


refs = scan_refs()
print("referenced photo sets:", sorted(refs))

orphan_sets = {}
for f in sorted(os.listdir(PHOTOS)):
    base = re.sub(r"-[0-9]+\.webp$", "", f)
    if base not in refs:
        orphan_sets.setdefault(base, []).append(os.path.join(PHOTOS, f).replace("\\", "/"))

targets = [p for v in orphan_sets.values() for p in v]
print(f"orphan sets: {len(orphan_sets)}   orphan files: {len(targets)}")

# ---- assertions BEFORE any deletion -------------------------------------------------
fail = 0
for base in orphan_sets:
    if not os.path.isfile(os.path.join(ARCHIVE, base + ".jpg")):
        print(f"REFUSE  {base}: no archive original in {ARCHIVE}/")
        fail += 1
for p in targets + EXTRA:
    if not os.path.isfile(p):
        print(f"REFUSE  {p}: not on disk")
        fail += 1
    elif not tracked(p):
        print(f"REFUSE  {p}: not tracked by git (would leave no history to restore from)")
        fail += 1
for p in EXTRA:
    name = os.path.basename(p)
    if any(name in open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
           for d, _, fs in os.walk(".") if "_tools" not in d and ".git" not in d
           for f in fs if f.endswith((".html", ".css", ".js"))):
        print(f"REFUSE  {p}: still referenced")
        fail += 1

if fail:
    print(f"\nABORTED -- {fail} refusal(s). Nothing deleted.")
    sys.exit(1)

# ---- delete -------------------------------------------------------------------------
all_targets = targets + EXTRA
r = subprocess.run(["git", "rm", "-q", "--"] + all_targets, capture_output=True, text=True)
print("git rm exit:", r.returncode, r.stderr.strip())

# ---- verify each deletion actually happened -----------------------------------------
missing = [p for p in all_targets if os.path.exists(p)]
staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=D"],
                        capture_output=True, text=True).stdout.split()
staged = [s.replace("\\", "/") for s in staged]
not_staged = [p for p in all_targets if p not in staged]

print(f"deleted from disk: {len(all_targets) - len(missing)}/{len(all_targets)}")
print(f"staged as deleted: {len(all_targets) - len(not_staged)}/{len(all_targets)}")
for p in missing:
    print("  STILL ON DISK:", p)
for p in not_staged:
    print("  NOT STAGED   :", p)

freed = 0
for p in all_targets:
    b = subprocess.run(["git", "cat-file", "-s", f"HEAD:{p}"], capture_output=True, text=True)
    if b.returncode == 0:
        freed += int(b.stdout.strip())

print(f"\nremoved {len(all_targets)} files, {freed/1024:.0f} KB out of the repo (blobs stay in history)")
print("failures:", len(missing) + len(not_staged))
sys.exit(1 if (missing or not_staged) else 0)
