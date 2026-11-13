# Shorts Studio — Phase 10.3 System Reliability & Architecture Review

**Reviewer:** Secondary agent (independent Principal Architect / Reliability Engineer role)
**Date:** 2026-10-30 · **Mode:** READ-ONLY audit. No files created/edited in code, no git operations, no scripts executed that modify state. QA-runs are pytest on test files only (non-mutating for repo outputs).

**Legend used throughout:**
- ✅ **Verified:** re-confirmed today in the working tree with file:line.
- ⚠️ **Potential:** observed pattern suggests risk; not reproduced end-to-end.
- 💡 **Recommendation / 🔎 Assumption:** clearly labeled.

Content is deliberately scoped to **not duplicate** Qoder's in-flight Phase 10.1.1 feed work (finding numbers F1–F5 of that audit chain are referenced, not re-owned). Phase 9 audio surfaces and publishing configuration are out of scope for change.

---

## 1. Executive summary

The architecture is fundamentally sound and has been hardened in Phase 10.1 (evidence-first ledger, fail-closed research, storyboard artifacts). The single most consequential finding of this review is **the automatic quality-downgrade fallback in the production entrypoint**: when the strong (evidence-first) pipeline fails, `pipelines/short.py` silently falls back to the legacy single-pass path — which by design bypasses research gates, the claim ledger and evidence linkage — and still lands its output in the same `data/metadata.json` slot that the human review process consumes. In scheduled runs (`run_scheduled_generation.sh` → `run_pipeline.sh`, which does **not** pass `--strict`), this downgrade path is **active by default**. This inverts the intended failure semantics (fail-closed) for exactly the runs that happen unattended.

Second theme: the pipeline stages are individually well-validated, but the **run as a whole is a fixed-name, single-slot artifact producer** (`outputs/voice.mp3`, `outputs/output_short.mp4`, `data/metadata.json`) with no run identity, no artifact manifest, and no interrupted-run metadata. This creates collision risk under concurrent triggers (the API accepts up to 50 jobs) and makes "which files belong to which run / which script version" a human-memory question rather than a machine-checkable one.

Third theme: **observability gaps** — stage payloads exist (`steps[]`) but carry no timestamps, durations, run ID, or error categories, which makes the existing rich payloads hard to use for postmortems.

Nothing here requires replacing the architecture; the recommendations are incremental (run manifests, deterministic recovery classification, observability fields, contract tests) and most touch 2–3 files each.

---

## 2. Current architecture map (verified)

**Production entrypoints**
- Scheduled short generation: `run_scheduled_generation.sh` (flock guard, `:13-20`) → `run_pipeline.sh` (`pipelines/short.py`, no `--strict`) → success: `review_bundle.py`; if `PUBLISH_MODE=publish` → `publish_all.py`.
- Strong pipeline CLI: `run_gen.sh` → `python -m app.script.pipeline` (verified in earlier audit).
- Long-form: `run_longform_pipeline.sh` → `pipelines/longform.py` → `review_longform.py`.

**Strong pipeline stage chain** (`app/script/pipeline.py:run`, `:252-490`) — verified sequential chain:

| Stage | Function (file:line) | Next stage input | Failure behavior |
|---|---|---|---|
| Topic selection | `select_topic` `pipeline.py:53-90` | topic | raises `RuntimeError` (no candidates / no topic meets bar) |
| Research | `build_research` `:93-101` → `desk.research_topic` | research dict | fail-closed (`desk.py:707-709 insufficient`) then `strict_research=True` raises in script stage |
| Evidence/ledger | `claims.build_ledger` + `write_ledger` `:296-297` | `claim_ledger.json`, `script_sha256`, `ledger_sha256` | — |
| Script | `studio.write_script(strict_research=True)` `:287` | voice_text, beat_sheet | raises |
| Voice | `generate_voice` → `voice_provider.synthesize` `:324-327` | master audio (lossless mix source preferred `:326`) | provider fallback chain |
| Captions | `build_captions` (ASR align) `:330` | `subtitles.ass` | — |
| Shots/plan | `motion_director.plan_shots` + `estimate_render_plan` `:332-333` | shots list | — |
| Render | `motion_render.render_video` `:341-348` → `assembly.render_video` | `output_short.mp4` + storyboard + cutout evidence | render QA `:349-359` |
| Metadata | assembled `:413-490` | `data/metadata.json` (via `pipelines/short.py:222`) | — |

