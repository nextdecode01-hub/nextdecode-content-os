# Phase 11 — Stage A (Discovery) & Stage B (Technical Design)

**Agent:** Qoder · **Date:** 2026-10-30 · **Mode:** discovery + design only, no implementation
**Status:** awaiting owner approval before Stage C

No implementation files were modified for this report. Nothing was staged, committed or pushed. Git snapshot at inspection time: 8 pre-existing staged renames, ~20 modified and ~30 untracked paths, unchanged.

---

## Stage A — Discovery

### A1. Method

Traced by reading, in full or in the named ranges: `app/visuals/chain.py`, `app/visuals/motion_director.py`, `app/visuals/stock_fetcher.py`, `app/visuals/visual_assets.py`, `app/visuals/visual_quality.py`, `app/visuals/vision_review.py`, `app/visuals/storyboard.py`, `app/visuals/cutouts.py`, `app/render/assembly.py`, `app/render/shots.py`, `app/render/ffmpeg_tools.py`, `app/script/pipeline.py`, `pipelines/short.py`.
Evidence artifacts: `outputs/phase7_final_benchmark_v2/`, `outputs/phase10_evidence_run2/`.
Prior reports: Phase 5 (semantic visual relevance), Phase 6 (visual fixes), Phase 7 (storyboard review gate).

### A2. Current flow (traced)

```
script (app/script/studio.py) ──► beats
   │
app/script/pipeline.py:332  motion_director.plan_shots(script, audio_duration)
   │
app/render/assembly.py:75   chain.plan_scenes(shots)          ← budgets, duplicate-card guard
   │
assembly.py:91-108          cutouts.select_cutout_scenes → build_source_card → rights_gate
   │
assembly.py:135             chain.resolve_scene(shot, …)      ← b-roll → still → AI image → gradient
assembly.py:157             motion_director.assign_motion(...) ← continuous zoom/pan
assembly.py:175             storyboard.build_storyboard(...)   ← contact sheet + review reasons
assembly.py:170             storyboard.enforce_review_gate()   ← default "warn"
   │
app/render/shots.py:51      render_shot() → ffmpeg Ken Burns / native / procedural
assembly.py                 concat + audio mix + burn captions + QA
   │
publish_all.py:113          approval + has_publishable_visuals() gate
```

### A3. Existing capabilities that must be reused (not rebuilt)

| Capability | Where | Evidence |
|---|---|---|
| Beat → shot timeline, 1.3–2.9 s bounds, MIN_SHOTS=8 | `app/visuals/motion_director.py:19`, `plan_shots:290` | 20 tests in `tests/test_motion.py` |
| Scene classification (footage / chart / typography / ui_demo / diagram / map / product) | `app/visuals/chain.py:321` | `test_ui_diagram_map_and_product_are_distinct_scene_types` |
| Stock budget (< half the scenes), max 2 consecutive cards, duplicate-figure → recap card | `chain.py:441`, `:57`, `:470` | `test_stock_cap_is_below_half_of_the_video`, `test_cards_and_recaps_never_run_three_in_a_row` |
| Provider chain with attempt trail: Pixabay → Pexels → Wikimedia → AI image → gradient → procedural | `chain.py:1277` | `test_successful_lower_tier_provider_keeps_the_attempt_trail` |
| Tag-overlap + vertical/aspect ranking, asset-id de-duplication | `chain.py:979` | 5 `_pick_hit` tests |
| Honest relevance semantics (lexical ≠ semantic; motion graphic = high) | `chain.py:858` | 8 validation tests |
| Low-light/flat clip rejection | `chain.py:1080` | `test_dark_or_flat_footage_is_flagged_and_downgraded` |
| Wikimedia licence/author/page provenance, generic-title rejection | `stock_fetcher.py:134`, `chain.py:1218` | `test_generic_wikimedia_title_is_rejected` |
| Cutout rights gate + hash-bound human approval + scene digest | `cutouts.py:262`, `storyboard.py:516` | 18 + 8 tests |
| Publish gate (approval + licence on every asset + no procedural shots) | `visual_quality.py:20`, `publish_all.py:113` | `tests/test_visual_quality.py` |
| Technical QA: resolution, duration, fps, audio level, black, frozen, caption presence, consecutive repeats | `ffmpeg_tools.py:555` | 19 `test_render_qa` tests |

Existing visual test coverage: chain 53, motion 20, storyboard 8, cutout rights 18, render QA 19, visual quality 6, longform visuals 8 — **132 tests**. Phase 11 must extend, not replace.

