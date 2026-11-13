# Phase 10.1.1 — Evidence Verification Hardening (final fixes)

Date: 2026-10-30
Scope: the five review findings, plus the two confirmed code defects (TOC/card-metadata contamination, independent-corroboration overcount) and the reporting/artifact corrections that followed. Phase 9 audio files, defaults, behaviour and tests were not touched. Nothing was staged, committed or pushed, and publishing stays disabled.

## 1. Files changed

| File | Change |
|---|---|
| `app/research/desk.py` | TOC/card-metadata machinery: `_TOC_MARKERS`, `_TOC_BREAK_RE`, `_TOC_METADATA_RE`, `_is_toc_or_metadata()`; `is_boilerplate()` rejects such sentences; `clean_article_text()` inserts boundaries around navigation blocks and drops marker sentences without deleting ordinary prose. Also `fetchable_url()` plus scheme validation inside `_dedupe_source_urls()`, and `research_topic()` now reports rejected candidate URLs instead of letting them reach the HTTP client |
| `app/research/claims.py` | `_independently_corroborated()` excludes the claim's own institution and partial evidence; `summarize()` uses it for `independently_corroborated` |
| `app/research/lineage.py` | `_match_key()` percent expansion, `registrable_host()` / `institution_of()` / `same_institution()`, `entity_groups()`, completeness rule in `anchor_support()`, institution-based independence, percent/measure boundary fix, month names not treated as subjects |
| `tests/fixtures/polluted_nist_guide.txt` | new — 918-character verbatim reproduction of the polluted guide text that produced `clm_a52b6624ed` |
| `tests/test_research_quality.py` | new `TocContaminationTests` (8 tests) + `RightsAndCutoutTests.test_card_excerpt_follows_the_cleaned_quote` |
| `tests/test_evidence_verification.py` | new `CorroborationCounterTests` (5 tests); 22 Phase 10.1.1 tests retained |
| `tests/test_research_feeds.py` | test-only: deterministic mocks, contract-aligned assertions, RSS/Atom/duplicate/malformed-XML/timeout/HTTP-failure coverage (see §7) |
| `reports/unattributed/PHASE10_1_1_EVIDENCE_VERIFICATION_REPORT.md` | this report, corrected: fixture and live-run results separated, exact IDs and counts |

`app/research/atomic.py`, `app/script/evidence.py`, `app/visuals/cutouts.py`, `app/visuals/storyboard.py` and `app/render/assembly.py` were inspected and left unchanged.

## 2. Fix 1 — TOC and card-metadata contamination

Root cause: `_sentence_split()` only splits before `[A-Z0-9(]`. A real sentence ending in `.` was followed by lowercase navigation (`governance 7 sections Last updated : March 28, 2026 Table of Contents …`), so prose and furniture fused into one "sentence" and became `clm_a52b6624ed`.

What changed in `clean_article_text()`:

- Navigation markers (`Table of Contents`, `Frequently Asked Questions`, `FAQ`, `Key Takeaways`, `On This Page`, `Jump to Section`, `N sections`) get their own sentence boundaries — a break is inserted *before and after* each marker.
- Sentences that are navigation/card metadata are dropped; sentences shorter than four words are dropped.
- Prose before and after the block is preserved. The rule is marker-based, not "contains the word sections": "7 sections of guidance", "updated twice" and "Its contents describe…" survive. A sentence whose subject *is* the table of contents is classified as furniture — a deliberate choice, asserted by its own test.
- `is_boilerplate()` rejects marker sentences before claim extraction, so a fused sentence can never reach the ledger.

Measured effect:

- `tests/fixtures/polluted_nist_guide.txt` (the exact 918-character polluted text) now yields no claim containing `Table of Contents`, `Last updated`, `N sections` or `Frequently Asked Questions`; prose before and after survives.
- In the fresh run (§5.4) there are **zero** marker hits across all ledger `narration`/`quote` fields and all storyboard narrations.
- `clm_a52b6624ed` is no longer produced. Claim IDs hash `topic + quote + url`, so a cleaned quote necessarily gets a new ID; the old ID and any approval bound to it are invalidated by design, not silently reused.

## 3. Fix 2 — independent corroboration counter

