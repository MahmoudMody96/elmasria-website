#!/usr/bin/env python3
"""Capture a selector from a local page, with a correct page height.

    python _tools/render/capture_section.py <page> <selector> <width> <out.png> [mode]

mode = crop (default)  -> tall window, crop the selector's band
       fixed           -> realistic phone viewport, crop the bottom band
                          (for position:fixed bars such as .mobile-call)

Why the content height is computed the way it is: measuring it as
max(documentElement.scrollHeight, body.scrollHeight) *inside an iframe of fixed
height* returns the IFRAME's height, because scrollHeight includes the viewport
-- any page taller than the iframe then reports the iframe's height (e.g. 6000)
instead of the real one, the capture window is too short, and the crop lands
outside the page. Computing it as the bottom of the lowest non-fixed child of
body is viewport-independent and correct.

Both passes force `.reveal` to its settled state (`.in`). The reveal animation is
untouched by this change and a real visitor always ends up in that state; without
forcing it a headless capture shows elements that are still transparent. The
count of not-yet-revealed elements is reported BEFORE forcing, so the signal is
not lost.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8911/"
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
# اللقطات مخرجات مش كود — بتتحفظ في _tools/shots (مستثنى من git)
OUT_DIR = os.path.join(ROOT, "_tools", "shots")

WRAP = """<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;background:#fff}iframe{width:%(w)dpx;height:%(h)dpx;border:0;display:block}</style>
</head><body><iframe id="f" src="%(url)s"></iframe>
<script>
document.getElementById('f').addEventListener('load',function(){setTimeout(function(){
  var o={}, f=document.getElementById('f'), d=f.contentDocument, w=f.contentWindow;
  try{
    o.notRevealedBefore=d.querySelectorAll('.reveal:not(.in)').length;
    [].slice.call(d.querySelectorAll('.reveal')).forEach(function(el){el.classList.add('in');});
    var el=d.querySelector('%(sel)s');
    if(!el){document.title='NOEL';return;}
    var r=el.getBoundingClientRect();
    o.top=Math.round(r.top); o.h=Math.round(r.height);
    /* ارتفاع المحتوى الحقيقي: أبعد نقطة سفلية لعناصر body غير الثابتة.
       العناصر position:fixed (الزر العائم وشريط الجوال و#toTop) قاعها = قاع
       الإطار، فلو حسبناها معاهم يطلع الارتفاع = ارتفاع الإطار (30000) بدل
       ارتفاع الصفحة، والقص يقع خارج الصفحة. */
    o.contentH=Math.round(Math.max.apply(null,[].slice.call(d.body.children)
        .filter(function(x){return w.getComputedStyle(x).position!=='fixed'})
        .map(function(x){return x.getBoundingClientRect().bottom})));
    o.innerW=w.innerWidth;
    o.notRevealedAfter=d.querySelectorAll('.reveal:not(.in)').length;
    document.title='R'+btoa(unescape(encodeURIComponent(JSON.stringify(o))));
  }catch(e){document.title='ERR '+e.message;}
},400);});
</script></body></html>"""


def run_chrome(args, timeout=180):
    return subprocess.run([CHROME] + args, capture_output=True, timeout=timeout)


def main() -> int:
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    page, selector, width, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    mode = sys.argv[5] if len(sys.argv) > 5 else "crop"
    url = page if page.startswith("http") else BASE + page
    os.makedirs(OUT_DIR, exist_ok=True)

    probe = os.path.join(ROOT, "_v26_cap_%d.html" % width)
    rel = "_v26_cap_%d.html" % width

    def measure(iframe_h: int):
        with open(probe, "w", encoding="utf-8", newline="") as fh:
            fh.write(WRAP % {"w": width, "h": iframe_h, "url": url, "sel": selector})
        r = run_chrome(["--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-prefers-reduced-motion",
                        "--virtual-time-budget=12000",
                        "--window-size=%d,4000" % (width + 40),
                        "--dump-dom", BASE + rel])
        dom = r.stdout.decode("utf-8", "replace")
        m = re.search(r"<title>([^<]*)</title>", dom)
        return m.group(1).strip() if m else ""

    try:
        # pass 1 - measure with a generous iframe so nothing is cut off
        t = measure(30000)
        if not t.startswith("R"):
            print("measure failed:", t[:200])
            return 1
        info = json.loads(base64.b64decode(t[1:]).decode("utf-8"))
        if abs(info["innerW"] - width) > 2:
            print("FAIL iframe laid out at %dpx not %dpx" % (info["innerW"], width))
            return 1
        print("measure: top=%d h=%d contentH=%d innerW=%d notRevealedBefore=%d"
              % (info["top"], info["h"], info["contentH"], info["innerW"],
                 info["notRevealedBefore"]))

        # pass 2 - capture at the real content height so the crop lands inside.
        # In `fixed` mode the iframe must be exactly the phone viewport height,
        # otherwise a position:fixed bar pins itself to the bottom of a very tall
        # iframe and falls outside the short screenshot window.
        viewport_h = info["contentH"] if mode == "crop" else 844
        iframe_h = max(info["contentH"], viewport_h) if mode == "crop" else viewport_h
        with open(probe, "w", encoding="utf-8", newline="") as fh:
            fh.write(WRAP % {"w": width, "h": iframe_h, "url": url, "sel": selector})
        png = os.path.join(OUT_DIR, "%s_%d.png" % (os.path.splitext(os.path.basename(out))[0], width))
        run_chrome(["--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--force-prefers-reduced-motion",
                    "--virtual-time-budget=12000",
                    "--window-size=%d,%d" % (width, viewport_h),
                    "--screenshot=" + png, BASE + rel])
    finally:
        if os.path.exists(probe):
            os.remove(probe)

    from PIL import Image
    im = Image.open(png)
    pad = 20
    if mode == "crop":
        box = (0, max(info["top"] - pad, 0),
               im.width, min(info["top"] + info["h"] + pad, im.height))
    else:
        box = (0, max(im.height - 150, 0), im.width, im.height)
    crop = im.crop(box)
    crop.save(out)
    print("saved %s (%dx%d from %dx%d)" % (out, crop.width, crop.height, im.width, im.height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
