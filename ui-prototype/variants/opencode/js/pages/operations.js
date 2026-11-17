/* operations.js — workers, heartbeat, queue depth, autonomy tasks, incidents,
   model health and the P0 governance gate display. Read-only operator view. */

import { el, fmtNum } from "../dom.js";
import { statusInfo } from "../status.js";
import {
  workers, incidents, tasks, models, governance, projectById, NOW_MS,
} from "../data.js";
import {
  pageHead, panel, statCard, badge, banner, dataTable, kv,
  relTime, drawer,
} from "../components.js";
import { navigate } from "../router.js";
import { toast } from "../toasts.js";

const TASK_STATES = ["queued", "running", "succeeded", "failed", "blocked"];

export default {
  id: "operations",
  title: "Operations",
  render(main) {
    const queueCounts = {};
    tasks.forEach((t) => { queueCounts[t.state] = (queueCounts[t.state] || 0) + 1; });
    const runningHealthy = tasks.filter((t) => t.state === "running" && !t.stale_lease).length;
    const runningStale = tasks.filter((t) => t.state === "running" && t.stale_lease).length;
    const failedTasks = tasks.filter((t) => t.state === "failed").length;

    let tasksRegion = el("div", {});

    function taskDrawer(t) {
      return el("div", { class: "stack" },
        el("div", { class: "drawer__section" },
          el("h3", {}, "Task"),
          kv([
            { k: "Task id", v: el("span", { class: "mono", style: "font-size:var(--fs-xs)" }, t.id) },
            { k: "Kind", v: t.kind },
            { k: "State", v: badge(t.state) },
            { k: "Attempts", v: `${t.attempts}/${t.max_attempts}` },
            { k: "Priority", v: String(t.priority) },
            ...(t.lease_owner ? [{ k: "Lease", v: `${t.lease_owner} · until ${relTime(t.lease_until)}${t.stale_lease ? " (expired)" : ""}` }] : []),
            ...(t.not_before ? [{ k: "Not before", v: relTime(t.not_before) }] : []),
            ...(t.error_code ? [{ k: "Error code", v: el("span", { class: "reason-code" }, t.error_code) }] : []),
            ...(t.note ? [{ k: "Note", v: t.note }] : []),
          ])),
        t.project_id ? el("div", { class: "drawer__section" },
          el("h3", {}, "Linked records"),
          kv([
            { k: "Project", v: projectById(t.project_id)?.title || t.project_id },
            ...(t.run_id ? [{ k: "Run", v: el("button", { class: "btn btn--sm", type: "button", on: { click: () => navigate("workflows", t.run_id) } }, `Open ${t.run_id}`) }] : []),
          ])) : null,
        banner({
          tone: "info", glyph: "info",
          body: "Task recovery (lease reclaim, redrive) happens in the engine — the dashboard never mutates queue state.",
        }));
    }

    function renderTasks() {
      tasksRegion.replaceChildren(dataTable({
        caption: `Autonomy task queue — ${tasks.length} tasks (sample data)`,
        columns: [
          { key: "kind", label: "Task", sortable: true, render: (t) => el("span", {}, el("span", { class: "rowlink" }, t.kind), el("span", { class: "text-faint mono", style: "display:block;font-size:var(--fs-xs)" }, t.id.slice(0, 8) + "…")) },
          { key: "state", label: "State", sortable: true, render: (t) => el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" }, badge(t.state), t.error_code ? el("span", { class: "text-danger mono", style: "font-size:var(--fs-xs)" }, t.error_code) : null) },
          { key: "attempts", label: "Attempts", sortable: true, align: "right", render: (t) => `${t.attempts}/${t.max_attempts}` },
          { key: "lease", label: "Lease", sortable: false, render: (t) => t.lease_owner ? el("span", { class: t.stale_lease ? "text-warn" : "" }, `${t.lease_owner} · ${relTime(t.lease_until)}${t.stale_lease ? " (expired)" : ""}`) : t.not_before ? el("span", { class: "text-faint" }, `not_before ${relTime(t.not_before)}`) : el("span", { class: "text-faint" }, "—") },
          { key: "created_at", label: "Created", sortable: true, render: (t) => relTime(t.created_at) },
        ],
        rows: tasks,
        stack: true,
        onRowActivate: {
          aria: (t) => `Open task ${t.kind}`,
          activate: (t) => drawer({
            title: t.kind,
            meta: `${t.id.slice(0, 12)}… · ${statusInfo(t.state).label}`,
            content: taskDrawer(t),
            onClose: () => history.replaceState(null, "", "#/operations"),
          }),
        },
        emptyMessage: "Queue is empty.",
      }));
    }
    renderTasks();

    const workersPanel = panel({
      title: "Workers", meta: "heartbeat (sample)",
      actions: el("button", {
        class: "btn btn--sm", type: "button",
        on: { click: () => toast("Sample view — heartbeats are static sample data, not live.") },
      }, "Refresh"),
      flush: true,
      body: workers.map((w) => el("div", { class: `worker worker--${w.state}` },
        el("span", { class: "worker__glyph", "aria-hidden": "true" }, w.state === "healthy" ? "●" : w.state === "stale" ? "▲" : "○"),
        el("div", { class: "stack", style: "gap:1px; min-width:0" },
          el("span", { class: "worker__name" }, `${w.id} — ${w.kind}`),
          el("span", { class: "worker__meta" }, `${statusInfo(w.state).label} · last heartbeat ${relTime(w.last_heartbeat)} · ${w.detail}`))))
    });

    const incidentsPanel = panel({
      title: "Incidents", meta: `${incidents.length} in window`,
      body: el("div", { class: "stack" },
        incidents.map((i) => el("div", { class: "stack", style: "gap:6px" },
          el("div", { class: "stack", style: "flex-direction:row; gap:8px; align-items:center; flex-wrap:wrap" },
            badge(i.state),
            el("span", { class: "pill" }, `${i.severity} severity`),
            el("strong", { style: "font-size:var(--fs-sm)" }, i.title)),
          el("span", { class: "text-muted", style: "font-size:var(--fs-sm)" }, i.detail),
          el("button", { class: "btn btn--sm", type: "button", on: { click: () => navigate("workflows", i.run_id) } }, `Open run ${i.run_id}`)))),
    });

    const governancePanel = panel({
      title: "Governance gates", meta: "P0 status (display-only)",
      body: el("div", {},
        dataTable({
          caption: "P0 governance gates (sample display)",
          columns: [
            { key: "gate", label: "Gate" },
            { key: "status", label: "Status", render: (r) => badge(r.status) },
            { key: "detail", label: "Detail" },
          ],
          rows: [
            ...governance.decisions.map((d) => ({ gate: `Decision ${d.id}`, status: d.status, detail: d.topic })),
            { gate: governance.api_lc.label, status: governance.api_lc.status, detail: governance.api_lc.detail },
            { gate: "GOV-09", status: governance.gov09.status, detail: governance.gov09.detail },
            { gate: governance.m6p_entries.label, status: governance.m6p_entries.status, detail: governance.m6p_entries.detail },
            { gate: "Autonomous publishing", status: governance.autonomy_publish.status, detail: governance.autonomy_publish.detail },
          ],
          stack: true,
          emptyMessage: "No gates.",
        }),
        el("p", { class: "text-faint", style: "font-size:var(--fs-xs); margin-top:10px" }, governance.note)),
    });

    const modelsPanel = panel({
      title: "Model health", meta: "last provider check 20d ago (stale — sample)",
      body: dataTable({
        caption: "Provider model health (sample)",
        columns: [
          { key: "provider", label: "Provider" },
          { key: "model", label: "Model", render: (m) => el("span", { class: "mono", style: "font-size:var(--fs-xs)" }, m.model) },
          { key: "chain", label: "Chain", align: "right", render: (m) => `${m.chain} model(s)` },
          { key: "state", label: "Health", render: (m) => m.ok ? badge("healthy") : el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" }, badge(m.configured ? "failed" : "offline"), el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" }, m.error || "")) },
          { key: "latency", label: "Latency", align: "right", render: (m) => (m.latency_ms ? `${fmtNum(m.latency_ms)}ms` : "—") },
          { key: "checked_at", label: "Checked", render: (m) => relTime(m.checked_at) },
        ],
        rows: models,
        stack: true,
        emptyMessage: "No providers configured.",
      }),
    });

    main.append(
      pageHead({
        title: "Operations",
        sub: "Worker heartbeat, queue depth, incidents, recovery and model health. Operator actions (restart, redrive) belong to the engine — this view never mutates queue state.",
      }),
      el("div", { class: "grid grid--kpi" },
        statCard({ label: "Queue depth", value: String(tasks.length), hint: TASK_STATES.map((s) => `${queueCounts[s] || 0} ${s}`).join(" · "), glyph: "inbox" }),
        statCard({ label: "Running (healthy lease)", value: String(runningHealthy), hint: runningStale ? `${runningStale} running lease expired (stale)` : "no stale leases", tone: runningStale ? "warn" : "", glyph: "play" }),
        statCard({ label: "Failed (budget exhausted)", value: String(failedTasks), hint: failedTasks ? "see task t05 (voice_render 3/3)" : "none", tone: failedTasks ? "danger" : "", glyph: "alert" }),
        statCard({ label: "Incidents", value: String(incidents.length), hint: `${incidents.filter((i) => i.state === "open").length} open · ${incidents.filter((i) => i.state !== "open").length} recovering`, tone: "warn", glyph: "operations" }),
      ),

      el("div", { class: "grid grid--main", style: "margin-top: var(--sp-4)" },
        el("div", { class: "stack" },
          panel({
            title: "Autonomy task queue", meta: "app/autonomy vocabulary",
            body: tasksRegion,
          }),
          modelsPanel,
        ),
        el("div", { class: "stack" },
          workersPanel,
          incidentsPanel,
          governancePanel,
        ),
      ),
    );
  },
};