### A4. Bottlenecks (code + artifact evidence)

**B1 — Duration policy is inconsistent, so pacing is accidental.**
`MAX_SHOT_DURATION = 2.9` exists (`motion_director.py:20`) but the beat-count branch bypasses it: `if len(beats) >= MIN_SHOTS: count = len(beats)` (`motion_director.py:322`). Measured baseline: 14 shots, **2.14–5.70 s**, avg 4.06 s in a 56.9 s video (`outputs/phase7_final_benchmark_v2/verification.json`). No per-intent duration (hook / evidence / payoff treated alike).

**B2 — Query repetition defeats "no repetitive shots".**
`plan_scenes` only swaps *consecutive* identical queries (`chain.py:455`). The baseline used `"programmer workstation"` for **6 of 14** scenes — exactly how Phase 5 produced three keyboard/cubicle "title match only" scenes (`PHASE5 §6`, `PHASE6 §5`: "replacement b-roll is not consistently better than the cards it replaced").

**B3 — Every stock clip is cut to 3.6 s and then looped inside longer shots.**
`STOCK_CLIP_SECONDS = 3.6` (`chain.py:31`) is hard-coded in `_prepare_clip` (`chain.py:1060`); `render_shot` uses `-stream_loop -1` (`shots.py:81`). A 5.7 s shot shows the same 3.6 s twice. Segment choice is only "skip a black lead-in" (`chain.py:1041`); no motion or content-based selection.

**B4 — Framing is a fixed centre crop.**
Ken Burns uses `x=iw/2-(iw/zoom)/2` (`ffmpeg_tools.py:265`); native footage uses `build_scale_crop_filter` (centre). Vertical crops of 16:9 stock cut subjects' heads/hands. No saliency or face-aware bias.

**B5 — Relevance is lexical/provenance only; review is opt-in.**
`validate_asset_relevance:858` states it never claims semantic understanding; vision review requires `VISION_REVIEW_PROVIDER=gemini` (`vision_review.py:18`). Baseline: 12 of 14 assets were `medium` + `semantic_review`, and QA emitted that warning (`verification.json → qa.warnings`). Weak scenes were only found by manual frame inspection.

**B6 — GIF is not supported at all.**
Only a magic-byte sniff exists (`visual_assets.py:36`); the renderer's suffix whitelists exclude `.gif` (`shots.py:35`, `:41`). A downloaded GIF silently falls through to a procedural card.

**B7 — Rights are resolved only at publish time, and are partial for video stock.**
Pixabay assets carry a licence string and title but **no source URL or creator** (Phase 7 §8). AI images return `"license": ""` (`chain.py:1268`) and still render; only `publish_all.py:113` stops them. The storyboard's rights language covers **cutouts only** (`storyboard.py:265`); a stock or AI clip with unresolved rights is not surfaced before render.

**B8 — The shot plan lacks the structured fields 11.1 asks for.**
Current shots have `index`, `claim`, `caption`, `asset_query`, `beat_label`, `motion` (`motion_director.py:358`); the scene brief adds `intent`, `visual_purpose`, `queries`, `fallback_chain` (`chain.py:402`). Missing: stable `shot_id` outside the storyboard (`storyboard.py:340`), subject/entity field, evidence/claim reference **at plan time**, and a pre-declared selection rationale.

**B9 — Narration→visual sync is proportional, not measured.**
Shots are planned from beat text and total audio duration (`pipeline.py:332`); captions are aligned separately from ASR (`pipeline.py:330`). A visual can change mid-word because no shot depends on a measured sentence boundary.

**B10 — No consolidated visual-quality evaluation artifact.**
QA is technical (`ffmpeg_tools.py:640-690`) plus storyboard counters (`storyboard.py:320`). There is no machine-readable score for relevance, script coverage, footage usage, duplicate frequency, continuity, pacing, text readability or brand consistency. Phase 6's own conclusion — "net visual-relevance improvement is not demonstrated" — is precisely the missing measurement.

### A5. Dependency map

```
app/script/studio.py ──script dict──┐
                                    ▼
app/script/pipeline.py ──► motion_director.plan_shots ──► shots[]
        │                          │
        │                          ├──► chain.plan_scenes ──► scenes{index: brief}
        │                          ├──► chain.resolve_scene ──► stock_fetcher / visual_assets
        │                          ├──► cutouts (ledger + rights)
        │                          ├──► motion_director.assign_motion
        │                          └──► storyboard.build_storyboard ──► review gate
        └──► render_video(assembly) ──► shots.render_shot ──► ffmpeg_tools ──► qa_video
                                        ▲
                     motion_render.py (thin wrapper) / pipelines/short.py (CLI)
```

