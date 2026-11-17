# NEXTDECODE Control Center — OpenCode engineering-grade prototype

**Variant:** `ui-prototype/variants/opencode/` · **Date:** 2026-11-13 · **Status:** sample prototype only

An independent, dependency-free Control Center dashboard concept for NEXTDECODE Content OS: ten sections, one coherent sample storyline, dark-first ChatGPT-inspired visual system, a global Dark/Light/System appearance selector, working navigation, filters, sorting, detail drawers, a command palette, and mock-only human-review actions.

> **What this is not:** there is no backend, API, database, storage, credential, provider call, upload, export, publishing or deployment anywhere in this prototype. Nothing outside `ui-prototype/variants/opencode/` was created or modified. **This prototype does not authorize P1 implementation or production integration.**

---

## 1. Quick preview

**Prerequisites:** any modern browser (Chrome/Edge/Firefox/Safari, current versions). No installs, no build step, no dependencies. ES modules require an HTTP origin, so serve the folder statically:

**Windows (PowerShell):**
```powershell
cd ui-prototype\variants\opencode
python -m http.server 8080
# open http://localhost:8080
```

**macOS / Linux / WSL:**
```bash
cd ui-prototype/variants/opencode
python3 -m http.server 8080
```

Any static file server works (e.g. `npx serve`, VS Code Live Server). Opening `index.html` directly via `file://` will **not** work in most browsers because ES modules are blocked on `file://` origins — that is a browser security rule, not a dependency.

**Preview checklist:**

1. Overview loads dark by default; the sidebar footer has a compact Dark/Light/System selector (also on Settings).
2. `Ctrl/⌘ + K` opens the command palette — search pages, projects, runs, reviews; arrow keys + Enter navigate.
3. Projects / Workflows / Research / Studio have live filters, search and sortable columns (click a header; `aria-sort` updates).
4. Activate any table row → detail drawer (Esc or overlay click closes; focus returns to the row).
5. Deep links work: `index.html#/workflows/r06`, `#/review/rv01`, `#/research/rp03` re-render with the drawer open; browser Back closes it.
6. Review & Approvals → “Record decision (mock)…” demonstrates the required fields (outcome, **required reviewer label**, note) and always ends with “no decision was recorded”.
7. Publishing shows readiness only; every action button is disabled with its reason code visible.
8. Settings → density switch and “Reset local preferences” persist via `localStorage`.
9. Narrow the window: sidebar collapses into a hamburger drawer < 900px; tables stack into labelled cards < 700px.
10. An unknown hash (e.g. `#/nope`) renders the Not-found state.

---

## 2. File inventory

```
opencode/
├── index.html                 shell: theme bootstrap (no FOUC), sidebar, topbar, main outlet
├── styles/
│   ├── tokens.css             design tokens (dark + light + density), single source of color
│   ├── base.css               reset, typography, focus-visible, sr-only, skip link, reduced motion
│   ├── layout.css             app grid, sidebar, topbar, page grids, responsive rules
│   └── components.css         panels, badges, tables, forms, states, timeline, overlays
├── js/
│   ├── main.js                shell wiring: nav, palette (Ctrl/⌘K), hamburger, router boot
│   ├── router.js              hash router (#/route/param), deep links, 404, focus management
│   ├── theme.js               Dark/Light/System + persistence + System live-follow + radiogroup
│   ├── store.js               plain state object + localStorage prefs (density)
│   ├── status.js              ★ state model: every status key → {label, tone}
│   ├── dom.js                 el() builder, inline icon set, date/number/hash formatting
│   ├── toasts.js              polite live-region toasts (used for mock-only confirmations)
│   ├── components.js          badge, panel, statCard, banner, dataTable, chipGroup, drawer,
│   │                          mockDialog, timeline, meters, kv, stageTrack, pageHead…
│   ├── chart.js               dependency-free SVG line chart + sparkline (labelled, with tables)
│   ├── data.js                ★ all sample data + cross-link helpers (one storyline)
│   └── pages/                 one self-contained module per section (10 files)
│       overview.js projects.js workflows.js research.js studio.js
│       review.js publishing.js analytics.js operations.js settings.js
├── README.md                  this file
└── TASK_PROMPT.md             (pre-existing assignment — untouched)
```

20 JS modules + 1 HTML + 4 CSS. No `package.json`, no `node_modules`, no build artifacts.

## 3. Architecture rationale

**Why dependency-free HTML/CSS/JS.** The repo has no root `package.json` and no `node_modules`; React+Vite would have required installs or manifest changes, both prohibited. Source-only React files were rejected because JSX cannot run without a toolchain — a non-runnable deliverable is a worse prototype than a runnable one. ES modules + hash routing deliver the same modular SPA architecture with zero tooling.

