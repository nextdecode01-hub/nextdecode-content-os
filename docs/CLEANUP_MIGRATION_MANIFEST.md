# Shorts Studio cleanup migration manifest

Date: 2026-11-05

## Scope

Organize project documentation and historical reports, establish a verified local mirror of the D-drive NEXTDECODE workspace, remove only confirmed empty/generated artifacts, and reorganize selected implementation modules into domain packages with root compatibility aliases. Package layout and internal imports changed; application behavior, data schemas, provider fallback policy, approval/rights/publishing gates, credentials, runtime outputs and active services were preserved.

## Report organization

- 54 report/design/verification files were moved into reports/ by evidenced provenance.
- Original paths, attribution basis and original/final SHA-256 values are recorded in reports/MIGRATION_MANIFEST.md.
- Path references were updated in moved reports, the WP1 register cross-reference and the run_tracker.py docstring; see reports/MIGRATION_MANIFEST.md for the report-move record.
- The original opencode/ and copilot report/ folders were removed after their report files were moved.
- One OpenCode report duplicate was removed only after exact SHA-256 equality with the retained copy was confirmed.
- Ambiguous authorship was not guessed; such records remain in reports/unattributed/ or reports/secondary-agent/.

## D-drive documentation mirror

- Canonical source: D:\\MsP\\NEXTDECODE_WORKSPACE\\.
- Local mirror: docs/nextdecode-workspace/.
- Copied folders 00_CONTROL_AND_INDEX through 08_P1_PRODUCT_EXPANSION.
- 247 files mirrored; 0 SHA-256 mismatches after a refresh from the current D-drive source. A later D-drive update added REG-078 and refreshed five control/index documents; the local mirror was re-synced before final verification.
- 09_ARCHIVE_AND_SUPERSEDED was intentionally excluded.
- Four Windows Zone.Identifier pseudo-files that crossed the WSL/Windows copy boundary were removed from the mirror; no source document content was removed.
- Source D:\\MsP\\NEXTDECODE_WORKSPACE remains authoritative. The local copy is a dated mirror, not an owner decision, contract freeze or implementation authorization.
- Detailed per-file source paths, hashes and timestamps are in docs/nextdecode-workspace/MIRROR_MANIFEST.md.

## Legacy source snapshot preservation

- Moved the former root folder content studio os file and structure/ to docs/archive/legacy-source-imports/.
- Preserved all 111 files.
- Inventory found 93 exact same-name/SHA-256 counterparts in the D-drive workspace and 18 without an exact same-name/hash counterpart.
- No source document was deleted.
- A root-level compatibility symlink was initially retained for historical report references; it was removed on 2026-11-07 to keep the repository root limited to working project entrypoints. The complete imported snapshot remains under docs/archive/legacy-source-imports/.

## Other documentation moves

| Original | New location | Handling |
|---|---|---|
| ROADMAP.md | docs/ROADMAP.md | Moved; root documentation symlink retired on 2026-11-07 |
| link.md | docs/references/links.md | Moved; content preserved |
| P0_WP1_OWNER_DECISION_REGISTER.md | docs/workstream-review/wp1/P0_WP1_OWNER_DECISION_REGISTER.md | Moved; still awaiting owner disposition |
| NEXTDECODE_Creation_and_Work_Execution_Protocol_v1.0.md | docs/nextdecode-workspace/06_AGENT_HANDOFFS/ | Root duplicate removed after SHA-256 equality with D-drive source and local mirror was verified |

## Generated/empty artifacts

- Removed .pytest_cache and all __pycache__ directories outside the virtual environments; these are regenerable test/Python caches.
- Removed the empty .claude directory; it contained no files or subdirectories.
- Retained .agents, .kilo and .vscode because they contain reusable skills, agent configuration/plans and working project tasks.
- Updated .agents/skills/p0-documentation-intelligence/SKILL.md to the owner-approved ChatGPT/OpenCode/Qoder collaboration model; refreshed SKILL.zip and verified the embedded SKILL.md SHA-256 matches the source.
- Retained the three Kilo plans (last modified 2026-10-24 to 2026-10-26) and Kilo MCP configuration. agent-manager.json has an activeTarget ID with no matching entry in its local worktrees/sessions maps or this repo's .git/worktrees; preserved it because Kilo may own additional state outside this checkout.
- Retained VS Code OmniRoute tasks because their configured local Node and OmniRoute executable paths exist.
- Retained venv, .venv, outputs, data, archive, .env, .n8n-docker.env, youtube_token.json, cloudflared and the scheduled-generation lock. These are runtime, environment, credential or state-bearing paths and were not cleanup candidates.\n- On 2026-11-07, moved .env.bak-2026-10-26 outside the repository to /home/demon/.local/share/nextdecode/shorts-studio-local/ (directory mode 700, file mode 600); SHA-256 was verified before/after. No secret values were read.