`independently_corroborated` counted a claim whose only full match came from a page of the claim's own institution. `_independently_corroborated()` now requires a `corroboration` record with `strength == "full"` from an institution other than the claim's own (`lineage.institution_of()` normalisation retained), and `summarize()` uses that predicate.

Measured effect on the reviewed live ledger: recomputing `summarize()` on `outputs/phase10_evidence/claim_ledger.json` gives **4**, not the 5 stored by the previous build. The four are `clm_a4218d5a2a`, `clm_054433a614`, `clm_2aeab69f5e`, `clm_fb2f1f8758`; `clm_e18e287f71` no longer counts because its match was a same-institution NIST page.

## 4. Fix 3 — research candidate URL validation

This item came back from the secondary agent as a conflict report (`reports/opencode/SECONDARY_URL_VALIDATION_CONFLICT_REPORT_2026-10-30.md`): it overlapped this workstream's active `app/research/desk.py` diff and contradicted the contract test written here, so it stopped and handed ownership back. Decision: implement it now, in this workstream, as an atomic change to the function plus the test that pins it.

Design, and why it is not the shape the report suggested:

- `fetchable_url()` is the single rule - absolute `http`/`https` with a non-empty network location. Bare hosts, `file:`, `data:`, `javascript:`, `ftp:`, empty, `None`, and `https://` (no host) are refused before the HTTP client is reached.
- Validation runs **before** de-duplication inside `_dedupe_source_urls()`, so a rejected entry can never mask an identical accepted one, and the mirror-collapse rules are unchanged.
- Nothing is invented or repaired: a schemeless string is not quietly rewritten to `https://…`, because that would fabricate a source that no feed ever named.
- `_dedupe_source_urls()` has no error channel, so `research_topic()` reports what it dropped: rejected candidates appear in `result["errors"]` as `rejected N non-fetchable candidate URL(s): …`, and if nothing fetchable remains the run fails closed with `no candidate source URLs for topic`. A rejected URL is never fetched and never silently vanishes.

Measured effect: valid HTTP/HTTPS behaviour is unchanged (live re-check of three NIST/blog pages: 3 pages fetched, 10 claims, `errors: []`); `file:///etc/passwd` and `not-a-url` candidates are now recorded and skipped; all existing dedupe expectations still hold (arXiv mirror collapse, trailing-slash and fragment collapse).

## 5. Datasets and measured results (kept separate)

Three different datasets were used, and they are not interchangeable. None of the numbers below is copied from an earlier report; each was recomputed from the file named.

### 5.1 Deterministic fixture — `tests/fixtures/phase10_nist_research.json`

Five pages, two institutions (`airia.com`, `nist.gov`), retrieved 2026-10-30. No page contains a table of contents.

| Measure | Value |
|---|---|
| Extracted claims in bundle / ledger | 14 / 14 |
| `supported` | 2 |
| `partially_supported` | 12 |
| `conflicting` / `unverified` / `outdated` | 0 / 0 / 0 |
| `independently_corroborated` | 2 |
| Temporal classes | 2 historical / 12 current / 0 forecast |
| Source pages / institutions | 5 / 2 |

The fixture contains **no** White House claim. The previous report's table (10 claims, 4 supported, 6 partial, 4/5/1 temporal) did not reproduce and is withdrawn.

### 5.2 Synthetic relationship case — `tests/test_evidence_verification.py`

`RELATION_CLAIM = "The AI RMF 1.0 is being revised as part of the White House AI Action Plan."`

- Against `HALF_RELATION_PAGE` ("… revised to address generative AI risks.") → not `full`; `missing_entities` contains `"White House AI Action Plan."`.
- Against `FULL_RELATION_PAGE` (names both subjects) → `full`.

This is a unit-level anchor test, not a fixture or live result. The previous report incorrectly presented it as a result "against the same five pages".

### 5.3 Live run #1 — `outputs/phase10_evidence/` (preserved, not modified)

Fetched `2026-10-30T04:15:32Z`, ledger created `2026-10-30T04:21:57Z`. Sources: the aisecurityandsafety.org guide plus three `nist.gov` pages and one `airc.nist.gov` page (five pages, two institutions). Script sha `44df6df8…9376b`; ledger sha `edb37cea…1f49` — unchanged and still matching its storyboard.

