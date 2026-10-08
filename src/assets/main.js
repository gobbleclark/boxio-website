/* Boxio — site interactions */

/*
 * FORM DELIVERY
 * Set FORM_ENDPOINT to a form backend URL (Formspree, Basin, HubSpot, Zapier webhook,
 * or your own API). Submissions are POSTed as JSON.
 * While it's empty, forms fall back to opening the visitor's email app addressed to FORM_EMAIL.
 */
const FORM_ENDPOINT = "";
const FORM_EMAIL = "hello@boxioship.com";

document.documentElement.classList.remove("no-js");
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---------- Header: scrolled state, mobile menu, dropdowns ---------- */
const header = $(".site-header");
const fab = $(".fab");
const onScroll = () => {
  const y = window.scrollY;
  header && header.classList.toggle("scrolled", y > 8);
  fab && fab.classList.toggle("show", y > 600);
};
window.addEventListener("scroll", onScroll, { passive: true });
onScroll();

const toggle = $(".menu-toggle");
toggle && toggle.addEventListener("click", () => {
  const open = header.classList.toggle("menu-open");
  toggle.setAttribute("aria-expanded", open);
});
$$(".dd > button").forEach((btn) => {
  btn.addEventListener("click", () => {
    const dd = btn.parentElement;
    const open = dd.classList.toggle("open");
    btn.setAttribute("aria-expanded", open);
  });
});
document.addEventListener("click", (e) => {
  $$(".dd.open").forEach((dd) => { if (!dd.contains(e.target)) { dd.classList.remove("open"); $("button", dd).setAttribute("aria-expanded", "false"); } });
});

/* ---------- Reveal on scroll + counters ---------- */
function countUp(el) {
  const target = parseFloat(el.dataset.count);
  const decimals = parseInt(el.dataset.decimals || "0", 10);
  const suffix = el.dataset.suffix || "";
  const prefix = el.dataset.prefix || "";
  const render = (v) => { el.textContent = prefix + v.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix; };
  if (reduceMotion) return render(target);
  const start = parseFloat(el.dataset.from || "0");
  const dur = 1600;
  const t0 = performance.now();
  const tick = (t) => {
    const p = Math.min(1, (t - t0) / dur);
    const eased = 1 - Math.pow(1 - p, 4);
    render(start + (target - start) * eased);
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

if ("IntersectionObserver" in window) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      en.target.classList.add("in");
      $$("[data-count]", en.target).forEach(countUp);
      if (en.target.matches("[data-count]")) countUp(en.target);
      io.unobserve(en.target);
    });
  }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
  $$(".reveal, .reveal-stagger, [data-count]").forEach((el) => io.observe(el));
} else {
  $$(".reveal, .reveal-stagger").forEach((el) => el.classList.add("in"));
  $$("[data-count]").forEach(countUp);
}

/* ---------- Generic tabs ---------- */
$$("[data-tabs]").forEach((group) => {
  const tabs = $$('[role="tab"]', group);
  const select = (tab) => {
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute("aria-selected", on);
      t.tabIndex = on ? 0 : -1;
      const panel = document.getElementById(t.getAttribute("aria-controls"));
      if (panel) panel.hidden = !on;
    });
  };
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => select(t));
    t.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      const next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
      next.focus(); select(next);
    });
  });
  group._select = select;
});

/* ---------- How-it-works auto stepper ---------- */
$$(".steps").forEach((wrap) => {
  const group = $("[data-tabs]", wrap);
  const tabs = $$('[role="tab"]', wrap);
  if (!group || reduceMotion) return;
  let i = 0, timer;
  const advance = () => { i = (i + 1) % tabs.length; group._select(tabs[i]); schedule(); };
  const schedule = () => { clearTimeout(timer); timer = setTimeout(advance, 6000); };
  tabs.forEach((t, idx) => t.addEventListener("click", () => { i = idx; schedule(); }));
  wrap.addEventListener("mouseenter", () => { clearTimeout(timer); wrap.classList.add("paused"); });
  wrap.addEventListener("mouseleave", () => { wrap.classList.remove("paused"); schedule(); });
  schedule();
});

