# Shorts Studio — Research Feed Dependency Audit (Secondary Agent)

- **Role:** Secondary / Research Feed Specialist
- **Date:** 2026-10-30
- **Mode:** Strictly read-only. No code modified, no git operations (status staged/unstaged/untracked kisi ne nahi badla).
- **Branch:** `main` (8 renames staged → `app/publish/*`, `app/visuals/*`; desk/selector/pipeline-tests wahi hain jo Qoder ka Phase 10.1.1 WIP hai).

---

## PART 1 — Re-inspection Audit (5 reported findings ki re-verification)

### Finding status summary

| # | Finding | Verdict | Location (current) |
|---|---|---|---|
| 1 | Stub fetchers in `desk.py` returning `[]` | **CONFIRMED** | `app/research/desk.py:29-52` |
| 2 | Duplicate `bundle_topic_and_research()` | **CONFIRMED (worse shape than reported)** | `app/research/desk.py:860-966` |
| 3 | Missing XML DTD/entity rejection in `trends.py` | **CONFIRMED — 3 call sites** | `trends.py:432, 745, 929` |
| 4 | Missing transient retry in `desk.fetch_url()` | **CONFIRMED** (refusal-class retry only) | `desk.py:271-297, 316-318` |
| 5 | Silent exception handling in `topics.py` | **CONFIRMED** | `topics.py:268-274, 236-242, 91-96` |

---

### Finding 1 — Stub fetchers (CONFIRMED)

- **Code:** `app/research/desk.py:29-52` — four functions hardcode `return []`. Comment (`:29`) aur docstrings claim *"sandbox environment network calls are blocked"* — ye premise aaj **do baar galat sabit hua**:
  1. Live probes: sabhi 6 feed endpoints HTTP 200 with real feed content (Reddit keyless RSS bhi 200/Atom).
  2. Naya test `tests/test_research_feeds.py::test_research_topic_error_handling` fail hua **kyunki network block nahi hai** — `research_topic()` ne live search kar liya.
- **Execution path:** stubs sirf `bundle_topic_and_research()` (`desk.py:876-879, 936-939`) aur CLI `--bundle` (`desk.py:983`) se call hote hain. Production pipeline unaffected — discovery `topics.discover_topics` se hoti hai (`pipeline.py:78`).
- **Qoder ke prepared scripts:** untracked `archive/abandoned-agent-scripts/replace_feed_fetchers.py` (4 stubs → delegation to `topics.*`, with `try/hasattr/except → []`) aur `archive/abandoned-agent-scripts/replace_desk_functions.ps1` (**abandoned partial duplicate** — sirf `_fetch_trends` replace karta hai). **Dono execute NAHI hue** — desk stubs abhi bhi stubs hain (line-by-line verified).
- **Risk in prepared scripts:** delegation wrappers har exception swallow karte hain (`except Exception: return []`) — Finding 5 ka pattern nayi jagah copy hoga. PS1 half-fix double-application confusion introduce kar sakta hai.

### Finding 2 — "Duplicate" bundle function (CONFIRMED, merged form)

Do `def` nahi hain — ye ek **merge residue hai**:
- `desk.py:860-910` — **naya** implementation (retry loop, `MAX_RETRIES`/`MIN_RANK` env, `:869-870`), do `return`s (`:908-910`);
- `desk.py:912-933` — purane implementation ka **orphan docstring** (bare string, unreachable);
- `desk.py:934-966` — **purane implementation ka body — unreachable dead code** (function hamesha `:882` ya `:908/:910` pe exit kar chuka hota hai).

**Actual impact:**
1. Non-hawaldar edit trap: "second definition" me koi bhi edit kuch nahi karta.
2. Retry loop **ineffective**: stubs `[]` return karte hain → attempt 1 pe hi `{"error": "no candidates found"}` (`:881-882`) — `MIN_RANK` check tak kabhi reach nahi hota.
3. `MAX_RETRIES`/`MIN_RANK` semantics sirf live limb me hain.

