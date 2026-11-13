# Shorts Studio — Strict Fail-Closed Architecture Review

**Reviewer:** Independent Principal Architect / Reliability Reviewer (secondary agent, not the implementation agent)
**Date:** 2026-10-30 · **Mode:** READ-ONLY audit. No files edited, created, deleted, renamed, or moved. No git operations. No modifying scripts executed. Phase 9 audio untouched; Phase 10.1.1 feed work untouched; approval/publishing safeguards untouched; publishing not enabled.
**Policy decision under review:** Option A — Strict Fail-Closed (Strong Pipeline mandatory; on failure, stop; never invoke legacy; no successful legacy output; preserve prior outputs; record clear diagnostics; do not weaken approval/publishing.)

**Legend:** ✅ Verified (file:line) · ⚠️ Potential · 💡 Recommendation · 🔎 Assumption · **FAIL/PASS/NEEDS REVIEW** = overall assessment per finding.

---

## 1. Executive summary

The codebase **contains the machinery** for strict fail-closed behavior (a `--strict` flag that re-raises on Strong Pipeline failure at `pipelines/short.py:340-341`), but **that machinery is not wired into any production caller**. Every production entrypoint — CLI scheduled generation, the API, and the n8n runner — invokes `pipelines/short.py` **without `--strict`**, so the default behavior on Strong Pipeline failure is to **fall back to the legacy standard path and emit a success status** (`pipelines/short.py:336-360`). The API additionally defaults to `quality="standard"` (`api/main.py:158`), bypassing the Strong Pipeline entirely.

**Bottom line:** Strict fail-closed is **NOT currently in effect**. Assessment: **FAIL** (mechanism exists, policy not enforced anywhere in the call chain). Nothing is broken in the sense of a crash; the architecture simply does not implement the owner's selected Option A.

---

## 2. Verified findings (with exact file/line references)

### F-STR-1. Strong→legacy fallback is the default, not the exception (✅ Verified — Critical)

- `pipelines/short.py:336-343`: `try: run_strong_pipeline(...) except Exception: if args.strict: raise; print(f"[!] ... falling back to the standard path.")` — when `--strict` is absent (the default), any Strong Pipeline exception is swallowed and execution falls through.
- `pipelines/short.py:362-398`: The fall-through block is the **legacy standard path**: `generate_script()`, `generate_voiceover()`, `get_background_video()`, `generate_subtitles()`, `render_final_short()`, then `json.dump(data, ..., metadata_file)` at line 365 (overwriting `data/metadata.json`), `archive_video()`, `record_topic()`, `recent_formats.txt` append, and a `{"status": "success", ...}` JSON print at lines 391-398.
- Impact: a failed Strong Pipeline run still produces a "success" response with a legacy-generated video and metadata that lacks research verdict, claim ledger, and evidence linkage — exactly what Option A forbids.

### F-STR-2. `--quality standard` skips the Strong Pipeline entirely (✅ Verified — High)

- `pipelines/short.py:336`: `if args.quality == "strong":` — only enters the Strong Pipeline branch when quality is "strong". Any other value (`"standard"`) goes straight to the legacy block at lines 362-398.
- Default quality: `os.getenv("VIDEO_QUALITY", "strong")` at line 301 — the env var `VIDEO_QUALITY=standard` silently routes every run to legacy without touching the Strong Pipeline.
- No evidence this env var is set in any caller today, but it is a **silent bypass path** that requires no code change to activate.

### F-STR.3. API-triggered execution defaults to legacy and never passes `--strict` (✅ Verified — High)

- `api/main.py:109`: `cmd = [sys.executable, "-m", "pipelines.short", "--quality", quality]` — no `--strict` flag ever appended.
- `api/main.py:158-160`: `quality = "standard" if not data else str(data.get("quality", "standard")).strip()` — default is `"standard"`; invalid values are coerced to `"standard"`. Only an explicit client-supplied `"strong"` reaches the Strong Pipeline branch, and even then without `--strict`.
- `api/main.py:123-130`: job is marked `"done"` when `proc.returncode == 0 and result` — since the fallback path exits 0 and prints a success JSON (`_extract_result` at lines 39-55 matches it), an API job whose Strong Pipeline would have failed is reported as **done** with a legacy video.
- Callers: `/start` endpoint (line 154) accepts `quality` from the client; n8n runner (`n8n_runner.py:97`) calls `run_scheduled_generation.sh`, not the API directly.

