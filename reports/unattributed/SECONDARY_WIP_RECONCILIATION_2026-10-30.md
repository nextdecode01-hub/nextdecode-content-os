# WIP Reconciliation — Research Feed Workstream vs OpenCode Audit (2026-10-30)

Read-only reconciliation. Nothing staged, committed, overwritten or deleted. Git state as-inspected this session.

---

## 1. Filing convention (hamesha)

- Har secondary report aaj ke date-stamped file me docs/ folder me save kiya jayega (standalone printable).
- Is file ke sath: file write karke pehle ye small-screen check — "file open karke users kitna file wala banaya (jo user ne approve kiya) — file to be ok" — isliye yahi file format: code-report style, table me direct "Go/ Fix" ka farak.

## 2. OpenCode's own footprint (kya maine touch kiya)

| File | Status of Me |
|---|---|
| `reports/opencode/SECONDARY_AUDIT_RESEARCH_FEEDS_2026-10-30.md` | Created by me (docs-only, at user request) |
| `reports/unattributed/SECONDARY_WIP_RECONCILIATION_2026-10-30.md` | Created by me (this file) |
| Koi code file, test, script | **Nahi** — I did not create/modify `scripts/*`, `tests/test_research_feeds.py`, `tests/fixtures/*`, or any `app/research/*` code. Mera pura audit session me koi repo-code modification nahi hua. |

Documented bas itna: attribution untracked scripts/tests ki daudi me main sirf path + content report kar sakta hoon. Confirmed via Git, current working tree.

---

## 3. File-by-file WIP reconciliation

