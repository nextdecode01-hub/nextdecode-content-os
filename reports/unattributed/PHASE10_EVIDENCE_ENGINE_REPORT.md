# Phase 10 — Evidence-First Research & Visual Verification

Date: 2026-10-30
Status: implemented and tested; a real-topic example is included. Phase 9 audio files and settings were not touched.

## 1. What was built

| File | Role |
|---|---|
| `app/research/lineage.py` | Canonical URLs, wire/press-release detection, shingle similarity, source clustering, independence counted per publisher |
| `app/research/claims.py` | Claim ledger: stable IDs, excerpt + character offset, source metadata, lineage notes, status/decision, script mapping, JSON persistence, ledger digest |
| `app/script/evidence.py` | Sentence→claim mapping, causation/forecast/number proportionality flags, unsupported-factual detection, coverage |
| `app/visuals/cutouts.py` | Source-cutout card renderer (ffmpeg drawtext, no new dependency), reuse-rights classification, publish-ready gate, balanced selection budget |
| `app/visuals/storyboard.py` (modified) | Scenes carry `claim_ids`, `evidence`, `evidence_visual`, `reuse_rights`, `attribution`; approvals bind scene digest + script hash + ledger hash |
| `app/render/assembly.py` (modified) | `render_video(..., evidence=...)`: builds cutouts for qualifying scenes, skips b-roll fetching for them, reports the rights gate |
| `app/script/pipeline.py` (modified) | Builds and writes `research/claim_ledger.json`, logs evidence warnings, passes the ledger to the render, records an `evidence` metadata block |

No duplicate research, script, asset or storage subsystem was created: the ledger consumes the existing `app/research/desk.py` output, the storyboard keeps its existing structure and review gate, and assets still flow through `app/visuals/chain.py`.

## 2. Behaviour