**Design decisions:**

- **Hash routing (`#/route/param`)** — deep links to runs/reviews/packages work without a server-side route config; drawer open/close is URL-driven (Back closes drawers); a Not-found route doubles as the error-state design.
- **One `data.js`** — the ten screens tell one story (a project fails at voice, recovers, gets rejected at review, etc.). A single data module with lookup helpers (`projectById`, `runById`, `reviewsForProject`…) keeps every cross-reference consistent and avoids premature per-domain abstractions.
- **One `status.js` registry** — every state rendered anywhere resolves through `statusInfo(key)` → `{label, tone}`. This is the enforcement point for “consistent state definitions across screens” (see §4).
- **Pages re-render only their results region** on filter/sort changes, so input focus is never lost; full re-render happens only on route change. No state framework, no virtual DOM — a plain `store` object holds per-page filter state for the session.
- **All dynamic values enter the DOM via `textContent`/element APIs** (never `innerHTML` with data), so sample data cannot inject markup. The only `innerHTML` uses are static internal icon path constants.
- **Fixed dataset capture point** (`NOW_ISO = 2026-11-13T10:30 IST`) — relative times (“3h ago”) are computed against a constant, so the prototype renders identically for every reviewer instead of drifting.
- **Governance boundaries are UI-enforced and visible:** mock dialogs state their own non-effects; publishing actions are disabled with machine reason codes; a “Sample data” pill is always on screen.

## 4. State model

All keys live in `js/status.js`. Tones: `ok · info · warn · danger · running · neutral · pending`.

| Domain | States (vocabulary source) |
|---|---|
| Project status | `active · needs_attention · blocked · completed · draft · archived` |
| Pipeline stages | `research → script → visuals → voice → render → review → publish` (engine module layout) |
| Run states | `in_progress · promoting · ok · failed · blocked` (`run_tracker.py`); stage states `ok · warn · failed · running · queued · blocked` |
| Autonomy tasks | `queued · running · succeeded · failed · blocked` (+ `error_code=dependency_failed`, lease owner/until, `not_before`, `attempts/max_attempts`) (`app/autonomy`) |
| Review package | `pending_human_review` → decision outcomes **APPROVED · REJECTED · CHANGES_REQUESTED · EXPIRED · REVOKED · WITHDRAWN** (CF-21); packages bind `video_sha256` + `metadata_sha256` (version-specific) |
| Package quality | `visual_quality_status: review_ready / draft_only`; `qa: pass/fail`; storyboard gate `off · skip · warn · require` with review_status `auto_approved / human_approved / blocked / pending` |
| Claims | `verified · supported` (passing) vs **blocking** `unverified · outdated · conflicting · unsupported` → publish violation `evidence_unsupported_status` |
| Rights | `permitted / restricted` (`reuse_rights`) |
| Publishing decision | `authorized / blocked_approval / blocked / not_ready` with reason codes `blocked_approval · rights_not_permitted · no_pending_package · decision_rejected`; ledger records for private destination; public publishing `disabled_pending_owner_policy`; 20:00 IST upload window is **opt-in** (`require_window=false`) |
| Operations | worker `healthy · stale · offline · paused`; incident `open · recovering · recovered`; model health `configured/ok/latency/chain` (incl. a stale “checked 20d ago” column) |
| Governance | D01–D12 `pending_owner` (D07 envelope freeze, D09 reviewer identity highlighted); API-LC-01..10 `open`; GOV-09 `open` (narrow conceptual separation recorded); M6-P ENTRY-01..12 `blocked`; autonomous publishing `blocked` — display-only everywhere |

**Coherence rules baked into the sample story:**

1. A package whose visuals are `draft_only` (rv02) is **not approvable** — mirrors the real approval gate that verifies package/metadata visuals equality.
2. An approval (rv06) does **not** create a publish grant — rights check still blocks p03 (`rights_not_permitted`).
3. Expiry (rv05) never implies approval; a repackage is required.
4. A REJECTED decision (rv04) is recorded in the existing immutable decision-record format and requests v2 changes.
5. `blocked` runs/tasks wait on dependencies (`dependency_failed`); `failed` exhausted retries (3/3).

## 5. Implemented interactions

