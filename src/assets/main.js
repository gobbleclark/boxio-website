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

/* ---------- Shipping coverage tile map ---------- */
const STATES = [
  ["AK", "Alaska", 0, 0], ["ME", "Maine", 0, 10],
  ["VT", "Vermont", 1, 9], ["NH", "New Hampshire", 1, 10],
  ["WA", "Washington", 2, 0], ["ID", "Idaho", 2, 1], ["MT", "Montana", 2, 2], ["ND", "North Dakota", 2, 3], ["MN", "Minnesota", 2, 4], ["IL", "Illinois", 2, 5], ["WI", "Wisconsin", 2, 6], ["MI", "Michigan", 2, 7], ["NY", "New York", 2, 8], ["RI", "Rhode Island", 2, 9], ["MA", "Massachusetts", 2, 10],
  ["OR", "Oregon", 3, 0], ["NV", "Nevada", 3, 1], ["WY", "Wyoming", 3, 2], ["SD", "South Dakota", 3, 3], ["IA", "Iowa", 3, 4], ["IN", "Indiana", 3, 5], ["OH", "Ohio", 3, 6], ["PA", "Pennsylvania", 3, 7], ["NJ", "New Jersey", 3, 8], ["CT", "Connecticut", 3, 9],
  ["CA", "California", 4, 0], ["UT", "Utah", 4, 1], ["CO", "Colorado", 4, 2], ["NE", "Nebraska", 4, 3], ["MO", "Missouri", 4, 4], ["KY", "Kentucky", 4, 5], ["WV", "West Virginia", 4, 6], ["VA", "Virginia", 4, 7], ["MD", "Maryland", 4, 8], ["DE", "Delaware", 4, 9],
  ["AZ", "Arizona", 5, 1], ["NM", "New Mexico", 5, 2], ["KS", "Kansas", 5, 3], ["AR", "Arkansas", 5, 4], ["TN", "Tennessee", 5, 5], ["NC", "North Carolina", 5, 6], ["SC", "South Carolina", 5, 7], ["DC", "Washington, D.C.", 5, 8],
  ["OK", "Oklahoma", 6, 3], ["LA", "Louisiana", 6, 4], ["MS", "Mississippi", 6, 5], ["AL", "Alabama", 6, 6], ["GA", "Georgia", 6, 7],
  ["HI", "Hawaii", 7, 0], ["TX", "Texas", 7, 3], ["FL", "Florida", 7, 8],
];
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

$$("[data-coverage-map]").forEach((root) => {
  const hubs = JSON.parse(root.dataset.hubs);
  const grid = $(".tile-map", root);
  const info = $(".map-info", root);
  const avgEl = $("[data-avg]", root);
  let mode = root.dataset.mode || "both";
  let active = root.dataset.focus || "TX";

  const daysFor = (code) => {
    const c = CENTROIDS[code];
    if (!c) return null;
    const out = {};
    hubs.forEach((h) => { out[h.key] = groundDays(miles(c, h.coords)); });
    return out;
  };
  const pick = (d) => {
    if (!d) return null;
    if (mode !== "both") return d[mode];
    return Math.min(...Object.values(d));
  };

  const tiles = {};
  grid.style.gridTemplateRows = "repeat(8, auto)";
  STATES.forEach(([code, name, row, col]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "tile";
    b.textContent = code;
    b.style.gridRow = row + 1;
    b.style.gridColumn = col + 1;
    b.setAttribute("aria-label", name);
    if (hubs.some((h) => h.state === code)) b.classList.add("hub");
    b.addEventListener("mouseenter", () => show(code));
    b.addEventListener("focus", () => show(code));
    b.addEventListener("click", () => show(code, true));
    grid.appendChild(b);
    tiles[code] = b;
  });

  function paint() {
    let sum = 0, n = 0;
    STATES.forEach(([code]) => {
      const d = pick(daysFor(code));
      tiles[code].className = "tile" + (hubs.some((h) => h.state === code) ? " hub" : "") + " " + (d ? "d" + d : "d5") + (code === active ? " active" : "");
      if (d) { sum += d; n++; }
    });
    if (avgEl) avgEl.textContent = (sum / n).toFixed(1);
  }

  function show(code, pin) {
    if (pin) active = code;
    const name = STATES.find((s) => s[0] === code)[1];
    const d = daysFor(code);
    let html = `<span class="fine">Estimated ground transit to</span><h3>${name}</h3>`;
    if (!d) {
      html += `<p>Alaska and Hawaii ship via expedited / air services from either warehouse.</p>`;
    } else {
      hubs.forEach((h) => {
        html += `<div class="row"><span>From ${h.label}</span><strong>${d[h.key]} ${d[h.key] === 1 ? "day" : "days"}</strong></div>`;
      });
      const best = hubs.reduce((a, b) => (d[b.key] < d[a.key] ? b : a));
      const tie = hubs.every((h) => d[h.key] === d[best.key]);
      html += `<span class="best">${tie ? "Either warehouse works" : "Fastest: " + best.label}</span>`;
    }
    info.innerHTML = html;
    $$(".tile.active", grid).forEach((t) => t.classList.remove("active"));
    tiles[active] && tiles[active].classList.add("active");
  }

  $$("[data-mode]", root).forEach((chip) => {
    chip.addEventListener("click", () => {
      mode = chip.dataset.mode;
      $$("[data-mode]", root).forEach((c) => c.setAttribute("aria-pressed", c === chip));
      paint();
    });
  });
  grid.addEventListener("mouseleave", () => show(active));
  paint();
  show(active, true);
});

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