## Preserved boundaries

- No application modules or tests were moved; one documentation-only path reference in run_tracker.py docstring was updated.
- No P0 canonical contract, owner decision or D-drive source file was edited.
- No credential values were read or printed.
- No tests were run during the file moves; post-cleanup regression verification is recorded separately. No live integrations, publishing, deployment, commit, push or merge were performed.
- The running n8n runner process was left untouched.


## Post-cleanup verification

- NP-1 notification boundary + existing Telegram API + production reliability suites: 37 passed.
- Markdown scan: 375 Markdown files scanned; 13 local links checked; 0 broken local links.
- Initial cleanup compatibility checks verified both root documentation symlinks; both were retired on 2026-11-07. Canonical documentation and imported-source archive targets remain intact.
- n8n_runner.py process was confirmed still running after cleanup and was not stopped or restarted.
- git diff --check reported pre-existing whitespace warnings in .env.example, publish_all.py and scheduled_publish.py. These files were already dirty before this cleanup and were not normalized or modified as part of the cleanup.
- At the initial cleanup stage, only the 37 focused tests had run. The subsequent full-suite and package-migration results are recorded in the final verification section below; no live/production pipeline was run.


## Abandoned agent work-artifact cleanup

- Moved scripts/replace_feed_fetchers.py and scripts/replace_desk_functions.ps1 into archive/abandoned-agent-scripts/.
- The OpenCode/Qoder historical audits identify both as unexecuted WIP; the PowerShell script is an abandoned partial duplicate, and the Python script has an exception-swallowing risk that requires fresh review before any future use.
- Repository reference search found no runtime import/call sites; only historical reports referenced the paths. Those report references were updated.
- Both scripts were preserved, not deleted or executed. The empty scripts/ directory was removed.


## Root-module package migration — 2026-11-05

- Moved six implementations into app/operations/: analytics_collect.py, meta_preflight.py, monetization_tracker.py, review_ledger.py, video_archive.py and workspace_sync.py.
- Kept root-level compatibility aliases for all six; five aliases delegate CLI execution to package main() while video_archive remains import-only, matching its prior behavior.
- Preserved the original ROOT/data path semantics by resolving the repository root from the new package depth.
- Original source files were backed up under /tmp/nd_operations_move_backup_20261105/ before migration; SHA-256 values and byte counts were recorded in the terminal execution evidence.
- Added tests/test_operations_package_layout.py to verify module identity, repository root/data paths and CLI delegate wiring.
- setup_check.py intentionally remains self-contained at root because its tests copy and execute it outside the repository package tree.
- No generated data, credentials, publishing authorization or external integrations were touched.


## Notification package migration — 2026-11-05

- Moved notify_status.py and notify_review.py implementations into app/notifications/.
- Preserved root-level import aliases and CLI behavior; notify_status still accepts one message and exits 2 when no message is supplied, without sending a request.
- Updated notify_review to import its sibling notification transport within the package and preserved repository-root data/output paths.
- Updated NP-1 boundary tests to inspect canonical package source and verify root alias identity/CLI compatibility.
- Telegram remains outbound-only; no webhook, polling, callback or approval surface was added.
- Original files backed up under /tmp/nd_notifications_move_backup_20261105/ before migration.


## Interim verification — operations/notifications tranche only

