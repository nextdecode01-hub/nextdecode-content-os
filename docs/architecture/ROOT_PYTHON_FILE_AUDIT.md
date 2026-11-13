# Root-Level Python File Audit

> **Historical snapshot note (2026-11-07):** The findings below describe the repository at the audit date and are not the current runtime inventory. The automation bridge, dedicated integration files, Docker/Compose assets, user data directory and systemd units were retired on 2026-11-07. See [current Autonomous Task Execution Core](../AUTONOMOUS_FREE_TOOLING_ARCHITECTURE.md) and [cutover manifest](../CLEANUP_MIGRATION_MANIFEST.md).

**Date:** 2026-11-05  
**Status:** Inventory and phased migration in progress; review, render, maintenance, approval-integrity and publishing-authorization implementations are package-owned while root CLI/import compatibility is preserved  
**Scope:** Root-level `*.py` files in `/home/demon/shorts_studio`  
**Authority:** Local engineering audit. It does not supersede canonical D-drive P0/P1 documents or authorize runtime, service or publishing changes.

## Executive summary

The root currently contains 33 Python files:

- **29 application compatibility facades** that delegate to canonical `app/` packages, plus one root maintenance-command compatibility shim.
- **1 hybrid compatibility adapter** (`motion_render.py`) that re-exports the new render package and preserves legacy asset-resolution behavior.
- **2 operational/domain/CLI entrypoints or canonical modules** that still have real root-level responsibilities and active callers.

The root is not simply cluttered with duplicate implementations. Most of the small files are migration bridges. The correct cleanup is caller-aware retirement, not bulk deletion.

## 1. KEEP - root-level project and operational entrypoints

| File | Why it stays for now | Evidence / dependency |
|---|---|---|
| `n8n_runner.py` | Runtime HTTP bridge used by the current n8n/Compose deployment. | Dockerfile copies it into the runner image; systemd runner was previously observed active. |
| `setup_check.py` | Project setup/readiness CLI; intentionally repository-root aware. | Existing setup documentation and package-layout tests expect a root CLI. |
| `backfill_governance.py` | Root compatibility CLI/import shim; implementation is `tools/maintenance/backfill_governance.py`. | Governance tests import and patch the root alias; the CLI path remains available. |

**Important:** `app/security/approval_integrity.py` contains security-sensitive shared primitives; `app/publish/authorization.py` remains the sole policy/authorization boundary. They are deliberately separate concepts. Both root import shims preserve compatibility; neither extraction changes policy.

## 2. COMPATIBILITY FACADE - retain until callers are migrated

These files are not the canonical implementations. Their implementations live under `app/`. Four review workflow implementations were migrated in the first package extraction.

| Root file | Canonical implementation |
|---|---|
| `approval_integrity.py` | `app/security/approval_integrity.py` |
| `publish_authorization.py` | `app/publish/authorization.py` |
| `meta_preflight.py` | `app/operations/meta_preflight.py` |
| `monetization_tracker.py` | `app/operations/monetization_tracker.py` |
| `review_ledger.py` | `app/operations/review_ledger.py` |
| `video_archive.py` | `app/operations/video_archive.py` |
| `workspace_sync.py` | `app/operations/workspace_sync.py` |
| `notify_status.py` | `app/notifications/notify_status.py` |
| `notify_review.py` | `app/notifications/notify_review.py` |
| `multi_model_ai.py` | `app/providers/multi_model_ai.py` |
| `model_health.py` | `app/providers/model_health.py` |
| `omniroute_client.py` | `app/providers/omniroute_client.py` |
| `run_tracker.py` | `app/tracking/run_tracker.py` |
| `publish_social.py` | `app/publish/social_orchestrator.py` |
| `facebook_reels_upload.py` | `app/publish/facebook_reels_upload.py` |
| `instagram_reels_upload.py` | `app/publish/instagram_reels_upload.py` |
| `youtube_upload.py` | `app/publish/youtube_upload.py` |
| `youtube_longform_upload.py` | `app/publish/youtube_longform_upload.py` |
| `scheduled_publish.py` | `app/publish/scheduler.py` |
| `motion_director.py` | `app/visuals/motion_director.py` |
| `visual_assets.py` | `app/visuals/visual_assets.py` |
| `visual_quality.py` | `app/visuals/visual_quality.py` |
| `stock_fetcher.py` | `app/visuals/stock_fetcher.py` |
| `publish_all.py` | `app/publish/orchestration.py` |
| `review_bundle.py` | `app/review/review_bundle.py` |
| `approve_review.py` | `app/review/approve_review.py` |
| `approve_longform.py` | `app/review/approve_longform.py` |
| `review_longform.py` | `app/review/review_longform.py` |

