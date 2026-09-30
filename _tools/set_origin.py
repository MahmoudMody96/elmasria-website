# -*- coding: utf-8 -*-
"""
نطاق واحد للموقع — إعادة كتابة + حارس.

المشكلة: 79 رابطًا مطلقًا في 17 صفحة + sitemap.xml + robots.txt كانوا بيشيروا
لـ`elmasria-eg.com` (موقع ووردبريس قديم على سيرفر تاني). يعني الموقع الجديد كان
بيقول لجوجل «النسخة الأصلية منّي بره»، و`sitemap.xml` كان بيدعو جوجل يزحف للنطاق القديم.

الحل: النطاق في ملف واحد (`_tools/site_origin.txt`) والسكربت ده بيوزّعه على كل حاجة.
أي نطاق تاني = خطأ بيمسكه `--check`.

القاعدة: أي `scheme://host` في الملفات المستهدفة يكون واحد من اتنين:
  1) نطاق الموقع (المكتوب في site_origin.txt)، أو
  2) خدمة خارجية معروفة (خطوط جوجل · واتساب · الخريطة · schema.org · sitemaps.org).
أي حاجة تالتة = «نطاق غريب» → بيتحوّل لنطاق الموقع، ولو `--check` بيفشل.

الاستخدام من جذر المستودع:
    python _tools/set_origin.py                      # يقرأ site_origin.txt ويوزّعه
    python _tools/set_origin.py https://new.tld      # يغيّر النطاق ثم يوزّعه
    python _tools/set_origin.py --check              # فحص بلا كتابة (حارس)

بيحافظ على CRLF (الـHTML في المستودع CRLF) وقابل لإعادة التشغيل.
"""
from __future__ import annotations

import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN_FILE = os.path.join("_tools", "site_origin.txt")

# خدمات خارجية مشروعة — وجودها مقصود ومش «انحراف نطاق».
# بتتقارن بعد شيل `www.` وتحويلها لحروف صغيرة.
THIRD_PARTY = {
    "wa.me",                        # روابط واتساب
    "fonts.googleapis.com",         # خطوط جوجل
    "fonts.gstatic.com",            # ملفات الخطوط
    "schema.org",                   # سياق JSON-LD
    "sitemaps.org",                 # xmlns في sitemap.xml
    "openstreetmap.org",            # خريطة صفحة التواصل
    "www.w3.org",                   # أي مراجع SVG مستقبلية
}

HOST_RE = re.compile(r"https?://([A-Za-z0-9._-]+)")


def target_files() -> list[str]:
    """كل ملفات الـHTML في المستودع (وليس ملفًا واحدًا) + sitemap + robots.

    قصدًا بـglob مش بقائمة مكتوبة: أي إعادة تقسيم أو صفحة جديدة تدخل الفحص
    تلقائيًا — الحارس اللي بيقرأ ملفًا واحدًا بيسيب فجوات صامتة.
    """
    files = sorted(glob.glob(os.path.join(ROOT, "*.html")))
    files += sorted(glob.glob(os.path.join(ROOT, "services", "*.html")))
    for extra in ("sitemap.xml", "robots.txt"):
        p = os.path.join(ROOT, extra)
        if os.path.exists(p):
            files.append(p)
    return files


def read(p: str) -> str:
    return io.open(p, encoding="utf-8", newline="").read()


def write(p: str, text: str) -> None:
    with io.open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def base(host: str) -> str:
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def read_origin() -> str:
    text = read(os.path.join(ROOT, ORIGIN_FILE))
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line.rstrip("/")
    raise SystemExit("FAIL: %s مش فيه سطر نطاق صالح" % ORIGIN_FILE)


def save_origin(origin: str) -> None:
    """يحدّث سطر النطاق في الملف من غير ما يلمس التعليقات."""
    p = os.path.join(ROOT, ORIGIN_FILE)
    lines = read(p).split("\n")
    done = False
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith("#"):
            lines[i] = origin
            done = True
            break
    if not done:
        lines.append(origin)
    write(p, "\n".join(lines))


def validate(origin: str) -> None:
    if not re.fullmatch(r"https?://[A-Za-z0-9._-]+", origin):
        raise SystemExit("FAIL: نطاق غير صالح: %r — المتوقع مثل https://example.com" % origin)


def classify(host: str, origin_host: str) -> str:
    if host.lower() == origin_host:
        return "origin"
    if base(host) in THIRD_PARTY:
        return "third"
    return "foreign"


