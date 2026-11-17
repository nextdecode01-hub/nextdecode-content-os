/* main.js — shell bootstrap: theme, sidebar nav, topbar context, command
   palette and the router. This is the only place that knows all pages. */

import { el, icon } from "./dom.js";
import { initTheme, themeRadiogroup } from "./theme.js";
import { startRouter } from "./router.js";
import { toast } from "./toasts.js";
import { projects, runs, reviews } from "./data.js";

import overview from "./pages/overview.js";
import projectsPage from "./pages/projects.js";
import workflows from "./pages/workflows.js";
import research from "./pages/research.js";
import studio from "./pages/studio.js";
import review from "./pages/review.js";
import publishing from "./pages/publishing.js";
import analytics from "./pages/analytics.js";
import operations from "./pages/operations.js";
import settings from "./pages/settings.js";

const PAGES = {
  overview, projects: projectsPage, workflows, research, studio,
  review, publishing, analytics, operations, settings,
};

const TITLES = Object.fromEntries(Object.entries(PAGES).map(([id, p]) => [id, p.title]));

const ICONS_BY_ROUTE = {
  overview: "overview", projects: "projects", workflows: "workflows",
  research: "research", studio: "studio", review: "review",
  publishing: "publishing", analytics: "analytics",
  operations: "operations", settings: "settings",
};

/* ---------------------------------------------------------------- palette */

function paletteItems() {
  const items = [];
  for (const [id, page] of Object.entries(PAGES)) {
    items.push({ kind: "Page", label: page.title, icon: ICONS_BY_ROUTE[id], hint: "Go to page", go: () => { window.location.hash = `#/${id}`; } });
  }
  projects.forEach((p) => items.push({ kind: "Project", label: p.title, icon: "projects", hint: p.id, go: () => { window.location.hash = "#/projects"; } }));
  runs.forEach((r) => items.push({ kind: "Run", label: `${r.id} — ${projects.find((p) => p.id === r.project_id)?.title || r.project_id}`, icon: "workflows", hint: r.state, go: () => { window.location.hash = `#/workflows/${r.id}`; } }));
  reviews.forEach((r) => items.push({ kind: "Review", label: `${r.id} — ${r.title}`, icon: "review", hint: r.status.replaceAll("_", " "), go: () => { window.location.hash = `#/review/${r.id}`; } }));
  return items;
}

function openPalette() {
  const lastFocus = document.activeElement;
  const overlay = el("div", { class: "palette-overlay" });
  const inputId = "palette-input";
  const listId = "palette-list";
  let filtered = paletteItems();
  let active = 0;

  const list = el("div", { class: "palette__list", id: listId, role: "listbox", "aria-label": "Results" });
  const input = el("input", {
    class: "palette__input", id: inputId, type: "text", placeholder: "Search pages, projects, runs, reviews…",
    role: "combobox", "aria-expanded": "true", "aria-controls": listId, "aria-autocomplete": "list",
    autocomplete: "off",
    on: { input: () => { query = input.value; active = 0; renderList(); } },
  });
  input.spellcheck = false;
  let query = "";

  function renderList() {
    const q = query.trim().toLowerCase();
    filtered = q ? paletteItems().filter((it) => `${it.label} ${it.kind} ${it.hint}`.toLowerCase().includes(q)) : paletteItems();
    active = Math.min(active, Math.max(0, filtered.length - 1));
    list.replaceChildren(
      filtered.length
        ? filtered.map((it, i) => el("div", {
            class: "palette__opt", role: "option", id: `palette-opt-${i}`,
            "aria-selected": String(i === active),
            on: { click: () => choose(i), mousemove: () => { if (active !== i) { active = i; paint(); } } },
          },
            el("span", { class: "nav__glyph", "aria-hidden": "true" }, icon(it.icon, 16)),
            el("span", { style: "min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap" }, it.label),
            el("span", { class: "palette__kind" }, `${it.kind} · ${it.hint}`)))
        : el("div", { class: "palette__empty" }, "No matches. Try a project title, run id or review id."));
    paint();
  }

  function paint() {
    list.querySelectorAll(".palette__opt").forEach((node, i) => {
      node.setAttribute("aria-selected", String(i === active));
    });
    if (filtered.length) input.setAttribute("aria-activedescendant", `palette-opt-${active}`);
    else input.removeAttribute("aria-activedescendant");
  }

  function choose(i) {
    const item = filtered[i];
    if (!item) return;
    close();
    item.go();
  }

  function keydown(e) {
    if (e.key === "Escape") { e.preventDefault(); close(); }
    else if (e.key === "ArrowDown") { e.preventDefault(); active = Math.min(active + 1, filtered.length - 1); paint(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); active = Math.max(active - 1, 0); paint(); }
    else if (e.key === "Enter") { e.preventDefault(); choose(active); }
  }

  function close() {
    document.removeEventListener("keydown", keydown, true);
    overlay.remove();
    if (lastFocus instanceof HTMLElement) lastFocus.focus();
  }

  const dlg = el("div", { class: "palette", role: "dialog", "aria-modal": "true", "aria-label": "Command palette (sample data)" },
    input, list,
    el("div", { class: "palette__foot" },
      el("span", {}, "↑↓ move"), el("span", {}, "↵ open"), el("span", {}, "esc close"),
      el("span", { style: "margin-left:auto" }, "Sample data only")));
  overlay.append(dlg);

  document.addEventListener("keydown", keydown, true);
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) close(); });
  document.body.append(overlay);
  input.focus();
  renderList();
}