**Downstream human-gate chain (verified earlier):** `review_bundle.py` → `data/review_package.json` → **manual approval** (`approve_review.py`, checklist, digest) → `data/review_approved.json` → `publish_all.py` (`approval_integrity.approved_today`, upload window). Storyboard pre-render gate: `storyboard.enforce_review_gate` (`storyboard.py:537-553`), default `warn` (`:540`, `:9-11`).

**Cross-cutting modules:** `app/research/*` (discovery + claims), `app/visuals/*` (chain/plan/quality), `app/render/*` (FFmpeg assembly, QA, audio diagnostics), `app/voice/*` (TTS providers), root shims (compat), `workflow_n8n_approved_schedule.json` (n8n → runner → entrypoints only; no publishing outside approval chain).

Cicrular dependencies: none verified in the stage chain (imports flow one direction: pipelines → app.script → app.research / app.visuals / app.render; shims point into `app.*`). ⚠️ The only two-way-ish pattern is `app/publish/youtube_longform_upload.py` importing root modules (`approval_integrity`, `notify_status`, `visual_quality`) — documented previously as shim-layering debt, not a cycle.

---

## 3. Findings (with exact references)

### F10.3-1. Silent quality-downgrade fallback (✅ Verified — **Critical**)
- `pipelines/short.py:336-343`: `except Exception` around `run_strong_pipeline` → prints "[!] Strong pipeline failed … falling back to the standard path." with **no strict requirement** to label the downgrade.
- `run_pipeline.sh` (used by the uninterrupted scheduler) invokes `pipelines/short.py` **without `--strict`**; the `--strict` opt-in exists (`pipelines/short.py:305-309, 340-341`) but is not the scheduler default.
- Impact: a legacy-path video (no research verdict, no claim ledger, `quality` ≠ "strong") is archived and lands in `data/metadata.json` → consumed by `review_bundle.py`. Evidence-layer guarantees (traceability, proportionality flags) do not exist for that output.
- Counter-evidence check (fairness): the legacy path *does* still flow through the human review package before publishing — **no automatic publishing is involved**. The harm is integrity/labeling, not automatic publication. 💡 This is also why it is *not* "broken" — it is a deliberate resilience feature that needs a guardrail, not removal.

### F10.3-2. Fixed-name artifact slots — collision & overwrite risk (✅ Verified — High)
- `pipelines/short.py:312-318`: `work_dir = outputs/`, fixed names `voice.mp3`, `background.mp4` (legacy), `subtitles.ass`, `output_short.mp4`; metadata at `data/metadata.json`.
- `pipeline.run` (`:323-341`) uses the same fixed names for voice/subtitles/render into `work/shots/`.
- `api/main.py` supports up to 50 concurrent jobs; `n8n_runner.py` wraps shell entrypoints; only the scheduled path has a flock (`run_scheduled_generation.sh:13-20`). ⚠️ Two concurrent strong runs (API-triggered or manual+scheduled race) write into the same slots — last-writer-wins on every artifact.
- Impact: silent topic/cut collision; review package could reference files the *next* run replaced (digest mismatch at approval time would catch content changes at the **packaging** level, but shot-level assets are not digested — see F10.3-5).