- At this intermediate point (before provider and tracking migrations), the full suite reported 671 passed, 1 warning and 53 subtests in 88.87s. This is superseded by the final full-suite run below.
- Focused operations/notification/API boundary tests after migration: **37 passed**.
- At this intermediate point, eight root compatibility imports resolved to the exact same module objects as their app/ package implementations.
- Four migrated operations CLI `--help` commands passed; review notifier `--help` and status notifier no-argument exit behavior passed.
- Intermediate Markdown verification: 381 files scanned, 20 local links checked, 0 broken links.
- Report manifest: 54 entries, 0 final SHA-256 mismatches.
- D-drive mirror: 247 files; refreshed manifest and source synchronization verified earlier with 0 mismatches.
- Existing n8n runner process remained active; no restart or workflow execution was initiated.
- No publishing, external provider calls, deployment, commit, push or merge were performed.
- The one test warning is the pre-existing deprecation warning from `google.generativeai`; no dependency was changed or installed.


## Provider package migration — 2026-11-05

- Moved multi_model_ai.py, model_health.py and omniroute_client.py implementations into app/providers/.
- Preserved root import aliases and CLI entrypoints. multi_model_ai now exposes a testable main(argv) equivalent to its previous inline CLI; provider generation/fallback logic is unchanged.
- Converted provider cross-imports to package-relative imports while preserving root alias identity for existing callers and monkeypatches.
- Preserved root .env loading and data/token_usage.json + data/model_health.json paths.
- No provider probe, API request, credential activation, package installation or paid-provider usage was performed.
- Original sources backed up under /tmp/nd_providers_move_backup_20261105/.

## Run-tracker package migration — 2026-11-05

- Moved run_tracker.py implementation into app/tracking/run_tracker.py; root run_tracker.py remains a module-identity compatibility alias.
- Preserved outputs/runs and data/runs/index.jsonl defaults, manifest schema, failure behavior and promotion journal semantics.
- Updated only stale module docstring text that incorrectly claimed the tracker had no callers; the short pipeline already imports start_run.
- Added tests/test_tracking_package_layout.py; focused tracker/publish/governance/storage tests passed 119 tests and 2 subtests.
- Original source backed up under /tmp/nd_tracking_move_backup_20261105/.


## Canonical internal-import migration — 2026-11-05

After preserving root compatibility aliases, internal application code was updated to import the canonical packages directly:
- Research/script/visual code imports `app.providers` for LLM calls and `app.operations.analytics_collect` for analytics history.
- Short/long pipelines import `app.tracking.run_tracker` and `app.operations.video_archive`.
- Publishing adapters and root publishing schedulers import `app.notifications.notify_status`.
- Provider health and generation modules use package-relative imports for their sibling modules.
- Added tests/test_package_internal_imports.py to prevent new legacy root imports from returning inside app/, pipelines/ and the two publishing orchestrators.
- Root shims remain for existing tests, CLI invocations and external callers.


## Final package-restructure acceptance — 2026-11-05

- Full repository suite after all package moves and canonical internal-import updates: **680 passed, 1 warning, 53 subtests passed in 99.77s**.
- The sole warning remains the existing `google.generativeai` package deprecation warning; no dependency was installed, upgraded or replaced.
- Focused package/boundary suite: **194 passed**; canonical internal-import guard: **2 passed**.
- All **12** legacy root module imports resolve to the exact same module objects as their canonical `app.*` implementations.
- CLI compatibility verified for four operations tools, the review notifier, both provider CLIs and the status notifier's no-message exit path. No provider API call was made.
- Markdown verification after all documentation changes: **383 files scanned, 22 local links checked, 0 broken links**.
- Reports archive: 54 migration-manifest entries; 0 final SHA-256 mismatches.
- D-drive workspace mirror: 247 files; 0 SHA-256 mismatches on the refreshed source synchronization.
- Legacy source snapshot: all 111 files remain preserved. Root compatibility symlinks resolve.
- All 12 root compatibility aliases verified; no generated cache directories remain outside virtual environments.
- n8n runner process remained active; no workflow execution or restart was initiated.
- No live production pipeline, publishing, provider activation, deployment, commit, push or merge was performed.
- Existing pre-cleanup dirty files and whitespace warnings were left intact; no broad formatting sweep was applied.


## Social publishing adapter package migration — 2026-11-05