**Callers:** sirf CLI (`desk.py:983`). Production pipeline (`research_topic`) unaffected.

### Finding 3 — trends.py XML hardening (CONFIRMED, teesri site bhi mili)

- Bare `ET.fromstring` teen jagah: `trends.py:432` (Google Trends RSS), `:745` (arXiv via `_fetch_with_retry`, timeout=90), aur **`:929` (PyPI RSS — naya)**.
- `topics._parse_xml` (`topics.py:32-36`) mein guard hai aur test-pinned hai (`tests/test_production_reliability.py:56-58`; `tests/test_research_feeds.py:181-190` bhi assert karta hai).
- **Impact:** stdlib ElementTree *external* entities resolve nahi karta, lekin **internal entity expansion** (billion-laughs) abhi bhi possible hai. Consistency fix — architecture change nahi.

### Finding 4 — fetch_url transient retry (CONFIRMED)

- `desk.py:271-275`: do Accept headers; `:278-286`: sirf `(401, 403, 406)` pe retry; baaki 4xx/5xx pe turant break (`:285`); Timeout/ConnectionError generic catch (`:316-318`) tak single attempt.
- Qoder ka test file khud gap document karta hai: `tests/test_research_feeds.py:162-179` ("fetch_url currently doesn't retry on timeout").
- **Impact:** ek transient 429/502/timeout poore run ke liye source drop → corroboration counts aur verdict down. `trends.py:290-304` me already 3-attempt/4s-backoff pattern hai — `desk.py` me chhota version compatible hai, naya architecture nahi.

### Finding 5 — Silent exception handling (CONFIRMED)

- `topics.discover_topics:268-274`, `topics.search_web:236-242`, `topics._fetch_hacker_news:91-96` — sab `except Exception: continue` + no notes.
- **Impact:** failed feed ≠ empty feed me koi farak run-logs me nahi; final symptom sirf `pipeline.py:80` ka "No research candidates were discovered". Diagnosis zero. `trends.fetch_all` (`:1113-1140`) aur `desk.research_topic` (`:705-706`) dono error notes dete hain — `topics.py` discovery exception hai.

---

## 2. Existing tests aur currently failing (run-verified)

- Research-suite baseline: `test_topic_research`, `test_research_desk`, `test_phase4_research_package`, `test_production_reliability`, `test_source_lineage` → **50 passed**.
- Qoder ka naya `tests/test_research_feeds.py` → **20 passed, 2 FAILED**:
  1. `test_research_topic_error_handling` — network-block assumption galat (live result mila: `examtopics.com`). Environment-dependent test.
  2. `test_malformed_url_handling` — `_dedupe_source_urls` (`desk.py:619-632`) **ka scheme validation nahi hai** (`not-a-url` pass hota hai). Test ka `duplicate/` expectation bhi galat hai (function intentionally sirf arXiv mirrors collapse karta hai).
- `test_desk_feed_fetchers_not_empty` (`:230-260`) aur `test_duplicate_bundle_function_not_called` (`:262-296`) **vacuously pass** — stubs/fetch_url patch karte hain, na dead-code block (`:912-966`) pakadte hain na stubs-under-retry condition.

---

## 3. File-level proposal (smallest safe fix per finding — APPLY NAHI kiya)