The compatibility files preserve old import identity and/or CLI behavior. They should be removed only when:

1. Internal imports use the canonical package path.
2. Shell scripts, service definitions, Docker build context, scheduled jobs and documentation no longer invoke the root name.
3. External/agent workflows have been checked for the old path.
4. Compatibility tests are replaced by canonical-package and CLI integration tests.
5. A focused regression suite passes.

Do not delete a facade solely because it is short or appears redundant.

## 3. HYBRID ADAPTER - compatibility retained after internal migration

| File | Current role | Required next step |
|---|---|---|
| `motion_render.py` | Re-exports render APIs from `app/render/`, delegates visual asset resolution to `app/visuals/chain.py`, and preserves legacy `resolve_asset_detail` / `resolve_asset` semantics. | Internal `app/script/pipeline.py` and `pipelines/short.py` callers have migrated. Retain this facade for tests and any external/legacy consumers until a separate caller retirement review. |

This is not a pure one-line shim. It must not be deleted or mechanically replaced until all compatibility behavior has a canonical home and tests cover the translated API.

## 4. Remaining root modules - require dedicated work packages

The `backfill_governance.py` implementation has already moved to `tools/maintenance/`; its root shim is retained for CLI and import compatibility.

| File | Possible future destination | Why not moved now |
|---|---|---|

| `n8n_runner.py` | `integrations/n8n/` after cutover | Dockerfile, Compose and service paths depend on the current root location. n8n is transitional but not yet retired. |
| `setup_check.py` | Root CLI may remain permanently | It is a natural project-level readiness command and is not feature implementation clutter. |

Both security modules now have canonical package locations: `app/security/approval_integrity.py` owns low-level integrity primitives; `app/publish/authorization.py` owns the single publishing policy decision. Both root import shims remain for compatibility.

## 5. Verified caller evidence

The following direct references were confirmed during this audit:

- `run_pipeline.sh` and `run_longform_pipeline.sh` continue to invoke root review CLI facades, which delegate to `app/review/`.
- `app/notifications/notify_review.py` references the stable root CLI commands `approve_review.py` and `approve_longform.py`.
- `app/publish/orchestration.py` and platform adapters import `app.publish.authorization`; maintenance tooling may continue importing the root shim.
- Review, scheduler, orchestration and publishing authorization modules import `app.security.approval_integrity`; publishing adapters import `app.publish.authorization`. Legacy tests/callers may continue importing both root shims.
- `app/script/pipeline.py` and `pipelines/short.py` now import render/subtitle APIs from `app.render`; no application/pipeline import of the root adapter remains.
- Tests directly import and monkeypatch root approval, review, runner and motion modules. Their module identity and patch behavior are part of the current compatibility surface.
- `Dockerfile.runner` copies `n8n_runner.py`; Compose builds using the repository root context.
- `app/publish/scheduler.py` invokes the root `youtube_longform_upload.py` CLI.

The repository now has explicit module-identity tests for all 29 retained application facades. CLI delegation and command behavior continue to be covered by the existing workflow and integration tests; external consumers still require a caller audit before facade retirement.

## 6. Root-level non-Python files

Keep conventional project-level files in root when tools expect them there:

- `README.md`, `requirements.txt`, `.gitignore`, `.dockerignore`, `.env.example`.
- `compose.yaml` and `Dockerfile.runner` may remain until the n8n migration/cutover; their build context and service references must move together.
- Runtime state and secrets such as `.env`, `.env.bak-*`, `.n8n-docker.env`, `youtube_token.json`, lock files, databases and generated media are not source files. Preserve them in their current runtime locations and never commit them.
- The root compatibility symlinks `ROADMAP.md` and `content studio os file and structure` are retained for historical references. `cloudflared` is an environment symlink and must not be treated as a normal source folder.

## 7. Recommended root cleanup sequence

