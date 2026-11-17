/* components.js — small shared building blocks used by every page.
   Deliberately plain: each component is a function returning DOM. No framework,
   no virtual DOM; pages re-render their results region on interaction. */

import { el, icon, fmtRel, hashShort, clampText } from "./dom.js";
import { statusInfo } from "./status.js";
import { NOW_MS } from "./data.js";
import { toast } from "./toasts.js";

/* ---- shared page header ---- */

export function pageHead({ title, sub, actions } = {}) {
  const h1 = el("h1", { tabindex: "-1" }, title);
  return el("div", { class: "page__head" },
    el("div", { class: "stack", style: "gap:2px; min-width:0" },
      h1,
      sub ? el("p", { class: "page__sub" }, sub) : null),
    actions ? el("div", { class: "page__actions" }, actions) : null);
}

/* ---- badges ---- */

export function badge(status, { title } = {}) {
  const info = statusInfo(status);
  return el("span", { class: `badge badge--${info.tone}`, title: title || null, "aria-label": title || null },
    el("span", { class: "badge__dot", "aria-hidden": "true" }),
    info.label);
}

export function hashChip(sha) {
  if (!sha) return el("span", { class: "text-faint" }, "—");
  const hue = [...sha.slice(0, 6)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 360, 7);
  return el("span", { class: "hash-chip", title: `sha256 ${sha}` },
    el("span", { class: "hash-chip__swatch", style: `background:hsl(${hue} 45% 55%)`, "aria-hidden": "true" }),
    hashShort(sha, 10));
}

/* ---- panels & cards ---- */

export function panel({ title, meta, actions, body, flush = false, class: cls = "" } = {}) {
  const head = (title || meta || actions)
    ? el("div", { class: "panel__head" },
        title ? el("h2", {}, title) : null,
        meta ? el("span", { class: "panel__meta" }, meta) : null,
        actions ? el("div", { class: "panel__actions" }, actions) : null)
    : null;
  const bodyEl = el("div", { class: flush ? "panel__body panel__body--flush" : "panel__body" }, body);
  return el("section", { class: `panel ${cls}`.trim() }, head, bodyEl);
}

export function statCard({ label, value, hint, tone = "", glyph = "" }) {
  return el("div", { class: `stat ${tone ? `stat--${tone}` : ""}` },
    glyph ? el("span", { class: "stat__glyph", "aria-hidden": "true" }, icon(glyph, 18)) : null,
    el("div", { class: "stat__label" }, label),
    el("div", { class: "stat__row" },
      el("span", { class: "stat__value" }, value),
      hint ? el("span", { class: "stat__hint" }, hint) : null));
}

/* ---- banners & states ---- */

export function banner({ tone = "info", glyph = "info", title, body } = {}) {
  return el("div", { class: `banner banner--${tone}`, role: "note" },
    el("span", { class: "banner__icon", "aria-hidden": "true" }, icon(glyph, 17)),
    el("div", { class: "banner__body" },
      title ? el("strong", { class: "banner__title" }, title) : null,
      typeof body === "string" ? el("span", {}, body) : body));
}

export function emptyState({ glyph = "inbox", title, body, action } = {}) {
  return el("div", { class: "empty" },
    el("div", { class: "empty__icon", "aria-hidden": "true" }, icon(glyph, 22)),
    el("div", { class: "empty__title" }, title),
    body ? el("p", { class: "empty__body" }, body) : null,
    action || null);
}

/* ---- form controls ---- */

export function searchInput({ label, value = "", placeholder = "Search…", onInput, class: cls = "" }) {
  const id = `fld-${Math.random().toString(36).slice(2, 8)}`;
  const input = el("input", {
    class: `input ${cls}`.trim(), id, type: "search", value, placeholder,
    autocomplete: "off",
    on: { input: () => onInput(input.value) },
  });
  return el("div", { class: "field" },
    el("label", { class: "field__label", for: id }, label),
    input);
}

export function chipGroup({ label, name, options, value, onChange, showCounts = true }) {
  const group = el("div", { class: "seg", role: "radiogroup", "aria-label": label });
  const total = options.reduce((a, o) => a + (o.count || 0), 0);
  options.forEach((opt) => {
    const count = opt.count ?? (opt.value === "all" ? total : null);
    const radio = el("button", {
      type: "button", class: "seg__opt", role: "radio",
      "aria-checked": String(opt.value === value),
      tabindex: opt.value === value ? "0" : "-1",
      on: {
        click: () => { set(opt.value); onChange(opt.value); },
        keydown: (e) => {
          const idx = options.findIndex((o) => o.value === current());
          if (["ArrowRight", "ArrowDown"].includes(e.key)) e.preventDefault(), set(options[(idx + 1) % options.length].value, true);
          if (["ArrowLeft", "ArrowUp"].includes(e.key)) e.preventDefault(), set(options[(idx - 1 + options.length) % options.length].value, true);
        },
      },
    }, opt.label, showCounts && count !== null ? el("span", { class: "seg__count" }, String(count)) : null);
    group.append(radio);
  });

  const current = () => options.find((o) => group.querySelector(`[data-v="${o.value}"]`)?.getAttribute("aria-checked") === "true")?.value;
  function set(v, focus = false) {
    options.forEach((o) => {
      const r = group.querySelectorAll(".seg__opt")[options.indexOf(o)];
      r.setAttribute("aria-checked", String(o.value === v));
      r.tabIndex = o.value === v ? "0" : "-1";
      r.dataset.v = o.value;
    });
    if (focus) {
      const elx = group.querySelector('[aria-checked="true"]');
      elx?.focus();
      elx?.click();
    }
  }
  set(value);
  return group;
}