/* ------------------------------------------------------------------ shell */

function wireNav() {
  const app = document.getElementById("app");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("nav-backdrop");
  const menuBtn = document.getElementById("nav-toggle");

  function setOpen(open) {
    app.dataset.navOpen = String(open);
    menuBtn.setAttribute("aria-expanded", String(open));
    if (open) {
      const first = sidebar.querySelector("a");
      if (first) first.focus();
    }
  }

  menuBtn.addEventListener("click", () => setOpen(app.dataset.navOpen !== "true"));
  backdrop.addEventListener("click", () => setOpen(false));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && app.dataset.navOpen === "true") {
      setOpen(false);
      menuBtn.focus();
    }
  });

  document.addEventListener("nd:route", () => {
    if (app.dataset.navOpen === "true") setOpen(false);
  });

  return { setOpen };
}

function wireNavCurrent() {
  const links = document.querySelectorAll("#sidebar .nav__link[data-route]");
  document.addEventListener("nd:route", (e) => {
    const route = e.detail?.route;
    links.forEach((link) => {
      const isCurrent = link.dataset.route === route;
      if (isCurrent) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    const crumb = document.getElementById("crumb-page");
    if (crumb && route && TITLES[route]) crumb.textContent = TITLES[route];
  });
}

function wirePaletteShortcut() {
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) {
      e.preventDefault();
      openPalette();
    }
  });
  document.getElementById("palette-open")?.addEventListener("click", openPalette);
  document.getElementById("palette-open-m")?.addEventListener("click", openPalette);
}

/* -------------------------------------------------------------------- boot */

initTheme();
wireNav();
wireNavCurrent();
wirePaletteShortcut();
document.getElementById("theme-slot").append(themeRadiogroup({ label: "Appearance", compact: true }));

startRouter({
  mount: document.getElementById("main"),
  pages: PAGES,
  notFound: {
    title: "Not found",
    render(outlet) {
      const h1 = el("h1", { tabindex: "-1" }, "Page not found");
      const note = el("div", { class: "banner banner--warn", role: "note", style: "margin-top:16px" },
        el("span", { class: "banner__icon", "aria-hidden": "true" }, icon("alert", 17)),
        el("div", { class: "banner__body" },
          el("strong", { class: "banner__title" }, "No screen exists at this address"),
          el("span", {}, "Use the sidebar or the command palette (Ctrl/⌘ + K) to navigate."),
          " "));
      const go = el("p", { style: "margin-top:16px" },
        el("a", { href: "#/overview" }, "← Back to Overview"));
      outlet.append(h1, note, go);
    },
  },
});

// Sample-mode reminder (once per session)
if (!sessionStorage.getItem("nd-cc-sample-note")) {
  try { sessionStorage.setItem("nd-cc-sample-note", "1"); } catch { /* ignore */ }
  toast("Sample prototype: all data is illustrative — no backend, no state changes.", 5200);
}
