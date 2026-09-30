/* EL MASRIA — shared behaviour (no framework, minimal JS) */
(function(){
  "use strict";
  var $ = function(s,c){ return (c||document).querySelector(s); };
  var $$ = function(s,c){ return Array.prototype.slice.call((c||document).querySelectorAll(s)); };

  /* sticky header shadow */
  var head = $("#siteHead");
  var onScroll = function(){ if(head) head.classList.toggle("scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, {passive:true}); onScroll();

  /* footer year — every page ships <span id="yy">2026</span> so it never goes stale */
  var yy = $("#yy");
  if(yy) yy.textContent = String(new Date().getFullYear());

  /* mobile drawer — keeps aria-expanded / aria-hidden / inert in sync with the CSS state */
  var burger = $("#burger"), drawer = $("#drawer");
  if(burger && drawer){
    var setDrawer = function(open){
      drawer.classList.toggle("open", open);
      drawer.setAttribute("aria-hidden", open ? "false" : "true");
      if("inert" in drawer) drawer.inert = !open;
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    };
    setDrawer(false);
    burger.addEventListener("click", function(){ setDrawer(true); });
    drawer.addEventListener("click", function(e){
      if(e.target.closest("[data-close]") || e.target.classList.contains("scrim")) setDrawer(false);
    });
    document.addEventListener("keydown", function(e){
      if(e.key === "Escape") setDrawer(false);
    });
  }

  /* reveal on scroll */
  var io = ("IntersectionObserver" in window) ? new IntersectionObserver(function(es){
    es.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add("in"); io.unobserve(en.target); } });
  },{threshold:.12}) : null;
  $$(".reveal,.reveal-img").forEach(function(el){ if(io) io.observe(el); else el.classList.add("in"); });

  /* experience-years derived from founding year 1999 (company-stated) — animated count-up */
  (function(){
    var reduceY = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function yearsOf(el){ return new Date().getFullYear() - (parseInt(el.getAttribute("data-years-since"),10) || 1999); }
    function animate(el){
      var target = yearsOf(el);
      if(reduceY || !("requestAnimationFrame" in window)){ el.textContent = String(target); return; }
      var t0 = null, dur = 1400;
      function fr(ts){
        if(!t0) t0 = ts;
        var p = Math.min((ts - t0) / dur, 1);
        el.textContent = String(Math.round(target * (1 - Math.pow(1 - p, 3))));
        if(p < 1) requestAnimationFrame(fr);
      }
      requestAnimationFrame(fr);
      setTimeout(function(){ el.textContent = String(target); }, dur + 400);
    }
    function watch(){
      $$("[data-years-since]").forEach(function(el){
        if(el.__counted) return; el.__counted = true;
        if(!("IntersectionObserver" in window)){ animate(el); return; }
        var o = new IntersectionObserver(function(es){
          es.forEach(function(en){ if(en.isIntersecting){ animate(el); o.disconnect(); } });
        }, {threshold:.4});
        o.observe(el);
      });
    }
    if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", watch);
    else watch();
  })();

  /* contact form: validate then open mail client (static hosting, no backend) */
  var form = $("#contactForm");
  if(form){
    /* preselect service when arriving from a service page (?service=slug) */
    try{
      var slug = (new URLSearchParams(window.location.search).get("service") || "").replace(/\.html?$/,"");
      var svcMap = {"safety":"السلامة والصحة المهنية","civil-defense":"الحماية المدنية",
        "iso":"التأهيل للحصول على شهادات الايزو","environmental":"الدراسات البيئية",
        "pest-control":"خدمة مكافحه الآفات والحشرات","cleaning":"خدمات اعمال النظافة",
        "landscape":"اللاند سكيب وتنسيق الحدائق","clinic":"خدمات العيادة",
        "manpower":"تعيين العمال بالأقسام الانتاجية لكل التخصصات",
        "construction":"اعمال المقاولات والانشاءات","football-fields":"انشاء وصيانة ملاعب كرة القدم"};
      if(svcMap[slug]){
        var sel = $("#cf-service");
        if(sel){
          for(var i=0;i<sel.options.length;i++){
            if(sel.options[i].text === svcMap[slug]){ sel.selectedIndex = i; break; }
          }
        }
      }
    }catch(_){}
    form.addEventListener("submit", function(e){
      e.preventDefault();
      var ok = true;
      $$("[data-req]", form).forEach(function(f){
        var err = f.closest(".f-group").querySelector(".f-err");
        var bad = !f.value.trim() || (f.type==="tel" && f.value.replace(/\D/g,"").length < 8);
        if(err) err.textContent = bad ? "هذا الحقل مطلوب — فضلاً أدخل بيانات صحيحة." : "";
        if(bad) ok = false;
      });
      if(!ok) return;
      var v = function(id){ return $("#"+id).value.trim(); };
      var msg = "طلب جديد من موقع الشركة:%0Aالاسم: " + encodeURIComponent(v("cf-name")) +
        "%0Aالشركة: " + encodeURIComponent(v("cf-company")) +
        "%0Aالهاتف: " + encodeURIComponent(v("cf-phone")) +
        "%0Aالخدمة: " + encodeURIComponent(v("cf-service")) +
        "%0Aالتفاصيل: " + encodeURIComponent(v("cf-msg"));
      window.open("https://wa.me/201000101040?text=" + msg, "_blank", "noopener");
      var done = $("#formDone");
      if(done){ done.hidden = false; done.scrollIntoView({behavior:"smooth",block:"center"}); }
      form.reset();
    });
  }

  /* motion v2.1 — hero parallax (background check: reduced motion) */
  (function(){
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var inner = document.querySelector(".hero-inner");
    var media = document.querySelector(".hero-media");
    if(inner){ setTimeout(function(){ inner.classList.add("anim-done"); }, 1500); }
    if(reduce || !("requestAnimationFrame" in window) || (!inner && !media)) return;
    var ticking = false;
    function onScroll(){
      if(ticking) return; ticking = true;
      requestAnimationFrame(function(){
        var y = window.scrollY || 0;
        if(y < window.innerHeight * 1.2){
          if(inner) inner.style.transform = "translateY(" + (y * 0.22) + "px)";
          if(media) media.style.transform = "translateY(" + (y * 0.08) + "px)";
        }
        ticking = false;
      });
    }
    window.addEventListener("scroll", onScroll, {passive:true});
  })();

  /* motion v2.2 — reading progress · back-to-top · hero scroll cue */
  (function(){
    var bar = $("#progress"), top = $("#toTop"), cue = $(".scroll-cue");
    if(!bar && !top && !cue) return;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var ticking = false;
    function paint(){
      ticking = false;
      var y = window.scrollY || window.pageYOffset || 0;
      var max = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
      if(bar) bar.style.transform = "scaleX(" + Math.min(y / max, 1).toFixed(4) + ")";
      if(top) top.classList.toggle("show", y > window.innerHeight * .6);
      if(cue) cue.classList.toggle("off", y > 80);
    }
    function queue(){ if(ticking) return; ticking = true; requestAnimationFrame(paint); }
    window.addEventListener("scroll", queue, {passive:true});
    window.addEventListener("resize", paint, {passive:true});
    paint();
    if(top){
      top.addEventListener("click", function(){
        if(reduce || !("scrollTo" in window) || !window.scrollTo.length){ window.scrollTo(0, 0); return; }
        window.scrollTo({top:0, behavior:"smooth"});
      });
    }
  })();

  /* v2.5 — touch dropdown toggle (hover:none devices) + WhatsApp form send */
  (function(){
    var noHover = window.matchMedia && window.matchMedia("(hover: none)").matches;
    if(noHover){
      $$(".has-drop > a.nl").forEach(function(a){
        a.addEventListener("click", function(e){
          var li = a.parentElement;
          if(!li.classList.contains("open")){ e.preventDefault(); li.classList.add("open"); }
        });
      });
      document.addEventListener("click", function(e){
        $$(".has-drop.open").forEach(function(li){
          if(!li.contains(e.target)) li.classList.remove("open");
        });
      });
    }
  })();

  /* v3.0 — home services filter
     يتحكم في ظهور مجموعات الخدمات فقط (.svc-group[data-group]) ولا يمس أي قسم آخر.
     عند إظهار مجموعة نُجبر .reveal داخلها على الحالة الظاهرة، لأن عنصرًا داخل
     مجموعة مخفية لا يمرّ عليه IntersectionObserver فيبقى شفافًا للأبد. */
  (function(){
    var filters = $$(".filters .filter");
    var groups = $$(".svc-group[data-group]");
    if(!filters.length || !groups.length) return;
    function apply(f){
      groups.forEach(function(g){
        var on = (f === "all" || g.getAttribute("data-group") === f);
        g.hidden = !on;
        if(on) $$(".reveal", g).forEach(function(el){ el.classList.add("in"); });
      });
    }
    filters.forEach(function(btn){
      btn.setAttribute("aria-pressed", btn.classList.contains("active") ? "true" : "false");
      btn.addEventListener("click", function(){
        var f = btn.getAttribute("data-filter") || "all";
        filters.forEach(function(b){
          var on = (b === btn);
          b.classList.toggle("active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        apply(f);
      });
    });
  })();
})();
