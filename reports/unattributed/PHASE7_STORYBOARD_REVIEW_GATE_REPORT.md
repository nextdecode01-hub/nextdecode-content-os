# Phase 7 — Pre-Render Storyboard and Review Gate

**Date:** 2026-10-29  
**Project:** `/home/demon/shorts_studio`  
**Branch:** `main`  
**Git:** no stage, commit, push, or branch switch  
**Publishing:** not triggered  
**New dependencies:** none

## 1. Assessment: what already existed

Before this phase, the repository already had:

- Structured scene briefs and a controlled provider chain.
- Lexical relevance confidence (`high`/`medium`/`low`/`none`), `semantic_review`, matched terms and review reasons in `app/visuals/chain.py`.
- Optional Gemini vision review in `app/visuals/vision_review.py`, disabled by default.
- Duplicate-card downgrade, low-light/flat-clip flagging, script-aligned captions and existing audio/render QA.
- Phase 4, 5 and 6 reports under `docs/`.
- A green baseline of **230 passed, 1 warning, 11 subtests** before this phase.

What did **not** exist:

- A storyboard artifact or contact sheet before rendering.
- An explicit scene-level review state.
- A way to stop the render because selected visuals needed review.
- A hash-bound human approval record.

## 2. Research recommendations still missing

Implemented in this phase:

- Pre-render storyboard/contact sheet with narration excerpts, provider, confidence and review reasons.
- Explicit `auto_approved` / `needs_review` / `blocked` state.
- Strict gate that blocks unreviewed plans.
- Hash-bound explicit approval after human review.
- Basic provenance in the storyboard (provider, asset ID, title, license, tags, query, content hash, file timestamp).

Still missing, deliberately deferred:

- Multi-candidate retrieval (8–15 candidates per scene) and multi-frame sampling.
- Text-to-image embedding ranking (OpenCLIP or another local model) with a human-labelled calibration set.
- An explainable weighted score breakdown.
- Unified render receipt across storyboard + QA + publish state.
- Complete provider provenance: Pixabay source URL/creator and uniform retrieval timestamps are not yet stored.
- Synthetic-media disclosure flag and a publish-state gate tied to storyboard approval.
- Golden visual fixtures and a human-labelled benchmark scorecard.

No OpenCLIP, Remotion, PySceneDetect, Pillow or other framework was added. The contact sheet uses FFmpeg only.

## 3. Smallest safe implementation

- New `app/visuals/storyboard.py`:
  - builds one thumbnail per scene using FFmpeg;
  - composes a 4-column contact sheet with `xstack`;
  - writes `storyboard.json` with narration, purpose, provider, confidence, fallback/review reasons and provenance;
  - computes review status;
  - supports `STORYBOARD_GATE=off|warn|require`;
  - writes/validates an explicit hash-bound approval via `python -m app.visuals.storyboard ... --reviewer ...`.
- `app/render/assembly.py`:
  - resolves all scene assets first;
  - builds the storyboard before any full render;
  - applies the gate;
  - then renders the shots.
- `app/script/pipeline.py`:
  - attaches storyboard status/path/contact sheet to the render step and top-level metadata.
- Existing publish behavior was not changed.

## 4. Files changed

| File | Change |
|---|---|
| `app/visuals/storyboard.py` | New storyboard/contact-sheet builder, review status, strict gate, approval CLI |
| `app/render/assembly.py` | Resolve-all → storyboard → gate → render; expose storyboard in result |
| `app/script/pipeline.py` | Persist storyboard status/path/contact sheet in pipeline metadata |
| `tests/test_storyboard.py` | 8 offline tests for artifacts, status, blocked plans, gate and approval |
| `tests/test_render_qa.py` | Storyboard assertions plus strict-gate-before-render test |
| `README.md` | Documents storyboard gate, approval command and review-state semantics |
| `reports/unattributed/PHASE7_STORYBOARD_REVIEW_GATE_REPORT.md` | This report |
| `outputs/phase6_storyboard_audit/` | Contact sheet + JSON generated from the existing Phase 6 resolved plan |

## 5. Review artifact

The existing Phase 6 resolved plan was rendered into a storyboard without re-rendering video:

- Contact sheet: `outputs/phase6_storyboard_audit/storyboard/contact_sheet.jpg`
- JSON: `outputs/phase6_storyboard_audit/storyboard/storyboard.json`
- Dimensions: 1080×1920, four columns.
- Scenes: 14.
- Review status: **needs_review**.
- Confidence: 3 high, 11 medium, 0 low/none.
- Review reasons: 11 lexical/title-match scenes.
- Missing assets: 0.
- Low-light assets: 0.
- Approval: **not approved**.

The contact sheet makes the weak choices immediately visible: the dark code screen (s04), handwriting (s06), cubicle (s11), PiCSTART hardware programmer (s12) and AI corridor (s13). No silent approval occurred.

## 6. Tests

```bash
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_storyboard.py tests/test_render_qa.py tests/test_motion.py tests/test_visual_chain.py
# 83 passed, 11 subtests passed in 37.32s

PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q
# 239 passed, 1 warning, 11 subtests passed in 53.84s
```

The warning is the pre-existing `google.generativeai` deprecation warning. Nine tests were added in this phase.

## 7. Acceptance criteria

| Criterion | Result |
|---|---|
| Storyboard JSON and contact sheet exist before render | Pass |
| One scene record per shot with narration and provenance | Pass |
| Low-confidence/lexical/fallback scenes produce `needs_review` | Pass |
| Missing assets produce `blocked` | Pass |
| Unreviewed `needs_review` cannot pass `STORYBOARD_GATE=require` | Pass |
| Explicit approval unlocks the strict gate | Pass |
| Approval is tied to the contact-sheet hash | Pass |
| Existing render/audio QA and wrappers remain intact | Pass |
| Full regression suite green | Pass |
| Fresh 45–60s end-to-end benchmark | Not run in this phase |

## 8. Limitations

- The contact sheet is an inspection aid, not semantic vision. It does not prove the visual matches the narration.
- Review status is conservative: all lexical stock/still matches require review, so most normal runs will be `needs_review`.
- Approval is a local JSON file bound to the contact-sheet hash; it is not an authenticated user identity or a publishing gate.
- The storyboard is generated after assets are downloaded, so it saves render cost but not provider-search cost.
- `blocked` means missing asset/provider data, not a judgment that a present asset is wrong.
- Current provenance is partial; Pixabay source URL and creator are not yet carried through.
- No fresh render was produced in this phase. The next render should be a new 45–60s end-to-end run with the gate and a human-reviewed storyboard.

## 9. Next step

Inspect the Phase 6 audit contact sheet, fix or explicitly accept the five weak scenes, then run a **fresh** 45–60s AI/tech end-to-end benchmark with:

```bash
STORYBOARD_GATE=require
```

The run should generate the storyboard first, stop if review is required, and only render after an explicit approval. Record the storyboard, contact sheet, approval, QA receipt, render time and remaining mismatches.