| # | File (state) | What it holds right now (current tree) | Reconciliation vs OpenCode findings | Isolation vs Evidence-Integrity (10.1/10.1.1) |
|---|---|---|---|---|
| 1 | `app/research/desk.py` — `M` (unstaged, +394/−18) | Phase 10.1 research-quality diffs already in working tree: retry-on-refusal fetch (`fetch_url`), `blocked`/`manual_review_required` flags, multi-source research_topic (round-robin + per-source cap), boilerplate cleanup (clean_article_text/is_boilerplate), atomic (atomic.split_atomic usage) — **SAHI hain**, test_green hai. **Abhi bhi feed-stubs `:29-52` aur dead block `:912-966` yahi par hai** (audit article me unko CONFIRMED bataya). | Isi file me **two workstreams** ki boundary: Phase 10.1 evidence-integrity work (upper half) + Phase 10.1.1 feed-fix (lower-half stubs). Feed-fix scripts un-stubs ko replace karte hain aur research_topic/fetch_url regions ko touch NAHI karte. | **Shared file: ek hi overlap.** Evidence regions se stubs fail nahi padhte; stubs ko replace karne se evidence regions badalne ho. Merge-commit sequence me (research-quality code pehle) feed fixes baad me. |
| 2 | `app/research/topics.py` — **unmodified** (kunstaged diff me NAHI) | Live production (used in production path — from pipeline.py:78 discovery). Confirms OpenCode findings on working tree: `ET.fromstring` at + `news_item` URLs discarded + duplicated citation-from-title + silent `except Exception: continue` at :268-274, :236-242. | **Feed-fix workstream primary target.** Eviden-integrity touch nahi. | Fully isolated. |
| 3 | `app/research/trends.py` — unmodified | Multi-source discovery (CLI `--demo` path). `ET.fromstring` at 3 sites (`:432`, `:745`, `:929`) — Finding 3 CONFIRMED hai. | Secondary feed workstream target. Evidence-integrity (lineage/claims) modules se koi coupling nahi. | Fully isolated. |
| 4 | `app/research/selector.py` — `M` (unstaged, only ±2 lines) | Chhota tweak (Phase 10.1 residue), feed workstream ke saath koi functional link nahi. | No overlap. | Isolated. |
| 5 | `app/script/pipeline.py` — `M` (+187) | Phase 10.1 evidence wiring (ledger step, warnings, cutouts evidence) — production research phase ko `topics.discover_topics` se chalata hai (`:78`). | Evidence-integrity workstream ka file feed changes ko **passive** touch karta hai (discovery only call karta hai, side-effect se modify nahi). | Coupling is one-way (pipeline consumes discovery). `discover_topics` me future signature change karne pe is line ko touch karna padega — current proposed feed-fix signatures ko preserve karte hain. |
| 6 | `archive/abandoned-agent-scripts/replace_feed_fetchers.py` (untracked, scripts/ workstream WIP, timestamps 02:34/03:34) | Regex rewrite def _fetch_trends/_fetch_hacker_news/_fetch_reddit/_fetch_arxiv in desk.py from stub → delegation wrappers to topics.* (`try/hasattr/except Exception: return []`). **Abhi tak EXECUTE NAHI hua** (desk stubs working tree me abhi bhi hardcode `return []`). | Finding 1 (stubs) ke liye fix, par naive error-swallowing ko feed diagnostics me le jaata hai; OpenCode recommendation: isko diversify karna — exceptions ko silently mat ghabrao, sirf print karo. `archive/abandoned-agent-scripts/replace_desk_functions.ps1` ka **abandoned partial duplicate** — the ps1 only rewrites `_fetch_trends`; the py script rewrites all 4 — no double-write got risk. | Desk.py me stub regions only tie-in — pure feed workstream; nobody in evidence-integrity calls these stubs directly (research_topic does not). |
| 7 | `archive/abandoned-agent-scripts/replace_desk_functions.ps1` (untracked) | WIP duplicate — half-fix variant of #6. Execution-order risk: agar executed after #6, harmless (duplicate path replaced no change). _Leave to the user to sync option._ | OpenCode recommends: phase 10.1.1 me ya to delete ya skip; use #6 only. | Isolated stubs only. |
| 8 | `tests/test_research_feeds.py` (untracked, created 02:34-ish per mtime earlier) | 22 tests, **2 currently FAIL** (`test_research_topic_error_handling` network-dep test, `test_malformed_url_handling` `_dedupe_source_urls` scheme check/`duplicate/` expectations). | Ya findings 2.5 ko partially pin-karta hai (DTD refusal in topics only, refusal retry present in Fay). **Naya part**: `tests/test_research_quality.py` se conflict no; 10.1 evidence test suite ko touch nahi karta. | Evidence suite run in same pytest: `tests/test_research_feeds.py` ka fail candidate (2 test) **overall suite me red rehta hai** jab tak feed-fix landing nahi hota — isolated-fix order me priority. |
| 9 | `tests/fixtures/phase10_nist_research.json` (untracked) | Phase 10.1 evidence-integrity test fixture (NIST research data) — feed workstream se koi overlap nahi. | — | Fully isolated. |
| 10 | `tests/test_research_quality.py` + `tests/test_claim_ledger.py` + `tests/test_source_lineage.py` + `tests/test_evidence_script.py` (untracked) | Evidence-integrity (10.1) tests: atomic/claims/lineage/evidence. **Green** aaj verify hua. | Feed fix un-evidence modules ko verify karega; run-suite me wo har evidence tests ke saath satisfy honge. | **Isolated** (green hai, feed changes unko test_green state at: 1 test exists per expected retesting). |
| 11 | `tests/test_production_reliability.py` — `M` | Phase 10.1 fix cover — `fetch_url` refusal semantics (HTTP 403 startswith, manual_review_required, blocked), `parse_xml` DTD test, search_web, etc. **20 passed**. | Feed-fix (Finding 4 transient retry) ko iska HTTP-403-startswith contract mitana-verify-karna hoga (non-refusal status pe retry FAIL fast; refusal pe retry with-alternate-accept already hai). F4 change evidence-string prefix preserve karega. | Coupled via `desk.fetch_url` — **not fully isolated**, but contract well-defined (refusal path vs transient path ko distinct test labels rakho). |
| 12 | `app/render/…`, `app/voice/…`, Phase 9 audio paths, publish paths — untouched by feed workstream. | — | — | Fully isolated — audit findings me koi publish/audio call path imported nahi hota. |

---

## 4. OpenCode findings vs current tree — status matrix

