# -*- coding: utf-8 -*-
"""
Visual / DOM check for the emoji → SVG icon migration.

It serves the site over http (needed so external <use href="…icons.svg#id"> works),
then asserts every rendered icon really paints (non-zero box + a <use> reference)
on desktop and mobile viewports, and writes reference screenshots.

Usage (from repo root):
    python _tools/visual_check.py
"""
from __future__ import annotations

import http.server
import os
import socketserver
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8899
SHOTS = os.path.join(ROOT, "_tools", "shots")
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"

JS_ICON_AUDIT = """
() => {
  const out = {total: 0, hidden: 0, broken: [], zero: [], unresolved: []};
  document.querySelectorAll('svg.ic').forEach((svg, i) => {
    const use = svg.querySelector('use');
    const href = use ? (use.getAttribute('href') || '') : '';
    if (!href) { out.broken.push({ i }); return; }
    out.total++;
    if (!svg.checkVisibility()) { out.hidden++; return; }   // inside a closed drawer / menu
    const box = svg.getBoundingClientRect();
    if (box.width === 0 || box.height === 0) out.zero.push({ href, w: box.width, h: box.height });
    // a broken external <use> renders nothing, so its painted box collapses to 0
    const painted = use.getBBox();
    if (painted.width === 0 && painted.height === 0) out.unresolved.push(href);
  });
  return out;
}
"""


