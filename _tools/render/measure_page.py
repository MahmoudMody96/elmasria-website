#!/usr/bin/env python3
"""Measure the v26 services redesign + WhatsApp additions in a real browser.

    python _tools/render/measure_page.py <page> <width>

Prints one JSON blob of *computed* values (not eyeballed ones) so the redesign
can be checked against its intent: column count, card width/height, the h3 and
p font metrics, whether the 3-line clamp is actually clipping, per-group card
heights (are they equal?), horizontal overflow, and the WhatsApp surfaces.

Mechanics are the proven ones from render_section.py:
  * the wrapper MUST be same-origin with the page, so it is written into the
    served tree and deleted in a finally block;
  * the iframe is laid out at the requested width and the run FAILS if
    innerWidth disagrees, because every number would then describe a different
    layout;
  * the result travels in <title> as base64 so no quoting/escaping can corrupt
    it, and no marker string can collide with page content.
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

PROBE = """<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0}iframe{width:%(w)dpx;height:20000px;border:0;display:block}</style>
</head><body><iframe id="f" src="%(url)s"></iframe>
<script>
function run(){
  var o={}, f=document.getElementById('f'), d=f.contentDocument, w=f.contentWindow;
  function gs(el,p){return w.getComputedStyle(el)[p]}
  function px(v){return Math.round(parseFloat(v)*100)/100}
  try{
    o.innerW=w.innerWidth;
    o.pageH=Math.max(d.documentElement.scrollHeight,d.body.scrollHeight);
    o.scrollW=d.documentElement.scrollWidth;
    o.clientW=d.documentElement.clientWidth;
    o.overflow=o.scrollW-o.clientW;
    o.notRevealed=d.querySelectorAll('.reveal:not(.in)').length;

    var g=d.querySelector('.svc-grid');
    if(g){
      o.cols=gs(g,'gridTemplateColumns').split(' ').length;
      o.gridCols=gs(g,'gridTemplateColumns');
      o.gap=gs(g,'gap');
      var cards=[].slice.call(g.querySelectorAll('.svc-card'));
      o.cards=cards.length;
      var c0=cards[0], r=c0.getBoundingClientRect();
      o.cardW=Math.round(r.width*100)/100; o.cardH=Math.round(r.height);
      o.cardRadius=gs(c0,'borderRadius');
      var im=c0.querySelector('.im');
      if(im) o.imH=Math.round(im.getBoundingClientRect().height);
      var h3=c0.querySelector('h3');
      o.h3={size:px(gs(h3,'fontSize')),weight:gs(h3,'fontWeight'),lh:px(gs(h3,'lineHeight'))};
      var p=c0.querySelector('p'), ps=gs(p,'fontSize'), plh=parseFloat(gs(p,'lineHeight'));
      o.p={size:px(ps),color:gs(p,'color'),lh:px(plh),
           clientH:p.clientHeight,scrollH:p.scrollHeight,
           clamped:p.scrollHeight>p.clientHeight+1,
           lines:Math.round(p.clientHeight/plh)};
      var link=c0.querySelector('.svc-link');
      if(link) o.svcLink=px(gs(link,'fontSize'));
      var num=c0.querySelector('.svc-num');
      if(num) o.svcNum=px(gs(num,'fontSize'));
      var gh=d.querySelector('.svc-group-head h3');
      if(gh) o.groupH3=px(gs(gh,'fontSize'));
      var gp=d.querySelector('.svc-group-head p');
      if(gp) o.groupP={size:px(gs(gp,'fontSize')),color:gs(gp,'color')};

      // كل الكروت: هل الوصف مقصوص فعلًا؟ وهل الارتفاعات متساوية داخل كل مجموعة؟
      var all=[].slice.call(g.querySelectorAll('.svc-card p'));
      o.pClampedCount=all.filter(function(x){return x.scrollHeight>x.clientHeight+1}).length;
      o.pTotal=all.length;
      o.pLineSpread=all.map(function(x){return Math.round(x.clientHeight/plh)});
      o.groups=[].slice.call(d.querySelectorAll('.svc-group')).map(function(gr){
        var hs=[].slice.call(gr.querySelectorAll('.svc-card')).map(function(c){
          return Math.round(c.getBoundingClientRect().height)});
        return {name:gr.getAttribute('data-group'),n:hs.length,
                min:Math.min.apply(null,hs),max:Math.max.apply(null,hs),hs:hs};
      });
      o.secH=Math.round(d.getElementById('services').getBoundingClientRect().height);
    }

    var wa=d.querySelector('.wa-first a');
    if(wa){
      o.wa={bg:gs(wa,'backgroundColor'),color:gs(wa,'color'),
            h:Math.round(wa.getBoundingClientRect().height),
            txt:wa.textContent.replace(/\\s+/g,' ').trim(),
            href:wa.getAttribute('href')};
    }
    var bar=d.querySelector('.mobile-call');
    if(bar){
      var mc=bar.querySelector('.mc-wa');
      o.mcwa={barDisplay:gs(bar,'display'),bg:gs(mc,'backgroundColor'),
              color:gs(mc,'color'),txt:mc.textContent.replace(/\\s+/g,' ').trim(),
              href:mc.getAttribute('href'),icon:mc.querySelector('use').getAttribute('href')};
    }
    var card=d.querySelector('.info-card');
    if(card){
      o.infoCard={h:Math.round(card.getBoundingClientRect().height),
                  waRows:card.querySelectorAll('.wa-first').length};
      o.contactGrid=gs(d.querySelector('.contact-grid'),'gridTemplateColumns');
    }
    document.title='R'+btoa(unescape(encodeURIComponent(JSON.stringify(o))));
  }catch(e){ document.title='ERR '+e.message; }
}
document.getElementById('f').addEventListener('load',function(){setTimeout(run,500);});
</script></body></html>"""


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    page, width = sys.argv[1], int(sys.argv[2])
    url = page if page.startswith("http") else BASE + page

    probe = os.path.join(ROOT, "_v26_probe_%d.html" % width)
    with open(probe, "w", encoding="utf-8", newline="") as fh:
        fh.write(PROBE % {"w": width, "url": url})
    try:
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-prefers-reduced-motion", "--virtual-time-budget=12000",
             "--window-size=%d,6000" % (width + 40), "--dump-dom",
             BASE + "_v26_probe_%d.html" % width],
            capture_output=True, timeout=180)
    finally:
        os.remove(probe)

    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r"<title>([^<]*)</title>", dom)
    if not m:
        print("ERR no title in dump")
        return 1
    title = m.group(1).strip()
    if title.startswith("ERR"):
        print(title)
        return 1
    if not title.startswith("R"):
        print("ERR unexpected title: %r" % title[:120])
        return 1

    data = json.loads(base64.b64decode(title[1:]).decode("utf-8"))
    if abs(data["innerW"] - width) > 2:
        print("FAIL iframe laid out at %dpx, not %dpx - numbers unusable"
              % (data["innerW"], width))
        return 1
    data["_page"] = page
    data["_width"] = width
    print(json.dumps(data, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
