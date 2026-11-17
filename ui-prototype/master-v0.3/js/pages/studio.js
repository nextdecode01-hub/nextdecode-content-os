/* studio.js — production workspace: script / storyboard-gate / visuals / voice
   / edit stages per content item, artifact readiness and the human checklist.
   Gate modes mirror STORYBOARD_GATE (off | skip | warn | require). */

import { el } from "../dom.js";
import { statusInfo } from "../status.js";
import {
  studio, projects,
} from "../data.js";
import { store } from "../store.js";
import {
  pageHead, badge, searchInput, chipGroup, dataTable, drawer, kv, banner,
  stageTrack, hashChip,
} from "../components.js";

const STAGE_KEYS = ["script", "visuals", "voice", "edit"];
const SORT_DEFAULT = { key: "project", dir: "asc" };

function filters() {
  if (!store.filters.studio) store.filters.studio = { q: "", readiness: "all" };
  if (!store.filters.studioSort) store.filters.studioSort = { ...SORT_DEFAULT };
  return store.filters.studio;
}

function artifactStats(item) {
  const total = item.artifacts.length;
  const ready = item.artifacts.filter((a) => a.state === "ready").length;
  const missing = item.artifacts.filter((a) => a.state === "missing").length;
  const draft = item.artifacts.filter((a) => a.state === "draft_only").length;
  return { total, ready, missing, draft };
}

function readinessBucket(item) {
  const s = artifactStats(item);
  if (s.missing) return "missing";
  if (s.draft || item.stages.visuals.quality === "draft_only") return "draft_only";
  return "review_ready";
}

function scriptCell(item) {
  const s = item.stages.script;
  if (!s.words) return badge(s.state === "in_progress" ? "in_progress" : "queued");
  const inRange = s.words >= s.word_range[0] && s.words <= s.word_range[1];
  return el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" },
    badge(s.state === "ok" || s.state === "changes_requested" ? s.state : "in_progress"),
    el("span", { class: `text-faint ${inRange ? "" : "text-warn"}`, style: "font-size:var(--fs-xs)", title: inRange ? "Within word range" : "Outside word range" },
      `${s.words}w ${inRange ? "" : "(out of range)"}`));
}

function storyboardCell(item) {
  const s = item.stages.storyboard;
  return el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" },
    el("span", { class: "pill", title: `STORYBOARD_GATE=${s.gate}` }, `gate:${s.gate}`),
    badge(s.review_status));
}

function visualsCell(item) {
  const s = item.stages.visuals;
  return el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" },
    badge(s.quality || s.state),
    el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" }, `${s.mode || "—"} · ${s.asset_count ?? 0} assets`));
}