| Finding | File : lines | Smallest safe change |
|---|---|---|
| 1 | `app/research/desk.py:29-52` | `archive/abandoned-agent-scripts/replace_feed_fetchers.py` ko review ke baad execute karo, par `except: return []` ki jagah ek diagnostic print (`[i] desk feed <name> unavailable: <ExceptionType>`). `archive/abandoned-agent-scripts/replace_desk_functions.ps1` delete ka kandidat (partial half-fix). `:29` stale comment update. |
| 2 | `app/research/desk.py:912-966` | Orphan docstring + unreachable old body delete. Retry limb rakho; `import os` (`:868`) module-imports me hoist. Pure dead-code removal — no behavior change. |
| 3 | `trends.py:432, 745, 929` | Teen `ET.fromstring()` → shared guarded parser. Smallest diff: `from app.research.topics import _parse_xml as parse_feed` aur 3 call-sites replace. Koi naya module nahi chahiye. |
| 4 | `app/research/desk.py:278-286` | Transient retry: `(Timeout, ConnectionError, 429, 502, 503, 504)` pe 1 extra attempt, 1–2 s backoff, max 2 total. Refusals (401/403/406) existing Accept-alternation path pe hi. Error string format stable rakho (`HTTP xxx` prefix) — `blocked`-flag logic aur existing tests protect karega. |
| 5 | `app/research/topics.py:268-274, 236-242` | Exceptions local `notes` list me collect; per-failure ek `[i] feed <name> failed: <Type>` print. Signature change nahi. |
| (test fix) | `tests/test_research_feeds.py:142, 400-431, 475-489` | Do failures production defect nahi: (a) `test_research_topic_error_handling` hermetic banao — `topics.search_web` patch karke `[]` return; (b) `test_malformed_url_handling` expectation set theo sahi karo (optional improvement: `_dedupe_source_urls` me `scheme in {"http","https"}` validation genuinely add karo — real chhota gap hai). |

---

## 4. Missing regression tests (purely mock-based, hermetic)

1. `bundle_topic_and_research` retry-path: rank < `MIN_RANK`, `MAX_RETRIES=2` → exactly 2 attempts (live limb assert + dead-code removal implicitly).
2. `_dedupe_source_urls` scheme validation (`not-a-url`, `ftp://`, empty) — fixed expectation ke saath.
3. `desk.fetch_url` transient retry: pehla Timeout, doosra success → `ok=True`, 2 attempts; dono timeout → `ok=False` + stable error text.
4. `trends` teeno feeds DTD/entity payloads refuse karein (topics wale test ka mirror).
5. `discover_topics`: ek feed raise, baaki items → partial results + failure notes printed (Finding 5).
6. Delegation wrappers (Finding 1 ke baad): `desk._fetch_hacker_news() == topics._fetch_hacker_news()` output; raising source → `[]` **aur** diagnostic print.

---

## 5. Security risk register

| Risk | Existing mitigation | Residual risk | Action |
|---|---|---|---|
| Internal entity expansion in feed XML | `topics.py` guard + test | `trends.py` ×3 unguarded | Finding 3 |
| Malformed feed → silent source loss | per-source swallow | diagnosability | Finding 5 |
| Transient failures degrade evidence quality | refusal-retry + `blocked`/`manual_review_required` flags | no transient retry in `desk.fetch_url` | Finding 4 |
| Unvalidated candidate URLs reach `fetch_url` | fetch-time exceptions contained | wasted slots, noisy errors | optional scheme validation |
| XML content article-text ki tarah accepted | content-type filter sirf non-text rokta hai | `text/xml` feeds `/rss` aaj bhi article HTML banke accept ho jate hain (`desk.py:298-305` verified) | Qoder ko flag (in-5-findings se bahar) |
| Publishing / Phase 9 exposure | paanchon findings publish ya audio paths ko touch nahi karti (verified) | — | none |

---

## 6. Dependencies with Phase 10.1.1