/* ---------- U.S. maps (hero + shipping-time map) ---------- */
// Approximate geographic centers, used only for transit estimates.
const CENTROIDS = {
  AL: [32.8, -86.8], AZ: [34.3, -111.7], AR: [34.9, -92.4], CA: [37.2, -119.5], CO: [39.0, -105.5], CT: [41.6, -72.7], DE: [39.0, -75.5], DC: [38.9, -77.0],
  FL: [28.6, -82.4], GA: [32.7, -83.4], ID: [44.4, -114.6], IL: [40.0, -89.2], IN: [39.9, -86.3], IA: [42.1, -93.5], KS: [38.5, -98.4], KY: [37.5, -85.3],
  LA: [31.1, -92.0], ME: [45.4, -69.2], MD: [39.0, -76.8], MA: [42.3, -71.8], MI: [44.3, -85.4], MN: [46.3, -94.3], MS: [32.7, -89.7], MO: [38.4, -92.5],
  MT: [47.0, -109.6], NE: [41.5, -99.8], NV: [39.3, -116.6], NH: [43.7, -71.6], NJ: [40.2, -74.7], NM: [34.4, -106.1], NY: [42.9, -75.5], NC: [35.6, -79.4],
  ND: [47.5, -100.5], OH: [40.3, -82.8], OK: [35.6, -97.5], OR: [43.9, -120.6], PA: [40.9, -77.8], RI: [41.7, -71.5], SC: [33.9, -80.9], SD: [44.4, -100.2],
  TN: [35.9, -86.4], TX: [31.5, -99.3], UT: [39.3, -111.7], VT: [44.1, -72.7], VA: [37.5, -78.9], WA: [47.4, -120.5], WV: [38.6, -80.6], WI: [44.6, -89.9], WY: [43.0, -107.6],
};
const miles = ([a, b], [c, d]) => {
  const r = Math.PI / 180, dLat = (c - a) * r, dLng = (d - b) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin(dLng / 2) ** 2;
  return 3959 * 2 * Math.asin(Math.sqrt(h));
};
const groundDays = (mi) => (mi <= 250 ? 1 : mi <= 750 ? 2 : mi <= 1300 ? 3 : mi <= 1900 ? 4 : 5);

const SVGNS = "http://www.w3.org/2000/svg";
const svgEl = (tag, attrs = {}, parent) => {
  const el = document.createElementNS(SVGNS, tag);
  for (const k in attrs) el.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(el);
  return el;
};
let mapPromise;
const loadMap = () => (mapPromise ||= fetch("/assets/us-states.json").then((r) => r.json()));

