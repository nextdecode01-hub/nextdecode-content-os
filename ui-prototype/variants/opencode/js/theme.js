/* theme.js — global Dark / Light / System appearance.
   - Dark is the default (dark-first product).
   - "System" follows prefers-color-scheme and updates live via matchMedia.
   - Choice persists in localStorage ('nd-cc-theme') and is applied to
     <html data-theme> so every page (SPA route) inherits it.
   - An inline bootstrap in index.html applies the saved theme before first
     paint to avoid a flash of the wrong theme. */

import { icon } from "./dom.js";

const THEME_KEY = "nd-cc-theme";
const media = window.matchMedia("(prefers-color-scheme: dark)");
let mode = "dark";

export function getTheme() {
  return mode;
}

export function resolvedTheme() {
  return mode === "system" ? (media.matches ? "dark" : "light") : mode;
}

function apply() {
  document.documentElement.dataset.theme = resolvedTheme();
  document.dispatchEvent(new CustomEvent("nd:theme", { detail: { mode, resolved: resolvedTheme() } }));
}

export function setTheme(next) {
  if (!["dark", "light", "system"].includes(next)) return;
  mode = next;
  try { localStorage.setItem(THEME_KEY, next); } catch { /* ignore */ }
  apply();
}

export function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem(THEME_KEY); } catch { /* ignore */ }
  mode = ["dark", "light", "system"].includes(saved) ? saved : "dark";
  media.addEventListener("change", () => { if (mode === "system") apply(); });
  apply();
}

/** Radiogroup control implementing the WAI-ARIA radio pattern with
    Left/Right/Up/Down arrow-key movement. Returns the group element. */
export function themeRadiogroup({ label = "Appearance", compact = false } = {}) {
  const options = [
    { value: "dark", icon: "moon", text: "Dark" },
    { value: "light", icon: "sun", text: "Light" },
    { value: "system", icon: "monitor", text: "System" },
  ];

  const group = document.createElement("div");
  group.setAttribute("role", "radiogroup");
  group.setAttribute("aria-label", label);
  group.className = compact ? "seg seg--theme" : "seg";

  const radios = options.map((opt) => {
    const r = document.createElement("button");
    r.type = "button";
    r.setAttribute("role", "radio");
    r.dataset.value = opt.value;
    r.className = "seg__opt";
    r.tabIndex = -1;
    r.setAttribute("aria-label", opt.text);
    r.append(icon(opt.icon, 15));
    if (!compact) r.append(document.createTextNode(opt.text));
    r.addEventListener("click", () => { setTheme(opt.value); sync(); });
    group.append(r);
    return r;
  });

  function sync() {
    radios.forEach((r) => {
      const checked = r.dataset.value === getTheme();
      r.setAttribute("aria-checked", String(checked));
      r.tabIndex = checked ? 0 : -1;
    });
  }

  group.addEventListener("keydown", (e) => {
    const values = options.map((o) => o.value);
    const idx = values.indexOf(getTheme());
    let next = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") next = values[(idx + 1) % values.length];
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") next = values[(idx - 1 + values.length) % values.length];
    if (next) {
      e.preventDefault();
      setTheme(next);
      sync();
      radios[values.indexOf(next)].focus();
    }
  });

  document.addEventListener("nd:theme", sync);
  sync();
  return group;
}
