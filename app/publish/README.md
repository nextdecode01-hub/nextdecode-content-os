# Publishing package

Canonical implementations and CLI entrypoints for platform publishing.

## Modules

- `youtube_upload.py` — YouTube Shorts uploader.
- `youtube_longform_upload.py` — long-form YouTube uploader.
- `facebook_reels_upload.py` — Facebook Reels uploader.
- `instagram_reels_upload.py` — Instagram Reels uploader.
- `social_orchestrator.py` — multi-platform social posting adapter.
- `orchestration.py` — Shorts preflight, authorization re-checks and cross-platform publishing.
- `scheduler.py` — 20:00 IST scheduler for approved Shorts and scheduled long-form uploads.
- `authorization.py` — shared publishing authorization boundary.

## Canonical invocation

Run package entrypoints from the repository root:

- `python -m app.publish.orchestration`
- `python -m app.publish.scheduler`
- `python -m app.publish.youtube_upload`
- `python -m app.publish.youtube_longform_upload`
- `python -m app.publish.social_orchestrator`

Shell scripts and the autonomous task worker invoke these package modules directly. Root-level forwarding/compatibility Python files have been retired; do not recreate them.

## Authorization boundary

- `authorization.py` is the canonical shared authorization decision boundary.
- Platform adapters and orchestration must not define their own approval policy or bypass shared authorization.
- Review approval, rights, quality, artifact/version binding, destination policy and upload authorization remain distinct gates.
- `--scheduled-approved` is a time-window restriction, not an authorization grant by itself.
- Automatic public publishing remains disabled unless separately authorized.
- Do not run live publish commands as package smoke tests. Use mocks, dry-run fixtures and governance tests.

## Verification

- `tests/test_publish_orchestration_package_layout.py` verifies canonical module paths and CLI help.
- Publishing governance and approval-integrity tests verify invocation and authorization contracts.
- Never use live platform credentials or network publishing as a migration test.


### WP5 protected-action receipt binding

The shared `authorize_publish` boundary now emits an `authorization_id` bound
to the policy version, action type, platform, purpose, private destination,
approval timestamp, reviewer, and exact metadata/video SHA-256 digests.
Publishing adapters verify the receipt scope and integrity before opening the
digest-pinned upload snapshot. The existing full authorization checks still
run for every publishing operation; the receipt is not a bearer token and
cannot independently grant authority.

Public/unlisted destinations remain blocked. The receipt does not replace
human approval, rights/evidence/storyboard gates, upload-time digest
verification, or platform-specific safeguards. This local receipt mechanism
is not yet the canonical WP5 authorization service/ledger.
