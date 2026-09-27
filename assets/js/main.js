/* EL MASRIA — shared behaviour (no framework, minimal JS) */
(function(){
  "use strict";
  var $ = function(s,c){ return (c||document).querySelector(s); };
  var $$ = function(s,c){ return Array.prototype.slice.call((c||document).querySelectorAll(s)); };

  /* sticky header shadow */
  var head = $("#siteHead");
  var onScroll = function(){ if(head) head.classList.toggle("scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, {passive:true}); onScroll();

  /* mobile drawer */
  var burger = $("#burger"), drawer = $("#drawer");
  if(burger && drawer){
    burger.addEventListener("click", function(){ drawer.classList.add("open"); document.body.style.overflow="hidden"; });
    drawer.addEventListener("click", function(e){
      if(e.target.closest("[data-close]") || e.target.classList.contains("scrim")){
        drawer.classList.remove("open"); document.body.style.overflow="";
      }
    });
    document.addEventListener("keydown", function(e){
      if(e.key === "Escape"){ drawer.classList.remove("open"); document.body.style.overflow=""; }
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
      var subject = encodeURIComponent("طلب تواصل من الموقع — " + v("cf-service"));
      var body = encodeURIComponent("الاسم: "+v("cf-name")+"\nالشركة: "+v("cf-company")+"\nالهاتف: "+v("cf-phone")+"\nالخدمة: "+v("cf-service")+"\n\nالرسالة:\n"+v("cf-msg"));
      window.location.href = "mailto:info@elmasria-eg.com?subject="+subject+"&body="+body;
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
})();
