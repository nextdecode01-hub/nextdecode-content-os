/* dom.js — tiny DOM builders, inline icon set, formatting helpers.
   No dependencies. All dynamic data is inserted via textContent (no innerHTML
   for sample values), so sample data cannot inject markup. */

const ICON_PATHS = {
  overview: '<rect x="3" y="3" width="7.5" height="7.5" rx="1.6"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.6"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.6"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.6"/>',
  projects: '<path d="M3.5 7.2A2.2 2.2 0 0 1 5.7 5h3.4l2 2h7.2a2.2 2.2 0 0 1 2.2 2.2v7.6a2.2 2.2 0 0 1-2.2 2.2H5.7a2.2 2.2 0 0 1-2.2-2.2z"/>',
  workflows: '<circle cx="5.5" cy="6" r="2.2"/><circle cx="18.5" cy="18" r="2.2"/><path d="M7.7 6h5.3a4.5 4.5 0 0 1 4.5 4.5v4.9"/>',
  research: '<circle cx="11" cy="11" r="6.5"/><path d="M15.8 15.8 21 21"/>',
  studio: '<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M3.5 9.5h17M8.3 5v4.5M13.3 5v4.5M18 5v4.5"/>',
  review: '<path d="M12 3.2 19 6v5.2c0 4.6-3.4 7.6-7 9-3.6-1.4-7-4.4-7-9V6z"/><path d="m9.2 12 2 2 3.8-4"/>',
  publishing: '<path d="M21.5 2.5 11 13"/><path d="M21.5 2.5 15 21.5l-4-8.5-8.5-4z"/>',
  analytics: '<path d="M4.5 19.5v-8M10.5 19.5v-14M16.5 19.5v-5M3 19.5h18"/>',
  operations: '<path d="M3 12.5h3.8L9 5.5l4.4 13 2-6H21"/>',
  settings: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.8v2.6M12 18.6v2.6M2.8 12h2.6M18.6 12h2.6M5.5 5.5l1.8 1.8M16.7 16.7l1.8 1.8M18.5 5.5l-1.8 1.8M7.3 16.7l-1.8 1.8"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M15.8 15.8 21 21"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5 5l1.4 1.4M17.6 17.6 19 19M19 5l-1.4 1.4M6.4 17.6 5 19"/>',
  moon: '<path d="M20.5 13.5A8.5 8.5 0 1 1 10.5 3.5a7 7 0 0 0 10 10z"/>',
  monitor: '<rect x="2.8" y="4" width="18.4" height="12.5" rx="2"/><path d="M8.5 20.5h7M12 16.5v4"/>',
  alert: '<path d="M12 3.5 2.5 20h19z"/><path d="M12 9.5v5M12 17.2h.01"/>',
  check: '<path d="m5 13 4.2 4.2L19 7.4"/>',
  checkCircle: '<circle cx="12" cy="12" r="8.5"/><path d="m8.5 12.3 2.3 2.3 4.7-5"/>',
  xCircle: '<circle cx="12" cy="12" r="8.5"/><path d="M9.2 9.2l5.6 5.6M14.8 9.2l-5.6 5.6"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.2V12l3.4 2.1"/>',
  lock: '<rect x="4.8" y="10.8" width="14.4" height="9.4" rx="2"/><path d="M8 10.8V7.8a4 4 0 0 1 8 0v3"/>',
  chevronRight: '<path d="m9.5 6 6 6-6 6"/>',
  arrowLeft: '<path d="M19 12H5.5M11 18l-6-6 6-6"/>',
  refresh: '<path d="M20.5 12a8.5 8.5 0 1 1-2.5-6M20.5 3.5V8H16"/>',
  pause: '<path d="M9 5.5v13M15 5.5v13"/>',
  play: '<path d="M8 5.2 19 12 8 18.8z"/>',
  file: '<path d="M6.5 2.5h6.8L18.5 7.7V21.5h-12z"/><path d="M13 2.5v5.5h5.5"/>',
  video: '<rect x="2.8" y="6.5" width="12.7" height="11" rx="2"/><path d="M15.5 10.4l5.7-3.2v9.6l-5.7-3.2"/>',
  mic: '<rect x="9" y="2.8" width="6" height="11" rx="3"/><path d="M5.5 11.3a6.5 6.5 0 0 0 13 0M12 17.8v3.7"/>',
  info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/>',
  shield: '<path d="M12 3.2 19 6v5.2c0 4.6-3.4 7.6-7 9-3.6-1.4-7-4.4-7-9V6z"/>',
  inbox: '<path d="M3.5 13.5h4.2l1.8 2.8h5l1.8-2.8h4.2"/><path d="M3.5 13.5 6 5h12l2.5 8.5v5.5a1.5 1.5 0 0 1-1.5 1.5H5a1.5 1.5 0 0 1-1.5-1.5z"/>',
  key: '<circle cx="8" cy="15.5" r="4.5"/><path d="m11.2 12.3 8.3-8.3M16.5 7l3 3M14 9.5l2.4 2.4"/>',
};

/** Build an element. attrs: {class, id, title, aria/data via keys, on:{evt:fn}}.
    Children: nodes, strings (textContent) or arrays (flattened). */
export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key === "on") for (const [evt, fn] of Object.entries(value)) node.addEventListener(evt, fn);
    else if (key in node && key !== "list" && key !== "form") {
      try { node[key] = value; } catch { node.setAttribute(key, value); }
    } else node.setAttribute(key, value);
  }
  appendChildren(node, children);
  return node;
}

function appendChildren(node, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

/** Inline stroke icon: icon("check") -> span.ic > svg */
export function icon(name, size = 18) {
  const path = ICON_PATHS[name];
  const span = el("span", { class: "ic", "aria-hidden": "true", style: `width:${size}px;height:${size}px;display:inline-flex` });
  if (!path) return span;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("width", size);
  svg.setAttribute("height", size);
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.7");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  svg.innerHTML = path; // static internal constant — safe
  span.append(svg);
  return span;
}

/* ---- formatting (all render against the fixed dataset capture time) ---- */

const DAY = 3600_000;
const MINUTE = 60_000;

export function fmtNum(n) {
  return new Intl.NumberFormat("en-US").format(n);
}

/** "13 Nov, 10:24" */
export function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false });
}

/** "13 Nov" */
export function fmtDay(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

/** Relative time against a fixed reference (passed in) — deterministic. */
export function fmtRel(iso, nowMs) {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  let diff = Math.round((nowMs - t) / MINUTE);
  const future = diff < 0;
  diff = Math.abs(diff);
  let out;
  if (diff < 1) out = "just now";
  else if (diff < 60) out = `${diff}m`;
  else if (diff < 24 * 60) out = `${Math.round(diff / 60)}h`;
  else out = `${Math.round(diff / DAY)}d`;
  if (out === "just now") return out;
  return future ? `in ${out}` : `${out} ago`;
}

/** "6.2h" / "34m" */
export function fmtHours(hours) {
  if (hours === null || hours === undefined) return "—";
  return hours >= 1 ? `${hours.toFixed(1)}h` : `${Math.round(hours * 60)}m`;
}

/** Short sha prefix "8f3a1c4d…" */
export function hashShort(sha, n = 12) {
  if (!sha) return "—";
  return `${sha.slice(0, n)}…`;
}

export function clampText(text, n = 90) {
  if (!text) return "";
  return text.length > n ? `${text.slice(0, n - 1)}…` : text;
}