function productionWorkstation(item) {
  const s = item.stages;
  const cards = [
    { key: "SCRIPT", title: "Narrative", state: s.script.state, detail: `${s.script.words ?? 0} words · target ${s.script.word_range?.[0] ?? "—"}–${s.script.word_range?.[1] ?? "—"}`, note: s.script.note || s.script.profile || "No script profile recorded" },
    { key: "STORYBOARD", title: "Scene plan", state: s.storyboard.review_status, detail: `Gate: ${s.storyboard.gate}`, note: "Storyboard acceptance is a separate human-controlled gate" },
    { key: "VISUALS", title: "Visual assets", state: s.visuals.quality || s.visuals.state, detail: `${s.visuals.asset_count ?? 0} assets · ${s.visuals.mode || "mode not set"}`, note: "Asset count is metadata, not proof that files are playable" },
    { key: "VOICE", title: "Narration", state: s.voice.state, detail: s.voice.provider || "Provider not recorded", note: s.voice.note || "Audio readiness is shown independently" },
    { key: "EDIT", title: "Assembly", state: s.edit.state, detail: s.edit.profile || "Edit profile not recorded", note: s.edit.note || "Render and timeline outputs remain artifact-gated" },
  ];
  const blocked = s.storyboard.review_status === "blocked" || s.visuals.quality === "draft_only";
  return el("div", { class: "drawer__section" },
    el("div", { style: "display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap" },
      el("h3", {}, "Production workstation"),
      el("span", { class: "pill" }, "Read-only · sample state")),
    el("div", { class: "grid grid--2" }, cards.map((c, i) => el("article", {
      class: "card stack", style: "gap:8px; min-width:0; padding:12px; border:1px solid var(--border); border-radius:var(--radius-md); background:var(--surface-1)"
    },
      el("div", { style: "display:flex; justify-content:space-between; align-items:center; gap:8px" },
        el("span", { class: "text-faint mono", style: "font-size:10px; letter-spacing:.1em" }, `${String(i + 1).padStart(2, "0")} · ${c.key}`), badge(c.state)),
      el("strong", {}, c.title),
      el("span", { style: "font-size:var(--fs-sm)" }, c.detail),
      el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" }, c.note)))),
    blocked ? banner({ tone: "warn", glyph: "lock", title: "Production is gated", body: "A blocked required storyboard or draft-only visual state must be resolved before this item can become approvable." }) : null,
    banner({ tone: "info", glyph: "info", body: "This workstation visualizes recorded stage metadata. It does not generate scripts, synthesize voice, fetch assets, render video or mutate pipeline state." }));
}

export default {
  id: "studio",
  title: "Studio",
  render(main) {
    const f = filters();
    let resultsRegion = null;

    function itemDrawer(item) {
      const p = projects.find((x) => x.id === item.project_id);
      const s = item.stages;
      const artifactsTable = dataTable({
        caption: `Artifacts for ${p.title} (sample)`,
        columns: [
          { key: "name", label: "Artifact" },
          { key: "path", label: "Path", render: (a) => el("span", { class: "mono", style: "font-size:var(--fs-xs)" }, a.path) },
          { key: "sha256", label: "SHA-256", render: (a) => hashChip(a.sha256) },
          { key: "state", label: "State", render: (a) => el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" }, badge(a.state), a.note ? el("span", { class: "text-faint", style: "font-size:var(--fs-xs)" }, a.note) : null) },
        ],
        rows: item.artifacts,
        stack: true,
        emptyMessage: "No artifacts yet.",
      });

      const checklist = el("div", { class: "checklist" },
        Object.entries({ ...item.checklist, note: undefined }).filter(([k]) => k !== "note").map(([key, val]) => {
          const labels = {
            primary_source_checked: "Primary source checked",
            two_sources_checked: "Two-source rule satisfied",
            claims_verified: "All claims verified (no blocking statuses)",
            rights_cleared: "Reuse rights cleared for all assets",
          };
          return el("div", { class: `checklist__item checklist__item--${val ? "ok" : "fail"}` },
            el("span", { class: "checklist__glyph", "aria-hidden": "true" }, val ? "✓" : "✗"),
            el("span", {}, labels[key] || key));
        }));

      return el("div", { class: "stack" },
        productionWorkstation(item),
        el("div", { class: "drawer__section" },
          el("h3", {}, "Stages"),
          kv([
            { k: "Pipeline", v: stageTrack(["research", "script", "visuals", "voice", "render", "review", "publish"], Math.max(1, STAGE_KEYS.indexOf("edit"))) },
            { k: "Script", v: `${s.script.words ?? "—"} words (range ${s.script.word_range?.[0]}–${s.script.word_range?.[1]}) · ${s.script.profile}${s.script.note ? ` · ${s.script.note}` : ""}` },
            { k: "Storyboard", v: el("span", { class: "stack", style: "flex-direction:row; gap:6px; align-items:center" }, el("span", { class: "pill" }, `gate:${s.storyboard.gate}`), badge(s.storyboard.review_status)) },
            { k: "Visuals", v: `${s.visuals.mode || "—"} · ${s.visuals.asset_count ?? 0} assets · ${statusInfo(s.visuals.quality || s.visuals.state).label}` },
            { k: "Voice", v: statusInfo(s.voice.state).label },
            { k: "Edit", v: statusInfo(s.edit.state).label },
          ])),
        item.stages.storyboard.review_status === "blocked"
          ? banner({
              tone: "warn", glyph: "lock", title: "Storyboard gate=require is holding the pipeline",
              body: "The scene pack stays draft-only until a human storyboard review records auto_approved or human_approved. Render and voice stay queued behind it.",
            })
          : null,
        item.rights
          ? banner({ tone: "danger", glyph: "lock", title: `Reuse rights ${item.rights.status}`, body: item.rights.detail })
          : null,
        el("div", { class: "drawer__section" },
          el("h3", {}, "Human checklist"),
          checklist,
          item.checklist.note ? el("p", { class: "checklist__note" }, item.checklist.note) : null),
        el("div", { class: "drawer__section" },
          el("h3", {}, "Artifacts"),
          artifactsTable),
      );
    }

    function applyFilters() {
      const q = f.q.trim().toLowerCase();
      let rows = studio.filter((item) => {
        const p = projects.find((x) => x.id === item.project_id);
        if (f.readiness !== "all" && readinessBucket(item) !== f.readiness) return false;
        if (!q) return true;
        return [p?.title, p?.pillar, item.stages.visuals.mode].join(" ").toLowerCase().includes(q);
      });
      const { key, dir } = store.filters.studioSort;
      const mul = dir === "asc" ? 1 : -1;
      rows = [...rows].sort((a, b) => {
        const pa = projects.find((x) => x.id === a.project_id);
        const pb = projects.find((x) => x.id === b.project_id);
        const va = pa?.title || ""; const vb = pb?.title || "";
        return va.localeCompare(vb) * mul;
      });
      return rows;
    }

    function renderResults() {
      const rows = applyFilters();
      resultsRegion.replaceChildren(dataTable({
        caption: `Content items — ${rows.length} of ${studio.length} shown (sample data)`,
        columns: [
          { key: "project", label: "Content item", sortable: true, render: (item) => { const p = projects.find((x) => x.id === item.project_id); return el("span", {}, el("span", { class: "rowlink" }, p.title), el("span", { class: "text-faint", style: "display:block;font-size:var(--fs-xs)" }, `${p.pillar} · ${p.stage}`)); } },
          { key: "script", label: "Script", sortable: false, render: scriptCell },
          { key: "storyboard", label: "Storyboard", sortable: false, render: storyboardCell },
          { key: "visuals", label: "Visuals", sortable: false, render: visualsCell },
          { key: "voice", label: "Voice", sortable: false, render: (item) => badge(item.stages.voice.state) },
          { key: "artifacts", label: "Artifacts", align: "right", sortable: false, render: (item) => { const s = artifactStats(item); return `${s.ready}/${s.total} ready${s.missing ? ` · ${s.missing} missing` : ""}`; } },
        ],
        rows,
        sort: store.filters.studioSort,
        onSort: (s) => { store.filters.studioSort = s; renderResults(); },
        onRowActivate: {
          aria: (item) => `Open production details for ${projects.find((x) => x.id === item.project_id)?.title}`,
          activate: (item) => {
            const p = projects.find((x) => x.id === item.project_id);
            drawer({
              title: p.title,
              meta: `${p.id} · ${p.pillar} · artifact readiness ${artifactStats(item).ready}/${artifactStats(item).total}`,
              content: itemDrawer(item),
              onClose: () => history.replaceState(null, "", "#/studio"),
            });
          },
        },
        emptyMessage: "No content items match the current filters.",
      }));
    }

    resultsRegion = el("div", {});
    renderResults();

    const buckets = { review_ready: 0, draft_only: 0, missing: 0 };
    studio.forEach((item) => { buckets[readinessBucket(item)] += 1; });

    main.append(
      pageHead({
        title: "Studio",
        sub: "Content production state: script, storyboard gate, visuals, voice and edit — plus artifact readiness. Artifact states decide whether a review package is approvable.",
      }),
      el("div", { class: "filterbar" },
        searchInput({ label: "Search items", value: f.q, placeholder: "Title, pillar, visual mode…", class: "search--table", onInput: (v) => { f.q = v; renderResults(); } }),
        chipGroup({
          label: "Filter by artifact readiness", name: "readiness", value: f.readiness,
          options: [
            { value: "all", label: "All", count: studio.length },
            { value: "review_ready", label: "Review-ready", count: buckets.review_ready },
            { value: "draft_only", label: "Draft only", count: buckets.draft_only },
            { value: "missing", label: "Missing artifacts", count: buckets.missing },
          ],
          onChange: (v) => { f.readiness = v; renderResults(); },
        }),
      ),
      resultsRegion,
      el("div", { class: "grid grid--2" },
        banner({ tone: "info", glyph: "info", title: "Storyboard gate modes", body: "off / skip run without review, warn generates with a warning, require holds the pipeline until a human storyboard review passes (default; unknown values fail closed)." }),
        banner({ tone: "warn", glyph: "alert", title: "Draft-only visuals block approval", body: "A package whose visual_quality_status is draft_only cannot be approved — the approval gate verifies package/metadata visuals equality." }),
      ),
    );
  },
};