function baseMap(container, data, hubs, label, pinScale = 1) {
  const svg = svgEl("svg", { viewBox: data.viewBox, class: "us-svg", role: "img", "aria-label": label });
  const states = svgEl("g", { class: "states" }, svg);
  const paths = {};
  data.states.forEach((s) => {
    const p = svgEl("path", { d: s.d, "data-id": s.id }, states);
    p.dataset.name = s.name;
    if (hubs.some((h) => h.state === s.id)) p.classList.add("hub-state");
    paths[s.id] = p;
  });
  const routes = svgEl("g", { class: "routes" }, svg);
  const pins = svgEl("g", { class: "pins" }, svg);
  hubs.forEach((h) => {
    const g = svgEl("g", { class: "hub-pin", "data-hub": h.key, transform: `translate(${h.xy[0]} ${h.xy[1]}) scale(${pinScale})` }, pins);
    svgEl("circle", { r: 26, class: "pin-pulse" }, g);
    svgEl("circle", { r: 13, class: "pin-halo" }, g);
    svgEl("circle", { r: 7, class: "pin-dot" }, g);
    const t = svgEl("text", { y: -22, "text-anchor": "middle", class: "pin-label" }, g);
    t.textContent = h.city.startsWith("[") ? h.label : `${h.city}, ${h.state}`;
  });
  container.appendChild(svg);
  return { svg, paths, routes };
}
const centerOf = (path) => { const b = path.getBBox(); return [b.x + b.width / 2, b.y + b.height / 2]; };
function arc(from, to, lift = 0.25) {
  const [x1, y1] = from, [x2, y2] = to;
  const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
  const dist = Math.hypot(x2 - x1, y2 - y1);
  return `M${x1},${y1} Q${mx},${my - dist * lift} ${x2},${y2}`;
}
function drawRoute(group, d, cls, duration) {
  const p = svgEl("path", { d, class: cls }, group);
  const len = p.getTotalLength();
  p.style.strokeDasharray = len;
  p.style.strokeDashoffset = reduceMotion ? 0 : len;
  if (!reduceMotion) p.animate([{ strokeDashoffset: len }, { strokeDashoffset: 0 }], { duration, easing: "cubic-bezier(.3,.7,.2,1)", fill: "forwards" });
  return p;
}
const whenVisible = (el, cb) => {
  if (!("IntersectionObserver" in window)) return cb(true);
  new IntersectionObserver((es) => es.forEach((e) => cb(e.isIntersecting)), { threshold: 0.05 }).observe(el);
};

// Hero map: both hubs, live "shipments" flying out of the selected warehouse
$$("[data-hero-map]").forEach(async (root) => {
  const hubs = JSON.parse(root.dataset.hubs);
  const data = await loadMap();
  const { paths, routes } = baseMap(root, data, hubs, "Map of Boxio fulfillment centers in Utah and Florida", 1.9);
  drawRoute(routes, arc(hubs[0].xy, hubs[1].xy, 0.32), "link-route", 1800);
  let active = hubs[0].key, visible = false, timer;
  const setActive = (key) => {
    active = key;
    root.querySelectorAll(".hub-pin").forEach((g) => g.classList.toggle("on", g.dataset.hub === key));
    Object.values(paths).forEach((p) => p.classList.toggle("on", p.classList.contains("hub-state") && hubs.find((h) => h.key === key).state === p.dataset.id));
  };
  setActive(active);
  const ids = Object.keys(paths).filter((id) => CENTROIDS[id]);
  const ship = () => {
    const hub = hubs.find((h) => h.key === active);
    const id = ids[Math.floor(Math.random() * ids.length)];
    if (id === hub.state) return;
    const to = centerOf(paths[id]);
    const r = drawRoute(routes, arc(hub.xy, to, 0.22), "ship-route", 1100);
    const dot = svgEl("circle", { cx: to[0], cy: to[1], r: 0, class: "ship-dot" }, routes);
    paths[id].classList.add("ping");
    dot.animate([{ r: 0, opacity: 1 }, { r: 30, opacity: 0 }], { duration: 900, delay: 900, easing: "ease-out" });
    setTimeout(() => { r.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 600, fill: "forwards" }); paths[id].classList.remove("ping"); }, 1500);
    setTimeout(() => { r.remove(); dot.remove(); }, 2200);
  };
  const loop = () => { clearInterval(timer); if (visible && !reduceMotion && !document.hidden) timer = setInterval(ship, 650); };
  whenVisible(root, (v) => { visible = v; loop(); });
  document.addEventListener("visibilitychange", loop);
  // Follow the Utah / Florida tabs
  const tabs = root.closest("[data-tabs]");
  tabs && $$('[role="tab"]', tabs).forEach((t) => t.addEventListener("click", () => setActive(t.id.replace("tab-", ""))));
});