### F10.3-3. No run identity / artifact manifest / interrupted-run record (✅ Verified — High)
- `pipeline.run` knows stage order (`steps[]`) but there is no per-run directory (`outputs/outputs/chain_run*` accumulations show per-topic manual runs instead), no manifest.json mapping artifacts → sha256 → stage, and no marker of a *partially completed* run.
- Interrupted rendering recovery: ⚠️ shot files are regenerated wholesale each run (`shots.py:60` writes `shot_{index:03d}.mp4` unconditionally; `render_shot` has no resume check). Correctness is preserved (idempotent re-render) at the cost of wasted work (~6-14 FFmpeg renders per retry).
- Data preserved for recovery after failure: ✅ ledger + metadata steps exist only for *completed* runs; failed runs leave orphaned intermediates (voice, shots, qa files) with no pointer to the failure.

### F10.3-4. Observability: stage payloads lack time, run-id, error taxonomy (✅ Verified — Medium)
- `step()` (`pipeline.py:269-270`) stores name+payload only; total elapsed only at the end (`:487`). Per-stage duration and timestamps: **absent**.
- Error categories: failures surface as free-text in `steps[].qa.warnings` or as exceptions with `type(exc).__name__` in `notify_status` messages. No enum (`network`, `render`, `validation`, `evidence`, `approval`).
- `_log` messages and `[storyboard]` prints lack run/scope prefixes; multi-line comparability across runs is manual.
- Source/asset lineage is otherwise good: ✅ evidence block links ledger & script hashes (`pipeline.py:447-458`), research includes `sources` subset with publisher/published (`:442-445`), storyboard carries digests (`storyboard.py:60-72`).

### F10.3-5. Hash coverage ends at the ledger; video/asset SHA recorded only at approval time (✅ Verified — Medium)
- `approval_integrity.sha256_file` is applied at approval/publish time (verified — finding F3 of a previous report), and the ledger has `ledger_sha256` + `script_sha256` (`pipeline.py:447-450`).
- ⚠️ Between render and approval, `output_short.mp4`, shot files and downloaded assets have no recorded hash in metadata — tamper/partial-write detection before approval relies on file existence/size only (`shot validity = stat size > 1000`, `shots.py:47-48`).
- Result: the human reviewer approves a review *bundle*; the bundle's media integrity is asserted, but there is no post-render manifest the reviewer (or approval script) can recheck against `outputs/`.

### F10.3-6. Storyboard gate default (`warn`) vs "human approval mandatory" policy (✅ code verified; 🔎 policy interpretation — Medium)
- `enqueue_review_gate` default is `warn`, not `require` (`storyboard.py:10-11, 540`): a blocked storyboard only prints reasons; the run continues to render, and the human gate arrives later via the review package.
- 🔎 Assumption: "human approval mandatory" is honored at the review-package gate (verified), and the pre-render storyboard gate is a *review friendliness* control. If policy intends a hard pre-render stop, set `STORYBOARD_GATE=require` via env, not a code change. **No change recommended now** — flagged for the human owner to decide.
- No inactivity/auto-approval found anywhere ✅: `approve_review.py`/`approve_longform.py` require explicit checklist + digest; `upload_window_open()` restricts scheduled publishing windows — verified. External publishing remains default-off (`publish_all.py` approval checks, `PUBLISH_MODE`).

### F10.3-7. Shot/artifact validity checks are size-based (⚠️ Potential — Medium)
- `_valid_output` (`shots.py:47-48`) accepts any file >1000 bytes as a valid render despite the codebase already having `ffmpeg_tools._ffprobe` for structural validation. A truncated/truncated-tail mp4 (disk full during render) passes this check into concat; `qa_video` would then flag it downstream as a *quality* warning, not a *artifact-integrity* error, complicating diagnosis.
- No evidence of this occurring in practice — mark potential.

### F10.3-8. Stage-contract contract drift between `studio.write_script` output and `pipeline.run` consumers (✅ partially verified — Medium)
- `metadata["research"]` duplicates the research dict in full (`pipeline.py:436-446`), while `metadata["evidence"]` carries a parallel *derived* summary (`:447-458`). Two representations coexist in the artifact; a future edit to one without the other creates silent divergence. 💡 Recommendation (not change): derive `research` summary from `ledger` (single source), or add an integrity test pinning their consistency.
- `duration_seconds` reports `qa.duration` with fallback to narration duration (`:422, :475-476`) — both fields coexist in `voice` (`:475-476`) ✅ good, but the top-level one can silently differ from reality if QA was skipped (`qa.duration` empty) — ⚠️ low.

