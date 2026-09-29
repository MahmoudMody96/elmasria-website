#!/usr/bin/env python3
"""تطبيق تعديلات «بلا خطوط خلفية + بطاقة رئيس بيضاء» على style.css.

كل استبدال بيتحقّق إنه حصل فعلًا، وإن عدد مرات الحدوث زي المتوقع.
بيوقف فورًا لو أي استبدال فشل — بدل ما يسيّب الملف نصف معدَّل.
"""
import sys

CSS = "assets/css/style.css"
src = open(CSS, encoding="utf-8").read()
orig = src
applied = []


def rep(label, old, new, expect=1):
    global src
    n = src.count(old)
    if n != expect:
        print(f"FAIL  {label}: لقيت {n} حدوث، المتوقع {expect}")
        sys.exit(1)
    src = src.replace(old, new)
    applied.append(label)
    print(f"OK    {label}  ({n})")


# ---- 1) توكن اللايم الغامق ----------------------------------------------
rep("token --lime-d",
    "  --lime:#bcd800;\n  --lime-soft:#f4f9d9;",
    "  --lime:#bcd800;\n"
    "  /* لايم غامق للنص والأيقونات على الخلفيات البيضاء — #bcd800 على أبيض = 1.62:1 (يسقط AA) */\n"
    "  --lime-d:#5f6b00;\n"
    "  --lime-soft:#f4f9d9;")

# ---- 2) شيل شبكة اللوحة الداكنة ----------------------------------------
rep("remove .card.dark grid",
    "/* اللوحة الداكنة: شبكة خفيفة + صورة صناعية ممزوجة في القاع */\n"
    ".card.dark{background:var(--g900);color:#fff;border-color:transparent;padding:34px;position:relative;overflow:hidden}\n"
    ".card.dark::before{content:\"\";position:absolute;inset:0;pointer-events:none;\n"
    "  background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),\n"
    "    linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:36px 36px}\n"
    ".card.dark>*{position:relative}",
    "/* اللوحة الداكنة — بلا شبكة خلفية */\n"
    ".card.dark{background:var(--g900);color:#fff;border-color:transparent;padding:34px;position:relative;overflow:hidden}\n"
    ".card.dark>*{position:relative}")

# ---- 3) شيل .grid-bg و .grid-bg-d --------------------------------------
rep("remove .grid-bg / .grid-bg-d",
    ".grid-bg{\n"
    "  background-image:linear-gradient(rgba(11,94,134,.07) 1px,transparent 1px),\n"
    "    linear-gradient(90deg,rgba(11,94,134,.07) 1px,transparent 1px);\n"
    "  background-size:34px 34px;\n"
    "}\n"
    ".grid-bg-d{\n"
    "  background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),\n"
    "    linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);\n"
    "  background-size:34px 34px;\n"
    "}\n",
    "")

# ---- 4) بطاقة القيادة بيضاء + بلا شبكة ---------------------------------
rep("chair-card -> white, no grid",
    ".chair-card{position:relative;overflow:hidden;border-radius:var(--r-lg);background:var(--g900);\n"
    "  color:#e8f1f6;display:grid;grid-template-columns:320px 1fr;box-shadow:var(--sh-lg)}\n"
    ".chair-card::before{content:\"\";position:absolute;inset:0;pointer-events:none;z-index:0;\n"
    "  background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),\n"
    "    linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:36px 36px}\n"
    ".chair-card>*{position:relative;z-index:2}",
    "/* بطاقة القيادة — بيضاء على قسم أبيض، بلا شبكة. لوحة الصورة تحتفظ\n"
    "   بالصورة + التدرّج الداكن لأن الاسم أبيض فوق الصورة ولازم يفضل مقروء. */\n"
    ".chair-card{position:relative;overflow:hidden;border-radius:var(--r-lg);background:#fff;\n"
    "  color:var(--ink);display:grid;grid-template-columns:320px 1fr;\n"
    "  border:1px solid var(--line);box-shadow:var(--sh-lg)}\n"
    ".chair-card>*{position:relative;z-index:2}")

# ---- 5) متن البطاقة: نصوص غامقة + لايم غامق ----------------------------
rep("cc-body colours",
    ".cc-body .kicker{color:var(--cyan);margin-bottom:12px}\n"
    ".cc-body .kicker::before{background:var(--lime)}\n"
    ".cc-body h3{color:#fff;font-size:clamp(20px,2.3vw,26px);line-height:1.45;margin:0 0 14px}\n"
    ".cc-body p{color:#bfd3de;margin:0}\n"
    ".cc-body .svc-link{margin-top:22px;color:var(--cyan);align-self:flex-start}\n"
    ".cc-body .svc-link:hover{color:#fff}",
    ".cc-body .kicker{color:var(--g700);margin-bottom:12px}\n"
    ".cc-body .kicker::before{background:var(--lime-d)}\n"
    ".cc-body h3{color:var(--ink);font-size:clamp(20px,2.3vw,26px);line-height:1.45;margin:0 0 14px}\n"
    "/* اللايم على الأبيض يسقط — نستخدم النسخة الغامقة جوه البطاقة فقط */\n"
    ".cc-body .hl-lime{color:var(--lime-d)}\n"
    ".cc-body p{color:var(--mut);margin:0}\n"
    ".cc-body .svc-link{margin-top:22px;color:var(--g700);align-self:flex-start}\n"
    ".cc-body .svc-link:hover{color:var(--g900)}")