- Global: hash routing + deep links, Back-button drawer closing, 404 state, command palette (`Ctrl/⌘K`, `/`-free — button + shortcut), theme selector on every page (sidebar + Settings), density preference, toasts, skip link, focus management on route/drawer changes.
- Tables: search, segmented status filters with counts, stage/claim selects, sortable columns (`aria-sort`), row activation (Enter/Space/click) → drawers, responsive stacking.
- Drawers: run stage-timeline, research claims + evidence signals, studio artifacts + checklist, review package (version binding, checks, platform copy, decision record, history, mock dialog), publish cards, task details.
- Mock-only review decision dialog: outcome radios, **required reviewer label** (submit stays disabled while empty — D-09), note field, submit → toast “Mock only — no decision was recorded.”
- Publishing: per-project authorization cards (approval/QA/rights/evidence/promotion/window checks), reason codes, disabled actions, policy panel, private-only ledger.
- Operations: worker heartbeats, queue table with lease state, model health (stale-check honesty), incidents, governance gates table.
- Settings: theme, density, storage keys explained, reset, workspace config placeholders, governance display.

## 6. Accessibility checklist

Implemented (verified by code inspection — see §9 for what was *not* done):

- [x] Landmarks: `header`, `nav[aria-label=Primary]`, `main#main`, `aside[aria-label=Sidebar]`; one `h1` per page; page `title` updates per route.
- [x] Skip link to `#main`; route change moves focus to the page `h1` (`tabindex="-1"`, `preventScroll`).
- [x] `aria-current="page"` on the active nav link; breadcrumbs reflect the section.
- [x] Theme control = WAI-ARIA **radiogroup** with arrow-key movement; “System” follows `prefers-color-scheme` live; no-FOUC inline bootstrap; `color-scheme` set for native controls.
- [x] All interactive elements are real `<button>`/`<a>`; icon-only buttons have `aria-label`; decorative SVGs are `aria-hidden`.
- [x] Tables: `caption`, `scope="col"`, sortable headers are buttons with `aria-sort`; horizontal scroll wrapper is a labelled focusable `role="region"`; stacked-card mode keeps `data-label` headings.
- [x] Row activation works with Enter/Space (rows are `tabindex=0` + `role=button` + `aria-label`).
- [x] Drawers/dialogs: `role="dialog"`, `aria-modal`, labelled title, Esc to close, overlay-click close, Tab cycle containment, focus restored to the opener.
- [x] Command palette: combobox/listbox pattern with `aria-activedescendant`, arrow navigation, `Esc`.
- [x] Status conveyed by **text + color** (badges always carry labels; ✓/✗ glyphs accompany checks) — color is never the only signal.
- [x] `:focus-visible` outlines everywhere (`--focus-ring`); `prefers-reduced-motion` disables animations/transitions/scroll-behavior.
- [x] Toasts via `role="status"` polite live region; disabled actions use `disabled` + `aria-disabled` + visible reason text (not color-only).
- [x] Density/typography: 13–14px base UI text, tabular numerals for operational figures.

**Known gaps (honest):** no automated screen-reader passes were run (see §9); the palette list can exceed the visible area without `aria-setsize` bookkeeping; drawer focus trap is a simple two-endpoint loop rather than a full inert-background implementation; table sticky headers rely on `thead th` positioning inside a scroll region (verified pattern, not regression-tested across browsers).

## 7. Responsive behavior

| Breakpoint | Behavior |
|---|---|
| ≥1280px | Full 3-zone layouts, 4-column KPI rows, sidebar persistent. |
| 900–1279px | KPI rows → 2 columns; side column narrows. |
| <900px | Sidebar becomes an off-canvas drawer (hamburger, `aria-expanded`, backdrop, Esc); two-pane pages stack. |
| <700px | Tables transform into labelled stacked cards (`data-label`); thead is visually hidden but screen-reader intact. |
| <640px | Topbar condenses (icon search, compact sample pill); single-column grids; palette stays usable. |

Horizontal-scroll table wrappers remain available as an alternative on any width (keyboard-scrollable, labelled).

## 8. Known limitations

1. **Sample data only** — one fixed storyline captured at 2026-11-13 10:30 IST; figures (analytics, heartbeats, review ages) are illustrative and do not reflect the repository’s actual runtime state (which currently has no completed runs and an empty approvals directory).
2. **No persistence beyond display prefs** — filters survive within a session only; refresh resets them by design.
3. **Review actions are mock** — the dialog never writes; real approvals are CLI-only with an immutable decision record. This is intentional, not a missing feature.
4. **Publishing is display-only** — no upload/export affordance exists; public publishing is shown as disabled pending owner policy.
5. **Charts are minimal** — a single-series SVG line chart with a table fallback; no tooltips/zoom (deferred to a real implementation).
6. **Not validated against WCAG with tooling** — the checklist reflects implementation intent; automated axe/screen-reader passes were out of scope for a no-dependency prototype.
7. **Single-tenant assumptions** — owner labels are static sample strings (“Owner (local)”); no auth/roles model is implied (roles remain unassigned per Q099).
8. **ES modules need HTTP** — `file://` open fails by browser rule; README documents the one-command preview.
9. **The 404 page and drawers are client-side only** — no SSR/prerender; the noscript fallback is minimal by design.