JS_SCROLL_UI = """
() => {
  const bar = document.querySelector('#progress');
  const top = document.querySelector('#toTop');
  const cue = document.querySelector('.scroll-cue');
  const out = {bar: !!bar, top: !!top, cue: !!cue};
  if (bar) out.barTransform = getComputedStyle(bar).transform;
  if (top) {
    out.topShown = top.classList.contains('show');
    const b = top.getBoundingClientRect();
    out.topBox = [Math.round(b.width), Math.round(b.height)];
    out.topUse = !!top.querySelector('use');
  }
  if (cue) out.cueOff = cue.classList.contains('off');
  out.y = Math.round(window.scrollY);
  return out;
}
"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # silence per-request logging
        pass


def serve():
    os.chdir(ROOT)
    httpd = socketserver.TCPServer(("", PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def audit(page, label, problems):
    res = page.evaluate(JS_ICON_AUDIT)
    print(f"  {label}: {res['total']} icons total "
          f"({res['hidden']} skipped as hidden), {len(res['broken'])} without <use>, "
          f"{len(res['zero'])} zero-sized, {len(res['unresolved'])} unresolved")
    for b in res["broken"][:5]:
        problems.append(f"{label}: icon without <use> ({b})")
    for z in res["zero"][:5]:
        problems.append(f"{label}: zero-sized icon {z}")
    for u in res["unresolved"][:5]:
        problems.append(f"{label}: <use> did not resolve: {u}")


def check_scroll_ui(page, label, problems, shot_path=None, expect_cue=True):
    """Exercise the motion v2.2 scroll UI: progress bar, back-to-top button, hero cue."""
    # make sure we really start from the top (desktop flow arrives after other scrolls)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(400)
    at_top = page.evaluate(JS_SCROLL_UI)
    if not at_top["bar"]:
        problems.append(f"{label}: missing #progress bar")
    if not at_top["top"]:
        problems.append(f"{label}: missing #toTop button")
    if expect_cue and not at_top["cue"]:
        problems.append(f"{label}: missing .scroll-cue")
    if at_top.get("topShown"):
        problems.append(f"{label}: #toTop is visible at the top of the page")
    if at_top.get("cueOff"):
        problems.append(f"{label}: .scroll-cue already faded at the top of the page")

    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(600)
    bottom = page.evaluate(JS_SCROLL_UI)
    if not bottom.get("topUse"):
        problems.append(f"{label}: #toTop has no <use> icon")
    if bottom.get("topBox") == [0, 0]:
        problems.append(f"{label}: #toTop has a zero box")
    if not bottom.get("topShown"):
        problems.append(f"{label}: #toTop did not appear after scrolling down")
    if bottom.get("barTransform") in (None, "none", "matrix(0, 0, 0, 1, 0, 0)"):
        problems.append(f"{label}: #progress did not advance (transform={bottom.get('barTransform')})")
    if expect_cue and not bottom.get("cueOff"):
        problems.append(f"{label}: .scroll-cue did not fade out after scrolling")
    if shot_path:
        page.screenshot(path=shot_path)

    print(f"  {label} scroll UI: toTop hidden@top={not at_top.get('topShown')} "
          f"shown@bottom={bottom.get('topShown')} box={bottom.get('topBox')} "
          f"bar={bottom.get('barTransform')} cueFaded={bottom.get('cueOff')}")

    page.click("#toTop")
    back = None
    for _ in range(12):          # the smooth scroll can take a couple of seconds
        page.wait_for_timeout(350)
        back = page.evaluate("() => Math.round(window.scrollY)")
        if back <= 60:
            break
    if back > 60:
        problems.append(f"{label}: clicking #toTop did not return to the top (scrollY={back})")
    return bottom


def main() -> int:
    os.makedirs(SHOTS, exist_ok=True)
    httpd = serve()
    problems: list[str] = []
    shot = lambda name: os.path.join(SHOTS, name)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        errors: list[str] = []

        def watch_errors(pg, label):
            pg.on("pageerror", lambda e: errors.append(f"{label}: JS error — {e}"))
            pg.on("console", lambda m: errors.append(f"{label}: console.{m.type} — {m.text}")
                  if m.type == "error" else None)

        # ---------- desktop ----------
        page.goto(f"http://localhost:{PORT}/index.html", wait_until="load")
        page.wait_for_timeout(600)
        watch_errors(page, "desktop")
        audit(page, "index.html desktop", problems)
        page.locator(".nav-links .has-drop").hover()
        page.wait_for_timeout(400)
        page.screenshot(path=shot("01-desktop-dropdown.png"),
                        clip={"x": 0, "y": 0, "width": 1440, "height": 460})
        page.locator("#services").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=shot("02-desktop-services.png"))
        page.locator(".check-list").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=shot("03-desktop-checklist.png"))
        page.locator("footer .foot-contact").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=shot("04-desktop-footer.png"))
        check_scroll_ui(page, "index.html desktop", problems, shot("14-desktop-totop.png"))

        page.goto(f"http://localhost:{PORT}/about.html", wait_until="load")
        page.wait_for_timeout(400)
        audit(page, "about.html desktop", problems)
        page.locator(".pol-grid").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=shot("05-desktop-about-values.png"))
        page.locator("footer .foot-contact").scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        page.screenshot(path=shot("06-desktop-about-footer.png"))

        page.goto(f"http://localhost:{PORT}/contact.html", wait_until="load")
        page.wait_for_timeout(400)
        audit(page, "contact.html desktop", problems)
        page.locator(".info-card").scroll_into_view_if_needed()
        page.wait_for_timeout(250)
        page.screenshot(path=shot("07-desktop-contact.png"))

        page.goto(f"http://localhost:{PORT}/projects.html", wait_until="load")
        page.wait_for_timeout(400)
        audit(page, "projects.html desktop", problems)
        page.locator(".why-card").first.scroll_into_view_if_needed()
        page.wait_for_timeout(250)
        page.screenshot(path=shot("08-desktop-projects.png"))

        # ---------- service detail ----------
        page.goto(f"http://localhost:{PORT}/services/safety.html", wait_until="load")
        page.wait_for_timeout(400)
        audit(page, "services/safety.html desktop", problems)
        page.screenshot(path=shot("09-desktop-service-hero.png"),
                        clip={"x": 0, "y": 0, "width": 1440, "height": 620})
        page.locator(".side-card").first.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=shot("10-desktop-service-side.png"))

        page.goto(f"http://localhost:{PORT}/services/index.html", wait_until="load")
        page.wait_for_timeout(400)
        audit(page, "services/index.html desktop", problems)

        # ---------- mobile ----------
        mob = browser.new_page(viewport={"width": 390, "height": 844},
                               is_mobile=True, has_touch=True, device_scale_factor=2)
        mob.goto(f"http://localhost:{PORT}/index.html", wait_until="load")
        mob.wait_for_timeout(600)
        watch_errors(mob, "mobile")
        audit(mob, "index.html mobile", problems)
        check_scroll_ui(mob, "index.html mobile", problems, shot("15-mobile-totop.png"))
        mob.screenshot(path=shot("11-mobile-header.png"),
                       clip={"x": 0, "y": 0, "width": 390, "height": 300})
        mob.locator("#burger").click()
        mob.wait_for_timeout(700)
        audit(mob, "index.html mobile drawer", problems)
        mob.screenshot(path=shot("12-mobile-drawer.png"))

        mob.goto(f"http://localhost:{PORT}/services/safety.html", wait_until="load")
        mob.wait_for_timeout(500)
        audit(mob, "services/safety.html mobile", problems)
        mob.screenshot(path=shot("13-mobile-service.png"))

        browser.close()

    httpd.shutdown()
    print(f"\nconsole/JS errors   : {len(errors)}")
    for e in errors[:8]:
        problems.append(e)
    print(f"screenshots -> {SHOTS}")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  - " + p)
        return 1
    print("All rendered icons have a <use> reference and a non-zero box; "
          "scroll UI works and no JS/console errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
