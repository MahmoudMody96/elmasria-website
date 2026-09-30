# -*- coding: utf-8 -*-
"""
إضافة واتساب حقيقي في صفحة التواصل + إصلاح زر الشريط السفلي للجوال (v26).

مشكلتان منفصلتان، وكل واحدة ليها تحقّقها الخاص:

1) كارت البيانات في `contact.html` ما كانش فيه أي صف واتساب، مع إن واتساب
   موجود في الموقع كله (الزر العائم `#waFloat`) - فالزائر اللي بيدوّر على
   رقم واتساب جوه الكارت ما كانش بيلاقيه.

2) الزر التاني في الشريط السفلي للجوال كلاسه `mc-wa` (أي «واتساب») لكنه
   ما كانش بيفتح واتساب إطلاقًا: على `contact.html` كان بيفتح `mailto:`،
   وعلى باقي الـ16 صفحة كان بيفتح `contact.html`. الاسم كان بيكدب على السلوك.
   صار الآن رابط `wa.me` حقيقي، بأيقونة `#i-wa` ونص «واتساب» ولون العلامة.

كل بند بيتأكّد لوحده بقائمة أخطاء مستقلة، ففشل بند ما بيمنعش كتابة الباقي
وما بيوسمش الباقي بالفشل وهو ما اتجرّبش. السكربت آمن لإعادة التشغيل
(idempotent): تشغيله تاني بيقول «already applied» وبيخرج بـ0.

كل الملفات CRLF وبتفضل 100% CRLF - القراءة والكتابة بـ`newline=""`.

الاستخدام من جذر المستودع:
    python _tools/add_whatsapp_v26.py --check   # فحص بلا كتابة
    python _tools/add_whatsapp_v26.py           # تنفيذ
"""
from __future__ import annotations

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# نفس الرابط والرسالة الجاهزة المستخدمين في الزر العائم `#waFloat` وفي `waSend`
# داخل `main.js` - رسالة واحدة متسقة في الموقع كله:
# «مرحباً، أرغب في الاستفسار عن خدماتكم»
WA = ("https://wa.me/201000101040?text="
      "%D9%85%D8%B1%D8%AD%D8%A8%D8%A7%D9%8B%D8%8C%20"
      "%D8%A3%D8%B1%D8%BA%D8%A8%20%D9%81%D9%8A%20"
      "%D8%A7%D9%84%D8%A7%D8%B3%D8%AA%D9%81%D8%B3%D8%A7%D8%B1%20"
      "%D8%B9%D9%86%20%D8%AE%D8%AF%D9%85%D8%A7%D8%AA%D9%83%D9%85")

PAGES = [
    "index.html", "about.html", "contact.html", "projects.html", "404.html",
    "services/civil-defense.html", "services/cleaning.html", "services/clinic.html",
    "services/construction.html", "services/environmental.html",
    "services/football-fields.html", "services/index.html", "services/iso.html",
    "services/landscape.html", "services/manpower.html", "services/pest-control.html",
    "services/safety.html",
]

# ---------- المرحلة 1: صف واتساب في كارت البيانات ----------
CONTACT = "contact.html"
CARD_ANCHOR = ('<h3 style="margin-top:22px"><svg class="ic" aria-hidden="true" '
               'focusable="false"><use href="assets/img/icons.svg#i-mail"></use></svg> '
               'البريد الإلكتروني</h3>')

WA_ROW = (
    '<h3 style="margin-top:22px"><svg class="ic ic-fill" aria-hidden="true" '
    'focusable="false"><use href="assets/img/icons.svg#i-wa"></use></svg> واتساب</h3>\r\n'
    '<div class="wa-first"><a href="' + WA + '" target="_blank" rel="noopener">'
    '<svg class="ic ic-fill" aria-hidden="true" focusable="false">'
    '<use href="assets/img/icons.svg#i-wa"></use></svg>'
    '<b>01000101040</b><span>راسلنا الآن</span></a></div>\r\n'
)

