# Root Module Dependency Map — canonical layout

Date: 2026-11-07
Repository: `/home/demon/shorts_studio`

## Current root policy

The repository root must contain only working project entrypoints, runtime/configuration files and required project folders. A Python file that merely forwards imports or CLI execution to an implementation under `app/` is not allowed at root.

**Allowed root Python files:**
- `setup_check.py` — standalone environment/setup diagnostic.

All other application implementations live in canonical packages. The root automation bridge was retired on 2026-11-07 after callers were migrated to the application-owned task API and worker.

## Canonical module map

| Domain | Canonical module |
|---|---|
| Operations | `app.operations.analytics_collect`, `meta_preflight`, `monetization_tracker`, `review_ledger`, `video_archive`, `workspace_sync` |
| Notifications | `app.notifications.notify_status`, `notify_review` |
| Providers | `app.providers.multi_model_ai`, `model_health`, `omniroute_client` |
| Autonomy | `app.autonomy.planner`, `registry`, `store`, `worker`, `tool_catalog` |
| Publishing | `app.publish.orchestration`, `scheduler`, `social_orchestrator`, `authorization`, `youtube_upload`, `youtube_longform_upload`, `facebook_reels_upload`, `instagram_reels_upload` |
| Approval/review | `app.security.approval_integrity`, `app.review.review_bundle`, `approve_review`, `approve_longform`, `review_longform` |
| Visuals/render adapter | `app.render.legacy_api`, `app.visuals.motion_director`, `stock_fetcher`, `visual_assets`, `visual_quality` |
| Maintenance | `tools.maintenance.backfill_governance` |

## Runtime entrypoints

- `run_pipeline.sh` calls `python -m app.review.review_bundle`, `app.notifications.notify_review`, `app.notifications.notify_status` and `app.publish.orchestration`.
- `run_scheduled_generation.sh` and `run_longform_pipeline.sh` call package modules directly.
- `api/main.py` exposes authenticated task/plan/capability routes; `app.autonomy.worker` owns durable task execution.
- `app.publish.orchestration` invokes each platform uploader with `python -m app.publish.<adapter>`.
- `app.publish.scheduler` invokes the Shorts orchestrator and long-form uploader by module name.
- Review reminders give the owner module-based approval commands.

## Removed root forwarding files

Thirty-one root forwarding/compatibility files were retired. Their original bytes and SHA-256 hashes are preserved outside the repository at:

`/home/demon/.local/share/nextdecode/shorts-studio-root-wrapper-backup-20261107/`

The backup is recovery material only; it is not a runtime dependency and must not be copied back into the root.

## Verification policy

- `tests/test_root_compatibility_facades.py` now enforces the allowed root Python-file set.
- Package-layout tests verify canonical package locations, project-root paths and module CLI entrypoints.
- Internal imports must use canonical `app.*` modules; root-level forwarding imports are prohibited.
- Keep this map current whenever a package or operational entrypoint changes.