## 9. Checks actually executed

| Check | Method | Result |
|---|---|---|
| JS syntax (all 20 modules) | `node --check` (Node v24.22.1, modules checked as ESM) | **0 failures** (1 real syntax error found & fixed during development; re-verified) |
| Sample-data integrity | Node script importing `data.js` + `status.js`: every run/review/research/studio/publish/task/incident cross-link resolved; every state key present in the registry; stage order valid; 31 timestamps within capture window | **ALL LINKS OK** (6 projects, 8 runs, 6 reviews, 5 packages, 6 studio items, 7 tasks, 12 events) |
| Asset resolution | `python -m http.server` on the variant dir; `Invoke-WebRequest` against all 25 referenced assets (HTML + 4 CSS + 20 JS) | **25/25 HTTP 200** |
| Icon coverage | grep of direct `icon("…")` calls + route-icon map vs `ICON_PATHS` keys | **all defined** |
| Import hygiene | grep for unused imports per module after edits | cleaned (`panel`/`toast`/`hashChip`/`store` etc. removed) |
| Payload size | byte count of shipped source | **~225KB uncompressed** (JS 182KB / CSS 39KB / HTML 10KB), no dependencies, no build artifacts |
| First real-browser session (owner report) | blank main area on desktop at `#/overview` | **bug found & fixed:** `.nav-backdrop` was styled only inside the ≤899px media query, so at desktop widths it became an unstyled `.app` grid item and pushed `maincol` (topbar + content) below the viewport; backdrop is now `position: fixed` at all widths |

**Not executed (no claims made):** browser rendering/console-error observation, automated accessibility scans, screen-reader passes, Lighthouse/performance measurement, cross-browser matrix. These require a browser session and are listed as gaps, not results.

## 10. Self-evaluation (weighted rubric)

Scores are reviewer judgments on the rubric’s 1–5 scale, not independent benchmarks. Confidence: **medium-high** for visual/workflow/responsive/accessibility (implemented + inspected, un-tested in browsers), **high** for component quality/performance (static analysis + measurements below).

| Criterion | Weight | Score | Weighted | Evidence |
|---|---:|---:|---:|---|
| Visual quality | 25% | 4 | 1.00 | Single token system (charcoal surfaces, muted text, restrained green/teal accent) applied uniformly across 10 screens; dense operational hierarchy (KPI row → panels → tables → drawers); badges/meters/timeline as a coherent kit; dark default, light theme fully tokenized. −1: no user testing of hierarchy comprehension; charts are visually plain. |
| Workflow usability | 25% | 4 | 1.00 | “What needs attention now” is the Overview’s first panel with reason-coded links; review flow is version-specific with explicit not-approvable/expired reasoning; mock dialog teaches the real gate (required reviewer label); publishing blockers carry machine reason codes; palette + deep links + Back-to-close drawers. −1: mock-only boundary means some flows intentionally dead-end. |
| Responsive behavior | 15% | 4 | 0.60 | 5 breakpoints, off-canvas nav, stacked tables preserving labels, scrollable-region fallback, single-column grids; specified and code-verified. −1: not exercised in real devices/orientations. |
| Accessibility | 15% | 4 | 0.60 | Radiogroup/listbox/dialog patterns, aria-sort/aria-current, focus management, skip link, reduced-motion, color-independent status, visible focus. −1: no automated scans or screen-reader verification; trap is simplified. |
| Component quality | 10% | 4 | 0.40 | 20 focused modules, one status registry, one data module, pages re-render regions (not globals), no premature abstraction, no state framework; consistent `el()` discipline. −1: a few inline styles remain where a token would be cleaner. |
| Performance | 10% | 5 | 0.50 | Zero dependencies, zero network, system fonts, inline SVG icons, hand-rolled charts; ~225KB uncompressed source total (182KB JS / 39KB CSS / 10KB HTML — data.js alone is 45KB), no build step; full re-render only on route change. |
| **Total** | **100%** | | **4.10 / 5** | |

**Trade-offs:** runnable-now (dependency-free) over React familiarity; fixed sample time over live-relative times; honest dead-end mock actions over simulated success; simple focus traps over full inert background.

---

## 11. Boundary statement

This prototype uses sample data only, performs no network/storage/publishing actions beyond local `localStorage` display preferences, and leaves every other file in the repository untouched. **Selecting, using or extending this prototype does not authorize P1 implementation, production integration, or any change to P0 governance: D01–D12 remain owner-pending, API-LC-01..10 remain open, GOV-09 remains open (narrow conceptual separation recorded), and M6-P implementation/test authorization gates remain binding. Human approval remains CLI-only with an attributable reviewer identity; public publishing remains disabled pending owner policy.**