1. **Completed:** classify all 33 root Python files; keep 29 app-package facades, one maintenance-command shim, one hybrid motion_render.py adapter and two root operational/shared/CLI entrypoints.
2. **Completed:** compatibility identity coverage spans the 28 facades in `tests/test_root_compatibility_facades.py` plus the approval-integrity root shim in `tests/test_approval_integrity.py`. Publishing authorization also has an explicit repository-root anchor assertion. Existing CLI/workflow tests cover selected command behavior; external/manual callers still require evidence before facade retirement.
3. **Completed:** internal motion_render callers in app/script/pipeline.py and pipelines/short.py now use canonical app.render APIs. Keep the hybrid root adapter until external callers and legacy behavior are cleared.
4. **Completed:** review implementations are canonical under app/review/; four root CLI/import facades remain for shell, notification, tests and legacy callers.
5. **Completed:** moved backfill_governance.py implementation to tools/maintenance/; root shim preserves import identity and CLI invocation. Governance tests verify root/data paths and journal patchability.
6. **Completed, dedicated security-aware extractions:** moved approval-integrity primitives to `app/security/approval_integrity.py` and the single publishing policy boundary to `app/publish/authorization.py`; retained both root import shims, migrated internal callers, and added identity/import-guard coverage. Policy logic and approval gates were not redesigned.
7. **Deferred:** move n8n assets only after application-owned durable scheduler/queue/worker replacement passes ADR-001 cutover criteria and the owner explicitly authorizes cutover.
8. Delete each compatibility facade individually only after Python, CLI, shell, Docker/Compose, service, scheduled-task, docs, external/manual and agent caller scans plus focused regression evidence.

## 8. Change-control outcome

- The initial inventory phase was read-only. Subsequent bounded package extractions are recorded in Sections 9 and 10.
- Four review implementations were moved to `app/review/`; root compatibility facades were retained.
- No root file was deleted, and no runtime data location was changed.
- No active service, n8n workflow, runner, OAuth token, database or publishing path was changed.
- No commit, push, merge, deployment or public publishing occurred.
- Existing uncommitted changes were preserved.

## 9. First migration execution - completed

**Date:** 2026-11-05

- `app/script/pipeline.py` now imports `render_video`, `qa_video` and `make_kinetic_ass` directly from `app.render`.
- `pipelines/short.py` now imports `make_kinetic_ass` from `app.render.subtitles`.
- The dry-run path no longer imports the root `motion_render` compatibility adapter.
- `tests/test_phase5_script_package.py` now patches the canonical subtitle function.
- `tests/test_package_internal_imports.py` now explicitly rejects internal `motion_render` imports.
- Added `tests/test_root_compatibility_facades.py` for the 28 general root facades, including publishing authorization; approval-integrity shim identity is separately asserted in `tests/test_approval_integrity.py`.

**Verification:**
- Focused rendering and visual regression tests: **96 passed, 51 subtests passed**.
- Compatibility identity, internal-import and storage-layout tests: **9 passed**.
- Full project suite using `./venv/bin/python -m pytest -q`: **688 passed, 1 warning, 53 subtests passed**.
- The warning is the existing `google.generativeai` package deprecation warning.
- Compile check passed for changed Python modules/tests.
- Repository-wide diff check still reports the previously existing trailing blank-line warning in `.env.example`; no unrelated edit was made to that file.
- A system-Python test attempt failed collection because system Python lacks FastAPI; rerunning with the project virtual environment passed.

**Outcome:** Internal application/pipeline code no longer imports `motion_render`. The root adapter remains intentionally available for external/legacy imports and tests. It is not yet safe to delete.

## 10. Review package extraction - completed

- Created `app/review/` for the cohesive review-package and human approval workflow.
- Moved the implementations of `review_bundle.py`, `approve_review.py`, `approve_longform.py` and `review_longform.py` into that package.
- Kept all four root paths as CLI/import compatibility facades; existing shell commands and notifications continue to use the same command names.
- Preserved root-relative runtime data/output paths using `Path(__file__).resolve().parents[2]` from the new package location.
- Preserved approval checklists, SHA-256 artifact binding, run-manifest verification, promotion journal checks, and explicit human approval semantics.
- Added `app/review/README.md` and extended the general root-facade identity coverage.

No publishing authorization, notification authority, approval policy or runtime data location was changed.


## 11. Approval-integrity primitives extraction — completed

- Canonical implementation: `app/security/approval_integrity.py`.
- Root `approval_integrity.py` remains a module-identity compatibility shim.
- Review, scheduler, orchestration and authorization internals import the canonical package path.
- The low-level helpers remain separate from publishing policy.
- Focused approval, provenance, governance, package-layout and import-guard tests: **73 passed**.

## 12. Publishing authorization policy extraction — completed

- Canonical implementation: `app/publish/authorization.py`.
- Root `publish_authorization.py` remains a module-identity compatibility shim for tests and owner-run maintenance tooling.
- In-package publisher adapters and orchestration import the canonical package path; maintenance backfill retains the root shim.
- The package module anchors `ROOT` at the repository root and imports canonical visual-quality and approval-integrity dependencies.
- Focused publishing governance, ND-ENG-006, upload safety, facade identity, approval/review, package-layout and n8n tests: **117 passed, 2 subtests passed**.
- The authorization policy itself was not redesigned. No live publishing or external side effect was invoked.
