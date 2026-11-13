# Repository Architecture and Rationalization Audit

> **Historical snapshot note (2026-11-07):** The findings below describe the repository at the audit date and are not the current runtime inventory. The automation bridge, dedicated integration files, Docker/Compose assets, user data directory and systemd units were retired on 2026-11-07. See [current Autonomous Task Execution Core](../AUTONOMOUS_FREE_TOOLING_ARCHITECTURE.md) and [cutover manifest](../CLEANUP_MIGRATION_MANIFEST.md).

**Date:** 2026-11-05  
**Status:** Evidence-backed archive disposition, reversible quarantine and n8n boundary documented  
**Authority:** Local engineering audit. Accepted P0/P1 owner decisions and the D-drive workspace remain authoritative.

## 1. Scope and baseline

This audit covers the holding/archive area, n8n's role, repository structure and safe consolidation. Repository: /home/demon/shorts_studio; this is not the separate engineering-command-center repository.

The working tree already contained extensive tracked modifications, deletions and untracked work from earlier packages. All existing work was preserved. No reset, broad cleanup, commit or push was performed.

## 2. Holding and archive disposition

- _holding/ is the reversible quarantine area. It is not runtime storage or a general dumping ground.
- _holding/legacy-oauth/manual_auth.py and _holding/legacy-oauth/get_code.py were moved unchanged from archive/legacy-oauth/ after a caller scan found no runtime imports or invocations.
- The two helpers remain unsafe/dormant legacy recovery material, not approved operational tools. manual_auth.py uses a legacy localhost:5678 callback; get_code.py exchanges a supplied code and writes the root YouTube token file.
- SHA-256 values, original paths, reasons and restore instructions are recorded in _holding/MANIFEST.md. Tests and dependency documentation were updated.
- Other previously reviewed obsolete utilities and prototypes were removed from the working tree after backup and reference review; the detailed item record remains in docs/CLEANUP_MIGRATION_MANIFEST.md.
- tools/dev/ollama_chat.py is a developer utility, not an active production dependency.
- docs/archive/legacy-source-imports/ retains historical source documents. The root content studio os file and structure symlink is retained because historical P0 reports reference it.
- .agents/, .kilo/, .vscode/, reports/, runtime data/ and outputs/, secrets, databases, tokens and virtual environments are not disposable clutter. Preserve them unless a separate evidence-backed decision says otherwise.

## 3. Duplicate and small-file consolidation policy

An exact SHA-256 scan found no duplicate active Python implementation files. It did find exact duplicate historical Markdown files between docs/archive/legacy-source-imports/ and the local docs/nextdecode-workspace/ mirror. Those are intentionally retained as historical source and working mirror; do not delete one without canonical-document authority and retention review.

Root Python modules include compatibility facades. They are not accidental duplicate implementations: tests/test_root_compatibility_facades.py verifies module identity against canonical packages. Do not merge or delete these facades until all external, CLI, shell, service, agent and test callers have been migrated.

Small files should be combined only when they share one cohesive responsibility, lifecycle, change cadence and owner. Keep separate modules where they represent different security, policy, provider, persistence or adapter boundaries. Avoid giant catch-all modules and speculative framework layers.

## 4. n8n versus dashboard decision

The accepted owner disposition is ADR-001: retain n8n temporarily as an optional transitional automation adapter; do not make it the permanent Content OS orchestrator. A dashboard does not replace durable scheduling, queues, workers, idempotency or recovery.

### Current dependency surface

- n8n_runner.py exposes /healthz, /run/generate and /run/publish; POST routes require bearer authentication, reject request bodies and invoke fixed commands. Generation forces review mode.
- workflow_n8n_approved_schedule.json calls studio-runner:8080.
- compose.yaml, Dockerfile.runner, .dockerignore, .n8n-docker.env, restore_n8n_workflow.sh, the runner/workflow tests and systemd configuration form one deployment boundary.
- The Dockerfile copies root n8n_runner.py; the runner invokes root scheduled_publish.py and the generation shell entrypoint. Moving one file independently would break path contracts.
- Runner PID 7327 was observed active in the earlier inspection. Docker CLI was unavailable in WSL, so Compose runtime status remains unverified. No workflow endpoint was invoked in this cleanup.
- Existing records show disagreement between the checked-in workflow export and the configured SQLite active flag. The n8n systemd service was previously observed crash-looping; the restore script default data path did not match the systemd N8N_USER_FOLDER.
- The systemd unit's plaintext runner-key assignment is a security risk. Secret values were not read or reproduced. Remediation and rotation require a controlled maintenance window.
- app/publish/scheduler.py enforces the publishing time window; app/tracking/run_tracker.py records run/artifact state. Neither is a durable workflow queue/worker recovery engine.

### Arrangement

integrations/n8n/README.md documents the current dependency surface and cutover requirements. Current runtime files remain at root until the full path-coupled migration is accepted. Target locations after cutover are integrations/n8n/ for adapter code and infra/automation/n8n/ for workflow/deployment assets.

Do not retire n8n until durable application-owned jobs, scheduling, worker leases, idempotency, retry/recovery, audit, observability, non-publishing shadow parity and rollback are accepted and the owner explicitly authorizes cutover.

## 5. Repository structure and consolidation boundaries

Use a feature-first modular monolith. app/ owns reusable application capabilities; api/ owns transport; root entrypoints remain thin compatibility/CLI adapters where required; tests mirror package boundaries; docs/ owns engineering records; tools/dev/ owns developer utilities; tools/maintenance/ is reserved for controlled operator tasks. Create web/, contracts/ and infra/ only when approved scope and actual artifacts require them.

Preserve the P0-A narrow vertical slice and Option A parallel feature-by-feature delivery with shared versioned contracts. Do not build a full Control Center or speculative orchestration framework as part of cleanup.

## 6. Security and change-control boundaries

- Keep approval_integrity.py and publish_authorization.py in their current locations until a dedicated security-aware migration is approved.
- Preserve exact human approval, artifact-hash binding, rights/quality gates and fail-closed publishing behavior.
- No public publishing, provider calls, OAuth execution, token reads, n8n workflow import/activation, service restart or database mutation occurred.
- No Docker build was claimed because Docker was unavailable.
- No commit, push, merge or deployment occurred.

## 7. Verification status

After the quarantine and documentation edits, the focused archive/dependency/facade/n8n suite passed: 17 passed. The full repository suite then passed: 688 passed, 1 warning and 53 subtests in 103.88s. The warning is the existing deprecated google.generativeai import. A control-byte scan found no control characters in the updated audit documents. git diff --check reports only the pre-existing .env.example blank line at EOF; that unrelated file was not changed.