Shared leaf dependencies in scope: `ffmpeg_tools` (`build_ken_burns_filter`, `qa_video`, `_black_intervals`, `_frozen_intervals`), `stock_fetcher`, `visual_assets`. None is Phase 9 audio except `ffmpeg_tools`' audio section, which Phase 11 will not touch.

### A6. Ownership and conflict map

| Area | Files | Owner per brief | Phase 11 stance |
|---|---|---|---|
| Strict Fail-Closed | `pipelines/short.py`, `api/main.py`, `tests/test_strict_fail_closed.py` | OpenCode (§10) | **Do not touch.** Conflict C1 |
| Run tracker / identity / recovery | (not yet in tree), `docs/SECONDARY_PHASE10_4_*` | OpenCode | No integration; interface documented only |
| Evidence semantics | `app/research/*`, `app/script/evidence.py`, claims/cutouts | Phase 10 (this workstream, uncommitted) | Read-only input; no changes |
| Visual engine | `app/visuals/chain.py`, `motion_director.py`, `stock_fetcher.py`, `storyboard.py`, `visual_assets.py` | **unassigned — Phase 11 proposes** | Primary implementation area |
| Renderer | `app/render/shots.py`, `assembly.py`, `ffmpeg_tools.py` | shared | Minimal, additive-only edits |
| Script/pipeline glue | `app/script/pipeline.py`, `pipelines/short.py` | Phase 10 | **No edits**; work through functions the pipeline already calls |
| Kilo | — | **unknown** | No Kilo ownership record exists in `docs/`; require confirmation |

**C1 — unresolved conflict in the working tree.** Strict Fail-Closed was implemented in this session at owner direction (`pipelines/short.py`, `api/main.py`, `tests/test_strict_fail_closed.py`) but is **uncommitted and untested** (its test run was interrupted). §10 assigns Strict Fail-Closed to OpenCode. Options: (a) keep and verify, (b) hand the diff to OpenCode, (c) revert that change set. No action taken.

**C2 — Phase 10.1.1 is finished but uncommitted.** `app/research/desk.py` URL validation + feed tests are complete and tested (189 passed). Phase 11 will not touch `app/research/*`.

### A7. Baseline to beat (measured, not estimated)

| Metric | Phase 7 final benchmark v2 |
|---|---|
| Duration / shots | 56.9 s / 14 |
| Shot length | avg 4.06 s, range 2.14–5.70 |
| Providers | 6 Pixabay, 6 Wikimedia, 2 motion cards |
| Confidence | 2 high, 12 medium (all `semantic_review`) |
| Duplicate queries | `programmer workstation` on 6 scenes |
| Unique asset IDs | 13 for 14 scenes |
| Consecutive repeats | 0 |
| QA | pass (incl. black/frozen/captions/audio) |
| Rights surfaced before render | 0 (stock/AI rights only checked at publish) |

Phase 10 run2 package, for the evidence path: 11 scenes from 7 sentences, 3 cutouts (nist.gov, `permitted`), 8 dry-run placeholders, `needs_review`, 0 blocked.

---

## Stage B — Technical Design (proposal, not implemented)

### B1. Boundaries

- **No changes** to `pipelines/short.py`, `api/main.py`, `app/script/pipeline.py`, `app/research/*`, `app/render/ffmpeg_tools.py` audio sections, or any Phase 9 test.
- All Phase 11 behaviour enters through functions the pipeline **already calls** (`plan_shots`, `plan_scenes`, `resolve_scene`, `assign_motion`, `build_storyboard`, `render_shot`, `qa_video`), additively: new keys, new optional params with defaults, no signature breaks.
- No new paid dependency. GIF via Wikimedia Commons (keyless); motion analysis via ffmpeg.
- Rights, approval and publish gates stay exactly as strict; the evaluator may only **add** blocking findings, never clear one.

### B2. Modules

