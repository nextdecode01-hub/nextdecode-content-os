# Phase 10.1 — Research Quality Hardening

Date: 2026-10-30
Scope: the seven defects found in the Phase 10 review. Phase 9 audio files, defaults, behaviour and tests were not touched.

## 1. Root cause of the two biggest issues

Both came from one design mistake: corroboration was measured with **whole-page n-gram Jaccard**. A narration sentence paraphrases its source, so the score for a genuine NIST confirmation of an Airia claim was **0.0062–0.0114** against a 0.18 threshold. Real evidence was invisible, and the only claims that ever matched were verbatim copies — which is why everything stayed pinned to one publisher.

The fix is anchor-level matching: extract the elements that actually carry a fact (dates, numbers, versions, named entities), require the decisive ones to appear in the other publisher's page, and store the page sentence that contains them as the supporting excerpt.

## 2. Issue-by-issue outcome

| # | Issue | Fix | Result |
|---|---|---|---|
| 1 | Claim 1 was nav + headline + byline | `clean_article_text()` strips the US-government banner, `All posts`, bylines, bare URLs, breadcrumb dates and the title echo; `is_boilerplate()` rejects menu-word runs, capitalised headline runs and citation fragments; sentences starting lowercase are dropped | **27 furniture sentences rejected** on the fixture; claim 1 is now `"The NIST AI Risk Management Framework has emerged as…"` |
| 2 | All 14 claims from one source | `research_topic()` now extracts from **every** ranked page and interleaves them round-robin with a 5-per-page cap, then merges cross-source duplicates | **1 publisher → 3** (`airia.com` 5, `www.nist.gov` 4, `airc.nist.gov` 1) on the fixture |
| 3 | NIST pages never attached as evidence | `lineage.extract_anchors()` + `anchor_support()`; `independent_confirmations()` counts distinct **publishers** with a full decisive match | **0 → 6 claims independently corroborated**, each with the exact supporting sentence stored (50 support records, 0 without an excerpt) |
| 4 | Compound claims | New `app/research/atomic.py`: splits coordinated clauses at verbatim boundaries, rejects truncated or subject-only fragments | **3 atomic claims** in the fixture, e.g. `"released by the National Institute of Standards and Technology in January 2023"` separated from `"is a voluntary framework designed to help…"`; every piece is a substring of its parent (`is_substring_of`) |
| 5 | `factual=false` on a factual sentence | `looks_factual()` now also fires on a named body doing something (practice verb + entity) | The auditors/benchmark sentence is classified factual; `"The office lights hum at night."` and `"We think this is a good idea"` still correctly non-factual |
| 6 | Empty `retrieved_at` | `fetch_url()` stamps `retrieved_at`; the ledger carries it per source | Every source record has an ISO timestamp, e.g. `2026-10-30T02:38:39+00:00` |
| 7 | HTTP 406 on the NIST PDFs | One retry with document content negotiation on the same public URL (no paywall, robots or rate-limit evasion); if the server still refuses or serves an unparsed PDF, the source is marked `blocked` + `manual_review_required` with **empty text** | In the fresh run the retry got through and the PDF is reported as `unsupported content-type: application/pdf - PDF is not parsed here, read it manually before citing`. Nothing was invented for it |

## 3. Old versus new, same fixture

| Measure | Phase 10 | Phase 10.1 |
|---|---|---|
| Claims in ledger | 14 | 10 |
| Distinct claim publishers | 1 | 3 |
| `supported` | 0 | 5 |
| `partially_supported` | 14 | 5 |
| `conflicting` / `unverified` / `outdated` | 0 / 0 / 0 | 0 / 0 / 0 |
| Claims with independent corroboration | 0 | 6 |
| Support records carrying an exact excerpt | 14 (origin only) | 50, none missing |
| Boilerplate sentences rejected | 0 (they became claims) | 27 |
| Atomic claims derived from compound sentences | 0 | 3 |
| Sources with a retrieval timestamp | 0 of 5 | 5 of 5 |
| Unresolved conflicts | 0 | 0 |
| Cutout rights | 1 blocked (unknown) | 1 blocked (unknown) |

Source count is not the metric — five URLs were already fetched in Phase 10 and produced zero corroboration. Genuinely independent corroboration went from 0 to 6.

## 4. Fresh live run (same topic, new code)

`research_topic("NIST AI risk management framework adoption")` → verdict `sufficient`, 5 sources, 10 claims from 3 publishers (`aisecurityandsafety.org` 5, `www.nist.gov` 4, `airc.nist.gov` 1): 5 `supported`, 2 `partially_supported`, 3 `outdated` (date-type claims past the 730-day window → decision `research_more`), 0 conflicting, 6 independently corroborated, 1 claim without a publication date, 1 narration sentence flagged for proportionality.

