# Visual Asset Intelligence & QA — 2026-11-15

## Scope and safety

This was an independent asset-intelligence task. It did not touch the Automated Edit Director, timeline/EDL, FFmpeg assembly, Dashboard, audio, script, or publishing governance. Pixabay, Pexels and Wikimedia Commons integrations, API keys and provider architecture were retained.

No production render, provider download/search, external publishing, commit or push was performed as part of this task. The contact-sheet QA below inspects already-downloaded files from an earlier run.

## Baseline

The accepted baseline was 14/14 shots classified as `motion_graphic`, zero stock clips selected, repeated MoE diagrams and generic gradient fallbacks. A later existing failed run contained four downloaded Pixabay candidates, but its storyboard selected only 10 local graphics and four gradients:

- Existing run: `20261115-153459-how-mixture-of-experts-models-route-toke`
- Manifest: `failed` at render stage; no completed production video.
- Storyboard: `needs_review`; 14 scenes; 10 motion graphics; 4 gradients.
- The four downloaded stock candidates were `stock_pixabay_002.mp4`, `stock_pixabay_003.mp4`, `stock_pixabay_012.mp4`, and `stock_pixabay_013.mp4`.

## Changes

### 1. Beat and visual-intent relevance

- `build_scene_brief` now preserves an explicit `visual_intent` (falling back to the existing `visual_purpose`).
- Search candidate generation prioritizes the explicit visual intent.
- `validate_asset_relevance` scores query overlap (35%), visual-intent overlap (40%) and narration overlap (25%). It evaluates title, description, tags and available source/author metadata. The numeric score is lexical evidence only; it is not represented as semantic vision approval.
- Pixabay ranking now includes visual-intent and narration metadata in addition to tag overlap, portrait fit, resolution and duration.
- Pexels ranking uses available title/description/tags, page URL and creator metadata. When the provider supplies no usable subject metadata, lexical confidence is low rather than being promoted by orientation alone.
- Wikimedia query matching now uses title, ObjectName and ImageDescription metadata. Author, credit, licence, licence URL, file page and source URL continue to be retained.

### 2. Cache and deduplication

- Pixabay cache identity is normalized for case/whitespace and versioned.
- Wikimedia search results now use a normalized, versioned 24-hour cache.
- Existing asset-ID and Wikimedia-title reuse prevention remains in place.
- Consecutive external footage is compared using a representative-frame difference hash. A candidate is rejected when the immediately previous external asset is composition-identical/near-identical (dHash distance <= 3). If frame decoding fails, this advisory check does not replace or weaken rights/vision review.

### 3. Offline asset QA

New `app.visuals.asset_qa` inspects existing storyboard assets and emits:
- ffprobe codec, dimensions, frame rate, duration, audio-stream presence and file size;
- expected/usable duration and duration coverage;
- SHA-256 exact-duplicate identity;
- representative-frame dHash and adjacent composition similarity;
- provider/media-type distribution;
- per-asset thumbnails and a contact sheet;
- a machine-readable `asset_qa.json` report.

Run it against an existing storyboard without launching a render:

```bash
venv/bin/python -m app.visuals.asset_qa \
  --storyboard outputs/runs/<run-id>/shots/storyboard/storyboard.json
```

### 4. Vision review resilience

- 429 and transient 5xx/network failures receive bounded exponential backoff.
- Numeric and HTTP-date `Retry-After` values are respected, within the configured maximum wait.
- Permanent 4xx responses are not retried.
- Review outcomes expose explicit statuses such as `disabled`, `unsupported`, `unavailable`, `rate_limited`, `invalid_response` and `reviewed`, plus attempt counts.
- Vision prompts include the exact visual intent and metadata as context, while requiring inspection of visible pixels. Metadata alone is not treated as proof of relevance.

## Before/after examples

These are deterministic unit-test examples, not claims of a new live provider run.

| Case | Before | After |
|---|---|---|
| Narration: “Cold plates cool GPU servers”; intent: “show liquid-cooled GPU server racks” | Candidate ranking primarily followed query/tag overlap and geometry | Candidate metadata matching liquid cooling, cold plates and GPU racks receives a stronger intent/narration score |
| Wikimedia title is generic, but ImageDescription says “Liquid cooled GPU server rack in a data center” | Query match examined the title only and could reject it | Title, ObjectName and description metadata contribute to query match; the actual image still requires visual review |
| Adjacent candidate files s02/s03 and s12/s13 in the existing run | Duplicate compositions were not surfaced in a dedicated asset QA report | SHA-256 and dHash both identify the pairs as exact duplicates; the resolver now rejects a near-identical adjacent external candidate |
| Repeated search phrase with case/whitespace differences | Separate cache keys could be created | Normalized, versioned cache keys reuse the same cached search result |