### F-STR-4. Scheduled generation runs without `--strict` (✅ Verified — High)

- `n8n_runner.py:97`: `/run/generate` → `run_scheduled_generation.sh`.
- `run_scheduled_generation.sh:18`: `PUBLISH_MODE=review bash "$ROOT/run_pipeline.sh"` — no `--strict`.
- `run_pipeline.sh:17`: `if "$PYTHON" "$DIR/pipelines/short.py" "$@"; then` — passes `"$@"` through with no `--strict` added.
- `run_pipeline.sh:25-29`: on exit 0 (including fallback-produced success), `review_bundle.py` runs and `notify_review.py short` fires — so a fallback legacy output enters the human review queue as if it were a strong run.

### F-STR-5. CLI `--strict` flag exists but is unused by every caller (✅ Verified — Medium)

- `pipelines/short.py:305-309`: `--strict` defined: "fail instead of falling back to the standard path when the strong pipeline fails".
- `pipelines/short.py:340-341`: `if args.strict: raise` — correct fail-closed behavior **only when the flag is present**.
- Zero callers pass `--strict`: `run_pipeline.sh`, `run_scheduled_generation.sh`, `api/main.py`, `run_gen.sh` (which calls `app.script.pipeline` directly, not `pipelines/short.py`).
- `archive/superseded/create_short.py:421-425` contains an identical `--strict` + fallback pattern, but that file is in `archive/superseded/` and is **not an active entrypoint** (verified: no caller imports or executes it).

### F-STR-6. `app/script/pipeline.py` (the Strong Pipeline module itself) is already fail-closed (✅ Verified — informational)

- `app/script/pipeline.py:run()` lines 252-490: every stage (`select_topic`, `build_research`, `script_studio.write_script(strict_research=True)`, `generate_voice`, `motion_render.render_video`, QA) raises on failure; there is **no try/except fallback** inside `run()`.
- `app/script/pipeline.py:main()` lines 493+: parses `--topic/--seconds/--work-dir/--min-topic-score` only — **no `--strict`** and no legacy branch. Called by `run_gen.sh` (`run_gen.sh:4`). This path is already fail-closed, but it is **not** the path used by scheduled generation or the API.

### F-STR-7. Internal fallbacks live inside the legacy path (✅ Verified — informational, not a strict-mode bypass)

- `generate_voiceover()` `pipelines/short.py:35-53`: edge-tts failure → gTTS fallback (prints "[!] ... falling back to gTTS", line 48).
- `get_background_video()` `pipelines/short.py:56-120`: AI scene assembly failure → procedural dark-tech background (line 107-120).
- These operate **after** the Strong/legacy branch decision, so they are not strict-mode bypasses per se, but they mean the legacy path can synthesize media even when external services fail.

---

## 3. Strict behavior verification matrix

| Question | Finding | Evidence | Assessment |
|---|---|---|---|
| CLI stops on Strong Pipeline failure? | Only with `--strict` | `pipelines/short.py:340-341`; flag unused by callers | **FAIL** by default |
| Scheduled execution stops on failure? | No — falls back to legacy, exit 0 | `run_scheduled_generation.sh:18`, `run_pipeline.sh:17`, `pipelines/short.py:336-360` | **FAIL** |
| API-triggered stops on failure? | No — defaults to `quality="standard"` (legacy), no `--strict` | `api/main.py:109,158-160,123-130` | **FAIL** |
| Exceptions propagated/reported correctly? | Non-strict: swallowed + fallback; strict: re-raised | `pipelines/short.py:336-343` | Partial — mechanism exists, unused |
| No legacy generation automatically? | False — legacy runs automatically on strong failure | `pipelines/short.py:362-398` | **FAIL** |
| Failed runs cannot create review-ready metadata? | False — fallback writes `data/metadata.json` and triggers `review_bundle.py` | `pipelines/short.py:365`, `run_pipeline.sh:25` | **FAIL** |

---

## 4. Existing output protection

### F-PROT-1. Previous `data/metadata.json` IS overwritten by a failed run's fallback (✅ Verified — High)

