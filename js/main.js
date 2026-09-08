/* ═══════════════════════════════════════════════════════════
   Raster — Home page interactions
   Parallax orbs · dropdowns · reveals
   ═══════════════════════════════════════════════════════════ */
(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(pointer: fine)");
  const desktop = window.matchMedia("(min-width: 1024px)");
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, min, max) => Math.min(max, Math.max(min, v));

  /* ── Header: scrolled state ── */
  const header = document.getElementById("siteHeader");
  let lastScrollY = -1;

  function onScroll() {
    const y = window.scrollY;
    if (y === lastScrollY) return;
    lastScrollY = y;
    header.classList.toggle("scrolled", y > 24);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ── Mobile menu ── */
  const menuToggle = document.getElementById("menuToggle");
  const mobileMenu = document.getElementById("mobileMenu");

  function setMenu(open) {
    document.body.classList.toggle("menu-open", open);
    menuToggle.setAttribute("aria-expanded", String(open));
    menuToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    if (open) {
      mobileMenu.hidden = false;
      requestAnimationFrame(() => mobileMenu.classList.add("open"));
      document.body.style.overflow = "hidden";
    } else {
      mobileMenu.classList.remove("open");
      document.body.style.overflow = "";
      setTimeout(() => { if (!document.body.classList.contains("menu-open")) mobileMenu.hidden = true; }, 320);
    }
  }
  menuToggle.addEventListener("click", () => setMenu(!document.body.classList.contains("menu-open")));
  mobileMenu.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
  desktop.addEventListener("change", (e) => { if (e.matches) setMenu(false); });

  /* ── Orb dropdowns ── */
  // only orbs that own a dropdown panel toggle; a plain-link orb just navigates
  const orbs = Array.from(document.querySelectorAll(".orb")).filter((o) => o.querySelector(".orb-panel"));

  function closeOrb(orb) {
    orb.classList.remove("open");
    orb.querySelector(".orb-btn").setAttribute("aria-expanded", "false");
  }
  function openOrb(orb) {
    orbs.forEach((o) => { if (o !== orb) closeOrb(o); });
    orb.classList.add("open");
    orb.querySelector(".orb-btn").setAttribute("aria-expanded", "true");
  }
  orbs.forEach((orb) => {
    const btn = orb.querySelector(".orb-btn");
    btn.addEventListener("click", () => {
      orb.classList.contains("open") ? closeOrb(orb) : openOrb(orb);
    });
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".orb")) orbs.forEach(closeOrb);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (document.body.classList.contains("menu-open")) { setMenu(false); menuToggle.focus(); return; }
    const open = orbs.find((o) => o.classList.contains("open"));
    if (open) { closeOrb(open); open.querySelector(".orb-btn").focus(); }
  });

  /* ── Carousels ──
     Scroll-snap does the moving; this only wires the buttons, keeps their
     disabled state in sync with the scroll position, and optionally
     auto-advances. Any number of carousels can coexist on a page. */
  document.querySelectorAll("[data-carousel]").forEach((root) => {
    const track = root.querySelector(".carousel-track");
    const prev = root.querySelector(".carousel-btn.prev");
    const next = root.querySelector(".carousel-btn.next");
    if (!track) return;

    const step = () => {
      const first = track.firstElementChild;
      if (!first) return track.clientWidth;
      const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      return first.getBoundingClientRect().width + gap;
    };
    const atStart = () => track.scrollLeft <= 1;
    // scrollWidth-clientWidth can land a fraction short of scrollLeft
    const atEnd = () => track.scrollLeft >= track.scrollWidth - track.clientWidth - 2;

    function sync() {
      if (prev) prev.disabled = atStart();
      if (next) next.disabled = atEnd();
    }
    function move(dir) {
      track.scrollBy({
        left: dir * step(),
        behavior: reduceMotion.matches ? "auto" : "smooth",
      });
    }
    prev?.addEventListener("click", () => move(-1));
    next?.addEventListener("click", () => move(1));
    track.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync, { passive: true });
    sync();

    // the track scrolls, so expose it as a labelled, focusable region
    track.tabIndex = 0;
    track.setAttribute("role", "group");

    const delay = parseInt(root.dataset.carouselAutoplay, 10);
    if (Number.isFinite(delay) && delay > 0) {
      let timer = null;
      // every condition that should hold autoplay, resolved in one place so a
      // resume can never override a still-active one (e.g. tab regains focus
      // while the pointer is parked on the carousel)
      const held = { hovered: false, offScreen: false };
      const shouldRun = () => !reduceMotion.matches && !document.hidden && !held.hovered && !held.offScreen;
      const tick = () => {
        if (atEnd()) track.scrollTo({ left: 0, behavior: "smooth" });
        else move(1);
      };
      const update = () => {
        if (shouldRun()) { if (!timer) timer = setInterval(tick, delay); }
        else if (timer) { clearInterval(timer); timer = null; }
      };
      const setHeld = (key, value) => { held[key] = value; update(); };

      // never animate under a viewer's own hover, focus or keyboard use
      ["pointerenter", "focusin", "touchstart"].forEach((e) =>
        root.addEventListener(e, () => setHeld("hovered", true), { passive: true }));
      ["pointerleave", "focusout"].forEach((e) =>
        root.addEventListener(e, () => setHeld("hovered", false)));
      document.addEventListener("visibilitychange", update);
      reduceMotion.addEventListener("change", update);

      // idle while scrolled past, so a viewer always arrives at the first slide
      // rather than wherever it drifted to while off-screen
      if ("IntersectionObserver" in window) {
        new IntersectionObserver(
          ([entry]) => setHeld("offScreen", !entry.isIntersecting),
          { threshold: 0 }
        ).observe(root);
      }
      update();
    }
  });

  /* ── Contact form ──
     Validates client-side, then POSTs to whatever `data-endpoint` names. There
     is no backend in this repo (serve.mjs is GET-only), so with the attribute
     empty it tells the visitor to email or call instead — it must never claim
     an enquiry was sent when nothing received it. Set data-endpoint on the
     form to the real handler and the fetch path takes over. */
  const MAX_UPLOAD = 5 * 1024 * 1024;   // 5 MB, matches the hint in the markup

  document.querySelectorAll("[data-form]").forEach((form) => {
    const status = form.querySelector(".form-status");
    const submit = form.querySelector("[type='submit']");
    const fields = Array.from(form.querySelectorAll(".field"));
    const control = (field) => field.querySelector("input, textarea, select");

    function setStatus(kind, message) {
      status.className = "form-status show " + kind;
      status.textContent = message;
    }
    function validate(field) {
      const input = control(field);
      if (!input) return true;
      const slot = field.querySelector(".err");
      let message = "";
      if (input.type === "file") {
        const file = input.files && input.files[0];
        if (!file) message = "Attach your CV.";
        else if (!/\.(pdf|docx?)$/i.test(file.name)) message = "Use a PDF or Word document.";
        else if (file.size > MAX_UPLOAD) message = "That file is over 5 MB — please attach a smaller one.";
      } else {
        const value = input.value.trim();
        if (!value) message = !input.required ? "" : input.tagName === "SELECT" ? "Choose an option." : "This field is required.";
        else if (input.type === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value)) message = "Enter a valid email address.";
        else if (/mobile|phone/.test(input.name) && value.replace(/\D/g, "").length < 8) message = "Enter a valid phone number.";
      }
      field.classList.toggle("invalid", Boolean(message));
      input.setAttribute("aria-invalid", message ? "true" : "false");
      if (slot) slot.textContent = message;
      return !message;
    }
    fields.forEach((field) => {
      const input = control(field);
      if (!input) return;
      input.addEventListener("blur", () => validate(field));
      // clear an error as soon as the visitor starts fixing it, never mid-typing
      const live = input.type === "file" || input.tagName === "SELECT" ? "change" : "input";
      input.addEventListener(live, () => { if (field.classList.contains("invalid")) validate(field); });
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const results = fields.map(validate);
      if (results.includes(false)) {
        setStatus("info", "Please correct the highlighted fields.");
        fields.find((f) => f.classList.contains("invalid"))?.querySelector("input, textarea, select")?.focus();
        return;
      }
      const endpoint = form.dataset.endpoint;
      // No handler wired up: say so. Never claim a submission that nothing received.
      if (!endpoint) { setStatus("info", form.dataset.fallback || "This form is not connected yet."); return; }
      submit.disabled = true;
      setStatus("info", "Sending…");
      try {
        const res = await fetch(endpoint, { method: "POST", body: new FormData(form) });
        if (!res.ok) throw new Error(String(res.status));
        form.reset();
        fields.forEach((f) => f.classList.remove("invalid"));
        setStatus("ok", form.dataset.success || "Thank you — that has been sent. We will be in touch shortly.");
      } catch {
        setStatus("info", form.dataset.fallback || "Sorry, that did not go through.");
      } finally {
        submit.disabled = false;
      }
    });
  });

  /* ── Demo request dialog ──
     Any [data-demo-open] control opens the shared <dialog>; a control may
     carry data-demo-solution="<slug>" to preselect the solution. The native
     dialog handles Escape, the focus trap and inertness; this only manages
     the body scroll lock, backdrop clicks and returning focus to the opener.
     Without dialog support the header link still goes to the contact page. */
  const demo = document.getElementById("demoDialog");
  if (demo && typeof demo.showModal === "function") {
    const solution = demo.querySelector('select[name="solution"]');
    let opener = null;
    document.querySelectorAll("[data-demo-open]").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        opener = el;
        if (solution && el.dataset.demoSolution) solution.value = el.dataset.demoSolution;
        demo.showModal();
        document.body.classList.add("dialog-open");
        demo.querySelector("input:not([type=hidden])")?.focus();
      });
    });
    demo.querySelectorAll("[data-demo-close]").forEach((b) => b.addEventListener("click", () => demo.close()));
    demo.addEventListener("click", (e) => { if (e.target === demo) demo.close(); });   // backdrop
    // explicit Escape: newer Chromes may withhold the native cancel event
    // without a user-activation, which left the dialog stuck open
    demo.addEventListener("keydown", (e) => { if (e.key === "Escape") { e.preventDefault(); demo.close(); } });
    // remember how the dialog was dismissed: keyboard users get their focus
    // back on the opener (with its ring); pointer users get no ring at all
    let closedByKey = false;
    demo.addEventListener("keydown", (e) => { if (e.key === "Escape" || e.key === "Enter") closedByKey = true; });
    demo.addEventListener("pointerdown", () => { closedByKey = false; });
    demo.addEventListener("close", () => {
      document.body.classList.remove("dialog-open");
      if (!opener) return;
      opener.focus({ preventScroll: true });
      if (!closedByKey) opener.blur();
      closedByKey = false;
    });
  }

  /* ── Mega dropdown ──
     Opening is pure CSS (:hover / :focus-within), so this only handles Escape:
     blurring whatever is focused inside collapses :focus-within, and focus goes
     back to the nav item rather than being dropped at the top of the document. */
  const mega = document.querySelector(".has-mega");
  if (mega) {
    const trigger = mega.querySelector(":scope > a");
    const undismiss = () => mega.classList.remove("mega-dismissed");

    mega.addEventListener("keydown", (e) => {
      if (e.key !== "Escape" || mega.classList.contains("mega-dismissed")) return;
      e.stopPropagation();                    // don't also close the mobile menu
      // Returning focus to the trigger would keep :focus-within true and hold
      // the panel open, so an explicit dismissed class has to override the CSS.
      mega.classList.add("mega-dismissed");
      trigger?.focus();
    });
    // re-arm once focus leaves the item entirely, or on a fresh mouse-in
    mega.addEventListener("focusout", (e) => {
      if (!mega.contains(e.relatedTarget)) undismiss();
    });
    mega.addEventListener("pointerenter", undismiss);
  }

  /* ── Solution-page side menu ──
     A <details> that stays open beside the content on wide screens (its
     summary is hidden there) and collapses to a toggle below 1024px, tracking
     resizes so a rotated tablet never ends up with the list hidden. */
  const sideNav = document.querySelector("details.side-nav");
  if (sideNav) {
    const wide = window.matchMedia("(min-width: 1024px)");
    // the rail is sticky only while it fits under the header; taller than
    // the viewport it flows with the page instead of becoming a scroll box
    const fits = () => sideNav.classList.toggle("is-flow", sideNav.offsetHeight + 140 > window.innerHeight);   // 128px sticky top + 12px breathing room
    const sync = () => { sideNav.open = wide.matches; fits(); };
    sync();
    wide.addEventListener("change", sync);
    window.addEventListener("resize", fits, { passive: true });
  }

  /* ── Table filter ──
     [data-filter] wraps a search input, a [data-filter-count] label and a
     table; rows that don't contain the typed text are hidden. Plain substring
     match across the whole row, which is all a make/model list needs. */
  document.querySelectorAll("[data-filter]").forEach((root) => {
    const input = root.querySelector("input");
    const count = root.querySelector("[data-filter-count]");
    const rows = Array.from(root.querySelectorAll("tbody tr"));
    if (!input || !rows.length) return;
    const update = () => {
      const q = input.value.trim().toLowerCase();
      let shown = 0;
      rows.forEach((row) => {
        const on = !q || row.textContent.toLowerCase().includes(q);
        row.hidden = !on;
        if (on) shown++;
      });
      if (count) count.textContent = q ? `${shown} of ${rows.length} instruments` : `${rows.length} instruments`;
    };
    input.addEventListener("input", update);
    update();
  });

  /* ── Tabs ──
     Follows the ARIA tabs pattern: only the selected tab is in the tab order,
     arrows/Home/End move between them, and each panel is toggled with [hidden].
     Deliberately no [data-reveal] inside a panel — an IntersectionObserver
     never fires on a display:none element, so a hidden panel's contents would
     stay stuck at opacity 0 when its tab was finally selected. */
  document.querySelectorAll("[data-tabs]").forEach((root) => {
    const tabs = Array.from(root.querySelectorAll("[role='tab']"));
    if (!tabs.length) return;
    const panels = tabs.map((t) => document.getElementById(t.getAttribute("aria-controls")));

    function select(index, moveFocus) {
      tabs.forEach((tab, i) => {
        const on = i === index;
        tab.setAttribute("aria-selected", on ? "true" : "false");
        tab.tabIndex = on ? 0 : -1;
        if (panels[i]) panels[i].hidden = !on;
      });
      if (moveFocus) tabs[index].focus();
    }

    tabs.forEach((tab, i) => tab.addEventListener("click", () => select(i, false)));
    root.addEventListener("keydown", (e) => {
      const current = tabs.indexOf(document.activeElement);
      if (current < 0) return;
      let next = null;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") next = (current + 1) % tabs.length;
      else if (e.key === "ArrowLeft" || e.key === "ArrowUp") next = (current - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = tabs.length - 1;
      if (next === null) return;
      e.preventDefault();
      select(next, true);
    });

    const initial = tabs.findIndex((t) => t.getAttribute("aria-selected") === "true");
    select(initial < 0 ? 0 : initial, false);
  });

  /* ── Gallery lightbox ──
     Reads whatever .gallery-item buttons are on the page, so adding photos to
     an article is markup-only. Each item carries data-full (the large source)
     and data-caption. */
  const gallery = document.querySelector("[data-gallery]");
  const lightbox = document.getElementById("lightbox");
  if (gallery && lightbox) {
    const items = Array.from(gallery.querySelectorAll(".gallery-item"));
    const lbImg = lightbox.querySelector("img");
    const lbCap = lightbox.querySelector(".lightbox-cap");
    const btnPrev = lightbox.querySelector(".lightbox-prev");
    const btnNext = lightbox.querySelector(".lightbox-next");
    const btnClose = lightbox.querySelector(".lightbox-close");
    let index = 0;
    let opener = null;

    // a single photo needs no paging arrows
    const single = items.length < 2;
    btnPrev.hidden = single;
    btnNext.hidden = single;

    function show(i) {
      index = (i + items.length) % items.length;
      const item = items[index];
      const thumb = item.querySelector("img");
      lbImg.src = item.dataset.full || thumb.src;
      lbImg.alt = thumb.alt || "";
      lbCap.innerHTML = (item.dataset.caption || thumb.alt || "") +
        (single ? "" : ` <b>${index + 1}/${items.length}</b>`);
    }
    function open(i, trigger) {
      opener = trigger;
      show(i);
      lightbox.hidden = false;
      document.body.style.overflow = "hidden";
      btnClose.focus();
    }
    function close() {
      lightbox.hidden = true;
      document.body.style.overflow = "";
      opener?.focus();           // return focus where the viewer left it
    }
    items.forEach((item, i) => item.addEventListener("click", () => open(i, item)));
    btnClose.addEventListener("click", close);
    btnPrev.addEventListener("click", () => show(index - 1));
    btnNext.addEventListener("click", () => show(index + 1));
    // click the backdrop, but not the figure itself
    lightbox.addEventListener("click", (e) => { if (e.target === lightbox) close(); });

    document.addEventListener("keydown", (e) => {
      if (lightbox.hidden) return;
      if (e.key === "Escape") { close(); return; }
      if (single) return;
      if (e.key === "ArrowLeft") { e.preventDefault(); show(index - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); show(index + 1); }
    });
    // keep Tab inside the dialog while it is open
    lightbox.addEventListener("keydown", (e) => {
      if (e.key !== "Tab") return;
      const focusable = [btnClose, btnPrev, btnNext].filter((b) => b && !b.hidden);
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  /* ── Reveal on scroll ── */
  const revealEls = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window && !reduceMotion.matches) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          io.unobserve(entry.target);
        }
      });
      // threshold stays 0: an area-based threshold silently never fires for a
      // container taller than the viewport (a 16-card grid stacked on mobile
      // can't ever show 18% of itself), leaving the section invisible forever.
      // The negative bottom margin is what delays the reveal instead.
    }, { threshold: 0, rootMargin: "0px 0px -10% 0px" });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("in-view"));
  }

  /* ── Stat counters ── */
  const counters = document.querySelectorAll("[data-count]");
  function runCounter(el) {
    const target = parseInt(el.dataset.count, 10);
    if (reduceMotion.matches || !Number.isFinite(target)) { el.textContent = target; return; }
    const dur = 900;
    const t0 = performance.now();
    (function tick(now) {
      const p = clamp((now - t0) / dur, 0, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    })(t0);
  }
  if ("IntersectionObserver" in window) {
    const cio = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { runCounter(entry.target); cio.unobserve(entry.target); }
      });
    }, { threshold: 0.6 });
    counters.forEach((el) => cio.observe(el));
  } else {
    counters.forEach(runCounter);
  }

  /* ═══════════ Parallax engine (floating buttons + cursor glow) ═══════════ */
  const parallaxEls = Array.from(document.querySelectorAll(".orb[data-depth], .tag-chip[data-depth], .hero-video[data-depth]"));
  const cursorGlow = document.getElementById("cursorGlow");

  // backdrop video: negative depth in the engine drifts it opposite the
  // buttons; honour reduced motion by not playing at all
  const heroVideo = document.querySelector(".hero-video");
  if (heroVideo) {
    if (reduceMotion.matches) heroVideo.pause();
    reduceMotion.addEventListener("change", (e) => {
      if (e.matches) heroVideo.pause();
      else heroVideo.play().catch(() => {});
    });
  }

  const state = {
    mx: 0, my: 0,           // normalized cursor from viewport centre (-1..1)
    cx: 0, cy: 0,           // lerped
    glowX: -600, glowY: -600, glowCX: -600, glowCY: -600,
    running: false,
  };

  function frame() {
    if (!state.running) return;

    // lerp cursor
    state.cx = lerp(state.cx, state.mx, 0.065);
    state.cy = lerp(state.cy, state.my, 0.065);

    // orbs / chips by depth
    for (const el of parallaxEls) {
      const d = parseFloat(el.dataset.depth) || 16;
      el.style.translate = `${state.cx * d}px ${state.cy * d * 0.72}px`;
    }

    // cursor glow
    state.glowCX = lerp(state.glowCX, state.glowX, 0.14);
    state.glowCY = lerp(state.glowCY, state.glowY, 0.14);
    cursorGlow.style.transform = `translate(${state.glowCX.toFixed(1)}px, ${state.glowCY.toFixed(1)}px)`;

    requestAnimationFrame(frame);
  }

  function onPointerMove(e) {
    state.mx = clamp((e.clientX / window.innerWidth) * 2 - 1, -1, 1);
    state.my = clamp((e.clientY / window.innerHeight) * 2 - 1, -1, 1);
    state.glowX = e.clientX;
    state.glowY = e.clientY;
  }

  function startEngine() {
    if (state.running || reduceMotion.matches) return;
    if (!(finePointer.matches && desktop.matches)) return;
    state.running = true;
    document.body.classList.add("has-pointer");
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    requestAnimationFrame(frame);
  }

  function stopEngine() {
    state.running = false;
    document.body.classList.remove("has-pointer");
    window.removeEventListener("pointermove", onPointerMove);
    parallaxEls.forEach((el) => { el.style.translate = ""; });
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) { state.running = false; }
    else { startEngine(); }
  });
  reduceMotion.addEventListener("change", (e) => (e.matches ? stopEngine() : startEngine()));
  startEngine();

  /* ═══════════ Figure head tracking (pose-loop scrubbing) ═══════════
     192 frames from Animate_human_muscle_fiber_head_202609042214.mp4
     (8s/24fps). Unlike earlier sources this one sweeps each side TWICE, so
     the right sector has real footage rather than a ¾ approximation:
       front → LEFT profile (p18-24) → up-left → UP (p48) → up-right
       → RIGHT profile (p72-80) → front (p88) → LEFT (p96-104)
       → RIGHT (p112-120) → DOWN-RIGHT (p126-130) → DOWN (p136-142)
       → down-left (p150-158) → LEFT (p162-176) → front (p191).
     POSES[i] holds frame p{i}.webp's gaze (x: -1 left … +1 right, y: -1 up
     … +1 down), interpolated between landmarks read off 430px head crops —
     the only reliable way to call turn direction here. The clip makes just
     ONE down-right pass (p122-p134); once the chin drops at p136-p142 the
     head turns left and never comes back, so p150+ is down-LEFT and the
     deepest down-right pose on offer is (0.6, 0.45) at p128. The cursor anywhere in the
     viewport maps to a target gaze; each tick picks the loop frame nearest
     that gaze and steps toward it ALONG the loop, so adjacent repaints are
     adjacent source frames and every direction moves the way the footage
     does. Because both sides are covered twice, most targets are now a
     short roll away.
     One exception remains: when the shorter loop path is still a big detour
     in pose space relative to the direct pose distance, the head snaps to
     the target frame — a quick correct-direction turn instead of a wrong-way
     roll. Idle returns always roll the loop.
     Exactly one opaque drawImage per repaint; frames are never blended. */
  const headCanvas = document.getElementById("headCanvas");
  const figWrap = document.getElementById("figureWrap");
  if (headCanvas && figWrap) {
    const ctx = headCanvas.getContext("2d");
    const BASE = "assets/img/head/";
    const POSES = [[0,0],[-0.056,0],[-0.111,0],[-0.167,0],[-0.222,0],[-0.278,0],[-0.333,0],[-0.389,0],[-0.444,0],[-0.5,0],[-0.556,0],[-0.611,0],[-0.667,0],[-0.722,0],[-0.778,0],[-0.833,0],[-0.889,0],[-0.944,0],[-1,0],[-1,0],[-1,0],[-1,0],[-1,0],[-1,0],[-1,0],[-0.968,-0.045],[-0.935,-0.09],[-0.902,-0.135],[-0.87,-0.18],[-0.838,-0.225],[-0.805,-0.27],[-0.772,-0.315],[-0.74,-0.36],[-0.708,-0.405],[-0.675,-0.45],[-0.642,-0.495],[-0.61,-0.54],[-0.577,-0.585],[-0.545,-0.63],[-0.512,-0.675],[-0.48,-0.72],[-0.448,-0.765],[-0.415,-0.81],[-0.383,-0.855],[-0.35,-0.9],[-0.262,-0.925],[-0.175,-0.95],[-0.088,-0.975],[0,-1],[0.031,-0.994],[0.062,-0.988],[0.094,-0.981],[0.125,-0.975],[0.156,-0.969],[0.188,-0.962],[0.219,-0.956],[0.25,-0.95],[0.297,-0.891],[0.344,-0.831],[0.391,-0.772],[0.438,-0.712],[0.484,-0.653],[0.531,-0.594],[0.578,-0.534],[0.625,-0.475],[0.672,-0.416],[0.719,-0.356],[0.766,-0.297],[0.812,-0.238],[0.859,-0.178],[0.906,-0.119],[0.953,-0.059],[1,0],[1,0],[1,0],[1,0],[1,0],[1,0],[1,0],[1,0],[1,0],[0.875,0],[0.75,0],[0.625,0],[0.5,0],[0.375,0],[0.25,0],[0.125,0],[0,0],[-0.125,0],[-0.25,0],[-0.375,0],[-0.5,0],[-0.625,0],[-0.75,0],[-0.875,0],[-1,0],[-1,0],[-1,0],[-1,0],[-1,0],[-1,0],[-1,0],[-1,0],[-1,0],[-0.75,0],[-0.5,0],[-0.25,0],[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.019],[1,0.037],[1,0.056],[1,0.075],[1,0.094],[1,0.112],[1,0.131],[1,0.15],[0.95,0.188],[0.9,0.225],[0.85,0.263],[0.8,0.3],[0.75,0.338],[0.7,0.375],[0.65,0.413],[0.6,0.45],[0.537,0.5],[0.475,0.55],[0.412,0.6],[0.35,0.65],[0.287,0.7],[0.225,0.75],[0.162,0.8],[0.1,0.85],[0.083,0.875],[0.067,0.9],[0.05,0.925],[0.033,0.95],[0.017,0.975],[0,1],[-0.045,0.985],[-0.09,0.97],[-0.135,0.955],[-0.18,0.94],[-0.225,0.925],[-0.27,0.91],[-0.315,0.895],[-0.36,0.88],[-0.405,0.865],[-0.45,0.85],[-0.504,0.784],[-0.557,0.718],[-0.611,0.651],[-0.665,0.585],[-0.719,0.519],[-0.772,0.452],[-0.826,0.386],[-0.88,0.32],[-0.895,0.292],[-0.91,0.265],[-0.925,0.237],[-0.94,0.21],[-0.955,0.182],[-0.97,0.155],[-0.985,0.128],[-1,0.1],[-0.988,0.088],[-0.975,0.075],[-0.963,0.062],[-0.95,0.05],[-0.938,0.038],[-0.925,0.025],[-0.912,0.012],[-0.9,0],[-0.825,0],[-0.75,0],[-0.675,0],[-0.6,0],[-0.525,0],[-0.45,0],[-0.375,0],[-0.3,0],[-0.257,0],[-0.214,0],[-0.171,0],[-0.129,0],[-0.086,0],[-0.043,0],[0,0]];
    const N = POSES.length;
    const imgs = new Array(N).fill(null);

    // pose-space length of each loop segment i -> i+1, and running total,
    // so travel cost is measured in how far the HEAD moves, not frame count
    const poseDist = (a, b) => Math.hypot(POSES[a][0] - POSES[b][0], POSES[a][1] - POSES[b][1]);
    const CUM = [0];
    for (let i = 0; i < N; i++) CUM.push(CUM[i] + poseDist(i, (i + 1) % N));
    const LOOP_LEN = CUM[N];
    // arc length at a FLOAT loop position — direction decisions must use the
    // same float position as the step size, or the two disagree right at the
    // target and the head lunges into an endless catch-up loop
    const cumAt = (p) => {
      const i = Math.floor(p);
      return CUM[i] + (CUM[i + 1] - CUM[i]) * (p - i);
    };

    const track = {
      tx: 0, ty: 0,       // target gaze (-1..1)
      cur: 0,             // float position along the loop
      lastMove: -1e9,
      lastImg: null,
      rect: null,
      ticks: 0,
      active: false,
      frontReady: false,
    };

    function loadImage(src) {
      return new Promise((resolve) => {
        const im = new Image();
        im.onload = () => resolve(im);
        im.onerror = () => resolve(null);
        im.src = src;
      });
    }

    let framesRequested = false;
    function ensureFrames() {
      if (framesRequested) return;
      framesRequested = true;
      loadFrames();
    }

    async function loadFrames() {
      imgs[0] = await loadImage(BASE + "p0.webp");
      track.frontReady = !!imgs[0];
      if (track.frontReady) {
        drawFrame(0);
        headCanvas.classList.add("ready");
        figWrap.classList.add("canvas-ready");   // poster hands off to the canvas
      }
      // coarse loop first, then fill in — early movement works at low pose
      // resolution and sharpens as the gaps land
      const order = [];
      const seen = new Set([0]);
      for (const stride of [24, 12, 6, 3, 1])
        for (let i = 0; i < N; i += stride)
          if (!seen.has(i)) { seen.add(i); order.push(i); }
      for (let i = 0; i < order.length; i += 6) {
        await Promise.all(order.slice(i, i + 6).map(
          (idx) => loadImage(`${BASE}p${idx}.webp`).then((im) => { imgs[idx] = im; })
        ));
      }
    }

    // shortest signed distance around the loop (in frames)
    function loopDelta(from, to) {
      let d = (((to - from) % N) + N) % N;
      if (d > N / 2) d -= N;
      return d;
    }

    // loop index whose pose best matches the target gaze; a mild penalty on
    // loop distance picks the nearer copy when two frames share a pose
    // (the left spoke appears both outbound and on the return leg)
    function targetIndex(gx, gy) {
      let best = 0, bestScore = Infinity;
      for (let i = 0; i < N; i++) {
        const dx = POSES[i][0] - gx, dy = POSES[i][1] - gy;
        const ld = loopDelta(track.cur, i) / N;
        const score = dx * dx + dy * dy + ld * ld * 0.35;
        if (score < bestScore) { bestScore = score; best = i; }
      }
      return best;
    }

    function drawFrame(idx) {
      let im = imgs[idx];
      for (let off = 1; !im && off <= N / 2; off++)   // nearest loaded stand-in
        im = imgs[(idx + off) % N] || imgs[(idx - off + N) % N];
      if (!im || im === track.lastImg) return;
      track.lastImg = im;
      ctx.clearRect(0, 0, headCanvas.width, headCanvas.height);
      ctx.drawImage(im, 0, 0);
    }

    function cacheFigRect() { track.rect = figWrap.getBoundingClientRect(); return track.rect; }

    function onMove(e) {
      const r = track.rect || cacheFigRect();
      const hx = r.left + r.width / 2;              // head anchor: centred, ~16% down
      const hy = r.top + r.height * 0.16;
      const dx = e.clientX - hx, dy = e.clientY - hy;
      // normalize per side so full deflection lands at the display edge in
      // every direction, wherever the head sits on screen
      const sx = (dx < 0 ? hx : window.innerWidth - hx) * 0.92;
      const sy = (dy < 0 ? hy : window.innerHeight - hy) * 0.92;
      track.tx = clamp(dx / Math.max(sx, 1), -1, 1);
      track.ty = clamp(dy / Math.max(sy, 1), -1, 1);
      track.lastMove = performance.now();
    }

    function tick(now) {
      if (!track.active) return;
      if (++track.ticks % 32 === 0) cacheFigRect();
      const idle = now - track.lastMove > 3500;      // ease home when idle
      const target = targetIndex(idle ? 0 : track.tx, idle ? 0 : track.ty);
      const stepsFwd = (((target - track.cur) % N) + N) % N;          // float, 0..N
      const arcF = (CUM[target] - cumAt(track.cur) + LOOP_LEN) % LOOP_LEN;
      const arcB = LOOP_LEN - arcF;
      const direct = poseDist(Math.round(track.cur) % N, target);
      if (!idle && Math.min(arcF, arcB) > Math.max(1.15, 2.6 * direct)) {
        // no usable footage between here and there — snap the short way
        track.cur = target;
      } else {
        // inside a zero-length (duplicate-pose) segment the arcs can't pick a
        // side — fall back to the shorter step count
        const d = Math.min(arcF, arcB) < 1e-6
          ? (stepsFwd <= N - stepsFwd ? stepsFwd : stepsFwd - N)
          : (arcF <= arcB ? stepsFwd : stepsFwd - N);
        track.cur = (track.cur + clamp(d * 0.12, -1.3, 1.3) + N) % N;
      }
      drawFrame(Math.round(track.cur) % N);   // no-ops unless the frame changed
      requestAnimationFrame(tick);
    }

    function startTracker() {
      if (track.active || reduceMotion.matches) return;
      if (!(finePointer.matches && desktop.matches)) return;
      ensureFrames();                       // pose frames only load where the tracker can run
      track.active = true;
      cacheFigRect();
      window.addEventListener("pointermove", onMove, { passive: true });
      requestAnimationFrame(tick);
    }

    function stopTracker() {
      track.active = false;
      window.removeEventListener("pointermove", onMove);
      track.tx = track.ty = 0;
      track.cur = 0;
      track.lastImg = null;
      drawFrame(0);
    }

    document.addEventListener("pointerleave", () => { track.tx = 0; track.ty = 0; });
    window.addEventListener("resize", cacheFigRect);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) { track.active = false; }
      else { startTracker(); }
    });
    reduceMotion.addEventListener("change", (e) => (e.matches ? stopTracker() : startTracker()));
    desktop.addEventListener("change", (e) => { if (e.matches) startTracker(); });

    startTracker();
  }
})();
