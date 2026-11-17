/* projects.js — portfolio table with search, status/stage filters and sorting.
   Row activation opens a project detail drawer (deep-linkable is not required
   here; the drawer is interaction-only). */

import { el } from "../dom.js";
import { STAGE_ORDER, statusInfo } from "../status.js";
import {
  projects, runById, reviewById, publishFor, researchFor, runForProject,
} from "../data.js";
import { store } from "../store.js";
import {
  pageHead, badge, searchInput, chipGroup, selectControl, dataTable,
  drawer, stageTrack, kv, banner, relTime,
} from "../components.js";
import { navigate } from "../router.js";

const SORT_DEFAULT = { key: "updated_at", dir: "desc" };

function portfolioBrief() {
  const counts = {
    active: projects.filter((p) => p.status === "active").length,
    attention: projects.filter((p) => p.status === "needs_attention").length,
    blocked: projects.filter((p) => p.status === "blocked").length,
    completed: projects.filter((p) => p.status === "completed").length,
  };
  const flagged = counts.attention + counts.blocked;
  return el("section", { class: "ops-command portfolio-brief", "aria-label": "Project portfolio summary" },
    el("div", { class: "ops-command__head" },
      el("div", {},
        el("div", { class: "ops-command__eyebrow" }, "PORTFOLIO CONTROL · CROSS-PROJECT VIEW"),
        el("h2", {}, "Every project. One operating picture."),
        el("p", {}, "Track ownership, production stage and project health together. Open any project to inspect its linked research, runs, reviews and distribution record.")),
      el("span", { class: `badge badge--${flagged ? "warn" : "ok"}` }, el("span", { class: "badge__dot" }), flagged ? `${flagged} need attention` : "Portfolio clear")),
    el("div", { class: "ops-command__grid" },
      briefProjectMetric("Active", counts.active, "in progress", "ok"),
      briefProjectMetric("Needs attention", counts.attention, "investigate next step", "warn"),
      briefProjectMetric("Blocked", counts.blocked, "dependency / gate", "danger"),
      briefProjectMetric("Completed", counts.completed, "recorded complete", "ok")));
}

function briefProjectMetric(label, value, detail, tone) {
  return el("div", { class: `ops-command__metric ops-command__metric--${tone}` },
    el("span", { class: "ops-command__metric-label" }, label),
    el("strong", {}, String(value).padStart(2, "0")),
    el("small", {}, detail));
}

function filters() {
  if (!store.filters.projects) store.filters.projects = { q: "", status: "all", stage: "all" };
  if (!store.filters.projectsSort) store.filters.projectsSort = { ...SORT_DEFAULT };
  return store.filters.projects;
}

function applyFilters() {
  const f = filters();
  const q = f.q.trim().toLowerCase();
  let rows = projects.filter((p) => {
    if (f.status !== "all" && p.status !== f.status) return false;
    if (f.stage !== "all" && p.stage !== f.stage) return false;
    if (!q) return true;
    return [p.title, p.topic, p.pillar, p.id, p.owner].join(" ").toLowerCase().includes(q);
  });

  const { key, dir } = store.filters.projectsSort;
  const mul = dir === "asc" ? 1 : -1;
  rows = [...rows].sort((a, b) => {
    let va = a[key]; let vb = b[key];
    if (key === "stage") { va = STAGE_ORDER.indexOf(a.stage); vb = STAGE_ORDER.indexOf(b.stage); }
    if (typeof va === "string") return va.localeCompare(vb) * mul;
    return ((va ?? "") > (vb ?? "") ? 1 : (va ?? "") < (vb ?? "") ? -1 : 0) * mul;
  });
  return rows;
}