- `pipelines/short.py:318`: `metadata_file = SCRIPT_DIR / "data" / "metadata.json"` — fixed single slot.
- `pipelines/short.py:364-365`: fallback path does `json.dump(data, f, indent=2)` to that same file, **overwriting any prior successful strong-pipeline metadata**.
- Option A requires "Preserve existing valid outputs and review packages" — this is violated by the fallback path.

### F-PROT-2. Previous review packages are not directly corrupted by fallback (✅ Verified — informational)

- `review_bundle.py` (`run_pipeline.sh:25`) reads `data/metadata.json` and writes `data/review_pending.json` / `data/review_package.json`. A fallback overwrites `metadata.json` first, so the **next** review package would describe the legacy output. No evidence of in-place corruption of an already-written `review_approved.json`, but the pipeline can chain fallback → bad metadata → review bundle on unverified content.

### F-PROT-3. Partial outputs can be mistaken for successful outputs (⚠️ Potential — Medium)

- Fixed-name slots: `outputs/voice.mp3`, `outputs/background.mp4`, `outputs/subtitles.ass`, `outputs/output_short.mp4` (`pipelines/short.py:312-317`), plus `shots/` directory (`app/script/pipeline.py:264-265`).
- A failed/legacy run rewrites these slots; `notify_review.py:29` and `api/main.py` key off `output_short.mp4` / success JSON, not a per-run manifest. No evidence of partial files being shipped, but no mechanism distinguishes "complete strong run output" from "fallback output" or "partial re-render".

### F-PROT-4. Failure diagnostics may leak secrets (⚠️ Potential — Medium)

- `pipelines/short.py:342`: `print(f"[!] Strong pipeline failed ({type(exc).__name__}: {exc}); ...")` — the raw exception `exc` is printed to stdout/logs. If a downstream stage's exception embeds a credential/token/URL secret, it is logged unredacted.
- `api/main.py:_redact()` (lines 31-36, 121) redacts env keys and URL-params in job logs — good defense at the API layer, but `pipelines/short.py` itself prints unredacted before API redaction can apply to the underlying stdout (the API writes raw subprocess stdout to `log_path` at line 116-119, then redacts only the tail at line 121).

---

## 5. Regression and bypass analysis

| # | Bypass / regression path | Location | How it defeats strict fail-closed |
|---|---|---|---|
| B1 | Default non-strict fallback | `pipelines/short.py:336-343,362-398` | Strong failure → legacy success |
| B2 | `VIDEO_QUALITY=standard` env var | `pipelines/short.py:301,336` | Skips Strong Pipeline entirely |
| B3 | `--quality standard` CLI arg | `pipelines/short.py:298-303,336` | Skips Strong Pipeline entirely |
| B4 | API defaults to `quality="standard"` | `api/main.py:158-160` | Legacy by default for all API jobs |
| B5 | API never sends `--strict` | `api/main.py:109` | Even `quality="strong"` jobs fall back |
| B6 | Scheduled runner never sends `--strict` | `run_scheduled_generation.sh:18`, `run_pipeline.sh:17` | Scheduled runs fall back |
| B7 | Exception message printed unredacted | `pipelines/short.py:342` | Possible secret leakage in failure logs |
| B8 | No per-run identity; fixed `data/metadata.json` slot | `pipelines/short.py:318,364-365` | Failed run overwrites prior good metadata |
| B9 | Legacy-path internal fallbacks (edge-tts→gTTS, AI→procedural) | `pipelines/short.py:48,107-120` | Legacy path can "succeed" with degraded media |

No alternate entrypoint was found that invokes legacy generation **inside** the Strong Pipeline module (`app/script/pipeline.py:run()` has no fallback — verified fail-closed). The bypasses are all at the **orchestration layer** (`pipelines/short.py` main, shell scripts, API).

Tests that pass without proving strict behavior: `tests/test_phase5_script_package.py:88-101` runs `pipelines/short.py --help` and asserts shell scripts call `pipelines/short.py`, but **does not assert `--strict` is passed or that fallback is disabled**. `tests/test_api_telegram.py:71,76` uses `quality: "standard"` with a mocked `_extract_result` — exercises the legacy/API path, not strict behavior.

---

## 6. Adversarial test matrix (15 deterministic scenarios)

Specifications only — do not create or modify tests. All hermetic (no network), tmp work dirs, do not touch `data/` state files.