# ---- 6) أرقام الملف المهني على الأبيض ----------------------------------
rep("kstat colours",
    ".kstat .ki{width:46px;height:46px;margin:0 auto 10px;border-radius:14px;display:grid;place-items:center;\n"
    "  background:rgba(255,255,255,.07)}\n"
    ".kstat .ki .ic{width:22px;height:22px}\n"
    ".kstat b{display:block;font-family:var(--font-h);font-size:24px;line-height:1.1;color:#fff}\n"
    ".kstat > b + span{display:block;margin-top:5px;color:#a8bdc8;font-size:12px;line-height:1.5}\n"
    ".kstat.cyan .ki{color:var(--cyan)}\n"
    ".kstat.lime .ki{color:var(--lime)}\n"
    ".kstat.org .ki{color:var(--org-lt)}",
    ".kstat .ki{width:46px;height:46px;margin:0 auto 10px;border-radius:14px;display:grid;place-items:center;\n"
    "  background:var(--paper);border:1px solid var(--line)}\n"
    ".kstat .ki .ic{width:22px;height:22px}\n"
    ".kstat b{display:block;font-family:var(--font-h);font-size:24px;line-height:1.1;color:var(--ink)}\n"
    ".kstat > b + span{display:block;margin-top:5px;color:var(--mut);font-size:12px;line-height:1.5}\n"
    "/* ألوان الأيقونات على الأبيض: السماوي 2.92 واللايم 1.62 والبرتقالي الفاتح 2.34 — كلهم يسقطوا AA */\n"
    ".kstat.cyan .ki{color:var(--g700)}\n"
    ".kstat.lime .ki{color:var(--lime-d)}\n"
    ".kstat.org .ki{color:var(--org-d)}")

# ---- 7) قائمة المؤهلات على الأبيض --------------------------------------
rep("cred-item colours",
    ".cred-item{display:flex;gap:10px;align-items:center;background:rgba(255,255,255,.06);\n"
    "  border:1px solid var(--line-d);border-radius:12px;padding:9px 12px;font-size:12.5px;\n"
    "  line-height:1.45;color:#e3eef4}\n"
    ".cred-item .ci{width:30px;height:30px;flex:none;border-radius:9px;display:grid;place-items:center;\n"
    "  background:rgba(188,216,0,.14);color:var(--lime)}",
    ".cred-item{display:flex;gap:10px;align-items:center;background:var(--paper);\n"
    "  border:1px solid var(--line);border-radius:12px;padding:9px 12px;font-size:12.5px;\n"
    "  line-height:1.45;color:var(--ink)}\n"
    ".cred-item .ci{width:30px;height:30px;flex:none;border-radius:9px;display:grid;place-items:center;\n"
    "  background:rgba(95,107,0,.12);color:var(--lime-d)}")

# ---- 8) قسم القيادة: أبيض ناصع بلا زخارف --------------------------------
rep("sec-lead -> pure white, no decorations",
    "/* قسم فاتح بزخارف: صورة صناعية باهتة أعلى + دائرة لايم في الزاوية */\n"
    ".sec-lead{position:relative;overflow:hidden;background:var(--paper)}\n"
    ".sec-lead::before{content:\"\";position:absolute;inset:0 0 auto 0;height:340px;pointer-events:none;\n"
    "  background:url(../img/photos/industrial-plant-960.webp) center 30%/cover no-repeat;opacity:.10;\n"
    "  -webkit-mask-image:linear-gradient(to bottom,#000,transparent);\n"
    "  mask-image:linear-gradient(to bottom,#000,transparent)}\n"
    ".sec-lead::after{content:\"\";position:absolute;inset-inline-start:-90px;top:-90px;width:260px;height:260px;\n"
    "  border-radius:50%;background:var(--lime);opacity:.13;pointer-events:none}\n"
    ".sec-lead .container{position:relative;z-index:1}",
    "/* قسم القيادة — أبيض ناصع بلا أي زخرفة أو خطوط خلفية */\n"
    ".sec-lead{position:relative;background:#fff}\n"
    ".sec-lead .container{position:relative;z-index:1}")

# ---- 9) شيل شبكة اللوحة الفنية -----------------------------------------
rep("remove .tech-panel grid",
    ".tech-panel::before{content:\"\";position:absolute;inset:0;\n"
    "  background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),\n"
    "    linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);\n"
    "  background-size:30px 30px;pointer-events:none}\n",
    "")

# ---- كتابة --------------------------------------------------------------
if src == orig:
    print("\nمفيش أي تغيير — حاجة غلط")
    sys.exit(1)
open(CSS, "w", encoding="utf-8", newline="").write(src)
print(f"\nاتكتب {CSS} — {len(applied)} تعديل")
print("الشبكات الباقية:", src.count("background-size:36px 36px") + src.count("background-size:34px 34px") + src.count("background-size:30px 30px"))
print("grid-bg باقي:", src.count("grid-bg"))
