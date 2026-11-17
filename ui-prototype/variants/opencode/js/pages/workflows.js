/* workflows.js — execution runs with state filters, sortable table and a
   run-detail drawer (deep-linkable: #/workflows/r05). States use the engine
   vocabulary: in_progress | promoting | ok | failed | blocked. */

import { el } from "../dom.js";
import { statusInfo } from "../status.js";
import {
  runs, projectById, tasksForRun, reviewsForProject, NOW_MS,
} from "../data.js";
import { store } from "../store.js";
import {
  pageHead, badge, searchInput, chipGroup, dataTable, drawer, kv, banner,
  timeline, relTime,
} from "../components.js";
import { navigate } from "../router.js";

const STATE_ORDER = ["in_progress", "promoting", "ok", "failed", "blocked"];
const SORT_DEFAULT = { key: "started_at", dir: "desc" };

function filters() {
  if (!store.filters.workflows) store.filters.workflows = { q: "", state: "all" };
  if (!store.filters.workflowsSort) store.filters.workflowsSort = { ...SORT_DEFAULT };
  return store.filters.workflows;
}

function currentStage(run) {
  const order = ["research", "script", "visuals", "voice", "render", "review_package"];
  const active = run.stages.find((s) => ["running", "queued", "blocked", "failed", "warn"].includes(s.state));
  if (active) {
    const idx = order.indexOf(active.name);
    return idx >= 0 ? `${idx + 1}/${order.length} · ${active.name}` : active.name;
  }
  return `${order.length}/${order.length} · done`;
}

