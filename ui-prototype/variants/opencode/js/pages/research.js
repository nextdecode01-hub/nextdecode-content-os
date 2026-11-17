/* research.js — research packages, source hygiene and claim verification.
   Blocking claim statuses (unverified | outdated | conflicting | unsupported)
   are highlighted because they become publish violations downstream
   (evidence_unsupported_status). Deep-linkable: #/research/rp03. */

import { el } from "../dom.js";
import { statusInfo } from "../status.js";
import {
  research, projectById, NOW_MS,
} from "../data.js";
import { store } from "../store.js";
import {
  pageHead, badge, searchInput, chipGroup, dataTable, drawer, kv, banner,
  relTime,
} from "../components.js";

const BLOCKING = ["unverified", "outdated", "conflicting", "unsupported"];
const SORT_DEFAULT = { key: "updated_at", dir: "desc" };

function filters() {
  if (!store.filters.research) store.filters.research = { q: "", status: "all" };
  if (!store.filters.researchSort) store.filters.researchSort = { ...SORT_DEFAULT };
  return store.filters.research;
}

function claimStats(pkg) {
  const total = pkg.claims.length;
  const passing = pkg.claims.filter((c) => !BLOCKING.includes(c.status)).length;
  const blocking = total - passing;
  return { total, passing, blocking };
}