| # | Scenario | Setup (monkeypatch/stub) | Expected strict result (Option A) |
|---|---|---|---|
| T1 | Research failure | `research_desk.research_topic` raises / returns `verdict: insufficient` | Process exits non-zero; no legacy output; no `metadata.json` overwrite; diagnostics recorded |
| T2 | Topic selection failure | `discover_topics` returns `[]` → `RuntimeError("No research candidates...")` | Non-zero exit; no output created |
| T3 | Evidence/ledger failure | `claims_ledger.build_ledger` raises | Non-zero exit; no render attempted |
| T4 | Script generation failure | `script_studio.write_script(strict_research=True)` raises (e.g. `validate_opening_quality`) | Non-zero exit; no voice/render stages |
| T5 | Voice failure | `voice_provider.synthesize_with_fallback` returns no path → `RuntimeError` | Non-zero exit; partial `voice.mp3` must not be treated as success |
| T6 | Render failure | `motion_render.render_video` raises or ffmpeg returns non-zero | Non-zero exit; no `output_short.mp4` success marker |
| T7 | QA failure (duration/dimension mismatch) | `qa_video` returns failing status | Non-zero exit; video not archived, no success JSON |
| T8 | Scheduler failure (strong pipeline crashes) | Monkeypatch `run_strong_pipeline` to raise; invoke `run_pipeline.sh` without `--strict` | **Currently FAILS** (falls back to legacy). After fix: non-zero exit, no legacy output, status "failed" |
| T9 | API-triggered failure | `api/main.py` `run_job` with `quality="strong"`, strong pipeline monkeypatched to raise | Job status `"failed"`; no `video_path`; not `"done"` |
| T10 | Legacy fallback invocation attempt | `quality="strong"`, `--strict` absent, strong pipeline raises | **Currently FAILS** (legacy runs, success printed). After fix: process must exit non-zero before legacy block |
| T11 | Existing metadata preservation | Pre-write `data/metadata.json` with known-good strong content; run failure; assert file unchanged (hash compare) | **Currently FAILS** (fallback overwrites line 365). After fix: hash unchanged |
| T12 | Partial output handling | Pre-create `outputs/output_short.mp4` (stale); run failure; assert stale file is not re-published / not marked success | No success JSON referencing stale file |
| T13 | Repeated execution after failure | Run fails (T1), then re-run succeeds; assert second run's metadata is the only valid one, first failure did not leave a "success" artifact | Each run independent; no carryover of partial success |
| T14 | `VIDEO_QUALITY=standard` bypass attempt | Env `VIDEO_QUALITY=standard`; strong pipeline is healthy | Strict mode must still either (a) reject `standard` in production or (b) log an explicit non-strong run. Option A: production = strong only |
| T15 | `--quality standard` CLI bypass attempt | CLI arg `--quality standard` | Same as T14 — legacy must not be silently chosen in strict production |
| T16 | Secret in exception message | Stage raises `RuntimeError("API key sk_live_... failed")`; capture stdout | Diagnostic must not print raw secret (redacted or generic category) |

Acceptance: all T1–T7 must pass in the Strong Pipeline module today (they do — `run()` raises). T8–T16 currently **fail** because of orchestration-layer fallback (F-STR-1..6). The fix target is the orchestration layer, not the Strong Pipeline stages.

---

## 7. Security and data-integrity risks

| Risk | Severity | Basis |
|---|---|---|
| Legacy video enters human review queue labeled as success | High | F-STR-1, F-STR-4: fallback writes `metadata.json` + triggers `review_bundle.py`; reviewer cannot distinguish strong vs legacy from metadata alone (`quality` field absent in fallback output at lines 391-398 — no `"quality": "strong"` key printed there) |
| Prior good metadata overwritten by failed run | High | F-PROT-1: fixed `data/metadata.json` slot, line 364-365 |
| Secret leakage in failure diagnostics | Medium | F-PROT-4: raw `exc` printed at line 342 |
| Silent bypass via `VIDEO_QUALITY=standard` or `--quality standard` | Medium | F-STR-2, B2/B3: no guardrail that production must be strong |
| API reports failed strong job as "done" | High | F-STR-3: fallback exits 0 with success JSON; `_extract_result` matches it |
| No run identity → orphaned partials indistinguishable from final | Medium | F-PROT-3: fixed-name slots, no manifest |

---

## 8. Acceptance criteria for strict fail-closed behavior (Option A)