1. `reports/unattributed/PHASE10_1_RESEARCH_QUALITY_REPORT.md` batata hai Phase 10.1 ka scope 7 research-quality defects the. **Phase 10.1.1 = feed-dependency follow-up**; uske artifacts untracked WIP ki tarah tree me hain: `archive/abandoned-agent-scripts/replace_feed_fetchers.py`, `archive/abandoned-agent-scripts/replace_desk_functions.ps1`, `tests/test_research_feeds.py` (+ `tests/fixtures/`).
2. **Ordering impact:** Finding 2 dead-code removal **pehle ya saath me** aana chahiye Finding 1 rewrite ke — rewrite stubs ko rewrite karta hai; dead block (`:934-966`) aaj bhi stubs call karta hai; delegation ke baad dead block harmless par aur confusing ho jayega.
3. `test_research_feeds.py` ke 2 failing tests Qoder ke in-flight QA hain — maine modify nahi kiya; Phase 10.1.1 gate ke under fix karein.
4. Phase 9 audio aur publishing surfaces paanchon findings se untouched hain (verified: affected call paths `app/voice/*`, `app/render/*` audio tools, `app/publish` import nahi karte).

---

## 7. Current Git status (is session ke samay, verified)

```
branch: main
staged:   8 renames → app/publish/*, app/visuals/*
modified: README.md, api/main.py, app/publish/{4 uploaders},
          app/research/{desk,selector}.py, app/script/{pipeline,studio}.py,
          app/visuals/{motion_director,visual_assets}.py, app/voice/provider.py,
          docs/TOOLING_STACK.md, motion_render.py, pipelines/short.py,
          publish_all.py, publish_social.py,
          tests/{test_motion,test_phase2_storage_layout,test_production_reliability}.py
untracked: reports/unattributed/PHASE10_1_RESEARCH_QUALITY_REPORT.md, reports/unattributed/PHASE10_EVIDENCE_ENGINE_REPORT.md,
          docs/PHASE4..PHASE9 reports, app/publish/__init__.py, app/render/, app/visuals/*,
          app/research/{atomic,claims,lineage}.py, app/script/evidence.py,
          app/voice/text_prep.py, root shims (youtube_upload.py, motion_director.py, …),
          tests/* (12 naye files), tests/fixtures/, scripts/  ← Phase 10.1.1 WIP
```

---

# PART 2 — Appendix: Feed Integration Audit (earlier, same day; prop>audit-pre-reinspection)

## Executive summary

Feed layer **zero external dependency** hai (`requests` + stdlib, `requirements.txt:23-25`) — `feedparser` ki zaroorat nahi. Architecture healthy hai aur **replace nahi hona chahiye**. Ek verified functional defect mila:

**Highest-risk (evidence-verified):** `topics._fetch_trends` Google Trends RSS ka `<link>` extract karta hai, lekin RSS ka `<link>` hamesha **feed URL itself** hota hai (`trending/rss?geo=IN` — probed). Trends topic ka citation research stage feed URL ko as primary source fetch karta hai → garbage/no text. `trends.py:440-446` already correct solution hai (`news_item_url`); `topics.py` ise discard karta hai.

## Dependency inventory

| Feed | Endpoint | Used by | Verified today |
|---|---|---|---|
| Hacker News | `hacker-news.firebaseio.com` | `topics._fetch_hacker_notes:80-97` (teek: `:80-97`) | 200 |
| arXiv | `export.arxiv.org/api/query` | `topics._fetch_arxiv:100-113` | 200 pattern |
| Google Trends RSS | `trends.google.com/trending/rss?geo=IN` | `topics._fetch_trends:131-143`; `trends.py:428-464` | 200, 21 KB |
| Reddit keyless | `reddit.com/r/<sub>/.rss` | `topics._fetch_reddit:116-128` | **200, atom+xml, 30 KB** (`trends.py:90` ka "retired" note outdated) |
| Reddit OAuth | `oauth.reddit.com` | `trends._fetch_reddit:651+` (keys required) | n/a |
| DuckDuckGo HTML | `html.duckduckgo.com` | `topics.search_web` primary | 200 |
| Bing News RSS | `bing.com/news/search?format=RSS` | `topics.search_web` fallback | 200 |
| Google News RSS | `news.google.com/rss/search` | `topics.search_related_news` (longform) | 200 |