| Measure | Stored by that build | Recomputed with current code |
|---|---|---|
| Claims | 10 | 10 |
| `supported` / `partially_supported` / `outdated` | 4 / 5 / 1 | 4 / 5 / 1 |
| Source pages / institutions | 5 / 2 | 5 / 2 |
| `independently_corroborated` | **5 (defect)** | **4** |
| Temporal classes | 5 historical / 5 current | 5 historical / 5 current |
| Flagged sentences | 1 | 1 |

Claim-level facts in that ledger:

- `clm_a3c949097d` ("The AI RMF 1.0 is being revised as part of the White House AI Action Plan.") is **`outdated`**, not `partially_supported`: the sentence is a current-state claim and its NIST page is dated 2023-01-26.
- `clm_a52b6624ed` is the polluted claim produced before Fix 1. Its narration still contains the navigation text because the stored bundle already contained it; the claim is `partially_supported`, `historical`.

### 5.4 Live run #2 — `outputs/phase10_evidence_run2/` (fresh, generated with the fixes)

Fetched `2026-10-30T12:35:05Z`, ledger created `2026-10-30T12:35:08Z`. Same URL set as run #1 but a new retrieval; the blog page's publication date was not parseable this time. Script sha `c6d3ed8e…9596`; ledger sha `9ae773eb…a372`.

| Measure | Value |
|---|---|
| Research verdict / errors | `sufficient` / 0 |
| Source pages / institutions | 5 / 2 (`nist.gov`, `aisecurityandsafety.org`) |
| Claims | 10 |
| `supported` / `partially_supported` / `outdated` | 2 / 7 / 1 |
| `conflicting` / `unverified` | 0 / 0 |
| `independently_corroborated` | 2 (`clm_1e873d5b4a`, `clm_4a50a969b8`) |
| Temporal classes | 3 historical / 7 current / 0 forecast |
| Claims without publication date | 6 |
| Flagged sentences | 1 (`clm_a3c949097d`, `outdated`) |
| TOC/card-metadata markers in ledger or storyboard | 0 |

Claim IDs: `clm_7b91655500`, `clm_a3c949097d`, `clm_8d7df7bacf`, `clm_16eeee2286`, `clm_7ea0d80bcf`, `clm_1e873d5b4a`, `clm_b8d077fa81`, `clm_4a50a969b8`, `clm_0f6f50d960`, `clm_9b0ddeb5b6`.

The blog-guide sentences that were fused with navigation in run #1 are now separate, clean claims (for example `clm_16eeee2286` is "Part 2 defines the four core functions — Govern, Map, Measure, and Manage — that compose the risk management process."). Run #1 and run #2 are different retrievals of the same URLs; they are **not** "the same five pages" as the fixture, which uses `airia.com` instead of the blog guide.

## 6. Artifact consistency and S00 verification (run #2)

Generation used the existing code paths only: `desk.research_topic()` → `claims.build_ledger()` / `write_ledger()` → `motion_director.plan_shots()` → `chain.plan_scenes()` / `resolve_scene(dry_run=True)` → `cutouts.select_cutout_scenes()` / `build_source_card()` / `rights_gate()` → `storyboard.build_storyboard()`. The narration is an evidence-demo script assembled from verbatim, non-atomic, supported/partially-supported sentences; it is not a Script Studio editorial script.

Checks that passed:

- Every ledger claim's `(quote, source_url)` exists in `research.json`.
- `source_manifest.json` sources equal the ledger sources (5); clusters 5.
- Every storyboard `claim_ids` entry exists in the ledger; every `asset_path` exists.
- `sha256(script voice_text) == ledger.script_sha256 == storyboard.script_sha256` (`c6d3ed8e…9596`).
- `ledger.ledger_sha256 == storyboard.ledger_sha256` (`9ae773eb…a372`), and re-hashing the canonical ledger payload (excluding `ledger_sha256`) reproduces it. The raw file hash is a different value because the file includes that digest field; it is not the value referenced by the storyboard.
- Contact sheet written; `approved: false`, `review_status: needs_review`, no approval file exists. The gate is not bypassed.
- **S00**: `provider: source_cutout`, scene `s00`, narration "On April 7, 2026, NIST released a concept note for an AI RMF Profile on Trustworthy AI in Critical Infrastructure .", `asset_path: outputs/phase10_evidence_run2/work/storyboard/cutouts/clm_0f6f50d960.png`, linked to `clm_0f6f50d960`. No navigation text in the narration or the rendered excerpt; no review reason on S00.
- **Rights gate active**: three cutouts placed (`clm_0f6f50d960`, `clm_7ea0d80bcf`, `clm_b8d077fa81`), all `nist.gov` → `permitted`, gate `{checked: 3, blocked: 0, publish_ready: true}`. Control run on the blog claim (`clm_7b91655500`, rights `unknown`) returns `{checked: 1, blocked: 1, publish_ready: false}`, so an unknown-rights card still blocks publish-ready.

Orphan/stale cutouts identified (nothing deleted):

- `outputs/phase10_evidence/storyboard/cutouts/clm_a52b6624ed.png` — belongs to the preserved run #1 ledger, but the fixed pipeline no longer produces that claim (polluted quote). Stale relative to current code.
- `outputs/phase10_evidence/storyboard/cutouts/clm_84b35cb468.png` — orphan: the claim ID appears in no ledger (left by an earlier ad-hoc run).
- `outputs/phase10_evidence/placeholder.png` — a dry-run placeholder referenced by scenes s01–s03 of the old storyboard; not an orphan, but not a real asset.
- Run #2 has no orphans: all three cutout PNGs are referenced by scenes.

## 7. Tests

New regression tests:

- `tests/test_research_quality.py::TocContaminationTests` — markers recognised; ordinary prose with the same words kept; a TOC-subject sentence rejected; polluted run split and navigation dropped; prose before/after survives; no extracted claim carries navigation text; a real bundle yields no polluted claims; card excerpt follows the cleaned quote.
- `tests/test_evidence_verification.py::CorroborationCounterTests` — same institution alone does not count; an independent institution counts once; partial evidence never inflates the counter; many pages from one institution count as one; the counter equals the per-claim view.

Feed tests (`tests/test_research_feeds.py`, test-only): `test_research_topic_error_handling` now asserts the real `errors` contract with `search_web` mocked; RSS/Atom assertions use the real parser and `_item()` signals; added `test_bundle_reports_no_candidates_when_feeds_are_empty`, `test_bundle_reports_no_suitable_candidate_after_retries`, `test_bundle_retries_until_rank_threshold_is_met`, `test_bundle_uses_the_highest_ranked_candidate`, `test_persistent_refusal_is_reported_for_manual_review`, `test_timeout_fails_closed_without_retry`, `test_broken_xml_raises_parse_error`, `test_empty_payload_is_not_a_feed`, `test_unparseable_publication_date_does_not_raise`, `test_item_requires_a_title_and_a_url`, `test_research_topic_fetch_failures_are_recorded`, `test_claim_extraction_attributes_each_source`; vacuous either/or and conditional assertions were replaced with exact contracts.

URL-validation tests (function and contract changed together): `test_malformed_url_handling` rewritten for the new `_dedupe_source_urls()` contract (schemeless and non-web entries refused, mirrors still collapsed, exact length 3), plus `test_fetchable_url_accepts_absolute_web_urls`, `test_fetchable_url_refers_non_web_schemes_and_broken_hosts`, `test_rejected_candidate_urls_are_reported_and_not_fetched` and `test_all_candidates_rejected_fails_closed`.

Commands and results:

- `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_research_feeds.py` → **34 passed in 0.25s**.
- `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_research_quality.py tests/test_evidence_verification.py tests/test_research_feeds.py tests/test_claim_ledger.py tests/test_evidence_script.py tests/test_cutout_rights.py tests/test_storyboard.py tests/test_source_lineage.py tests/test_research_desk.py tests/test_topic_research.py tests/test_production_reliability.py tests/test_phase4_research_package.py` → **189 passed in 20.22s** (includes the dedupe/arXiv-mirror expectations in `test_production_reliability.py` and the `http://bad` fixture in `test_research_desk.py`, both of which are fetchable URLs and keep passing).
- `PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q` → **433 passed, 1 warning, 11 subtests passed in 134.88s** for the evidence work; the full suite was re-run again after the URL-validation change (see below). The warning is the pre-existing `google.generativeai` deprecation notice from `multi_model_ai.py`. The two feed tests that failed in the previous pass now assert the real contracts and pass.