### F10.3-9. Network reliability of the research layer (✅ Verified — reference to Phase 10.1.1, not re-owned)
- Fail-closed research, refusal-retry, blocked/manual-review reporting and abort-on-no-candidates verified. Known gaps (transient retry in `fetch_url`, silent feed exceptions, Trends URL defect) are **owned by Qoder's Phase 10.1.1**; see `reports/opencode/SECONDARY_AUDIT_RESEARCH_FEEDS_2026-10-30.md`. The determinism principle there (do not retry permanent failures) applies to the whole pipeline and is adopted in the roadmap below.

### F10.3-10. Resource usage (✅ Mostly fine; two concrete notes)
- Caching systems that work: trend cache 6h TTL (`trends.py:66`), asset keyword cache (`chain._cached_hits`, `:732-737`), asset reuse planner (`chain.py:1295-1304`).
- Concrete waste: every pipeline re-run re-renders all shots even when the script/shots plan is byte-identical (no digest-based skip). Expensive-but-measured via `estimate_render_plan`.
- FFmpeg: `FFMPEG_TIMEOUT=300` per command (`ffmpeg_tools.py:13, 56`) protects hangs; ⚠️ the concat/assembly step is the longest command — a timeout there burns 5 min and yields a partial file the QA then flags (rare, per-instance). Acceptable; not a paid-service case per your constraint.

### F10.3-11. `bundle_topic_and_research()` merge residue + feed debt (owned)
- Deferred to Phase 10.1.1 (Qoder). Listed here only to mark ownership and avoid double-implementation: `desk.py:860-966`, stubs `:29-52`, `trends.py:432/745/929`, silent exceptions `topics.py:268-274/236-242`, Trends URL defect.

### F10.3-12. `data/` single-slot vs review integrity (✅ Verified — Medium, labeling only)
- One `data/metadata.json` + one `data/review_pending.json` + one `data/review_approved.json` at a time (Phase 2 test `tests/test_phase2_storage_layout.py` pins this layout). With F10.3-2 the slot model amplifies collision risk; with the human-approval chain it also creates a simple, auditable protocol (one pending item = unambiguous approval target). 💡 Keep the slot model; make it collision-safe via run manifests instead of renaming the contract.

---

## 4. Risk register (top items only; full detail above)

| ID | Risk | Likelihood | Impact | Priority | Status |
|---|---|---|---|---|---|
| R1 | Silent strong→legacy fallback in scheduled runs produces unaudited, non-evidence video into the human review queue | Medium (any strong-stage failure) | High (integrity) | **Critical** | ✅ Verified |
| R2 | Concurrent runs collide on fixed-name outputs → review package references replaced media | Low–Medium (API peak) | High | High | ⚠️ Verified pattern, race not reproduced |
| R3 | Interrupted/partial runs leave orphaned intermediates; no manifest → unreviewable provenance; wasted re-renders on retry | High (any crash) | Medium | High | ✅ Orphan dirs verified; resume-cost verified |
| R4 | Media/hash integrity gap between render and approval (no artifact manifest) | Low | Medium (integrity of *what human approves*) | Medium | ✅ Verified absence |
| R5 | Postmortem cost: steps lack timestamps/durations/error categories | High (every failure) | Medium (debugging speed) | Medium | ✅ Verified |
| R6 | Truncated media passes size check into concat | Low | Low–Medium | Medium | ⚠️ Potential |
| R7 | Policy question: storyboard pre-render gate default `warn` vs mandatory-approval intent | Owner decision | Low–Medium | Medium | ✅ code verified; policy assumption flagged |
| R8 | Network-layer reliability gaps in feeds | Already in remediation | Medium | — | Owned by 10.1.1 (Qoder) |
| R9 | Contract drift between duplicated research representation and ledger summary | Low | Medium | Medium | ⚠️ Verified duplication |