- **Statuses:** `supported` (≥1 independent publisher, different from the claim's own), `partially_supported` (single source, or coverage that only repeats the announcement), `conflicting` (desk contradiction on the same metric), `unverified` (no verbatim excerpt), `outdated` (time-sensitive claim past the freshness window, default 730 days).
- **Decisions:** include / qualify / research_more / exclude, mapped from the status.
- **No fabrication:** missing publication dates stay empty with `date_confidence: "unknown"` and a flag; a quote that is not in the source text becomes `unverified`; a claim whose source is absent from the fetched list is flagged.
- **Independence:** identical text across hosts clusters into one voice; same-publisher pages count once; a report that only repeats someone else's announcement ("according to a company announcement") is marked `dependent` and does not confirm.
- **Cutouts:** only claims of type statistic / funding / forecast / announcement / quote / research with a supported or partially supported status are eligible; at most 34% of scenes and never two adjacent scenes; the card shows publisher, date, wrapped excerpt and URL.
- **Rights gate:** government sources and explicit open-licence markers are `permitted`; everything else stays `unknown`, `publish_ready` is false, and the storyboard records a blocking review reason. Attribution alone is never treated as permission.
- **Approval safety:** an approval records the contact-sheet hash, scene digest, script hash and ledger hash. Editing the script or ledger invalidates the approval.

## 3. Acceptance criteria — evidence

| # | Criterion | Where demonstrated |
|---|---|---|
| 1 | Traceability | `tests/test_claim_ledger.py::TraceabilityTests`; real ledger: 14/14 claims with ID, quote, offset, source |
| 2 | No fabricated evidence | `NoFabricationTests` (missing date, quote absent from source, claim source not fetched) |
| 3 | Independence | `tests/test_source_lineage.py::SyndicationTests`, `IndependenceTests` |
| 4 | Conflict handling | `ConflictTests` — status `conflicting`, decision `research_more`, both sources kept |
| 5 | Freshness | `FreshnessTests` — old statistic → `outdated`; old announcement is not forced stale |
| 6 | Evidence→script mapping | `ScriptBindingTests`, `tests/test_evidence_script.py::MappingTests`; real ledger: 0 unmapped narration sentences |
| 7 | Balanced visual selection | `tests/test_cutout_rights.py::SelectionTests` (budget, no adjacency, weak claims excluded); real preview: 1 cutout in 3 scenes |
| 8 | Faithful excerpts | Cards quote the verbatim excerpt (42-word limit with an explicit `...`); `CardRenderTests` |
| 9 | Rights gate | `RightsTests`, `StoryboardEvidenceTests::test_blocked_cutout_rights_show_up_in_review`; real preview: 1/1 cutout blocked |
| 10 | Attribution | Card shows publisher, date, URL; `attribution_lines` recorded in storyboard and metadata |
| 11 | Version safety | `test_approval_is_invalidated_by_a_new_script_hash` / `_ledger_hash` |
| 12 | Regression safety | Full suite 346 passed; Phase 7/8/9 tests unchanged |
| 13 | Human-review honesty | This report separates automated checks (§4) from listening/visual judgment (§6) |

## 4. Real-topic example

Topic: **"NIST AI risk management framework adoption"**, run against the live web through the existing research desk.

- Research verdict `sufficient`, 5 sources fetched, 14 claims.
- Sources: `airia.com` (blog), `www.nist.gov` ×2 (government), `airc.nist.gov` ×2 (government).
- Two NIST PDF URLs returned **HTTP 406** to the fetcher; recorded in `errors`, not retried, not invented.
- Ledger: **14 claims — 0 supported, 14 partially_supported, 0 conflicting, 0 unverified, 0 outdated**, all decision `qualify`. Every claim came from the single blog source, so the ledger correctly refuses to call them confirmed.
- Claim types: 10 statement, 2 capability, 1 announcement, 1 date.
- 5 source clusters, each a single outlet (no syndication in this sample).
- Storyboard preview: 3 scenes, **3/3 linked to claim IDs**, 1 source cutout (the NIST framework description), **rights gate blocks that cutout** because `airia.com` has no reuse statement, review status `needs_review`.

Artifacts under `outputs/phase10_evidence/`:

- `claim_ledger.json` — full ledger
- `source_manifest.json` — sources and clusters
- `research.json` — raw desk output
- `storyboard/storyboard.json` + `work/storyboard/contact_sheet.jpg` — preview
- `storyboard/cutouts/clm_84b35cb468.png` — the rendered source card

## 5. Tests

Full suite: `346 passed, 1 warning, 11 subtests passed in 107.10s`
(`PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q`). The warning is the pre-existing `google.generativeai` deprecation notice.

New tests (52) in `tests/test_source_lineage.py`, `tests/test_claim_ledger.py`, `tests/test_evidence_script.py`, `tests/test_cutout_rights.py`, all deterministic except the ffmpeg card renders (skipped when ffmpeg is absent).

## 6. What automated checks do not prove

- The ledger proves that wording is traceable and proportionate **to the fetched evidence**, not that the evidence is true.
- The cutout is a faithful text excerpt, not a screenshot of the page; a human still has to confirm the excerpt is not misleading out of context.
- Rights classification is conservative pattern matching. `unknown` is the default and blocks publish; a human must record the permission basis before anything ships.
- No external publishing was enabled. Nothing was staged, committed or pushed.

## 7. Limitations

- `app/research/desk.py` extracts claims from the primary page and at most one secondary page, so multi-source verification is bounded by what that stage fetches. Wider corroboration would mean changing the research stage itself; that was out of scope here.
- PDF sources are rejected by some servers (HTTP 406 in this run). HTML sources work.
- The cutout card is text-on-background. Cropping a page screenshot was deliberately not implemented: it needs a headless renderer and a copyright review per source.
- Freshness uses publication metadata when the page provides it; sites without dates are flagged, not guessed.
- The production default remains `MUSIC_BED=off`, Phase 9 mixing settings untouched, and no audio file was modified in this phase.