| Module | Type | Purpose |
|---|---|---|
| `app/visuals/shotplan.py` | new | `plan_shot_plan(script, ledger, audio_duration)` → ShotPlan v2. Pure/deterministic; wraps `motion_director.plan_shots` timing |
| `app/visuals/beats.py` | new | Narration segmentation with subject/action/context/emotion extraction (rule-based first; no LLM in unit tests) |
| `app/visuals/media.py` | new | `probe_asset()`, `validate_media()`, `normalize_gif()`, `select_segment()` (duration, motion, black/frozen rejection) |
| `app/visuals/framing.py` | new | `crop_bias(asset)` → `{x_bias, y_bias}` from saliency/luma heuristic; default `(0,0)` = today's centre crop |
| `app/visuals/evaluate.py` | new | `evaluate_package(storyboard, ledger, script)` → `visual_quality.json` + text report; delegates blocking to existing gates |
| `app/visuals/brand.py` | new | NEXTDECODE tokens (font, accent, safe zones, lower-third rules) + `check_brand(scene)` |
| `chain.py` | modify | scene brief carries `shot_id`, `subject`, `evidence_ids`; query-repetition guard across the whole video; per-shot clip length |
| `motion_director.py` | modify | duration policy by intent (hook/evidence/payoff) with a documented max; keep existing defaults if intent missing |
| `stock_fetcher.py` | modify | carry `page_url`/`creator` for every asset; optional Commons GIF search |
| `storyboard.py` | modify | surface `rights_state` for **all** assets, not only cutouts; add quality section |
| `render/shots.py` | modify | accept normalized `.gif`→`.mp4`; optional `framing` offsets (default current behaviour) |
| `visual_quality.py` | modify | publishability also requires resolved rights for stock/AI assets |

### B3. Data contracts

**ShotPlan v2** (superset of the current shot dict — old keys retained):

```json
{
  "shot_id": "s00", "index": 0,
  "narration_ref": {"sentence_index": 0, "text": "…", "claim_ids": ["clm_…"]},
  "visual_objective": "locate the story geographically",
  "subject": {"name": "NIST AI RMF", "type": "organisation"},
  "action": "released a concept note",
  "context": "critical infrastructure",
  "emotion": "measured",
  "visual_type": "motion_graphic",
  "scene_type": "typography",
  "expected_duration": 4.2,
  "duration_basis": "intent:hook | words:18 | audio_ratio:0.074",
  "search": {"primary": "nist ai risk management", "variants": ["…"], "negative": ["keyboard"]},
  "transition_intent": "cut | fade | none",
  "evidence": {"claim_ids": ["clm_…"], "required": true},
  "rationale": "numeric beat → card; stock budget exhausted for this run"
}
```

**ResolvedScene v2** (additive): `media` (`width/height/duration/codec/motion_score`), `segment` (`in/out/source_duration`), `framing`, `rights_state` (`permitted | unknown | incompatible`), `provenance` (`page_url`, `creator`, `license_url`), `quality` (relevance + technical + brand findings).

**VisualQualityReport v1** (`data/visual_quality.json`):

```json
{"schema": 1, "generated_at": "…",
 "metrics": {"relevance": {"strong": 6, "partial": 5, "weak": 3},
             "script_coverage": 1.0, "footage_usage": 0.43,
             "duplicate_visuals": 1, "continuity": "ok",
             "pacing": {"avg": 4.0, "longest": 5.7}, "text_readability": "ok",
             "technical": {"black": 0, "frozen": 0}, "brand": "pass"},
 "blocking": [{"kind": "rights", "scene": "s03", "detail": "unknown reuse basis"}],
 "publish_ready": false}
```

`publish_ready` is true only if `blocking` is empty **and** the existing approval/rights gates already said yes — the evaluator never grants readiness itself.

### B4. Workstream mapping

| WS | Concrete change | Reuses |
|---|---|---|
| 11.1 | `beats.py` + `shotplan.py`; structured plan emitted before resolution; duration by intent | `plan_shots`, scene brief, `_infer_intent` |
| 11.2 | global query/variant de-duplication; subject match scored separately from tag overlap; rights state on every asset | `_pick_hit`, `validate_asset_relevance`, `reuse_rights` |
| 11.3 | `.gif` normalization + Commons GIF search + `media.py` validation + segment selection by duration/motion; provenance fields | `stock_fetcher`, `_prepare_clip`, `_visual_quality` |
| 11.4 | intent-aware pacing, transition chosen from continuity (not index), framing bias, hook/payoff composition rules | `assign_motion`, `build_ken_burns_filter`, `build_scale_crop_filter` |
| 11.5 | `brand.py` tokens + `check_brand`; opening/closing treatment checks; no asset replacement | existing card renderer, `FONT_PATH`, `ACCENT` |
| 11.6 | `evaluate.py` report + storyboard section + optional CLI; blocking findings delegate to rights/approval | `qa_video` results, storyboard summary |

### B5. Implementation order (each step independently testable)