---

## 5. Recommended test matrix (specifications only — do not create tests now)

All tests should be hermetic (no network), use tmp dirs for work artifacts, and avoid touching `data/` state files.

| # | Test spec | Level | Asserts | Protects |
|---|---|---|---|---|
| T1 | **Stage contract: pipeline.run metadata schema** | Contract | For a synthetic strong run (research+script mocked, voice=silent provider, render=procedural): metadata contains `quality=="strong"`, `evidence.ledger_sha256` non-empty, `evidence.script_sha256` equals sha256(voice_text), `steps` covers {topic, research, evidence, script, shots, render, visuals} | Cross-stage integrity (F10.3-8) |
| T2 | **Ledger↔script hash binding** | Integrity | `claims.build_ledger` with same script twice → identical `script_sha256`; differing scripts → differing digests; ledger contains one `narration` per sentence | Evidence version consistency |
| T3 | **Fallback labeling (R1)** | Contract | Run `pipelines/short.py` main with strong-stage monkeypatched to raise and stub legacy path → produced metadata must contain a `quality_fallback: true`-style marker (test asserts whatever contract is chosen in the fix) | Regression protection for the downgrade path |
| T4 | **Scheduler passes strict gate** | Smoke/config | Parse `run_pipeline.sh` → assert either `--strict` present or fallback-label contract test (T3) exists and passes | Deployment-safety regression |
| T5 | **Concurrent run collision** | Race (single-thread simulation) | Two sequential `run()` calls with distinct manifests → each manifest resolves to its own artifacts; shared-slot mode flagged | Detects collision prevention work |
| T6 | **Manifest integrity** | Recovery | After a full synthetic render, manifest exists with sha256 for output_short.mp4, voice master, shots; corrupting one file → manifest validation fails | F10.3-5 closure |
| T7 | **Truncated media detection** | Recovery | 1001-byte fake shot file → shot-level validation must reject (after F10.3-7 fix) or qa_video must classify as integrity error | F10.3-7 |
| T8 | **Failed-run orphan bookkeeping** | Recovery | Kill render stage mid-way (simulate via monkeypatched exception) → rerun produces no reuse of stale intermediate (assert re-render call count) and no crash | F10.3-3 |
| T9 | **Review gate regression** | Approval safety | `approve_review` with wrong digest → rejected; `upload_window_open` outside window → blocked; storyboard gate modes off/warn/require behave per current contract | Publishing safeguards — **must not change behavior, only pin it** |
| T10 | **Stage observability fields** | Observability | `steps[]` rows include `ts` and optional `elapsed` after Phase 10.5 fix | Debugging |
| T11 | **Error taxonomy** | Observability | Forced failures per category (network/render/validation) classify into the enum after Phase 10.5 | Postmortems |
| T12 | **Stale-artifact detector** | Housekeeping | Given `outputs/` with artifacts not referenced by any manifest/metadata → detector lists them (spec-level; runtime tool, not test) | Disk hygiene |

Priority order: T1, T2, T3, T9 first (cheap, protect core), then T6–T8 post-manifest implementation.

---

## 6. Prioritized improvement backlog

