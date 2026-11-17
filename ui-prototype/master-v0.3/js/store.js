/* store.js — minimal client-side state for the prototype.
   No state-management framework: one plain object plus localStorage-backed
   display preferences. Filters are per-page and survive in-session navigation. */

const PREFS_KEY = "nd-cc-prefs";

export const store = {
  /** Per-page filter state, keyed by route id. */
  filters: {},
  /** UI-only flags (not persisted). */
  ui: {},
};

/** Read display prefs (density). Theme is owned by theme.js ('nd-cc-theme'). */
export function loadPrefs() {
  try {
    return JSON.parse(localStorage.getItem(PREFS_KEY)) || {};
  } catch {
    return {};
  }
}

export function savePrefs(prefs) {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  } catch {
    /* storage unavailable (e.g. restricted mode) — prototype keeps working */
  }
}

export function clearPrefs() {
  try {
    localStorage.removeItem(PREFS_KEY);
    localStorage.removeItem("nd-cc-theme");
  } catch {
    /* ignore */
  }
}
