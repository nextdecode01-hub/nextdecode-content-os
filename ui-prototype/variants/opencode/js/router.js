/* router.js — dependency-free hash router for the SPA shell.
   URLs look like #/workflows/run-06 — route + optional param (deep links to a
   specific run, review or research package). Unknown routes render a 404 page
   (also demonstrates the error-state design). */

let routes = {};
let outlet = null;
let lastKey = null;
let fallbackPage = null;

export function parseHash() {
  const raw = window.location.hash.replace(/^#\/?/, "");
  const [route = "", param = ""] = raw.split("/");
  return { route: route || null, param: param || null };
}

export function navigate(route, param = null) {
  const target = param ? `#/${route}/${param}` : `#/${route}`;
  if (window.location.hash === target) {
    render(); // same hash — re-render explicitly (e.g. re-open drawer)
  } else {
    window.location.hash = target;
  }
}

export function currentRoute() {
  return parseHash().route;
}

function render() {
  const { route, param } = parseHash();
  const page = routes[route] || fallbackPage;
  if (!page || !outlet) return;

  outlet.replaceChildren();

  try {
    page.render(outlet, param);
  } catch (err) {
    outlet.replaceChildren();
    const h1 = document.createElement("h1");
    h1.textContent = "Render error";
    h1.tabIndex = -1;
    const p = document.createElement("p");
    p.className = "text-danger";
    p.textContent = `The ${route || "requested"} page failed to render in this browser.`;
    outlet.append(h1, p);
    console.error("Render failed:", err);
  }

  document.title = `${page.title} · NEXTDECODE Control Center (sample)`;
  document.dispatchEvent(new CustomEvent("nd:route", { detail: { route: routes[route] ? route : "__notfound", param } }));

  // Move focus to the page heading on route change (not on param-only changes,
  // which open a drawer that manages its own focus).
  const key = `${route}|${param}`;
  if (key !== lastKey && (!route || !param || lastKey === null || (lastKey || "").split("|")[0] !== route)) {
    const h1 = outlet.querySelector("h1");
    if (h1) h1.focus({ preventScroll: true });
  }
  lastKey = key;
}

export function startRouter({ mount, pages, notFound }) {
  outlet = mount;
  routes = pages;
  fallbackPage = notFound;
  window.addEventListener("hashchange", render);
  render();
}