export default {
  id: "workflows",
  title: "Workflows",
  render(main, param) {
    const f = filters();
    let resultsRegion = null;

    function runDrawer(run) {
      const project = projectById(run.project_id);
      const review = reviewsForProject(run.project_id)[0] || null;
      const stageTimeline = run.stages.map((s) => ({
        at: s.started_at || run.started_at,
        tone: s.state === "ok" ? "ok" : s.state === "failed" ? "danger" : s.state === "warn" || s.state === "blocked" ? "warn" : s.state === "running" ? "running" : "neutral",
        glyph: s.state === "ok" ? "check" : s.state === "failed" ? "close" : s.state === "warn" ? "alert" : s.state === "running" ? "play" : "clock",
        title: s.name,
        detail: [
          s.started_at && s.finished_at ? `${relTime(s.started_at, NOW_MS)} · finished` : s.state === "running" ? "running now" : s.state === "queued" ? "queued" : null,
          s.note,
        ].filter(Boolean).join(" — "),
      }));

      const relatedTasks = tasksForRun(run.id);

      return el("div", { class: "stack" },
        el("div", { class: "drawer__section" },
          el("h3", {}, "Run state"),
          kv([
            { k: "State", v: badge(run.state) },
            ...(run.error_code ? [{ k: "Error code", v: el("span", { class: "reason-code" }, run.error_code) }] : []),
            { k: "Trigger", v: run.trigger },
            { k: "Attempts", v: `${run.attempts}/${run.max_attempts}` },
            { k: "Started", v: relTime(run.started_at) },
            { k: run.finished_at ? "Finished" : "Updated", v: run.finished_at ? relTime(run.finished_at) : "in flight" },
            ...(run.promotion ? [{ k: "Promotion", v: `${statusInfo(run.promotion.status).label}${run.promotion.completed_at ? ` · ${relTime(run.promotion.completed_at)}` : ""}` }] : []),
          ])),
        el("div", { class: "drawer__section" },
          el("h3", {}, "Stage timeline"),
          timeline(stageTimeline)),
        relatedTasks.length ? el("div", { class: "drawer__section" },
          el("h3", {}, "Related autonomy tasks"),
          el("div", { class: "stack", style: "gap:8px" }, relatedTasks.map((t) => el("div", { class: "stack", style: "flex-direction:row; gap:8px; align-items:center; flex-wrap:wrap" },
            badge(t.state),
            el("span", { class: "mono" }, t.kind),
            el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" },
              `attempts ${t.attempts}/${t.max_attempts}${t.lease_owner ? ` · lease ${t.lease_owner}` : ""}${t.error_code ? ` · ${t.error_code}` : ""}`),
          )))) : null,
        el("div", { class: "drawer__section" },
          el("h3", {}, "Linked records"),
          kv([
            { k: "Project", v: el("button", { class: "btn btn--sm", type: "button", on: { click: () => navigate("projects") } }, project?.title || run.project_id) },
            ...(review ? [{ k: "Review", v: el("button", { class: "btn btn--sm", type: "button", on: { click: () => navigate("review", review.id) } }, `Open ${review.id}`) }] : []),
          ])),
        run.state === "blocked" ? banner({ tone: "warn", glyph: "lock", title: "Blocked — not failed", body: "Blocked runs are waiting on a dependency (e.g. human input or a parent task), not necessarily erroring. Recovery is automatic once the dependency resolves." }) : null,
      );
    }

    function applyFilters() {
      const q = f.q.trim().toLowerCase();
      let rows = runs.filter((r) => {
        if (f.state !== "all" && r.state !== f.state) return false;
        if (!q) return true;
        const p = projectById(r.project_id);
        return [r.id, p?.title, r.error_code, r.trigger].join(" ").toLowerCase().includes(q);
      });
      const { key, dir } = store.filters.workflowsSort;
      const mul = dir === "asc" ? 1 : -1;
      rows = [...rows].sort((a, b) => {
        let va = a[key]; let vb = b[key];
        if (key === "project") { va = projectById(a.project_id)?.title || ""; vb = projectById(b.project_id)?.title || ""; }
        if (key === "state") { va = STATE_ORDER.indexOf(a.state); vb = STATE_ORDER.indexOf(b.state); }
        if (typeof va === "string") return va.localeCompare(vb) * mul;
        return ((va ?? "") > (vb ?? "") ? 1 : (va ?? "") < (vb ?? "") ? -1 : 0) * mul;
      });
      return rows;
    }

    function openRun(run) {
      drawer({
        title: `Run ${run.id}`,
        meta: `${projectById(run.project_id)?.title || run.project_id} · ${run.trigger}`,
        content: runDrawer(run),
        onClose: () => history.replaceState(null, "", "#/workflows"),
      });
    }

    function renderResults() {
      const rows = applyFilters();
      resultsRegion.replaceChildren(dataTable({
        caption: `Execution runs — ${rows.length} of ${runs.length} shown (sample data)`,
        columns: [
          { key: "id", label: "Run", sortable: true, render: (r) => el("span", {}, el("span", { class: "rowlink mono" }, r.id), el("span", { class: "text-faint", style: "display:block;font-size:var(--fs-xs)" }, r.trigger)) },
          { key: "project", label: "Project", sortable: true, render: (r) => projectById(r.project_id)?.title || r.project_id },
          { key: "state", label: "State", sortable: true, render: (r) => el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" }, badge(r.state), r.error_code ? el("span", { class: "text-danger mono", style: "font-size:var(--fs-xs)" }, r.error_code) : null) },
          { key: "stage", label: "Stage progress", sortable: false, render: (r) => currentStage(r) },
          { key: "attempts", label: "Attempts", sortable: true, align: "right", render: (r) => `${r.attempts}/${r.max_attempts}` },
          { key: "started_at", label: "Started", sortable: true, render: (r) => relTime(r.started_at) },
          { key: "finished_at", label: "Finished", sortable: false, render: (r) => (r.finished_at ? relTime(r.finished_at) : el("span", { class: "text-faint" }, "in flight")) },
        ],
        rows,
        sort: store.filters.workflowsSort,
        onSort: (s) => { store.filters.workflowsSort = s; renderResults(); },
        onRowActivate: {
          aria: (r) => `Open run ${r.id}`,
          activate: openRun,
        },
        emptyMessage: "No runs match the current filters.",
      }));
    }

    resultsRegion = el("div", {});
    renderResults();

    main.append(
      pageHead({
        title: "Workflows",
        sub: "Execution runs with retries, failures and blocked states. Runs are engine executions; review decisions are human-controlled and shown separately under Review & Approvals.",
      }),
      el("div", { class: "filterbar" },
        searchInput({ label: "Search runs", value: f.q, placeholder: "Run id, project, error code…", class: "search--table", onInput: (v) => { f.q = v; renderResults(); } }),
        chipGroup({
          label: "Filter by state", name: "state", value: f.state,
          options: ["all", ...STATE_ORDER].map((s) => ({
            value: s,
            label: s === "all" ? "All" : statusInfo(s).label,
            count: s === "all" ? runs.length : runs.filter((r) => r.state === s).length,
          })),
          onChange: (v) => { f.state = v; renderResults(); },
        }),
      ),
      resultsRegion,
      el("div", { class: "grid grid--2" },
        banner({ tone: "warn", glyph: "alert", title: "Blocked ≠ failed", body: "A blocked run (r08) is waiting on a human dependency with error_code=dependency_failed. Failed runs (r06) exhausted their retry budget." }),
        banner({ tone: "info", glyph: "info", title: "Retries are engine-managed", body: "Attempts/max_attempts and leases come from the autonomy task queue. The dashboard never restarts runs." }),
      ),
    );

    if (param) {
      const run = runs.find((r) => r.id === param);
      if (run) openRun(run);
    }
  },
};