# ---------- المرحلة 2: زر الشريط السفلي ----------
# الرابط الحالي إما صفحة التواصل أو mailto، والكلاس اسمه mc-wa.
# `[^>]*>` بعد الـhref ضرورية: الزر الجديد بيضيف target وrel بعد الـhref، فالنمط
# اللي بيفترض إن `href="…">` هي آخر الوسم بيفشل على الزر الجديد نفسه (اتكشف
# بالحارس قبل أي كتابة: كان بيرجّع 0 نتائج على الناتج).
MC_WA_RE = re.compile(r'<a class="mc-wa" href="[^"]*"[^>]*>.*?</a>')
ICON_PREFIX_RE = re.compile(r'href="((?:\.\./|/)?)assets/img/icons\.svg#i-mail"')
MOBILE_BAR_RE = re.compile(r'<div class="mobile-call">.*?</div>')

failures: list[str] = []


def read(rel: str) -> str:
    return io.open(os.path.join(ROOT, rel.replace("/", os.sep)),
                   encoding="utf-8", newline="").read()


def write(rel: str, text: str) -> None:
    with io.open(os.path.join(ROOT, rel.replace("/", os.sep)),
                 "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def crlf_problem(rel: str, text: str) -> str:
    """كل ملفات HTML في المستودع CRLF، فأي سطر LF لوحده معناه إن التعديل كسر الاتفاق."""
    if text.count("\r\n") != text.count("\n"):
        return "%s: CRLF %d / LF %d - خطوط مختلطة" % (
            rel, text.count("\r\n"), text.count("\n"))
    return ""


def phase1(check_only: bool) -> None:
    print("== المرحلة 1: صف واتساب في كارت البيانات (%s) ==" % CONTACT)
    text = read(CONTACT)

    if 'class="wa-first"' in text:
        n = text.count('class="wa-first"')
        print("   already applied - wa-first x%d" % n)
        if n != 1:
            failures.append("%s: wa-first متكرر %d مرة" % (CONTACT, n))
        p = crlf_problem(CONTACT, text)
        if p:
            failures.append(p)
        return

    hits = text.count(CARD_ANCHOR)
    if hits != 1:
        failures.append("%s: نقطة الإدراج ظهرت %d مرة بدل 1" % (CONTACT, hits))
        print("   FAIL - نقطة الإدراج ظهرت %d مرة بدل 1" % hits)
        return

    wa_before = text.count("wa.me/201000101040")
    new = text.replace(CARD_ANCHOR, WA_ROW + CARD_ANCHOR, 1)

    # التحقّق على الناتج نفسه، مش على النية
    errs: list[str] = []
    if new.count('class="wa-first"') != 1:
        errs.append("%s: wa-first مش ظاهر مرة واحدة بعد الإدراج" % CONTACT)
    if new.count("wa.me/201000101040") != wa_before + 1:
        errs.append("%s: عدد روابط wa.me ما زادش بمقدار 1" % CONTACT)
    if CARD_ANCHOR not in new:
        errs.append("%s: نقطة الإدراج نفسها اتكسرت" % CONTACT)
    if "icons.svg#i-wa" not in new:
        errs.append("%s: أيقونة واتساب مش موجودة بعد الإدراج" % CONTACT)
    p = crlf_problem(CONTACT, new)
    if p:
        errs.append(p)

    if errs:
        failures.extend(errs)
        print("   FAIL - لم يُكتب الملف")
        for e in errs:
            print("     - " + e)
        return

    if not check_only:
        write(CONTACT, new)
    print("   OK - أُدرج صف واتساب (%s)" % ("فحص فقط" if check_only else "مكتوب"))


def phase2(check_only: bool) -> None:
    print("== المرحلة 2: زر الشريط السفلي -> واتساب حقيقي (%d صفحة) ==" % len(PAGES))
    applied = already = 0

    for rel in PAGES:
        text = read(rel)
        matches = MC_WA_RE.findall(text)

        if len(matches) != 1:
            failures.append("%s: لقيت %d من أزرار mc-wa بدل 1" % (rel, len(matches)))
            print("   FAIL %-32s mc-wa x%d" % (rel, len(matches)))
            continue

        old = matches[0]
        if "wa.me/201000101040" in old:
            already += 1
            p = crlf_problem(rel, text)
            if p:
                failures.append(p)
            print("   --   %-32s already applied" % rel)
            continue

        pm = ICON_PREFIX_RE.search(old)
        if not pm:
            failures.append("%s: مش لاقي بادئة الأيقونة في: %s" % (rel, old[:80]))
            print("   FAIL %-32s مش لاقي بادئة الأيقونة" % rel)
            continue
        prefix = pm.group(1)

        new_anchor = (
            '<a class="mc-wa" href="' + WA + '" target="_blank" rel="noopener">'
            '<svg class="ic ic-fill" aria-hidden="true" focusable="false">'
            '<use href="' + prefix + 'assets/img/icons.svg#i-wa"></use></svg> واتساب</a>'
        )
        new = text.replace(old, new_anchor, 1)

        # التحقّق على الزر الجديد نفسه وعلى الناتج
        errs: list[str] = []
        if "wa.me/201000101040" not in new_anchor:
            errs.append("%s: رابط wa.me مش موجود في الزر الجديد" % rel)
        if "icons.svg#i-wa" not in new_anchor:
            errs.append("%s: الأيقونة مش #i-wa" % rel)
        if "icons.svg#i-mail" in new_anchor:
            errs.append("%s: أيقونة البريد لسه في زر mc-wa" % rel)
        if "واتساب" not in new_anchor:
            errs.append("%s: النص مش «واتساب»" % rel)
        if MC_WA_RE.findall(new) != [new_anchor]:
            errs.append("%s: الزر بعد التعديل مش مطابق للمتوقع" % rel)
        p = crlf_problem(rel, new)
        if p:
            errs.append(p)

        if errs:
            failures.extend(errs)
            print("   FAIL %-32s لم يُكتب" % rel)
            for e in errs:
                print("     - " + e)
            continue

        if not check_only:
            write(rel, new)
        applied += 1
        print("   OK   %-32s %s -> واتساب (بادئة الأيقونة %r)"
              % (rel, "href=%r" % old.split('href="')[1].split('"')[0], prefix or "."))

    print("   معدَّل: %d · مطبَّق سابقًا: %d · الإجمالي: %d/%d"
          % (applied, already, applied + already, len(PAGES)))


def final_sweep() -> None:
    """فحص نهائي على القرص: مفيش زر mc-wa إلا وهو واتساب حقيقي."""
    print("== فحص نهائي ==")

    bad = 0
    for rel in PAGES:
        for m in MC_WA_RE.finditer(read(rel)):
            a = m.group(0)
            href = a.split('href="')[1].split('"')[0]
            if href == WA and "icons.svg#i-wa" in a and "واتساب" in a:
                continue
            bad += 1
            failures.append("%s: زر mc-wa لسه مش واتساب (%s)" % (rel, href[:60]))
    print("   أزرار mc-wa غير واتساب: %d" % bad)

    stale = 0
    for rel in PAGES:
        for m in MOBILE_BAR_RE.finditer(read(rel)):
            if "mailto:" in m.group(0):
                stale += 1
                failures.append("%s: الشريط السفلي لسه فيه mailto" % rel)
    print("   mailto في الشريط السفلي: %d" % stale)

    c = read(CONTACT)
    n = c.count('class="wa-first"')
    print("   wa-first في contact.html: %d" % n)
    if n != 1:
        failures.append("contact.html: wa-first مش مرة واحدة (%d)" % n)

    wa_links = sum(read(r).count("wa.me/201000101040") for r in PAGES)
    print("   إجمالي روابط wa.me في الصفحات: %d" % wa_links)


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    if check_only:
        print("وضع الفحص فقط - لن يُكتب أي ملف\n")

    phase1(check_only)
    print()
    phase2(check_only)
    print()
    if check_only:
        # الفحص النهائي بيقرأ من القرص، ففي وضع الفحص بيبلّغ عن تعديلات لسه ما
        # اتكتبتش - فبنشيله بدل ما نطلع فشلًا وهميًا.
        print("== فحص نهائي: متخطّى في وضع --check (بيقرأ من القرص) ==")
    else:
        final_sweep()

    print()
    if failures:
        print("FAIL - %d مشكلة:" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