// Shipping-time map: color states by estimated ground days, hover for details
$$("[data-coverage-map]").forEach(async (root) => {
  const hubs = JSON.parse(root.dataset.hubs);
  const box = $(".us-map", root);
  const info = $(".map-info", root);
  const avgEl = $("[data-avg]", root);
  let mode = "both", active = root.dataset.focus || "TX", line;
  const data = await loadMap();
  const { paths, routes } = baseMap(box, data, hubs, "U.S. map of estimated shipping times from Boxio warehouses");

  const daysFor = (id) => {
    const c = CENTROIDS[id];
    if (!c) return null;
    const out = {};
    hubs.forEach((h) => { out[h.key] = groundDays(miles(c, h.coords)); });
    return out;
  };
  const pick = (d) => (!d ? null : mode === "both" ? Math.min(...Object.values(d)) : d[mode]);
  const fastestHub = (d) => {
    const pool = mode === "both" ? hubs : hubs.filter((h) => h.key === mode);
    return pool.reduce((a, b) => (d[b.key] < d[a.key] ? b : a));
  };

  Object.entries(paths).forEach(([id, p]) => {
    p.setAttribute("tabindex", "0");
    p.setAttribute("aria-label", p.dataset.name);
    p.addEventListener("mouseenter", () => show(id));
    p.addEventListener("focus", () => show(id));
    p.addEventListener("click", () => show(id, true));
  });
  box.addEventListener("mouseleave", () => show(active));

  function paint() {
    let sum = 0, n = 0;
    Object.entries(paths).forEach(([id, p]) => {
      const d = pick(daysFor(id));
      p.classList.remove("d1", "d2", "d3", "d4", "d5");
      p.classList.add(d ? "d" + d : "d5");
      if (d) { sum += d; n++; }
    });
    if (avgEl) avgEl.textContent = (sum / n).toFixed(1);
    show(active);
  }
  function show(id, pin) {
    if (pin) active = id;
    const p = paths[id];
    const d = daysFor(id);
    let html = `<span class="fine">Estimated ground transit to</span><h3>${p.dataset.name}</h3>`;
    if (line) { line.remove(); line = null; }
    if (!d) {
      html += `<p>Alaska and Hawaii ship via expedited / air services from either warehouse.</p>`;
    } else {
      hubs.forEach((h) => { html += `<div class="row"><span>From ${h.label}</span><strong>${d[h.key]} ${d[h.key] === 1 ? "day" : "days"}</strong></div>`; });
      const best = fastestHub(d);
      const tie = mode === "both" && hubs.every((h) => d[h.key] === d[best.key]);
      html += `<span class="best">${tie ? "Either warehouse works" : "Ships from " + best.label}</span>`;
      if (id !== best.state) line = drawRoute(routes, arc(best.xy, centerOf(p), 0.2), "hover-route", 700);
    }
    info.innerHTML = html;
    Object.values(paths).forEach((x) => x.classList.remove("active"));
    p.classList.add("active");
    p.parentNode.appendChild(p); // bring outline to front
  }
  $$("[data-mode]", root).forEach((chip) => chip.addEventListener("click", () => {
    mode = chip.dataset.mode;
    $$("[data-mode]", root).forEach((c) => c.setAttribute("aria-pressed", c === chip));
    root.querySelectorAll(".hub-pin").forEach((g) => g.classList.toggle("dim", mode !== "both" && g.dataset.hub !== mode));
    paint();
  }));
  paint();
});