export function selectControl({ label, options, value, onChange }) {
  const id = `sel-${Math.random().toString(36).slice(2, 8)}`;
  const select = el("select", {
    class: "select", id, autocomplete: "off",
    on: { change: () => onChange(select.value) },
  }, options.map((o) => el("option", { value: o.value, selected: o.value === value ? true : null }, o.label)));
  return el("div", { class: "field" },
    el("label", { class: "field__label", for: id }, label),
    select);
}

/* ---- data table (responsive + sortable) ---- */

export function dataTable({ caption, columns, rows, sort = null, onSort = null, stack = true, onRowActivate = null, emptyMessage = "No rows match the current filters." }) {
  if (!rows.length) {
    return emptyState({ glyph: "search", title: "Nothing to show", body: emptyMessage });
  }

  const headCells = columns.map((col) => {
    const sorted = sort && sort.key === col.key;
    if (!col.sortable || !onSort) {
      return el("th", { scope: "col", class: col.align === "right" ? "num" : "", style: col.width ? `width:${col.width}` : null }, col.label);
    }
    return el("th", {
      scope: "col",
      "data-sortable": "",
      "aria-sort": sorted ? (sort.dir === "asc" ? "ascending" : "descending") : null,
      class: col.align === "right" ? "num" : "",
    }, el("button", {
      class: "th-sort", type: "button",
      on: { click: () => onSort({ key: col.key, dir: sorted && sort.dir === "asc" ? "desc" : "asc" }) },
    },
      col.label,
      el("span", { class: "th-sort__arrow", "aria-hidden": "true" })));
  });

  const bodyRows = rows.map((row) => {
    const tr = el("tr", {});
    columns.forEach((col) => {
      const td = el("td", {
        class: col.align === "right" ? "num" : "",
        "data-label": col.label,
      });
      const value = col.render ? col.render(row) : row[col.key];
      if (value instanceof Node) td.append(value);
      else if (value !== null && value !== undefined) td.textContent = String(value);
      tr.append(td);
    });
    if (onRowActivate) {
      tr.tabIndex = 0;
      tr.setAttribute("role", "button");
      tr.setAttribute("aria-label", onRowActivate.aria(row));
      tr.addEventListener("click", () => onRowActivate.activate(row));
      tr.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRowActivate.activate(row); }
      });
    }
    return tr;
  });

  const wrap = el("div", {
    class: "table-wrap",
    tabindex: "0",
    role: "region",
    "aria-label": caption,
  });
  const table = el("table", { class: `data-table ${stack ? "stack" : ""}` },
    el("caption", {}, caption),
    el("thead", {}, el("tr", {}, headCells)),
    el("tbody", {}, bodyRows));
  wrap.append(table);
  return wrap;
}

/* ---- meters, kv, timeline ---- */

export function meterRow({ label, value, total, unit = "%", tone = "", note }) {
  const pct = total ? Math.round((value / total) * 100) : 0;
  return el("div", { class: `meter ${tone ? `meter--${tone}` : ""}` },
    el("div", { class: "meter__top" },
      el("span", { class: "meter__label" }, label),
      el("span", { class: "meter__value" }, `${value}${unit === "%" ? "%" : ""}${note ? "" : ""}${unit === "pct_of" ? ` / ${total}` : ""}`)),
    el("div", { class: "meter__track", role: "img", "aria-label": `${label}: ${value}${unit === "%" ? "%" : ` of ${total}`}` },
      el("div", { class: "meter__fill", style: `width:${Math.min(100, unit === "%" ? value : pct)}%` })));
}

export function kv(items) {
  return el("dl", { class: "kv" },
    items.flatMap(({ k, v, mono }) => [
      el("dt", {}, k),
      el("dd", { class: mono ? "mono" : "" }, v instanceof Node ? v : String(v ?? "—")),
    ]));
}