Storyboard preview: 4 scenes, 4/4 linked to claim IDs, 1 source cutout, **rights gate blocks it** (`aisecurityandsafety.org` carries no reuse statement) → `needs_review`. The duplicate-claim guard also fired correctly (`s01: claim clm_a52b6624ed already used by s00`).

Artifacts: `outputs/phase10_evidence/{claim_ledger.json, source_manifest.json, research.json, work/storyboard/storyboard.json, work/storyboard/contact_sheet.jpg, storyboard/cutouts/*.png}`.

## 5. Files changed

- `app/research/lineage.py` — anchor extraction, `anchor_support()`, publisher-level independence, subject-scoped conflict detection
- `app/research/desk.py` — `clean_article_text()`, `is_boilerplate()`, retrieval timestamps, refusal retry + manual-review path, all-source extraction with round-robin, `merge_duplicate_claims()`
- `app/research/atomic.py` (new) — verbatim atomic clause splitting
- `app/research/claims.py` — `support` / `contradict` records per claim, `atomic_of`, `also_reported_by`, summary counters for corroboration and open conflicts
- `app/script/evidence.py` — practice-verb + entity factual classification
- `app/visuals/cutouts.py` — dated claims are cutout-worthy material
- `tests/test_research_quality.py` (new, 22 tests) + `tests/fixtures/phase10_nist_research.json` (the real Phase 10 bundle, now a regression fixture)
- `tests/test_production_reliability.py` — `test_fetch_url_rejects_http_errors` updated to the new contract: still rejects the error, and additionally asserts the manual-review flag and that no text was fabricated

Architecture is unchanged: no new subsystem, no storage layer, no pipeline rewrite.

## 6. Safeguards kept

- A claim is `supported` only when a **different publisher** matches all decisive anchors. A test asserts that adding a source that shares nothing decisive leaves the status byte-identical, so more fetched URLs can never inflate confidence.
- Derivative coverage ("according to a company announcement") still counts as one voice, not corroboration.
- Conflicts are preserved with both values and both excerpts; nothing is averaged into a false consensus.
- Rights gate unchanged: unknown reuse rights block publish-ready, and attribution is not treated as permission.
- Approvals remain bound to the scene digest + script hash + ledger hash.
- Publishing stays disabled; nothing was staged, committed or pushed.

## 7. Phase 9 overlap

None. Phase 10.1 touched only `app/research/*`, `app/script/evidence.py`, `app/visuals/cutouts.py` and the two research tests. No file owned by Phase 9 (`app/voice/provider.py`, `app/render/ffmpeg_tools.py`, `app/render/assembly.py`, `pipelines/short.py`, the voice/mix path in `app/script/pipeline.py`, `tests/test_audio_*`, `tests/test_voice_naturalness.py`, `tests/test_phase6_voice_package.py`, `tests/test_render_qa.py`, `tests/test_audio_diagnostics.py`) was modified, and all of those suites are green inside the full run.

## 8. Tests

Full suite: **368 passed, 1 warning, 11 subtests passed in 122.01s** (`PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q`), up from 346. The warning is the pre-existing `google.generativeai` deprecation notice. Targeted evidence run (`test_research_quality`, `test_source_lineage`, `test_claim_ledger`, `test_evidence_script`, `test_cutout_rights`, `test_storyboard`, `test_production_reliability`): 80 passed in 5.33s.

## 9. Remaining limitations

- **Anchor matching is string-level.** It proves the same date/number/entity appears in both places; it does not prove the two pages mean the same thing. A human still reads the excerpt pair before publishing.
- **PDFs are not parsed.** They are now reported for manual review instead of failing silently. Adding a PDF text extractor would be a new dependency and needs approval.
- **No date means no freshness check.** Such claims are flagged, not guessed.
- **`outdated` uses a fixed 730-day window** for time-sensitive types; a topic with genuinely stable dates will over-flag, and the window is a parameter, not a learned value.
- **Claim extraction still depends on sentence splitting.** Text with no punctuation between the nav bar and the article can still fuse, which is why the furniture rejection is pattern-based rather than structural.
- **Corroboration breadth is capped by what the desk fetches** (5 sources). Widening search is a research-stage change, out of scope here.
- Perceptual and editorial judgment — is this the right excerpt, is it fair out of context — remains a human decision. Nothing in this phase claims otherwise.