def scan(files: list[str], origin_host: str) -> dict[str, list[tuple[str, str, int]]]:
    """يرجّع {التصنيف: [(ملف, host, عدد), ...]}"""
    out: dict[str, list[tuple[str, str, int]]] = {"origin": [], "third": [], "foreign": []}
    for p in files:
        counts: dict[str, int] = {}
        for m in HOST_RE.finditer(read(p)):
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
        for host, n in sorted(counts.items()):
            out[classify(host, origin_host)].append((os.path.relpath(p, ROOT), host, n))
    return out


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    args = [a for a in argv if not a.startswith("--")]

    origin = args[0].rstrip("/") if args else read_origin()
    validate(origin)
    origin_host = origin.split("//", 1)[1]

    if args and not check_only:
        save_origin(origin)
        print("النطاق في %s -> %s" % (ORIGIN_FILE, origin))

    files = target_files()
    print("النطاق المرجعي : %s" % origin)
    print("ملفات مستهدفة  : %d (html + sitemap + robots)\n" % len(files))

    before = scan(files, origin_host)

    print("-- الخدمات الخارجية المقصودة (مش بتتغير) --")
    for f, host, n in before["third"]:
        print("   %-34s %-26s x%d" % (f, host, n))
    print("   الإجمالي: %d مرجع\n" % sum(n for _, _, n in before["third"]))

    print("-- نطاق الموقع (صح) --")
    print("   الإجمالي: %d مرجع في %d ملف\n"
          % (sum(n for _, _, n in before["origin"]),
             len({f for f, _, _ in before["origin"]})))

    if before["foreign"]:
        print("-- نطاقات غريبة (لازم تتحوّل) --")
        for f, host, n in before["foreign"]:
            print("   %-34s %-26s x%d" % (f, host, n))
        print("   الإجمالي: %d مرجع\n" % sum(n for _, _, n in before["foreign"]))
    else:
        print("-- نطاقات غريبة: صفر --\n")

    if check_only:
        if before["foreign"]:
            print("FAIL — %d مرجع لسه بيشير لنطاق تاني:"
                  % sum(n for _, _, n in before["foreign"]))
            for f, host, n in before["foreign"]:
                print("  - %s: %s x%d" % (f, host, n))
            return 1
        print("ALL PASS — مفيش أي مرجع لنطاق غير %s" % origin_host)
        return 0

    if not before["foreign"]:
        print("مفيش حاجة تتغيّر — الملفات كلها على النطاق الصح.")
        return 0

    changed = 0
    total = 0
    for p in files:
        text = read(p)
        rel = os.path.relpath(p, ROOT)

        # عدد المراجع الغريبة الفعلي. مينفعش نستخدم قيمة `subn` لأنه بيعدّ *كل*
        # مطابقة بيمرّ عليها — بما فيها روابط الخطوط والواتساب اللي بتتساب زي ما
        # هي — فبتطلع 6 بدل 1. الحارس مسكها: «عدد مراجع النطاق مش متسق».
        foreign_before = sum(1 for m in HOST_RE.finditer(text)
                             if classify(m.group(1), origin_host) == "foreign")
        if foreign_before == 0:
            continue

        def repl(m: re.Match) -> str:
            return origin if classify(m.group(1), origin_host) == "foreign" else m.group(0)

        new = HOST_RE.sub(repl, text)

        # التحقق على الناتج نفسه
        left = [h for h in HOST_RE.findall(new) if classify(h, origin_host) == "foreign"]
        if left:
            print("   FAIL %-34s نطاقات غريبة باقية: %s" % (rel, sorted(set(left))))
            return 1
        if new.count(origin_host) != text.count(origin_host) + foreign_before:
            print("   FAIL %-34s عدد مراجع النطاق مش متسق (%d -> %d، متوقع +%d)"
                  % (rel, text.count(origin_host), new.count(origin_host), foreign_before))
            return 1
        # الثابت الصح هو إن نهايات الأسطر ما اتغيرتش — مش إن الملف CRLF.
        # الـHTML في المستودع CRLF لكن sitemap.xml وrobots.txt LF، فافتراض
        # «كل ملف CRLF» كان بيرفض ملفات سليمة تمامًا.
        if new.count("\r") != text.count("\r") or new.count("\n") != text.count("\n"):
            print("   FAIL %-34s نهايات الأسطر اتغيرت (%d\\r/%d\\n -> %d\\r/%d\\n)"
                  % (rel, text.count("\r"), text.count("\n"),
                     new.count("\r"), new.count("\n")))
            return 1
        write(p, new)
        changed += 1
        total += foreign_before
        print("   OK   %-34s %d مرجع -> %s" % (rel, foreign_before, origin_host))

    print("\nاتغيّر %d مرجع في %d ملف." % (total, changed))

    after = scan(files, origin_host)
    if after["foreign"]:
        print("FAIL — لسه فيه نطاقات غريبة بعد الكتابة")
        return 1
    print("ALL PASS — كل الملفات بقت على %s" % origin_host)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