Dead code: `desk.py:30-52` stubs (Finding 1). `selector._demo_candidates`/`trends.fetch_all` sirf CLI `--demo` (`selector.py:1893`) se chalta hai.

**Live call graph:** `run_pipeline.sh` → `pipelines/short.py` → `pipeline.py:78 discover_topics()` → `pipeline.py:280 _candidate_urls()` → `desk.research_topic()` → `fetch_url` → `extract_claims` → `claims.build_ledger`.

## Risk analysis (pre-reinspection numbering)

- **R1** Trends citation defect (HIGH, verified) — upar summary.
- **R2** Reddit guidance contradiction (MEDIUM) — keyless works aaj, par 3/6 discovery jobs unowned.
- **R3** Silent failure swallowing (MEDIUM) → Finding 5.
- **R4** XML hardening inconsistency (MEDIUM) → Finding 3.
- **R5** Test coverage gaps: `_fetch_hacker_news` (None JSON → TypeError path), `_fetch_reddit` Atom, `_fetch_trends` (R1 pakadta), `discover_topics` cross-source isolation, `trends._fetch_google_trends`, XML-as-article-evidence.
- **R6** Ledger integration safe (fail-closed verified): blocked sources never in `result["sources"]` (`desk.py:702-704`), `retrieved_at` always stamped (`:266`) aur ledger me preserved (`test_research_quality.py:97-102`).

## Implementation plan (integration-audit version; re-inspection ke saath reconcile)

- **A. `app/research/topics.py`** — `_fetch_trends`: `news_item_url` extraction (trends.py pattern), feed-self-citation guard; `_get`: halka retry (2 attempts ~2 s); `discover_topics`/`search_web`: per-source failure notes (Part 1 Finding 5 jaisa).
- **B. Shared `app/research/feedxml.py`** (~20 lines) DTD-refusing parser — dono modules use karein. (Part 1 se reconcile: even smaller option = `topics._parse_xml` reuse in `trends.py`; dono allowed, decide by Qoder.)
- **C. `app/research/trends.py`** — guard adopt + stale Reddit note (`:90`) correction.
- **D. `app/research/desk.py`** — `fetch_url:298-305`: `text/xml`, `application/xml`, `atom/rss+xml` ko PDF jaisi `unsupported content-type` + `blocked` + `manual_review_required` treat karo (feed page ≠ article evidence). Phle review me notes: koi caller XML-as-text success pe depend nahi karta.
- **E. `requirements.txt` / deployment** — koi naya package nahi; `Dockerfile.runner` research code volume-mount se aata hai → no change.

## Test plan (integration-audit additions)

`tests/test_topic_research.py` me: `_fetch_hacker_news` (json None/deleted/rank filter/item tolerance), `_fetch_arxiv` (missing `rel="alternate"` → dropped), `_fetch_reddit`, `_fetch_trends` (news-item URL + publisher attribution + no feed-self citation — R1 regression), `discover_topics` partial failure, retry observation. `tests/test_feed_xml.py` (naya): DTD refusal + trends use. `tests/test_research_quality.py`: sirf XML-feed source → `ok=False`, verdict `insufficient`, `unsupported content-type`.

## Production-readiness assessment

| Area | Verdict |
|---|---|
| Evidence integrity | Fail-closed safe; Trends-origin runs aaj reference-free ho sakte hain aur empty-content noise hota hai — D-fix hard guarantee. |
| Reliability | retry + per-source notes ke baad discovery transient 429/5xx survive karta hai. |
| Security | DTD guard preserve + second consumer tak extend. |
| Deploy impact | Zero: no new packages, no publish paths, no Phase 9 surface, tests all local mocks. |
| Recommended order | A1 (Trends source fix) → D (XML-not-evidence) → B (shared gate) → A2/A3 → C. Phase 10.1.1 se coordinate (desk.py/selector.py Qoder WIP). |

---

*Report generated by secondary agent (GLM), strictly read-only session. Koi bhi code/git change apply nahi hua.*