- Moved the multi-platform social publisher implementation from publish_social.py into app/publish/social_orchestrator.py.
- Preserved root publish_social.py as a module-identity import alias and CLI delegate.
- Preserved repository-root paths and existing authorization checks; no publishing action or live platform request was made.
- Added tests/test_publish_social_package_layout.py for root alias identity, project-root path and CLI help compatibility.
- Focused publish social package, upload-safety, publish-governance, archive and setup tests: 79 passed.
- Original source backed up under /tmp/nd_publish_social_move_backup_20261105/.


## Final post-publishing migration audit — 2026-11-05

- Full repository suite after all current package migrations: **682 passed, 1 existing deprecation warning, 53 subtests passed in 98.19s**.
- Final Markdown audit: **384 files scanned, 23 local links checked, 0 broken links**.
- All **13** root compatibility aliases resolve to their canonical package module objects.
- Report manifest: 54 entries, 0 final SHA-256 mismatches.
- Canonical D-drive workspace mirror: 247 files; legacy source snapshot: 111 files preserved.
- Existing n8n runner PID 7327 remained active; no restart or workflow execution initiated.
- No staged changes, commit, push, merge, deployment, provider activation or publishing action.


## Publishing orchestration restructure and duplicate audit - 2026-11-05

- Moved the implementation from root `publish_all.py` to `app/publish/orchestration.py`; retained the root CLI/import-identity shim.
- Moved the implementation from root `scheduled_publish.py` to `app/publish/scheduler.py`; retained the root CLI/import-identity shim.
- Updated package implementations to resolve repository root from their new package location. No data, output, credential, approval or runtime-state paths were relocated.
- Caller map verified: `run_pipeline.sh` -> root `publish_all.py`; `n8n_runner.py` -> root `scheduled_publish.py`; Docker runner image copies standalone `n8n_runner.py`; n8n workflow continues to call fixed HTTP endpoints.
- Root compatibility aliases preserve module identity for existing imports and monkeypatch-based tests.
- Shared `publish_authorization.py`, approval/rights modules, upload adapters and long-form adapter were left untouched.
- Added `tests/test_publish_orchestration_package_layout.py`; focused package, governance, approval, dependency-map and n8n tests: **71 passed**.
- Full repository suite: **685 passed, 1 existing Google Generative AI deprecation warning, 53 subtests passed in 97.99s**.
- Exact duplicate scan outside docs/reports/runtime found no duplicate implementation files. Only identical empty `__init__.py` package markers were present; they are intentional package markers and were retained.
- Exact matches between `docs/nextdecode-workspace/` and `docs/archive/legacy-source-imports/` are intentional mirror/archive preservation copies. They were not deleted. A semantic/near-duplicate documentation reconciliation remains a separate evidence-led pass.
- Source backups retained at `/tmp/nd_publish_orchestration_move_backup_20261105/`.
- No n8n workflow execution or runner restart, live publishing, credential access, dependency install, deployment, commit, push or merge occurred.

## Archive rationalization - 2026-11-05

- Removed archive/abandoned-agent-scripts/ after reviewing both unexecuted WIP scripts. The Python script performed broad regex rewrites and swallowed all exceptions; the PowerShell script was only a partial duplicate. Neither had active references or execution history.
- Removed archive/legacy-oauth/server_5678.py after confirming it started no server and only printed the YouTube client ID.
- Before removal, all three items plus the WIP README were copied to /tmp/nd_archive_rationalization_backup_20261105/; SHA-256 hashes were recorded during the copy.
- Updated archive tests and documentation to distinguish intentionally retained historical utilities from removed dead/abandoned artifacts.
- No active pipeline, OAuth token, n8n workflow, scheduler or publishing code was changed.

## Second archive rationalization pass - 2026-11-05

