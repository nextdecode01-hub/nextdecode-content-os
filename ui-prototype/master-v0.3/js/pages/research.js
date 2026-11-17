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

function claimWorkstation(pkg) {
  const cards = pkg.claims.map((claim) => {
    const blocked = BLOCKING.includes(claim.status);
    const evidence = claim.evidence || [];
    const sourceCards = evidence.length
      ? evidence.map((item) => el("div", {
          class: "surface-subtle",
          style: "padding:10px;border-radius:10px;min-width:0",
        },
          el("div", { class: "row", style: "justify-content:space-between;gap:8px;align-items:center" },
            el("strong", {}, item.source),
            el("span", { class: "text-faint mono" }, `Rank ${item.rank ?? "not recorded"} · score ${item.score ?? "not recorded"}`)),
          el("div", { class: "text-muted", style: "font-size:var(--fs-xs);margin-top:6px" },
            `Published: ${item.published || "not recorded"} · URL: ${item.url || "not recorded"}`),
          item.signals ? el("div", { class: "text-faint", style: "font-size:var(--fs-xs);margin-top:5px" },
            `Title relevance ${item.signals.title_relevance} · Source relevance ${item.signals.source_relevance} · Freshness ${item.signals.freshness} · Engagement ${item.signals.engagement}`) : null))
      : [el("div", { class: "text-faint" }, "No evidence records attached to this claim.")];

    return el("article", {
      class: "surface-card stack",
      style: "padding:14px;gap:12px;border:1px solid var(--border-subtle);border-radius:12px",
    },
      el("div", { class: "row", style: "justify-content:space-between;align-items:flex-start;gap:10px" },
        el("div", { class: "stack", style: "gap:4px" },
          el("span", { class: "text-faint mono", style: "font-size:var(--fs-xs)" }, claim.id),
          el("strong", {}, claim.text)),
        badge(claim.status)),
      el("div", { class: "row", style: "gap:8px;flex-wrap:wrap" },
        badge(`${evidence.length} evidence record(s)`),
        badge(blocked ? "Blocks evidence gate" : "Non-blocking status")),
      el("div", { class: "stack", style: "gap:8px" },
        el("div", { class: "text-faint", style: "font-size:var(--fs-xs);font-weight:650;text-transform:uppercase;letter-spacing:.06em" }, "Source provenance records"),
        ...sourceCards),
      el("div", { class: "text-muted", style: "font-size:var(--fs-xs);padding-top:8px;border-top:1px solid var(--border-subtle)" },
        "Script linkage: not recorded in this sample. No downstream script impact is inferred." ));
  });

  const totalEvidence = pkg.claims.reduce((sum, claim) => sum + (claim.evidence?.length || 0), 0);
  const blocking = pkg.claims.filter((claim) => BLOCKING.includes(claim.status)).length;
  const corroborated = pkg.claims.filter((claim) => (claim.evidence?.length || 0) >= 2).length;
  return el("section", { class: "stack", style: "gap:14px" },
    el("div", { class: "grid grid--3", style: "gap:10px" },
      ...[
        ["Atomic claims", pkg.claims.length],
        ["Evidence records", totalEvidence],
        ["Claims with 2+ records", corroborated],
      ].map(([label, value]) => el("div", { class: "surface-subtle", style: "padding:12px;border-radius:10px" },
        el("div", { class: "text-faint", style: "font-size:var(--fs-xs)" }, label),
        el("strong", { style: "font-size:1.25rem" }, String(value)))),
    ),
    blocking ? banner({
      tone: "danger", glyph: "alert",
      title: `${blocking} blocking claim(s)`,
      body: "Unverified, outdated, conflicting and unsupported statuses remain evidence-gate blockers. Source count alone does not clear a claim.",
    }) : banner({
      tone: "info", glyph: "check",
      title: "No blocking claim status recorded",
      body: "This is a sample-data status view, not an independent verification of the underlying sources.",
    }),
    el("div", { class: "stack", style: "gap:10px" }, ...cards),
  );
}

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
        el("div", { class: "drawer__section stack" },
          el("h3", {}, "Evidence workstation"),
          el("p", { class: "text-muted", style: "font-size:var(--fs-xs)" }, "Atomic claim review with the provenance and scoring fields present in this sample dataset. URLs are displayed as recorded and are not independently verified here."),
          claimWorkstation(pkg)),
        el("div", { class: "drawer__section" },
          el("h3", {}, "Claims register"),
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
