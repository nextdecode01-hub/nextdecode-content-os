# Central Publishing Authorization — Review Checklist

**Review ID:** ND-QA-003B  
**Date:** 2026-11-01  
**Mode:** Read-only checklist based on ND-QA-002/003A and the current source snapshot. No tests run; no repository changes.

## Highest-priority checks

- [ ] **P0 — Every publishing entrypoint uses the same policy.** Inspect `publish_authorization.py::authorize_publish`; `app/publish/youtube_upload.py::upload_video` and CLI `__main__`; `app/publish/facebook_reels_upload.py::publish`; `app/publish/instagram_reels_upload.py::publish`; `app/publish/youtube_longform_upload.py::main`; `publish_social.py::publish`, `publish_all_social`, and `main`; `publish_all.py::run`. **Evidence required:** direct library calls and CLI invocations both reject missing/stale approval before any platform client call; no caller flag or helper option disables authorization; mocks assert zero remote requests.

- [ ] **P0 — Rights and governance metadata fail closed when absent or malformed.** Inspect `publish_authorization.py::_check_direct_entry`, `_rights_violations`, `authorize_publish`; metadata builders in `app/script/pipeline.py`; approval paths in `publish_all.py::run`. **Evidence required:** missing `governance`, missing `evidence.cutouts`, empty cutouts where rights are required, absent/null/wrong-type `reuse_rights`, missing/empty/unknown status, and every status other than `permitted` block. Confirm any legitimate no-cutout case is explicitly specified and tested. Check that blocked rights never reach a publisher.

- [ ] **P0 — Public release is separately authorized for every public destination.** Inspect `publish_authorization.py::_check_destination`, `_public_release_decision`; the Facebook `video_state="PUBLISHED"` and Instagram `media_publish` calls; YouTube destination handling. **Evidence required:** social public publishing requires current owner public-release authorization bound to metadata/video hashes; missing, expired, wrong-owner, or mismatched release records block before the public API call. Do not treat editorial approval alone as release approval.

- [ ] **P0 — Approval freshness/hash checks resist artifact drift (TOCTOU).** Inspect `publish_authorization.py::_approval_records`, `_bind_artifacts`, `authorize_publish`; `publish_all.py::run` per-destination reauthorization; each adapter’s final authorization-to-request sequence. **Evidence required:** metadata-only and video-only changes, future/expired approval and IST-midnight boundaries are rejected; mutation between cross-post destinations blocks remaining posts; no platform request proceeds if content changes after authorization. Confirm the final request uses the exact hashed artifact (or an immutable snapshot), not a mutable path re-read later.

- [ ] **P0 — Long-form defaults private and public needs explicit release approval.** Inspect `app/publish/youtube_longform_upload.py::main` and `publish_authorization.py::DEFAULT_DESTINATION`, `_check_destination`. **Evidence required:** omitted destination yields `privacyStatus=private`; `public` without separate release approval is blocked; valid release approval is bound to the exact long-form metadata/video; invalid destination is rejected; `--dry-run` does not upload.

- [ ] **P0 — API authentication protects all non-health routes and fails closed.** Inspect `api/main.py::require_api_key`, route dependencies on `/start`, `/jobs`, `/status/{job_id}`. **Evidence required:** absent server key returns service-unavailable/fail-closed; missing, wrong-scheme, empty, whitespace-padded, and wrong bearer token rejected; all protected routes reject and start no job/thread/process; `/health` is intentionally public and reveals no job state or secrets.

- [ ] **P1 — Dry-run has no side effects beyond validation.** Inspect each publisher’s `publish(..., dry_run=True)`, `publish_social.py::publish_all_social`, `publish_all.py` orchestration and Instagram tunnel setup. **Evidence required:** authorization still runs, but dry-run performs no upload, public URL/tunnel startup, ledger write, metadata/video mutation, or misleading success notification. Assert all such mocks are untouched.

- [ ] **P1 — Partial/ambiguous cross-post results are honest and safe to retry.** Inspect `publish_all.py::run`; publisher ledger writes and `ambiguous` outcomes in `app/publish/*`. **Evidence required:** one destination success followed by failure/drift/ambiguous ledger write reports per-platform states and non-atomic partial completion; retry reconciles or blocks rather than duplicating; no aggregate “completed” claim while any destination is failed, blocked, or ambiguous.

## Evidence package

Use mocked Google/Meta clients, temporary files and an injected clock; no network or real publishing. Provide focused test output for each checked policy path, plus call-count assertions proving blocked paths never invoke the adapter. Record the exact policy version and test names. **Unknown:** confirm the intended policy for no-cutout content and whether social public release uses the same separate authorization artifact as YouTube.