| Finding | Working-tree status | Qoder's WIP me | Working tree me still-open item |
|---|---|---|---|
| F1 stubs | CONFIRMED — desk.py:29-52 stubs not yet replaced | archive/abandoned-agent-scripts/replace_feed_fetchers.py **prepared but unexecuted**; archive/abandoned-agent-scripts/replace_desk_functions.ps1 (abandoned partial) | Apply execution after review |
| F2 dead block bundle | CONFIRMED | abhi koi script de-it ka rule nahi; manually delete-only | delete desk.py:912-966 |
| F3 `trends.py` unguarded XML | CONFIRMED (3 sites) | koi script ne touch nahi | 3 `ET.fromstring` call sites → guarded parser |
| F4 transient retry missing | CONFIRMED | — | desk.fetch_url 2-attempt transient (Timeout/Conn/429/502/503/504) |
| F5 silent feed exceptions | CONFIRMED | — | topics./discover/search har exception swalla per-source failure note |
| Google-Trends topic URL defect | CONFIRMED (feed-cite-same-feed bug) | koi script ne touch nahi | topics.py_news-item URL/publisher ka extraction |
| 2 failing tests (new file me) | CONFIRMED | in-flight QA | Hermetic фикс (test_research_topic_error_handling patch, test_malformed_url_handling expectations) |

---

## 5. Isolation verdict: Kya Phase 10.1.1 Evidence Integrity work **isolated** reh sakta hai?

**Haan, mostly — 3 coupling points hain, sab managed hone wale:**

1. **`app/research/desk.py` — single shared file.** Evidence-integrity diff (`research_topic`, `fetch_url` refusal logic, clean_article, blocked flags) aur feed workstream stubs (line range me separate = nahiota region) ek hi file me hai, distinct-horizontal blocks. Feed-fix (stub replace+dead code) evidence limb ko touch nahi karta — stub file-region me ho. **Merge risk = zero, only file-clutter risk.**
2. **`tests/test_research_feeds.py` + backbone tests** — feed-fix workstream tests `desk.fetch_url` behavior (refusal etc.) ko Phase 10.1 ke saath bhi assert karti hai. F4 (transient retry) evidence-string prefix preserve karega — Phase 10.1's pinned tests (HTTP 403 startswith, malformed-xml refusal etc.) perturb NAHI karne chahiye. Label test files accordingly.
3. **`app/render/…`, `app/voice/…`, Phase 9 audio paths, publish paths — untouched by feed workstream.** Audit findings me koi publish/audio call path imported nahi hota. Fully isolated.

---

## 6. Proposed execution order (no action by OpenCode; Qoder/primary decides)

1. **1. F2 dead code removal** — `desk.py:912-966` (behavior-neutral; merge-clarity; sabhi later steps ka ground floor).
2. **2. F1 stubs → delegation** — in `archive/abandoned-agent-scripts/replace_feed_fetchers.py` execution after (a) `replace_desk_functions.ps1` skip/delete decision, (b) bare-except → diagnostic-print amendment (OpenCode-documented).
3. **3. Repair 2 failing feed tests** (environment-dependent test hermetic fix; scheme-validation expectation; optional `_dedupe_source_urls` scheme check in `desk.py:619-632` if desired).
4. **4. F3 `trends.py` XML guard** — 3 call sites via guarded parse (topics._parse_xml reuse ya shared feedxml module — Qoder's call).
5. **5. F4 desk.fetch_url transient retry** — 2-attempt cap, preserve refusal-path semantics; contract stable error strings; refuse-only-limbs ko Phase 10.1 tests ko perturb NAHI karna chahiye (run `tests/test_production_reliability.py` after).
6. **6. F5 topics.py per-source failure notes prints** — standalone, no signature change.
7. **7. Google Trends topic-URL defect fix** — `topics.py::_fetch_trends` news_item URLs / publisher attribution (highest-evidence-value fix, untracked aaj tree me til ab untouched).
8. **8. Full suite re-run gate** — research-suite (50 tests) + `test_research_feeds.py` green; Evidence suite (atomic/chain/lineage) untouched-green. Git stage/commit on user/primary decision.

**Rejecitivity:** agar steps badhe cross-file lरहे ho — isolation group bhi (topics/trends en block) ya desk-level targeted (per-finding) — apply order step-by-step hi rakho; step 1 aur 8 ke beech evidence-suite har step par run karo (2-min target).

---

*Reconciliation report generated by OpenCode (secondary agent, strictly read-only, no repo changes beyond these two docs files, git untouched).*