| Step | Change | Acceptance |
|---|---|---|
| I1 | `shotplan.py` + `beats.py` (no renderer change) | plan covers 100% of narration sentences; schema test |
| I2 | Global query de-dup + repetition guard | no query used for >2 scenes unless flagged; baseline `programmer workstation` drops |
| I3 | Duration-by-intent + longest-shot bound | 45–60 s sample has no shot > policy max; hook ≤ 4 s in fixture |
| I4 | `media.py` validation + GIF normalisation + segment selection | corrupted/oversized GIF/MP4 rejected with reason; loop repeat eliminated |
| I5 | Framing bias (default centre) | crop metadata present; pixel output unchanged when bias = 0 |
| I6 | Rights/provenance propagation + evaluator + storyboard section | unknown rights block publish-ready; evaluator cannot raise readiness |
| I7 | Integration test + controlled 45–60 s sample | full run with new artifacts; before/after table |

### B6. Test matrix (deterministic, fixtures/mocks only)

| Required area | Planned tests |
|---|---|
| Shot plan structure + coverage | `test_plan_has_required_fields`, `test_every_sentence_maps_to_one_shot`, `test_subject_extraction` |
| Relevance/matching | extended `validate_asset_relevance` cases; subject vs tag split; weak-match downgrade |
| Missing/invalid metadata | asset without licence/creator → `rights_state=unknown`, not publish-ready |
| Rights propagation | stock/AI rights reach storyboard; no promotion to `permitted` |
| Duplicate detection | same asset ID, same subject different ID, repeated query |
| Video/GIF validation | corrupt file, unsupported codec, oversized, `gif`→`mp4` |
| Unsupported media | `.gif` in renderer whitelist path; unknown suffix |
| Crop/aspect | 16:9→9:16 bias decisions; no-bias regression |
| Shot duration | min/max, intent bounds, total 45–60 s |
| Storyboard invalidation | script/ledger change invalidates approval (existing digest test extended) |
| Quality evaluation | blocking rights wins over high score; coverage maths; duplicate count |
| Blocking propagation | evaluator blocked → publish gate refuses |
| Integration | one mocked end-to-end `plan → resolve → storyboard → evaluate` |

### B7. Phase 10 interface needs

- **Input (read-only):** callable ledger with `claim_ids` per sentence — already available (`claims_for_scene`).
- **Needed later, not now:** a run-scoped artifact directory (run identity). Until OpenCode exposes it, Phase 11 writes its report next to the storyboard (`work/storyboard/visual_quality.json`) and accepts an optional `work_dir` argument. No new cross-phase contract.
- **Do not** import or depend on the unfinished Run Tracker.

### B8. Cost

| Item | Cost |
|---|---|
| Wikimedia Commons stills/GIF | free, keyless |
| Pixabay/Pexels video | free, keys optional (already optional today) |
| AI image providers | unchanged, optional, quota-limited |
| ffmpeg motion/segment analysis | local CPU only; ~0.2–0.5 s per clip at 3.6 s length |
| Vision review | unchanged, opt-in, paid only if the owner enables it |

### B9. Risks

1. **Pacing change is visible** — a longer hook shot changes the feel; needs owner sign-off (Q2).
2. **Global query de-dup can starve b-roll** — mitigation: allow a repeated subject only with a different visual purpose, and flag it.
3. **Framing bias is heuristic** — default `(0,0)` means zero behaviour change until reviewed.
4. **GIF sources** — Commons GIFs are often low quality; they must pass the same size/light/validation gates.
5. **Evaluator scope creep** — it reports and blocks only through existing gates; it never approves.
6. **Shared-file friction** — edits to `chain.py`/`storyboard.py` conflict with any concurrent Phase 10 work on the same files; require an ownership confirmation (C3).

### B10. Decisions required before Stage C

1. **C1:** what happens to the uncommitted Strict Fail-Closed + URL-validation changes now that §10 assigns Phase 10 to OpenCode?
2. **C3:** confirm Kilo has no ownership of `app/visuals/*` or `app/render/*` (no record in `docs/`).
3. **Q2:** approve changing the shot-duration policy (currently an inconsistent 2.9 s cap) to intent-based durations with a documented maximum?
4. **Q4:** should `STORYBOARD_GATE` stay `warn` by default (renders proceed, publish still blocked by approval), or should a *blocking* visual-quality finding stop the render? Recommendation: keep `warn` and route blocking findings to the publish gate, so nothing existing is weakened.
5. **Q5:** NEXTDECODE brand assets — where are the approved logo/typography/lower-third references? No brand identity will be invented.

No implementation will start until Stages A/B are approved and C1/C3/Q2/Q4/Q5 are answered.