export default {
  id: "research",
  title: "Research",
  render(main, param) {
    const f = filters();
    let resultsRegion = null;

    function packageDrawer(pkg) {
      const project = projectById(pkg.project_id);

      const claimsTable = dataTable({
        caption: `Claims in ${pkg.id} (sample)`,
        columns: [
          { key: "text", label: "Claim", render: (c) => el("span", {}, c.text) },
          { key: "status", label: "Status", render: (c) => badge(c.status) },
          { key: "evidence", label: "Evidence", align: "right", render: (c) => `${c.evidence.length} source(s)` },
          { key: "top", label: "Top source", render: (c) => { const e = c.evidence[0]; return e ? `${e.source} · score ${e.score}` : "—"; } },
        ],
        rows: pkg.claims,
        stack: true,
        emptyMessage: "No claims recorded.",
      });

      const evidenceRows = pkg.claims.flatMap((c) => c.evidence.map((e) => ({ claim: c, e })));
      const signalsTable = dataTable({
        caption: "Evidence signals for the top-ranked source of each claim (sample)",
        columns: [
          { key: "claim", label: "Claim", render: (r) => `${r.claim.id} — ${r.claim.text.slice(0, 44)}…` },
          { key: "source", label: "Source" },
          { key: "published", label: "Published" },
          { key: "score", label: "Score", align: "right" },
          { key: "rank", label: "Rank", align: "right", render: (r) => r.e.rank?.toFixed(1) },
          { key: "signals", label: "Signals", render: (r) => `t+r:${r.e.signals.title_relevance + r.e.signals.source_relevance} · fresh:${r.e.signals.freshness.toFixed(1)} · eng:${r.e.signals.engagement.toFixed(1)}` },
        ],
        rows: evidenceRows,
        stack: true,
        emptyMessage: "No evidence recorded.",
      });

      return el("div", { class: "stack" },
        el("div", { class: "drawer__section" },
          el("h3", {}, "Package"),
          kv([
            { k: "Project", v: project?.title || pkg.project_id },
            { k: "Status", v: badge(pkg.status) },
            { k: "Sources", v: `${pkg.source_count} · primary checked: ${pkg.primary_source_checked ? "yes" : "no"} · two-source rule: ${pkg.two_sources_checked ? "pass" : "fail"}` },
            { k: "Freshness", v: `${pkg.freshness_days}d · updated ${relTime(pkg.updated_at)}` },
          ])),
        el("div", { class: "drawer__section" },
          el("h3", {}, "Claims"),
          claimsTable),
        pkg.claims.some((c) => BLOCKING.includes(c.status))
          ? banner({
              tone: "danger", glyph: "lock", title: "Blocking claims present",
              body: "Publish authorization requires zero claims with status unverified, outdated, conflicting or unsupported. Resolve evidence before packaging for review.",
            })
          : el("div", { class: "drawer__section" },
              el("h3", {}, "Downstream effect"),
              kv([{ k: "Publish gate", v: "No blocking claims — evidence check can pass." }])),
        el("div", { class: "drawer__section" },
          el("h3", {}, "Evidence signals"),
          signalsTable),
      );
    }

    function applyFilters() {
      const q = f.q.trim().toLowerCase();
      let rows = research.filter((pkg) => {
        if (f.status !== "all" && pkg.status !== f.status) return false;
        if (!q) return true;
        const p = projectById(pkg.project_id);
        return [pkg.topic, pkg.id, p?.title, pkg.claims.map((c) => c.text).join(" ")].join(" ").toLowerCase().includes(q);
      });
      const { key, dir } = store.filters.researchSort;
      const mul = dir === "asc" ? 1 : -1;
      rows = [...rows].sort((a, b) => {
        let va = a[key]; let vb = b[key];
        if (key === "claims") { va = claimStats(a).blocking; vb = claimStats(b).blocking; }
        if (key === "project") { va = projectById(a.project_id)?.title || ""; vb = projectById(b.project_id)?.title || ""; }
        if (typeof va === "string") return va.localeCompare(vb) * mul;
        return ((va ?? "") > (vb ?? "") ? 1 : (va ?? "") < (vb ?? "") ? -1 : 0) * mul;
      });
      return rows;
    }

    function renderResults() {
      const rows = applyFilters();
      resultsRegion.replaceChildren(dataTable({
        caption: `Research packages — ${rows.length} of ${research.length} shown (sample data)`,
        columns: [
          { key: "topic", label: "Package", sortable: true, render: (p) => el("span", {}, el("span", { class: "rowlink" }, p.topic), el("span", { class: "text-faint mono", style: "display:block;font-size:var(--fs-xs)" }, p.id)) },
          { key: "project", label: "Project", sortable: true, render: (p) => projectById(p.project_id)?.title || p.project_id },
          { key: "status", label: "Status", sortable: true, render: (p) => badge(p.status) },
          { key: "sources", label: "Sources", align: "right", sortable: true, render: (p) => el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center; justify-content:flex-end" }, String(p.source_count), el("span", { class: p.two_sources_checked ? "text-ok" : "text-warn", title: p.two_sources_checked ? "Two-source rule satisfied" : "Two-source rule not yet satisfied", "aria-label": p.two_sources_checked ? "Two-source rule satisfied" : "Two-source rule not satisfied" }, p.two_sources_checked ? "✓2" : "✗2")) },
          { key: "claims", label: "Claims", sortable: true, align: "right", render: (p) => { const s = claimStats(p); return s.blocking ? el("span", { class: "text-danger" }, `${s.passing}/${s.total} · ${s.blocking} blocking`) : `${s.passing}/${s.total}`; } },
          { key: "updated_at", label: "Updated", sortable: true, render: (p) => relTime(p.updated_at) },
        ],
        rows,
        sort: store.filters.researchSort,
        onSort: (s) => { store.filters.researchSort = s; renderResults(); },
        onRowActivate: {
          aria: (p) => `Open research package ${p.topic}`,
          activate: (p) => drawer({
            title: p.topic,
            meta: `${p.id} · ${p.source_count} sources · ${relTime(p.updated_at)}`,
            content: packageDrawer(p),
            onClose: () => history.replaceState(null, "", "#/research"),
          }),
        },
        emptyMessage: "No research packages match the current filters.",
      }));
    }

    resultsRegion = el("div", {});
    renderResults();

    const withBlocking = research.filter((p) => claimStats(p).blocking).length;

    main.append(
      pageHead({
        title: "Research",
        sub: "Research packages with source counts, the two-source rule and claim verification. Claim statuses map directly to publish gates downstream.",
      }),
      el("div", { class: "filterbar" },
        searchInput({ label: "Search packages", value: f.q, placeholder: "Topic, claim text, project…", class: "search--table", onInput: (v) => { f.q = v; renderResults(); } }),
        chipGroup({
          label: "Filter by status", name: "status", value: f.status,
          options: ["all", "verified", "needs_review"].map((s) => ({
            value: s,
            label: s === "all" ? "All" : statusInfo(s).label,
            count: s === "all" ? research.length : research.filter((p) => p.status === s).length,
          })),
          onChange: (v) => { f.status = v; renderResults(); },
        }),
      ),
      resultsRegion,
      banner({
        tone: withBlocking ? "warn" : "info", glyph: "alert",
        title: withBlocking ? `${withBlocking} package(s) carry blocking claims` : "All claims verified",
        body: "Blocking statuses: unverified, outdated, conflicting, unsupported. Packages with blocking claims cannot pass publish authorization (evidence_unsupported_status).",
      }),
    );

    if (param) {
      const pkg = research.find((r) => r.id === param);
      if (pkg) {
        drawer({
          title: pkg.topic,
          meta: `${pkg.id} · ${pkg.source_count} sources · ${relTime(pkg.updated_at)}`,
          content: packageDrawer(pkg),
          onClose: () => history.replaceState(null, "", "#/research"),
        });
      }
    }
  },
};