export function timeline(items) {
  return el("div", { class: "timeline" },
    items.map((it) => el("div", { class: "timeline__item" },
      el("span", { class: `timeline__dot timeline__dot--${it.tone || "neutral"}`, "aria-hidden": "true" }, icon(it.glyph || "info", 12)),
      el("div", { class: "stack", style: "gap:1px" },
        el("span", { class: "timeline__time" }, fmtRel(it.at, NOW_MS)),
        el("span", { class: "timeline__title" }, it.title),
        it.detail ? el("span", { class: "timeline__detail" }, it.detail) : null))));
}

/* ---- attention item (Overview) ---- */

export function attend({ tone = "warn", glyph = "alert", title, meta, linkLabel, onLink }) {
  return el("div", { class: `attend attend--${tone}` },
    el("span", { class: "attend__glyph", "aria-hidden": "true" }, icon(glyph, 17)),
    el("div", { class: "stack", style: "gap:1px; min-width:0" },
      el("span", { class: "attend__title" }, title),
      meta ? el("span", { class: "attend__meta" }, meta) : null),
    linkLabel ? el("button", { class: "attend__link", type: "button", on: { click: onLink } },
      linkLabel, icon("chevronRight", 13)) : null);
}

/* ---- stage track (pipeline chips) ---- */

export function stageTrack(stages, currentIndex) {
  const nodes = stages.map((name, idx) => {
    let state = "todo";
    if (idx < currentIndex) state = "done";
    if (idx === currentIndex) state = "current";
    return el("span", { class: `stagetrack__node stagetrack__node--${state}` },
      idx < currentIndex ? icon("check", 10) : null,
      name);
  });
  const linked = nodes.flatMap((n, i) => (i < nodes.length - 1
    ? [n, el("span", { class: "stagetrack__link", "aria-hidden": "true" }, icon("chevronRight", 10))]
    : [n]));
  return el("div", { class: "stagetrack", "aria-label": "Pipeline stage" }, linked);
}

/* ---- drawer (detail overlay) ---- */

export function drawer({ title, meta, content, onClose }) {
  const lastFocus = document.activeElement;
  const overlay = el("div", { class: "drawer-overlay" });
  const dlg = el("aside", { class: "drawer", role: "dialog", "aria-modal": "true", "aria-labelledby": "drawer-title" });

  const titleEl = el("h2", { id: "drawer-title", class: "drawer__title", tabindex: "-1" }, title);
  const closeBtn = el("button", { class: "iconbtn", type: "button", "aria-label": "Close details", on: { click: close } }, icon("close", 17));

  // If navigation happens while the drawer is open (e.g. a cross-link button
  // inside the drawer), auto-close so the new page renders without stacking.
  function onHashChange() { close(); }
  window.addEventListener("hashchange", onHashChange);

  function keydown(e) {
    if (e.key === "Escape") { e.preventDefault(); close(); return; }
    if (e.key === "Tab") {
      const focusables = dlg.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }

  function close() {
    window.removeEventListener("hashchange", onHashChange);
    document.removeEventListener("keydown", keydown, true);
    overlay.remove();
    document.body.style.overflow = "";
    if (lastFocus instanceof HTMLElement && lastFocus.isConnected) lastFocus.focus();
    onClose?.();
  }

  dlg.append(
    el("div", { class: "drawer__head" }, el("div", { class: "stack", style: "gap:1px" }, titleEl, meta ? el("span", { class: "drawer__meta" }, meta) : null), closeBtn),
    el("div", { class: "drawer__body" }, content),
  );
  overlay.append(dlg);
  document.body.style.overflow = "hidden";
  document.addEventListener("keydown", keydown, true);
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) close(); });
  document.body.append(overlay);
  titleEl.focus();
  return { close };
}

/* ---- mock dialog (review decision) ---- */

export function mockDialog({ title, body, onClose }) {
  const lastFocus = document.activeElement;
  const overlay = el("div", { class: "dialog-overlay" });
  const dlg = el("div", { class: "dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": "mockdlg-title" });
  const titleEl = el("h2", { id: "mockdlg-title", tabindex: "-1" }, title);

  function keydown(e) { if (e.key === "Escape") { e.preventDefault(); close(); } }
  function close() {
    window.removeEventListener("hashchange", onHashChange);
    document.removeEventListener("keydown", keydown, true);
    overlay.remove();
    if (lastFocus instanceof HTMLElement && lastFocus.isConnected) lastFocus.focus();
    onClose?.();
  }
  function onHashChange() { close(); }
  window.addEventListener("hashchange", onHashChange);

  dlg.append(titleEl, el("div", { class: "dialog__body", style: "margin-top:8px" }, body));
  overlay.append(dlg);
  document.addEventListener("keydown", keydown, true);
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) close(); });
  document.body.append(overlay);
  titleEl.focus();
  return { close };
}

/* ---- misc ---- */

export function relTime(iso) {
  return fmtRel(iso, NOW_MS);
}

export function clamp(value, n) {
  return clampText(value, n);
}

export { toast };