- Removed unused prototype infrastructure: logging_config.py and resilience.py. Neither had active imports or tests; the implementations were not suitable to promote without redesign and secret-redaction validation.
- Removed publish_review_safe.py because no runtime caller used it and the active scheduler/runner already handles intentional review-only outcomes.
- Removed superseded/create_short.py because its production responsibilities had been split into the maintained app/script and pipelines modules; Git history remains the recovery source.
- Removed duplicate legacy OAuth callback servers auth_server.py and server_3000.py, plus duplicate exchange_token.py. No active runtime path referenced them.
- Retained only manual_auth.py and get_code.py as temporary manual YouTube OAuth recovery helpers until a replacement flow is verified. They are not part of runtime execution and require security review before use.
- Moved the optional local Ollama chat client from archive/optional-cli/ to tools/dev/; it is a manual developer utility, not a pipeline dependency.
- Removed now-empty archive groups unused-infra, optional-cli and superseded.
- All removed/moved sources were backed up under /tmp/nd_archive_rationalization_backup_20261105/ with SHA-256 hashes recorded. No OAuth token, credential, active pipeline, scheduler or publishing configuration was changed.

## Legacy source archive recovery - 2026-11-05

- The compatibility symlink "content studio os file and structure" was found pointing to a missing target.
- Four temporary recovery copies were found. All four contained the same 111 relative file paths and identical SHA-256 hashes.
- Restored the 111-file snapshot to docs/archive/legacy-source-imports/ and recreated its local README; the original root compatibility symlink now resolves to that path.
- Verified all 111 restored source files against the retained recovery copy: 0 missing, 0 extra, 0 hash mismatches.
- Removed three redundant temporary copies after verification; retained one recovery copy at /tmp/trial002b/content studio os file and structure.

## 2026-11-05 — legacy OAuth helper quarantine

- Created _holding/ as a reversible, manifest-backed quarantine area.
- Moved archive/legacy-oauth/manual_auth.py and archive/legacy-oauth/get_code.py unchanged to _holding/legacy-oauth/.
- Caller scan found no runtime imports or invocations; references were documentation and archive tests only.
- SHA-256 hashes, restore paths and security rationale are recorded in _holding/MANIFEST.md.
- Updated archive regression tests and the dependency map. No OAuth flow was executed and no token or credential was read.
- These files are not deleted. They remain blocked from routine use until a secure replacement re-authentication flow is verified.


## 2026-11-05 — maintenance package migration

- Moved the implementation of backfill_governance.py to tools/maintenance/backfill_governance.py.
- Kept the root backfill_governance.py as an import-identity and CLI compatibility shim.
- Updated the canonical implementation's ROOT calculation so the journal and metadata paths remain anchored at the repository root.
- Added tools/maintenance/README.md and package initialization; updated root-module and repository-layout documentation.
- Added a regression assertion for module identity, repository root and journal path.
- Focused archive and governance tests: 31 passed, 2 subtests passed.
- Root and package module CLI --help smoke checks passed. The execute path was not invoked; no live governance journal or artifact was changed.
- setup_check.py remains at root because its tests copy and run it independently of the package tree.
- approval_integrity.py and publish_authorization.py remain untouched as security-critical shared boundaries.


## 2026-11-05 — approval-integrity security-primitives package extraction

- Moved the unchanged shared primitives from root `approval_integrity.py` to `app/security/approval_integrity.py` and added `app/security/` package documentation.
- Kept the root `approval_integrity.py` as a `sys.modules` compatibility alias, preserving module identity for legacy imports and monkeypatching.
- Migrated internal review, scheduler, orchestration and publishing-authorization imports to the canonical `app.security.approval_integrity` path.
- Added the root-shim identity regression assertion and extended the AST import guard so application/pipeline code cannot regress to the root import.
- Kept `publish_authorization.py` separate and unchanged in policy/authority; it remains the single publishing authorization boundary. No approval semantics, expiry rules, hashing behavior, 20:00 IST window, destination policy or publisher behavior was intentionally changed.
- Focused approval, review-provenance, publishing-governance, package-layout and internal-import tests: **73 passed**.
- No publishing command was executed; no live upload, credential access, service restart, workflow execution, commit, push, merge or deployment occurred.


## 2026-11-05 — publishing authorization policy package extraction