## Existing downloaded-asset QA

The existing run's downloaded Pixabay candidates were inspected without making network calls or rendering a video.

- QA output: `outputs/runs/20261115-153459-how-mixture-of-experts-models-route-toke/shots/storyboard/asset_qa_downloaded/asset_qa.json`
- Contact sheet: `outputs/runs/20261115-153459-how-mixture-of-experts-models-route-toke/shots/storyboard/asset_qa_downloaded/asset_qa_contact_sheet.jpg`
- Assets inspected: 4 Pixabay MP4 files.
- Missing files: 0.
- Duration shortfalls: 0.
- Adjacent exact duplicate pairs: s02/s03 and s12/s13.
- Adjacent composition similarity: both pairs had dHash distance 0.
- The contact sheet visibly confirms two repeated compositions.

Important limitation: the old failed run's storyboard had not retained the rejected candidates' original provider title/description/tag payloads, licence, credit/author or source URL. Its QA records therefore identify the downloaded files and their planned narration/query, but cannot reconstruct metadata that the earlier run never persisted. These candidates were not selected into the storyboard and are not eligible for publishing or reuse until provider provenance and licence metadata are recovered and verified.

## Files changed in this task

- `app/visuals/chain.py` — visual-intent query generation, metadata-aware relevance/ranking, adjacent composition rejection, normalized Pixabay cache key.
- `app/visuals/stock_fetcher.py` — Wikimedia title/ObjectName/description matching and 24-hour search cache; existing attribution/licensing fields preserved.
- `app/visuals/vision_review.py` — bounded retry/backoff, Retry-After parsing, explicit review status and visual-intent-aware prompt.
- `app/visuals/storyboard.py` — persists visual intent and available provider metadata into storyboard records.
- `app/visuals/asset_qa.py` — new offline metadata/duration/dedup/contact-sheet QA utility.
- `tests/test_visual_asset_metadata.py` — metadata relevance, visual-intent ranking, Wikimedia description matching and cache tests.
- `tests/test_visual_asset_qa.py` — ffprobe metadata, usable-duration coverage, exact/near-duplicate detection and missing-file reporting tests.

## Test results

Command:

```bash
venv/bin/python -m py_compile app/visuals/asset_qa.py app/visuals/chain.py app/visuals/stock_fetcher.py app/visuals/storyboard.py app/visuals/vision_review.py tests/test_visual_asset_qa.py tests/test_visual_asset_metadata.py
venv/bin/python -m pytest -q \
  tests/test_visual_asset_qa.py \
  tests/test_visual_asset_metadata.py \
  tests/test_visual_chain.py \
  tests/test_query_dedup.py \
  tests/test_storyboard.py \
  tests/test_storyboard_pipeline_integration.py \
  tests/test_visual_provider_fallback.py \
  tests/test_visual_classification_regression.py \
  tests/test_shot_plan.py \
  tests/test_visual_quality.py
```

Result: **154 passed, 1 skipped, 54 subtests passed**. Python compilation passed.

## Boundaries verified

The following files were already dirty before this task and remain untouched by this task:
- `app/render/edit_director.py`
- `app/render/timeline.py`
- `app/render/ffmpeg_tools.py`
- `app/render/assembly.py`
- `tests/test_edit_director.py`
- `tests/test_editorial_timeline.py`

No Dashboard, audio, script, or publishing-governance files were edited. No production run, external publishing, commit or push was initiated.

## Remaining gaps / risks

1. No new production render was run by explicit instruction. Therefore the new selection/scoring changes have not yet been demonstrated in a fresh end-to-end video.
2. The current vision-review lock serializes calls within a process; simultaneous independent processes may still compete for the same provider quota. Bounded 429 retries remain the safety net.
3. Pexels does not consistently expose descriptive title/tags in its video search response. Missing metadata is treated conservatively; this can reduce Pexels acceptance until visual review confirms the candidate.
4. dHash is a coarse composition detector, not a semantic visual model. It can miss visually similar footage with different frames or flag genuinely different footage with similar composition. The threshold is deliberately conservative and applies only to adjacent external assets.
5. The old run did not persist the original metadata for rejected candidates. Future attempts will have richer storyboard metadata for selected assets, but rejected-candidate metadata still needs a durable attempt ledger if full auditability of every rejected search result is required.
6. Live provider rate-limit behavior was not exercised in this no-network task. Retry behavior is covered by unit tests; provider quota and actual API response headers remain environment-dependent.