export default {
  id: "projects",
  title: "Projects",
  render(main) {
    const f = filters();
    let resultsRegion = null;

    function stageCell(p) {
      return stageTrack(STAGE_ORDER, STAGE_ORDER.indexOf(p.stage));
    }

    function projectDrawer(p, close) {
      const run = runById(p.run_id);
      const review = reviewById(p.review_id);
      const pub = publishFor(p.id);
      const rp = researchFor(p.id);
      const projectRuns = runForProject(p.id);

      const runList = el("div", { class: "stack", style: "gap:6px" },
        projectRuns.map((r) => el("div", { class: "stack", style: "gap:2px" },
          el("div", { class: "stack", style: "gap:4px; flex-direction:row; align-items:center" },
            badge(r.state),
            el("span", { class: "mono text-nowrap" }, r.id),
            el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" },
              r.error_code ? `error_code=${r.error_code}` : r.trigger)),
        )));

      return el("div", { class: "stack" },
        el("div", { class: "drawer__section" },
          el("h3", {}, "Identity"),
          kv([
            { k: "Topic", v: p.topic },
            { k: "Pillar", v: p.pillar },
            { k: "Owner", v: p.owner },
            { k: "Updated", v: relTime(p.updated_at) },
            { k: "Note", v: p.note },
          ])),
        el("div", { class: "drawer__section" },
          el("h3", {}, "Linked records"),
          kv([
            { k: "Run(s)", v: runList },
            { k: "Review", v: review ? el("button", { class: "btn btn--sm", type: "button", on: { click: () => { close(); navigate("review", review.id); } } }, `Open ${review.id} (${statusInfo(review.status).label})`) : "—" },
            { k: "Research", v: rp ? `${rp.id} — ${statusInfo(rp.status).label}` : "—" },
            { k: "Publish", v: pub ? `${statusInfo(pub.state).label}${pub.reason_code ? ` (${pub.reason_code})` : ""}` : "—" },
          ])),
        run ? el("div", { class: "drawer__section" },
          el("h3", {}, "Latest run"),
          kv([
            { k: "State", v: badge(run.state) },
            { k: "Attempts", v: `${run.attempts}/${run.max_attempts}` },
            { k: "Started", v: relTime(run.started_at) },
            ...(run.promotion ? [{ k: "Promotion", v: statusInfo(run.promotion.status).label }] : []),
          ])) : null,
        banner({
          tone: "info", glyph: "info",
          body: "Actions on projects are not available in the sample — the Control Center is display-only in this prototype.",
        }),
      );
    }

    function renderResults() {
      const rows = applyFilters();
      resultsRegion.replaceChildren(dataTable({
        caption: `Projects — ${rows.length} of ${projects.length} shown (sample data)`,
        columns: [
          { key: "title", label: "Project", sortable: true, render: (p) => el("span", {}, el("span", { class: "rowlink" }, p.title), el("span", { class: "text-faint", style: "display:block;font-size:var(--fs-xs)" }, `${p.pillar} · ${p.id}`)) },
          { key: "stage", label: "Stage", sortable: true, render: stageCell },
          { key: "status", label: "Status", sortable: true, render: (p) => badge(p.status) },
          { key: "owner", label: "Owner", sortable: true },
          { key: "run_id", label: "Latest run", sortable: false, render: (p) => { const r = runById(p.run_id); return r ? el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" }, badge(r.state), el("span", { class: "mono" }, r.id)) : "—"; } },
          { key: "updated_at", label: "Updated", sortable: true, render: (p) => relTime(p.updated_at) },
        ],
        rows,
        sort: store.filters.projectsSort,
        onSort: (s) => { store.filters.projectsSort = s; renderResults(); },
        onRowActivate: {
          aria: (p) => `Open details for project ${p.title}`,
          activate: (p) => drawer({
            title: p.title,
            meta: `${p.id} · ${p.pillar} · owner ${p.owner}`,
            content: projectDrawer(p, () => {}),
            onClose: () => history.replaceState(null, "", "#/projects"),
          }),
        },
        emptyMessage: "No projects match the current filters.",
      }));
    }

    resultsRegion = el("div", {});
    renderResults();

    main.append(
      pageHead({
        title: "Projects",
        sub: "Portfolio with stage, status, owner and health. Stages follow the engine pipeline: research → script → visuals → voice → render → review → publish.",
      }),
      portfolioBrief(),
      el("div", { class: "filterbar" },
        searchInput({ label: "Search projects", value: f.q, placeholder: "Title, topic, pillar, owner…", class: "search--table", onInput: (v) => { f.q = v; renderResults(); } }),
        chipGroup({
          label: "Filter by status", name: "status", value: f.status,
          options: ["all", "active", "needs_attention", "blocked", "completed"].map((s) => ({
            value: s,
            label: s === "all" ? "All" : statusInfo(s).label,
            count: s === "all" ? projects.length : projects.filter((p) => p.status === s).length,
          })),
          onChange: (v) => { f.status = v; renderResults(); },
        }),
        selectControl({
          label: "Stage", value: f.stage,
          options: [{ value: "all", label: "All stages" }, ...STAGE_ORDER.map((s) => ({ value: s, label: statusInfo(s).label }))],
          onChange: (v) => { f.stage = v; renderResults(); },
        }),
      ),
      resultsRegion,
      banner({
        tone: "info", glyph: "info",
        body: "Rows are interactive — activate a row for details. Sample data only; nothing here mutates project state.",
      }),
    );
  },
};