/* ---------- Interactive backgrounds ---------- */
// Dot grid that lights up around the cursor, with "packages" gliding along the rows. Click to send a ripple.
function fxBackground(host) {
  const c = document.createElement("canvas");
  c.className = "fx-canvas";
  c.setAttribute("aria-hidden", "true");
  host.prepend(c);
  const ctx = c.getContext("2d");
  const GAP = 26;
  let w = 0, h = 0, cols = 0, rows = 0, raf = 0, running = false;
  const mouse = { x: -1e4, y: -1e4, tx: -1e4, ty: -1e4 };
  const packets = [], ripples = [];
  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = host.clientWidth; h = host.clientHeight;
    c.width = w * dpr; c.height = h * dpr;
    c.style.width = w + "px"; c.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cols = Math.ceil(w / GAP) + 1; rows = Math.ceil(h / GAP) + 1;
    if (!running) frame(performance.now());
  };
  const spawn = () => {
    const dir = Math.random() < 0.5 ? 1 : -1;
    packets.push({ row: 1 + Math.floor(Math.random() * (rows - 2)), x: dir > 0 ? -40 : w + 40, dir, v: 0.6 + Math.random() * 1.1 });
  };
  function frame(t) {
    ctx.clearRect(0, 0, w, h);
    mouse.x += (mouse.tx - mouse.x) * 0.12;
    mouse.y += (mouse.ty - mouse.y) * 0.12;
    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        const x = i * GAP, y = j * GAP;
        const dm = Math.hypot(x - mouse.x, y - mouse.y);
        let glow = Math.max(0, 1 - dm / 170);
        for (const r of ripples) {
          const dr = Math.abs(Math.hypot(x - r.x, y - r.y) - r.r);
          if (dr < 24) glow = Math.max(glow, (1 - dr / 24) * r.a);
        }
        const wave = 0.5 + 0.5 * Math.sin(t * 0.0012 + (x + y) * 0.012);
        ctx.fillStyle = glow > 0.02 ? `rgba(254,70,8,${0.25 + glow * 0.65})` : `rgba(11,14,26,${0.07 + wave * 0.07})`;
        ctx.beginPath();
        ctx.arc(x, y, 1.1 + glow * 2.6, 0, 6.283);
        ctx.fill();
      }
    }
    for (let k = packets.length - 1; k >= 0; k--) {
      const p = packets[k];
      p.x += p.v * p.dir * (1 + Math.max(0, 1 - Math.abs(p.row * GAP - mouse.y) / 120) * 2);
      const y = p.row * GAP;
      const g = ctx.createLinearGradient(p.x - 90 * p.dir, y, p.x, y);
      g.addColorStop(0, "rgba(254,70,8,0)"); g.addColorStop(1, "rgba(254,70,8,.45)");
      ctx.strokeStyle = g; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(p.x - 90 * p.dir, y); ctx.lineTo(p.x, y); ctx.stroke();
      ctx.fillStyle = "#fe4608";
      ctx.beginPath(); ctx.roundRect ? ctx.roundRect(p.x - 4, y - 4, 8, 8, 2) : ctx.rect(p.x - 4, y - 4, 8, 8); ctx.fill();
      if (p.x < -120 || p.x > w + 120) packets.splice(k, 1);
    }
    for (let k = ripples.length - 1; k >= 0; k--) {
      const r = ripples[k];
      r.r += 6; r.a *= 0.965;
      if (r.a < 0.03) ripples.splice(k, 1);
    }
    if (packets.length < Math.max(3, Math.round(w / 260)) && Math.random() < 0.03) spawn();
    if (running) raf = requestAnimationFrame(frame);
  }
  const start = () => { if (running || reduceMotion) return; running = true; raf = requestAnimationFrame(frame); };
  const stop = () => { running = false; cancelAnimationFrame(raf); };
  host.addEventListener("pointermove", (e) => { const b = host.getBoundingClientRect(); mouse.tx = e.clientX - b.left; mouse.ty = e.clientY - b.top; });
  host.addEventListener("pointerleave", () => { mouse.tx = mouse.ty = -1e4; });
  host.addEventListener("pointerdown", (e) => {
    if (e.target.closest("a, button, input, select, textarea, label, iframe, svg")) return;
    const b = host.getBoundingClientRect();
    ripples.push({ x: e.clientX - b.left, y: e.clientY - b.top, r: 0, a: 1 });
  });
  window.addEventListener("resize", resize);
  whenVisible(host, (v) => (v && !document.hidden ? start() : stop()));
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));
  resize();
}
$$(".hero, .page-hero").forEach(fxBackground);

// Cursor spotlight on cards
document.addEventListener("pointermove", (e) => {
  const card = e.target.closest && e.target.closest(".card, .int, .form-card");
  if (!card) return;
  const r = card.getBoundingClientRect();
  card.style.setProperty("--mx", e.clientX - r.left + "px");
  card.style.setProperty("--my", e.clientY - r.top + "px");
});