Live re-check after the change (three real pages, one command, no stubs): `verdict: sufficient`, 3 sources, 10 claims, `errors: []` — valid HTTP/HTTPS fetching is unchanged.

## 8. Remaining limitations

- **Percentages are not detected as unsupported numbers.** `find_unsupported_numbers()` matches `2x` but not `95%`: the token regex ends in `\b` after `%`, the same boundary mistake fixed in `lineage` during Phase 10.1.1. Found while strengthening the feed tests; not fixed here because it is outside the two authorised defects. `tests/test_research_feeds.py::test_find_unsupported_numbers` asserts the current behaviour and points at this report.
- **URL validation checks the scheme and host presence, not host legitimacy.** `http://` is still accepted (some publishers serve plain HTTP and redirect), and unusual but well-formed hosts such as `http://intranet` or `http://localhost:8000/x` pass the rule. Blocking private-loop and link-local addresses is a deliberate non-goal here because it would need an allow/deny policy the research contract does not define; it belongs with the production fetch layer if wanted.
- **The cutout selector has no per-claim guard.** `select_cutout_scenes()` can nominate the same claim for two non-adjacent scenes. The run #2 generator de-duplicated by `claim_id` before rendering; production code was not changed.
- **The two NIST PDFs were not reached in run #2.** `max_sources` (5) filled before the PDFs were processed, so no `unsupported content-type` error was recorded this time; run #1 reported both for manual review. PDFs remain unread.
- **Run #2 scenes without a cutout are dry-run placeholders** (motion cards and gradient captions); no stock network provider was called, and the storyboard says so in its review reasons.
- **The run #2 script is a demo narration**, not an editorial script; it exists to exercise the evidence chain end to end.
- **String-level matching, 60% thresholds and tense heuristics** are unchanged from Phase 10.1.1: a full anchor match proves the same dates, numbers and subjects appear in both places, not that both sentences assert the same thing; a paraphrase can still be admitted or a genuine confirmation rejected; a historical fact written in the present tense can still be flagged `outdated`.
- **A missing publication date still blocks freshness checks** (6 claims in run #2), and is flagged rather than guessed.

## 9. Safeguards confirmed

- **Human approval preserved.** Storyboard approvals remain bound to contact-sheet hash, scene digest, script hash and ledger hash; `approve_storyboard()` still requires a named reviewer and refuses a blocked package. The fresh package is `needs_review` with no approval file.
- **Rights gate intact.** Unknown or incompatible reuse rights still block publish-ready; the control check in §6 demonstrates it, and attribution is still not treated as permission.
- **No inflation.** No page from a claim's own institution can corroborate it; partial evidence never counts as complete corroboration.
- **Publishing disabled.** No upload path was touched or invoked.
- **Phase 9 protected.** This workstream modified no Phase 9 file: `app/voice/provider.py`, `app/render/ffmpeg_tools.py`, `app/render/assembly.py`, the voice/mix path in `app/script/pipeline.py`, `tests/test_audio_quality.py`, `tests/test_audio_diagnostics.py`, `tests/test_render_qa.py`, `tests/test_voice_naturalness.py` and `tests/test_phase6_voice_package.py` are untouched and pass in the full run. (`pipelines/short.py` was untouched here too; it was changed later, in the separate Strict Fail-Closed task, and only in its orchestration/exit-status logic - no voice, mix, SFX or loudness default was altered.)
- **Git safety.** No staging, commit, push, branch switch or destructive command was run. Existing outputs were preserved; run #2 was written to a new directory.

## 10. Final git status

Untracked (new this pass): `outputs/phase10_evidence_run2/`, `tests/fixtures/polluted_nist_guide.txt`, this report. Modified (this pass): `app/research/desk.py`, `app/research/claims.py`, `tests/test_research_quality.py`, `tests/test_evidence_verification.py`, `tests/test_research_feeds.py`. All pre-existing staged renames, unstaged changes and untracked work remain as found; nothing was deleted.