| ID | Improvement | Priority | Modules | Complexity | Dependencies | Acceptance criteria | Regression risk |
|---|---|---|---|---|---|---|---|
| B1 | Fallback guardrail: label legacy-fallback metadata (`quality_fallback: true`, notify as distinct event); scheduler uses `--strict` OR the label makes review bundle reject unlabelled downgrades | **Critical** | `pipelines/short.py`, `review_bundle.py`, `run_pipeline.sh` | Low | Human decision on policy (strict default vs labeled downgrade) | Scheduled run with broken strong pipeline never produces unlabeled non-evidence metadata; T3 passes | Low (behavior visible in logs both ways) |
| B2 | Run manifests: per-run `outputs/<run_id>/manifest.json` with stage list + sha256 of voice/output/shots/ledger; keep legacy fixed names as *pointers* alongside (metadata.json still written for compatibility) | High | `app/script/pipeline.py`, `app/render/*` (hash on exit), `video_archive.py` (option) | Medium | B2 uses existing `hashlib` only | T6 passes; every generated review package referenceable by one manifest | Low-Medium (new module; additive) |
| B3 | Deterministic retry/recovery classification: retry only {timeout, connection, 429/5xx}; permanent failures (validation, evidence, approval) fail-fast with category field; no silent re-run loops | High | `app/research/desk.py` (shared w/ 10.1.1), `app/script/pipeline.py` top-level | Low-Medium | Coordinate with 10.1.1 Qoder on `fetch_url` retry | T11 taxonomy; strong run makes at most N transient retries and never masks permanent failure | Low |
| B4 | Failure-run bookkeeping: on stage exception, write `outputs/<run_id>/failure.json` (stage, exception, category, partial artifacts list) before re-raising | High | `pipelines/short.py`, `app/script/pipeline.py` | Low | B2 (run_id) | T8 partially; failure.json exists for a killed run | Low |
| B5 | Observability: timestamps + per-stage elapsed in `steps[]`; run_id emitted in `_log` prefixes; error categories appended to failure logs | Medium | `app/script/pipeline.py` | Low | B3 categories | T10 passes; postmortem readable from metadata alone | Very low |
| B6 | Structural media validation: ffprobe each rendered shot before concat (reuse `ffmpeg_tools._ffprobe`) replacing size-only `_valid_output` | Medium | `app/render/shots.py` | Low | none | T7 passes | Very low (adds ~14 quick ffprobe calls) |
| B7 | Shot re-render skip when shots plan digest unchanged and existing files validate (reuse `storyboard.py` digest pattern) | Medium | `app/render/shots.py`, `assembly.py` | Medium | B2/B6 validation basis | T8 re-render count drops on byte-identical rerun | Medium — must key on full input digest, not mtime; off by default until proven |
| B8 | Contract test suite T1/T2/T9 as permanent regression protection | Medium | `tests/` (future) | Low-Medium | none | Suite green on current code (pin current contracts, not aspirational) | None (tests only) |
| B9 | Policy decision: `STORYBOARD_GATE` default (`warn` → keep / `require`) — human owner decision, env-only change | Medium | env/config only | Trivial | Human sign-off | Documented choice + T9 green | None if env-only |

Not recommended (out of scope / not justified by evidence): paid stock/TTS upgrades, architecture rewrite, multi-tenant review queue redesign, feedparser dependency, replacing `requests` with anything else, Phase 9 audio changes, publishing automation of any kind.

---

## 7. Three-phase roadmap (post-10.3)

### Phase 10.4 — Run identity, artifacts & deterministic recovery *(targets R1–R4)*
1. B1 fallback guardrail (highest urgency; small diff).
2. B2 run manifests + B4 failure bookkeeping.
3. B6 ffprobe shot validation.
- **Acceptance:** review package always traceable to an evidence-backed or (explicitly labeled) legacy fallback run; every crash leaves a machine-readable failure record; interrupted renders never produce a "green" qa from stale partials.
- **Regression risk:** touching `pipelines/short.py` main flow — mitigated by keeping metadata.json semantics unchanged and additive manifest.
- **Dependencies:** none on 10.1.1 except sharing the failure-category enum definition (define once, both use).

### Phase 10.5 — Observability & failure taxonomy *(targets R5, R4 residual, R9)*
1. B3/B5 (categories, timestamps, elapsed, run-id logs).
2. Publish a `docs/PIPELINE_FAILURE_RUNBOOK.md` mapping categories → actions (human-facing).
3. Optional: metadata `tool_versions` record (ffmpeg -version, tts provider) for reproducibility.
- **Acceptance:** any CI-stored metadata is self-explanatory postmortem (stage timings + failure category + versions present). Regression risk: minimal (additive fields).