// Gentle 3D tilt on the hero map card
if (!reduceMotion && window.matchMedia("(pointer: fine)").matches) {
  $$("[data-tilt]").forEach((el) => {
    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
      el.style.transform = `perspective(1000px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg)`;
    });
    el.addEventListener("pointerleave", () => { el.style.transform = ""; });
  });
}

// Scroll progress bar
(() => {
  if (!header) return;
  const bar = document.createElement("div");
  bar.className = "scroll-progress";
  header.appendChild(bar);
  const set = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = `scaleX(${max > 0 ? window.scrollY / max : 0})`;
  };
  window.addEventListener("scroll", set, { passive: true });
  set();
})();

/* ---------- Integrations filter ---------- */
$$("[data-int-filter]").forEach((root) => {
  const items = $$(".int", root);
  const input = $("input[type=search]", root);
  const empty = $(".empty", root);
  let cat = "all";
  const apply = () => {
    const q = (input.value || "").trim().toLowerCase();
    let shown = 0;
    items.forEach((it) => {
      const ok = (cat === "all" || it.dataset.cat === cat) && it.dataset.name.toLowerCase().includes(q);
      it.hidden = !ok;
      if (ok) shown++;
    });
    empty.hidden = shown > 0;
  };
  $$("[data-cat]", root).forEach((chip) => {
    if (!chip.classList.contains("chip")) return;
    chip.addEventListener("click", () => {
      cat = chip.dataset.cat;
      $$(".chip[data-cat]", root).forEach((c) => c.setAttribute("aria-pressed", c === chip));
      apply();
    });
  });
  input.addEventListener("input", apply);
});