- Moved the existing single publishing authorization implementation from root `publish_authorization.py` to `app/publish/authorization.py` without redesigning its policy logic.
- Kept root `publish_authorization.py` as a `sys.modules` compatibility alias, preserving module identity and mutable `ROOT` monkeypatch behavior for legacy tests and maintenance tooling.
- Updated the package implementation's repository-root anchor to `Path(__file__).resolve().parents[2]` and switched its visual-quality dependency to the canonical `app.visuals.visual_quality` module.
- Migrated all in-package platform adapters and orchestration to `app.publish.authorization`; the owner-run maintenance backfill retains its root import through the compatibility shim.
- Added the root alias to the facade identity test and an explicit assertion that the canonical module still resolves `ROOT` to the repository root. Extended the AST import guard against internal root-shim imports.
- Focused publishing governance, ND-ENG-006, upload safety, compatibility identity, approval/review, package-layout and n8n regression tests: **117 passed, 2 subtests passed**.
- The separate `app.security.approval_integrity` package remains responsible only for low-level integrity primitives. Publishing authorization remains the sole policy decision point; review, rights, quality, artifact binding, destination restrictions and human approval semantics are unchanged.
- No live publisher, n8n workflow, credential, service, network upload or public publishing path was executed or changed. No commit, push, merge or deployment occurred.


## 2026-11-05 — n8n restore backup safety repair

- Corrected the restore script's default SQLite data directory to `/home/demon/.n8n`.
- Replaced raw database file copying with Python SQLite online backup and a backup-side integrity check.
- Missing database now stops the script before any API request. Backup directory and files receive restrictive permissions.
- Added isolated tests using temporary SQLite data and a fake HTTP API: **8 passed** across restore, runner and workflow suites.
- Runtime inventory and remaining n8n cutover/security blockers are documented in `integrations/n8n/README.md`.
- No live database, workflow, credential, service, upload, commit, push or deployment was modified or invoked.



## Root forwarding-wrapper retirement — 2026-11-07

- Retired 30 root-level Python forwarding/import-identity wrappers after migrating application, test, shell, scheduler and n8n callers to canonical package modules.
- Canonical imports now target `app.operations`, `app.security`, `app.review`, `app.publish`, `app.notifications`, `app.providers`, `app.tracking`, `app.visuals` and `tools.maintenance` directly.
- Updated `run_pipeline.sh`, `run_scheduled_generation.sh`, `run_longform_pipeline.sh` and `n8n_runner.py` to invoke package modules with `python -m`. The HTTP paths exposed to n8n were not changed.
- Publishing orchestration now launches each platform adapter as a canonical package module. The scheduler invokes the Shorts orchestrator and long-form uploader the same way. Telegram review reminders now provide module-based approval commands.
- Root Python policy is enforced by tests: only `n8n_runner.py`, `motion_render.py` and `setup_check.py` may remain at repository root.
- Original wrapper bytes were backed up outside the repository at `/home/demon/.local/share/nextdecode/shorts-studio-root-wrapper-backup-20261107/`; all 30 backup SHA-256 values were checked before deleting root copies. The backup is not a runtime dependency and is not part of Git.
- Human approval, artifact hashing, rights checks, quality gates, private destination defaults and public-publishing authorization were not weakened. No upload, provider call, deployment, commit or push was performed.


## 2026-11-07 — Complete n8n runtime retirement and application-owned task core

- Removed the root HTTP bridge, workflow export, restore script, dedicated integration package/tests, environment file, Dockerfile/Compose assets and transitional ADR from the active repository.
- Disabled and removed the old n8n and studio-runner systemd user services; removed the installed n8n package, its user data directory and local cache/log files. No old service unit remains enabled.
- Verified the active repository contains zero files with n8n in their names and no active runtime references in the current app/API/pipeline/tooling paths. Historical architecture snapshots and the dated canonical workspace mirror are retained as historical evidence and are not runtime dependencies.
- Replaced the old orchestration role with `app.autonomy`: versioned task/plan contracts, allow-listed capabilities, SQLite WAL task store, atomic DAG persistence, dependencies, idempotency, worker leases, retry/backoff, append-only events, authenticated API routes, CLI and systemd worker.
- Added a ranked tool catalogue with primary/fallback candidates and explicit license/cost/qualification notes. Catalogue entries do not install or invoke tools.
- Publishing remains blocked in the autonomous capability registry; generation defaults to dry-run and refuses non-dry-run requests. No public upload, paid provider activation, commit, push or deployment occurred.
- Verification at cutover: focused autonomy/API/catalog suites passed; full repository suite is being rerun against the final revision. See the final handoff for exact result.
