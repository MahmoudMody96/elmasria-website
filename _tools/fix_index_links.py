#!/usr/bin/env python3
"""Point every "home" link at the directory, not the file.

WHY
---
All 17 pages linked to the *file* (`index.html`, `../index.html`, `/index.html`).
Because the href names the file rather than the directory, clicking the logo or
"الرئيسية" navigates the browser to `https://<host>/index.html`, so that is what
the address bar shows. nginx serves `/index.html` as-is with 200 (no 301 back to
`/`), so the URL sticks — two URLs for one page.

WHAT
----
    href="../index.html"  ->  href="../"      (service pages)
    href="/index.html"    ->  href="/"        (404.html)
    href="index.html"     ->  href="./"       (root pages)

The three patterns are mutually exclusive once anchored on `href="`, because the
substring `href="index.html"` cannot occur inside `href="../index.html"` (after
`href="` comes `../`, not `index`). Order therefore does not matter — but each
rule is asserted anyway.

EOL: the working tree is 100% CRLF and core.autocrlf=true, so both the read and
the write use newline='' to leave every line ending byte-identical.
"""
import glob
import sys

RULES = [
    # (label, old, new, expected_count)
    ("service pages  ../index.html", 'href="../index.html"', 'href="../"', 48),
    ("404.html       /index.html",   'href="/index.html"',   'href="/"',    4),
    ("root pages     index.html",    'href="index.html"',    'href="./"',  15),
]

EXPECTED_TOTAL = sum(r[3] for r in RULES)


def pages():
    out = []
    for f in sorted(glob.glob("**/*.html", recursive=True)):
        f = f.replace("\\", "/")
        if f.startswith("_tools") or "_worktree" in f:
            continue
        out.append(f)
    return out


def main() -> int:
    files = pages()
    print(f"pages scanned: {len(files)}")
    print()

    totals = {label: 0 for label, *_ in RULES}
    touched = 0

    for f in files:
        with open(f, encoding="utf-8", newline="") as fh:
            s = orig = fh.read()
        per = []
        for label, a, b, _ in RULES:
            c = s.count(a)
            if c:
                s = s.replace(a, b)
                totals[label] += c
                per.append(f"{label.split()[-1]}={c}")
        if s != orig:
            with open(f, "w", encoding="utf-8", newline="") as fh:
                fh.write(s)
            touched += 1
        if per:
            print(f"{f:42} {', '.join(per)}")

    print()
    print(f"files modified: {touched}")
    print()

    ok = True
    grand = sum(totals[label] for label, *_ in RULES)

    # --- verification: no `index.html` may survive inside any href -------------
    leftovers = []
    for f in files:
        with open(f, encoding="utf-8", newline="") as fh:
            s = fh.read()
        if 'href="' in s:
            for chunk in s.split('href="')[1:]:
                target = chunk.split('"', 1)[0]
                if "index.html" in target:
                    leftovers.append((f, target))

    # A re-run legitimately finds nothing to change. That is success, not failure —
    # but only when nothing is left over. Distinguish the two, so the script stays
    # re-runnable instead of "failing" forever once it has done its job.
    already_applied = (grand == 0 and not leftovers)

    for label, _, _, expected in RULES:
        got = totals[label]
        if already_applied:
            flag = "already applied"
        else:
            flag = "OK" if got == expected else f"EXPECTED {expected}"
            if got != expected:
                ok = False
        print(f"  {label:32} {got:>3}  {flag}")

    if already_applied:
        print(f"  {'TOTAL':32} {grand:>3}  nothing to do")
    else:
        print(f"  {'TOTAL':32} {grand:>3}  "
              f"{'OK' if grand == EXPECTED_TOTAL else 'EXPECTED ' + str(EXPECTED_TOTAL)}")
        if grand != EXPECTED_TOTAL:
            ok = False

    print()
    if leftovers:
        ok = False
        print(f"FAIL — {len(leftovers)} href(s) still name index.html:")
        for f, t in leftovers[:20]:
            print(f"   {f}: {t}")
    else:
        print("verified: zero hrefs still name index.html")

    # --- verification: EOL unchanged (still 100% CRLF) ------------------------
    print()
    mixed = []
    for f in files:
        b = open(f, "rb").read()
        total = b.count(b"\n")
        crlf = b.count(b"\r\n")
        if total != crlf:
            mixed.append((f, crlf, total - crlf))
    if mixed:
        ok = False
        print("FAIL — line endings changed:")
        for f, c, l in mixed:
            print(f"   {f}: CRLF={c} LF-only={l}")
    else:
        print("verified: every page still 100% CRLF")

    print()
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