/* ---------- Form helpers ---------- */
function validateField(field) {
  const input = $("input, select, textarea", field);
  if (!input) return true;
  const ok = input.checkValidity();
  field.classList.toggle("invalid", !ok);
  return ok;
}
async function deliver(subject, data) {
  if (FORM_ENDPOINT) {
    const res = await fetch(FORM_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ _subject: subject, ...data }),
    });
    if (!res.ok) throw new Error("Form endpoint returned " + res.status);
    return;
  }
  const body = Object.entries(data).map(([k, v]) => `${k}: ${v}`).join("\n");
  window.location.href = `mailto:${FORM_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
const collect = (form) => {
  const fd = new FormData(form);
  const out = {};
  for (const [k, v] of fd.entries()) {
    if (k === "_gotcha") continue;
    out[k] = out[k] ? out[k] + ", " + v : v;
  }
  return out;
};

/* ---------- Quote wizard ---------- */
const VOLUME_LABELS = ["Under 100", "100–500", "500–1,000", "1,000–5,000", "5,000–10,000", "10,000+"];
$$("[data-wizard]").forEach((form) => {
  const steps = $$("fieldset", form);
  const bars = $$(".progress i", form);
  const back = $("[data-back]", form);
  const next = $("[data-next]", form);
  const submit = $("[data-submit]", form);
  const label = $(".step-label", form);
  const range = $("input[type=range]", form);
  const out = $("output", form);
  let i = 0;

  if (range && out) {
    const sync = () => { out.textContent = VOLUME_LABELS[range.value] + " / mo"; };
    range.addEventListener("input", sync);
    sync();
  }

  // Prefill from ?orders=&hub=&email= (used by the quick-quote form on the home page)
  const params = new URLSearchParams(location.search);
  if (params.get("orders") && range) { range.value = params.get("orders"); range.dispatchEvent(new Event("input")); }
  if (params.get("hub")) { const r = $(`input[name="Preferred warehouse"][value="${params.get("hub")}"]`, form); if (r) r.checked = true; }
  if (params.get("email")) { const e = $('input[name="Email"]', form); if (e) e.value = params.get("email"); }

  const render = () => {
    steps.forEach((s, idx) => { s.hidden = idx !== i; });
    bars.forEach((b, idx) => b.classList.toggle("on", idx <= i));
    back.hidden = i === 0;
    next.hidden = i === steps.length - 1;
    submit.hidden = i !== steps.length - 1;
    label.textContent = `Step ${i + 1} of ${steps.length}`;
  };
  const stepValid = () => {
    let ok = true;
    $$(".field", steps[i]).forEach((f) => { if (!validateField(f)) ok = false; });
    const req = steps[i].dataset.requireOne;
    const msg = $(".group-err", steps[i]);
    if (req) {
      const any = $$(`input[name="${req}"]`, steps[i]).some((x) => x.checked);
      if (msg) msg.hidden = any;
      if (!any) ok = false;
    }
    return ok;
  };
  const focusStep = () => { const first = $("input, select, textarea", steps[i]); first && first.focus({ preventScroll: true }); form.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" }); };

  next.addEventListener("click", () => { if (!stepValid()) return; i++; render(); focusStep(); });
  back.addEventListener("click", () => { i--; render(); focusStep(); });
  $$(".field input, .field select, .field textarea", form).forEach((el) => el.addEventListener("blur", () => validateField(el.closest(".field"))));
  $$("input[type=checkbox], input[type=radio]", form).forEach((el) => el.addEventListener("change", () => { const m = $(".group-err", el.closest("fieldset")); if (m) m.hidden = true; }));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!stepValid()) return;
    if ($('input[name="_gotcha"]', form)?.value) return; // spam bot
    const data = collect(form);
    if (range) data["Monthly orders"] = VOLUME_LABELS[range.value];
    submit.disabled = true;
    submit.textContent = "Sending…";
    try {
      await deliver(`Free quote request — ${data["Company"] || data["Name"]}`, data);
      const rows = ["Monthly orders", "Preferred warehouse", "Sales channels", "Services"].filter((k) => data[k]).map((k) => `<div><dt>${k}</dt><dd>${escapeHtml(data[k])}</dd></div>`).join("");
      form.innerHTML = `<div class="success" role="status" tabindex="-1">
        <div class="check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div>
        <h2>Thanks, ${escapeHtml((data["Name"] || "").split(" ")[0] || "we got it")}!</h2>
        <p class="lede" style="margin:0 auto 20px">Your quote request is on its way. A fulfillment specialist will reach out within one business day.</p>
        <dl class="summary">${rows}</dl></div>`;
      $(".success", form).focus();
    } catch (err) {
      submit.disabled = false;
      submit.textContent = "Get my free quote";
      alert(`Sorry, something went wrong sending your request. Please email ${FORM_EMAIL} or call us.`);
    }
  });
  render();
});

/* ---------- Simple forms (contact, quick quote) ---------- */
$$("[data-simple-form]").forEach((form) => {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    let ok = true;
    $$(".field", form).forEach((f) => { if (!validateField(f)) ok = false; });
    if (!ok) return;
    if ($('input[name="_gotcha"]', form)?.value) return;
    const btn = $("button[type=submit]", form);
    btn.disabled = true;
    const data = collect(form);
    try {
      await deliver(form.dataset.subject || "Website message", data);
      form.innerHTML = `<div class="success" role="status" tabindex="-1">
        <div class="check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div>
        <h2>Message sent</h2><p class="lede" style="margin:0 auto">Thanks for reaching out. We'll get back to you within one business day.</p></div>`;
      $(".success", form).focus();
    } catch (err) {
      btn.disabled = false;
      alert(`Sorry, something went wrong. Please email ${FORM_EMAIL} or call us.`);
    }
  });
  $$(".field input, .field select, .field textarea", form).forEach((el) => el.addEventListener("blur", () => validateField(el.closest(".field"))));
});

// Quick quote on the home page hands off to the full wizard
$$("[data-quick-quote]").forEach((form) => {
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const p = new URLSearchParams();
    const fd = new FormData(form);
    for (const [k, v] of fd.entries()) if (v) p.set(k, v);
    window.location.href = form.action + "?" + p.toString();
  });
});

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
