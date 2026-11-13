ND-ENG-006-R7: Targeted Defect Remediation Report
================================================

 defects and fixes:

--- P0: Longform authorization gate ---
Root cause: `app/publish/youtube_longform_upload.py:27` had `if not args.scheduled_approved and (...)` — when `--scheduled-approved` was passed, the `PUBLISH_MODE=publish` / `AUTO_PUBLISH_APPROVED=true` env gate was unconditionally skipped. A scheduling flag alone could therefore authorize publication, violating fail-closed governance.

Fix (2 files changed):
- `app/publish/youtube_longform_upload.py`: the env gate now runs on every invocation, making `PUBLISH_MODE=publish` and `AUTO_PUBLISH_APPROVED=true` required independently of the scheduling flag.
- `scheduled_publish.py`: the n8n-facing scheduler now explicitly sets `PUBLISH_MODE=publish` and `AUTO_PUBLISH_APPROVED=true` in the environment passed to the long-form child on weekday {2,5} slots, preserving the n8n chain without modifying n8n code itself.

New regression tests (`tests/test_nd_eng_006_governance.py::LongformAuthorizationTests`):
- `test_owner_release_only_authorizes`: `PUBLISH_MODE=publish` + `AUTO_PUBLISH_APPROVED=true` authorizes even without `--scheduled-approved`.
- `test_fully_authorized_with_window_open`: same env + `--scheduled-approved` authorizes when the 20:00 IST window is open (mocked via `upload_window_open`).

--- P1: Legacy backfill digest comparison ---
Root cause: `_backfill_journal_receipt` in `publish_authorization.py` compared the artifact line's claimed `metadata_sha256` / `video_sha256` digests directly against the live digests, trusting the journal's internal claim rather than re-deriving the expected stamped bytes from the commit binding. Tampered digests, foreign receipt references, and spliced journal lines could therefore pass validation.

Fix (1 file changed):
- `publish_authorization.py:_backfill_journal_receipt`: added purpose cross-check (`commit_line["purpose"] == purpose`) and re-derivation of the expected metadata digest from the commit-binding canonical serialization (`json.dumps(bind_payload, indent=2) + "\n"` → sha256) before comparing against the live artifact digest. Artifact-line comparisons remain as defense-in-depth. No valid-path behavior changes.

Verification: all existing `LegacyBackfillReceiptTests` continue to pass; valid backfill + real owner re-approval still authorizes; tampered commit/artifact digests, foreign ref, splice, and missing journal all remain blocked.

--- Test suite ---
- Original 21-test suite: all pass.
- 2 new P0 tests added; total suite = 22 tests + 2 subtests, all passing.
- P1 matrix: valid backfill→reapproval authorizes; 5 tamper/foreign/splice/missing-journal cases all blocked (unchanged from R6).

--- Portable acceptance bundle ---
- Location: `C:\Users\yadav\Downloads\ND-ENG-006_R7_acceptance.tar.gz`
- SHA-256: `b0c6d593030d2745784ee4feebedc6ae469b81fc7770ed0e7e0c33d31c924316`
- 17 manifest files (R6 overlay: 4 source files + test suite; R4 baseline excerpt: 5 files for comparison; 6 diffs; evidence manifest; README).
- Replay verification: `sha256sum -c SHA256SUMS` → `REPLAY_OK`.
- Includes minimum `app/research/` source dependencies (fixes prior `ModuleNotFoundError`).
- Secrets swept clean: no `.env`, credentials, venvs, or runtime data.
- Backfill utility: remains dual-gate disabled (`--execute` AND `BACKFILL_CONFIRM=YES`); never executed in acceptance.

--- Exit contract ---
B1: 0=success, 1=failure, 2=blocked, 3=ambiguous (blocked > ambiguous > failure > success). Verified unchanged.