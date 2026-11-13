# Handover — Strict Fail-Closed (Phase 10) → OpenCode

**From:** Qoder · **Date:** 2026-10-30 · **Status:** implemented, **not executed, not verified**
**Reason for handover:** the owner assigned all remaining Phase 10 work to OpenCode. The diff below was written earlier in this session at the owner's direction; it has been left exactly as-is, unstaged, uncommitted and un-run.

> **Do not merge this diff before running the tests listed in §4.** None of them has been executed. No claim of correctness is made beyond what is stated here.

## 1. Working-tree state (verified, not modified)

- Nothing was staged, committed, pushed, stashed, cleaned or reset.
- The files in §2 remain as uncommitted modifications/additions in the shared working tree.
- A separate, **tested** change set also exists in the same tree: `app/research/desk.py` (candidate URL validation) + `tests/test_research_feeds.py` (URL tests). It is Phase 10.1.1 work, not part of this handover, and must not be committed without explicit owner approval.

## 2. Files changed for Strict Fail-Closed

| File | Change |
|---|---|
| `pipelines/short.py` | Removed the automatic legacy fallback. Strong-pipeline failure now records sanitized diagnostics and exits **1**; `--quality standard` / `VIDEO_QUALITY=standard` are refused with exit **2** unless `--allow-standard` is passed explicitly. `--strict` kept as an accepted no-op. Legacy body moved verbatim into `run_standard_pipeline()`. Added `_redact()`, `_record_failure()` writing `data/last_failure.json`, and a `"quality": "standard"`/`"legacy": true` tag on legacy success output. |
| `api/main.py` | `/start` defaults `quality` to `"strong"` and returns HTTP 400 for any other value unless `SHORTS_STUDIO_ALLOW_STANDARD=1`. `run_job` appends `--allow-standard` only in that opt-in case. A job becomes `"done"` only when `returncode == 0` **and** the success payload's `quality` equals the requested quality (dry runs exempt); otherwise `"failed"` and any `video_path` is removed. |
| `tests/test_strict_fail_closed.py` | **New, never run.** 8 CLI tests (success, failure stops, no legacy call, metadata/review preservation, redaction, standard refusal, `VIDEO_QUALITY` bypass, explicit legacy opt-in, `--strict` parity), 2 shell tests (`run_pipeline.sh`, `run_scheduled_generation.sh` stop before review bundle), 6 API tests (default strong, standard rejected, failed run not `done`, legacy payload cannot close a production job, strong completes, opt-in path). |

## 3. Behaviour summary (as written, not validated)

- Strong Pipeline is mandatory; failure → exit 1, no legacy generation, no success JSON.
- Prior `data/metadata.json`, review files and outputs are not written on a failed run.
- Failure diagnostics are redacted (env-value masking, `key=…` patterns, token shapes) and stored separately in `data/last_failure.json`.
- Legacy path is reachable only via explicit `--allow-standard` (CLI) or `SHORTS_STUDIO_ALLOW_STANDARD=1` (API server env).

## 4. Unrun tests — run these first

```bash
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_strict_fail_closed.py
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q tests/test_api_telegram.py tests/test_phase5_script_package.py
PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q        # full suite
```

Expected first-run risks (deliberately listed, unverified):

1. `ShellChainTests` spawn `/bin/bash run_pipeline.sh` and `run_scheduled_generation.sh` with a stub interpreter; `run_scheduled_generation.sh` touches `.scheduled_generation.lock` (0-byte lock file in the repo root). Confirm the stub is picked up via `SHORTS_STUDIO_PYTHON` on this machine.
2. `ApiEntryPointTests` patch `api_main.threading` with a fake thread; confirm FastAPI import time does not create a real thread pool race.
3. `test_failure_diagnostics_are_sanitized` asserts `key=***` survives redaction; check against the real `_redact()` implementation order.
4. The existing `tests/test_api_telegram.py::RunJobNotifyTests` passes `quality="standard"` directly to `run_job` with `dry_run=True`; the new done-gate exempts dry runs, so it should still pass — verify.
5. `pipelines/short.py` exit codes changed (1/2 instead of 0); any external caller that treats non-zero as retryable should be reviewed.

## 5. Not included in this handover

- No edits to `app/research/*`, `app/script/*`, `app/visuals/*`, renderer, approval or publishing paths for this change set.
- No changes to `run_pipeline.sh` / `run_scheduled_generation.sh` — they already propagate a non-zero exit and skip `review_bundle.py`/`notify_review.py` on failure once `pipelines/short.py` exits non-zero.
- Phase 9 audio files, defaults and tests untouched.