All must hold before this review can be marked PASS:

1. **CLI:** `python pipelines/short.py --quality strong` (no `--strict`) on Strong Pipeline failure → non-zero exit, no legacy block executed, no success JSON, `data/metadata.json` unchanged.
2. **CLI strict flag:** `python pipelines/short.py --quality strong --strict` on failure → non-zero exit, exception propagates (existing behavior at line 340-341, already correct).
3. **Scheduled:** `run_scheduled_generation.sh` on strong failure → non-zero exit, no legacy output, no `review_bundle.py` run, no `notify_review.py` success call.
4. **API:** `/start` with `quality: "strong"` and strong failure → job status `"failed"`, no `video_path`, not `"done"`.
5. **API default:** API must not default to legacy for production; either default `quality` to `"strong"` or reject non-strong in production mode.
6. **Metadata preservation:** pre-existing `data/metadata.json` hash unchanged after any failed run.
7. **No review package from failed run:** `review_bundle.py` / `notify_review.py` not invoked when pipeline exits non-zero.
8. **Diagnostics:** failure messages must not print raw credentials/secrets (redact exception text at `pipelines/short.py:342`).
9. **Approval/publishing safeguards unchanged:** `approve_review.py`, `approval_integrity.py`, `upload_window_open()`, `publish_all.py` gates remain exactly as-is (not weakened).
10. **Phase 9 audio, Phase 10.1.1 feeds untouched:** no changes to `ffmpeg_tools` audio defaults, `app/voice/*`, `app/research/*` feed modules, or `trends.py`/`topics.py`/`desk.py` feed logic.

---

## 9. PASS / FAIL / NEEDS REVIEW assessment

| Area | Assessment | Rationale |
|---|---|---|
| Strong Pipeline module internal fail-closed | **PASS** | `app/script/pipeline.py:run()` raises on every stage failure; no internal fallback (verified :252-490) |
| `--strict` flag mechanism | **PASS** (mechanism only) | `pipelines/short.py:340-341` re-raises correctly when flag present |
| Strict fail-closed **in production callers** | **FAIL** | Zero callers pass `--strict`; scheduled + API + CLI default all fall back or skip Strong Pipeline (F-STR-1..6) |
| Output protection (metadata preservation) | **FAIL** | Fallback overwrites `data/metadata.json` (F-PROT-1) |
| No automatic legacy generation | **FAIL** | Legacy runs automatically on strong failure (F-STR-1) |
| Diagnostics & secret safety | **NEEDS REVIEW** | API redacts (`api/main.py:31-36`) but `pipelines/short.py:342` prints raw exception |
| Review/publish safeguards | **PASS** (unchanged) | Not touched by this audit; human approval gate intact |

**Overall: FAIL.** The owner's Option A (Strict Fail-Closed) is **not enforced** anywhere in the production call chain. The `--strict` opt-in exists but is unused; default behavior is fallback-to-legacy-with-success. Implementation work (to be decided by the owner / primary agent Qoder) would target the orchestration layer: make `pipelines/short.py` non-strict-by-default fail-closed, wire `--strict` (or equivalent) into `run_pipeline.sh`, `run_scheduled_generation.sh`, and `api/main.py`, protect `data/metadata.json` from overwrite on failure, and redact exception diagnostics. No code changes are made by this reviewer.

---

## 10. Areas confirmed NOT in scope for this review (no change recommended)

- Phase 9 audio fidelity / voice clarity / SFX mixing (`ffmpeg_tools.py` loudnorm targets, `app/voice/*` provider contracts).
- Approval & publishing safeguards: `approve_review.py`, `approve_longform.py`, `approval_integrity.py` digests/upload window, `publish_all.py` approval gates, `scheduled_publish.py` 20:00 IST window, n8n workflow JSON.
- Phase 10.1 evidence ledger schema (`LEDGER_VERSION`, `ledger_sha256`, claim vocab).
- Phase 10.1.1 feed work (Qoder): `desk.py` stubs/dead block, `trends.py` XML guard, `topics.py` exceptions, Trends URL defect, `archive/abandoned-agent-scripts/replace_feed_fetchers.py`.
- `archive/superseded/create_short.py` — archived, not an active entrypoint; left as-is.

*Report by the independent secondary reviewer. Nothing implemented. Awaiting owner review before any further implementation.*
