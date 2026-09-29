#!/usr/bin/env python3
"""
verify_span_scope.py — حارس «تسريب الوسم على الـspan المتداخل».

المشكلة اللي بيمسكها:
  قاعدة CSS زي `.kstat span{...}` بتستهدف *أي* span جوّه المكوّن. لو جوه
  المكوّن span متداخل (زي `<b><span dir="ltr"><span data-years-since>27</span>+</span></b>`)
  فالابن بياخد ستايل الوسم: بيتقلب display:block (فينكسر «27+» على سطرين)
  ويتصغّر وياخد لون رمادي. **مفيش أي خطأ بيظهر** — الشكل بس بيبوظ.

القاعدة: الوسم بيتكتب مقيّدًا بـ`>` أو `+`:
    .kstat > b + span{...}     صحيح
    .kstat span{...}           تسريب

الخروج بـ1 لو لقى أي قاعدة سليل مجرّد بتلمس span متداخل.
"""
import re
import sys
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "assets/css/style.css")

# تعليقات CSS بتتشال قبل الفحص — قاعدة معلَّقة مش قاعدة شغّالة
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
# سيلكتور ينتهي بـ`span` مجرّد عبر مُركّب السليل (مسافة) — مش `>span` ولا `+span`
BARE_SPAN = re.compile(r"(?:^|[\s>+~])(?:[\w.#\[\]=\"'-]*\s)*span$")
SELECTOR_TAIL = re.compile(r"span$")


def bare_descendant_span_selectors(css_text):
    """كل السيلكتورات اللي آخر عنصر فيها `span` مجرّد ومُركّبه سليل (مسافة)."""
    text = CSS_COMMENT.sub(" ", css_text)
    found = set()
    # كل كتلة سيلكتور{...}
    for m in re.finditer(r"([^{}]+)\{", text):
        block = m.group(1).strip()
        if block.startswith("@"):
            continue
        for sel in block.split(","):
            sel = " ".join(sel.split())
            if not sel:
                continue
            # آخر مُركّب لازم يكون مسافة (سليل) مش > أو + أو ~
            if re.search(r"[>+~]\s*span$", sel):
                continue                      # مقيّد — آمن
            if re.match(r"^span$", sel):
                found.add(sel)                # `span` عريان تمامًا
                continue
            if not re.search(r"[\s]\s*span$", sel):
                continue                      # آخر مُركّب مش سليل
            found.add(sel)
    return sorted(found)


def anchor_classes(sel):
    return re.findall(r"\.([A-Za-z_][\w-]*)", sel)


def html_files():
    out = []
    for pat in ("*.html", "*/*.html", "*/*/*.html"):
        out.extend(glob.glob(os.path.join(ROOT, pat)))
    return [f for f in sorted(set(out))
            if ".git" not in f and ".workbuddy-ai" not in f]


NESTED_SPAN = re.compile(r"<span\b[^>]*>(?:(?!</span>).)*?<span\b", re.S)

# عناصر فاضية/ذاتية الإغلاق — من غير وسم إغلاق، فمتتحسبش في العدّ
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
        "path", "circle", "rect", "line", "polyline", "polygon",
        "ellipse", "use", "stop", "image"}

TAG_OPEN = re.compile(r"<([A-Za-z][\w-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>")
TAG_CLOSE = re.compile(r"</([A-Za-z][\w-]*)\s*>")


def balanced_subtree(text, start):
    """يرجّع نص الشجرة المتوازنة للعنصر اللي بيبدأ عند `start` (موضع `<`).

    الاعتماد على عدّاد عمق بنفس اسم الوسم — بدل نافذة أحرف ثابتة، لأن
    النافذة الثابتة بتعدّي حدود العنصر وتطلّع نتائج كاذبة.
    """
    m = TAG_OPEN.match(text, start)
    if not m:
        return None
    tag = m.group(1).lower()
    if m.group(3) == "/" or tag in VOID:
        return ""
    depth = 1
    i = m.end()
    while i < len(text):
        nxt_open = TAG_OPEN.search(text, i)
        nxt_close = TAG_CLOSE.search(text, i)
        if not nxt_close:
            return text[m.end():]                    # مفيش إغلاق — خُد الباقي
        if nxt_open and nxt_open.start() < nxt_close.start():
            inner_tag = nxt_open.group(1).lower()
            if inner_tag == tag and nxt_open.group(3) != "/" and inner_tag not in VOID:
                depth += 1
            i = nxt_open.end()
            continue
        if nxt_close.group(1).lower() == tag:
            depth -= 1
            if depth == 0:
                return text[m.end():nxt_close.start()]
        i = nxt_close.end()
    return text[m.end():]


def find_leaks(selectors, files):
    leaks = []
    for sel in selectors:
        classes = anchor_classes(sel)
        if not classes:
            continue
        for path in files:
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for cls in classes:
                pat = re.compile(r'class="[^"]*\b' + re.escape(cls) + r'\b[^"]*"')
                for m in pat.finditer(text):
                    # ارجع لبداية الوسم اللي شايل الكلاس
                    lt = text.rfind("<", 0, m.start())
                    if lt < 0:
                        continue
                    body = balanced_subtree(text, lt)
                    if body is None:
                        continue
                    if NESTED_SPAN.search(body):
                        leaks.append((sel, os.path.relpath(path, ROOT).replace("\\", "/"), cls))
    return leaks


def main():
    if not os.path.exists(CSS):
        print("FAIL  style.css مش موجود")
        return 1
    css = open(CSS, encoding="utf-8").read()
    sels = bare_descendant_span_selectors(css)
    files = html_files()

    print(f"ملفات HTML المفحوصة : {len(files)}")
    print(f"قواعد span سليل مجرّد: {len(sels)}")

    if not sels:
        print("\nOK  مفيش أي قاعدة سليل مجرّد على span — كلها مقيّدة بـ> أو +.")
        return 0

    leaks = find_leaks(sels, files)

    print("\n== كل قاعدة سليل مجرّد على span ==")
    for s in sels:
        hit = [l for l in leaks if l[0] == s]
        mark = "تسريب!" if hit else "آمن (مفيش span متداخل)"
        print(f"   {s:26s} {mark}")

    if leaks:
        print("\nFAIL  قواعد بتلمس span متداخل — قيّدها بـ`>` أو `+`:")
        seen = set()
        for sel, path, cls in leaks:
            key = (sel, path)
            if key in seen:
                continue
            seen.add(key)
            print(f"   {sel}   في {path}   (حول .{cls})")
        print("\n   الحل: بدل `.x span{...}` اكتب `.x > b + span{...}`")
        print("   أو اكتب وسمًا صريحًا وحُط عليه كلاس.")
        return 1

    print("\nOK  مفيش تسريب — كل قواعد span إما مقيّدة أو من غير span متداخل.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