### Phase 10.6 — Contract test architecture & housekeeping automation *(targets regression protection, T-matrix, disk hygiene)*
1. B8 permanent suite (T1/T2/T9 minimum; then T6–T8 from 10.4).
2. Stale-artifact detector CLI (spec; runtime read-only list — deletion stays manual/human).
3. Shot re-render skip behind env flag (B7) — only after manifest validation proven in production runs.
- **Acceptance:** full test suite green; detector lists orphan dirs (like current `chain_run*`, `card_check`) without deleting; CI-able local pytest run < 12 min.
- **Dependencies:** 10.4/10.5 landed; 10.1.1 (Qoder) feed fixes stable so shared contracts (error strings) don't drift mid-test.

**Explicit cross-phase constraint honored:** every phase keeps the human-gate protocol untouched and additive-only in metadata JSON (no schema break of the approval/publish flow).

---

## 8. Areas that must NOT be changed (verified intention + ownership)

1. **Phase 9 audio fidelity chain** — `ffmpeg_tools` music bed defaults, loudnorm targets, SFX mixing, `app/voice/*` provider contracts and tests (audio_settings, master path). Out of bounds for this initiative.
2. **Approval & publishing safeguards** — `approve_review.py` / `approve_longform.py` checklist semantics, `approval_integrity.py` digests/upload window, `publish_all.py` approval gates, n8n workflow JSON, scheduled publish behavior. Any change here requires human sign-off beyond this audit.
3. **Storyboard review statuses & digest schema** (`storyboard.py`) — pinned by existing tests and human reviewer's tools.
4. **Phase 10.1 evidence semantics** — ledger schema v1 (`LEDGER_VERSION`), `ledger_sha256` digest content, status/decision vocab (`claims.py`).
5. **Phase 10.1.1 scope (Qoder)** — feed stubs/delegation in `desk.py`, `trends.py` XML guard, `topics.py` exception handling, Trends URL extraction, `archive/abandoned-agent-scripts/replace_feed_fetchers.py`. Do not double-implement; coordinate via the reconciliation report.
6. **Fixed-name top-level contract** `data/metadata.json` / `data/review_*.json` (single pending item) — it is the human protocol; make it collision-safe **alongside** (manifests), not instead of.
7. **Root compatibility shims** — the CLI shim contract that `publish_all.PUBLISHERS` and `scheduled_publish.py` depend on (previously flagged separately; retention policy decision pending, but renaming/removal here is out of this phase).
8. **`.env`-driven default behaviors that users rely on** (TTS voice/prosody opt-ins, `SHOT_SFX=off` default, music bed opt-in) — no default flips without explicit owner approval.

---

## 9. Verified vs not: summary of evidence discipline

- ✅ Verified with today's working tree: F10.3-1..5, F10.3-8 (duplication), F10.3-10 (cache existence), architecture map, risk register rows marked ✅.
- ⚠️ Potential (pattern-level, not reproduced end-to-end): concurrent-run race (R2), truncated-media acceptance (F10.3-7), QA-duration fallback edge (F10.3-8 low sub-item).
- 💡 Recommendations are explicitly flagged as policy/owner decisions where behavior is currently *intentional* (fallback design, storyboard warn default).
- 🔎 Assumptions declared: policy interpretation of "human approval mandatory" wrt pre-render storyboard gate; ownership attribution of untracked WIP files.
- Tests consulted (read-only): `test_phase2_storage_layout.py`, `test_production_reliability.py`, `test_research_quality.py`, `test_topic_research.py`, `test_research_desk.py`, `test_phase4_research_package.py`, `test_source_lineage.py` — research suite 50/50 green as of audit start; feed-file 20/22 with 2 known fails (owned by 10.1.1).

*Report by the independent secondary reviewer. Nothing implemented; awaiting human review of proposals.*
