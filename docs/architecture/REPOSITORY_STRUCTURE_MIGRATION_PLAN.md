# NEXTDECODE Repository Structure Migration Plan

**Status:** Recommended phased plan; owner-approved repository direction, not a P0/P1 contract freeze  
**Date:** 2026-11-05  
**Applies to:** `/home/demon/shorts_studio`

> **Superseded for automation/runtime decisions on 2026-11-07.** This document is retained as a dated migration-planning snapshot. Its transitional automation bridge, Compose/Docker runner and future external workflow adapter recommendations have been retired. The current implementation is documented in [Autonomous Task Execution Core](../AUTONOMOUS_FREE_TOOLING_ARCHITECTURE.md), [dependency map](../dependency_map.md) and [root module map](../ROOT_MODULE_DEPENDENCY_MAP.md). Do not execute the old automation phases below.

## 1. Migration objective

Evolve the existing Shorts Studio repository into a maintainable Content OS codebase without replacing the working production engine, creating speculative services, breaking historical entrypoints or expanding P0-A into a full dashboard.

The target is a **feature-first modular monolith** with explicit API/contracts and adapter boundaries. Deployable services are introduced only when operational evidence justifies them.

## 2. Current-state baseline

Already present and treated as canonical application packages:

- `app/research/`
- `app/script/`
- `app/voice/`
- `app/visuals/`
- `app/render/`
- `app/publish/`
- `app/providers/`
- `app/notifications/`
- `app/operations/`
- `app/tracking/`

Existing transport and entrypoint boundaries:

- `api/` - legacy generation API; not yet the complete Content OS control plane.
- `pipelines/` - specialist CLI/pipeline entrypoints.
- Root Python files - a mixture of stable CLI entrypoints and temporary compatibility facades.
- `data/` and `outputs/` - live runtime state and generated artifacts; preserve their paths and semantics.
- `docs/nextdecode-workspace/` - dated mirror; the D-drive workspace remains canonical.
- `n8n_runner.py`, workflow JSON, Compose/Docker assets and restore script - transitional automation assets with live/runtime path dependencies.

No `web/`, `contracts/`, `infra/` or `integrations/` application structure is created solely to make the tree resemble a template. Create each when its first approved implementation needs it.

## 3. Phased migration

### Phase 0 - Stabilize and document current ownership (completed for this cleanup)

- Keep feature code inside its existing `app/<feature>/` package.
- Keep root aliases for legacy callers, but prohibit new internal imports from using them.
- Preserve runtime paths, generated outputs, credentials and active services.
- Keep archive evidence and migration manifests inspectable.
- Maintain tests for module identity, CLI behavior and data-path compatibility.

**Exit evidence:** package layout tests pass; internal-import guard passes; no unexplained duplicate implementation remains in the reviewed scope.

### Phase 1 - Close application workflow ownership gaps (not started)

Before building a general scheduler, map the existing generation pipeline, run tracker, review/approval store, publishing authorization and notification boundary to the canonical P0/P1 contracts.

Design one versioned application workflow/job contract that specifies:

- job identity, idempotency key, trigger source and requested schedule;
- state transitions, ownership, timestamps and terminal/ambiguous outcomes;
- worker lease, retry/backoff, cancellation and stale-job recovery;
- run ID and artifact references (reuse the current run tracker);
- human-review state as a distinct state from automated policy disposition;
- rights, quality and publishing authorization as separate fail-closed gates;
- audit events, observability and operator actions.

Do not create a second approval store or a second run/artifact ledger. If a canonical contract or owner decision is missing, name the exact dependency and pause that part rather than inventing it.

### Phase 2 - Implement application-owned scheduling and workers (future, separately scoped)

After Phase 1 contracts and scope are approved:

- Add a durable scheduler/queue and worker lifecycle behind application-owned interfaces.
- Reuse existing pipeline modules, run tracking and protected publishing adapters.
- Keep transport separate: API/CLI enqueue jobs; workers execute use cases; domain policy controls allowed transitions.
- Add recovery, idempotency, retry and dead-letter handling with operator visibility.
- Add integration and end-to-end tests using isolated state and no real platform upload.

Do not treat the current `app/publish/scheduler.py` as this system; it only enforces the 20:00 IST publishing window.

### Phase 3 - Migrate n8n as an external adapter (after application replacement works)

Only after Phase 2 passes its acceptance criteria:

1. Inventory all active workflows, webhook URLs, runner endpoints, service units, databases, environment files and restore paths.
2. Move deployment/workflow assets to `infra/automation/n8n/` and adapter code to `integrations/n8n/` in one caller-aware migration.
3. Update service paths, workflow references, environment loading and restore tooling together.
4. Verify service startup, workflow import/export, health checks, secrets, rollback and non-publishing shadow execution.
5. Compare schedule outcomes and failure/recovery behavior against the application scheduler.
6. Obtain explicit owner approval before disabling the old schedule or changing production service state.

Do not move files while systemd or workflows still point at their current locations. Do not run the existing restore script until its configured data directory matches the actual n8n user folder.

### Phase 4 - Add the Content OS API and dashboard surfaces (separately authorized)

- Evolve `api/` into versioned transport endpoints only as approved contracts become implementable.
- Create `contracts/` for approved OpenAPI, event and JSON schemas; validate compatibility in CI.
- Create `web/` only after the frontend framework, authentication model and UI scope are approved.
- The UI reads/writes through authenticated APIs; it never reads local worker files or edits queue/run/approval records directly.
- Keep P0-A narrow. Full Control Center, broad analytics dashboards and P1 product expansion remain deferred until separately approved.

### Phase 5 - Retire compatibility and transitional assets

- Search every import, CLI, shell script, service unit, scheduled task, test, documentation link and external caller.
- Replace callers with canonical package/API paths.
- Verify module identity is no longer required by any legacy consumer.
- Remove one compatibility facade at a time with focused tests.
- Retire n8n only after the ADR-001 cutover criteria, workflow export/backup, owner authorization and rollback window are satisfied.
- Remove legacy OAuth helpers only after a secure, verified replacement re-authentication path exists.

## 4. Real-world workflow-to-code mapping

| Real workflow | Application owner | External adapter role |
|---|---|---|
| Daily topic discovery | Research use case + durable scheduler | n8n may forward a calendar/RSS/form event |
| Research-to-video generation | Pipeline worker + run tracker | n8n may send a bounded trigger during transition |
| Script/final-video review | Review/approval domain and authenticated UI | Notification adapter sends reminder only |
| Failed or ambiguous render | Worker recovery + run state + operator audit | n8n may route an alert |
| Scheduled cross-platform publishing | Publishing scheduler + authorization + platform adapters | n8n may wake/notify; cannot authorize or upload around policy |
| Analytics/feedback ingestion | Operations/analytics package | External integrations deliver validated events |

## 5. Non-negotiable migration rules

1. One canonical implementation per capability.
2. One active writer per file; parallel work only across independent packages and shared versioned contracts.
3. Never move a live path without a caller map, compatibility test and rollback plan.
4. Never move runtime data, OAuth tokens, environment secrets or generated media into source packages.
5. No speculative empty folders, generic `utils.py`, or premature microservices.
6. Do not combine distinct domain concepts merely to reduce folder count; preserve clear boundaries.
7. New code imports canonical package paths. Root facades are compatibility-only and have a removal condition.
8. Tests are reorganized gradually by layer; no mass test move during unrelated implementation.
9. Documentation mirrors remain read-only copies of the canonical D-drive workspace unless the owner explicitly changes the source of truth.
10. No commit, push, merge, deployment, service restart, workflow execution or public publishing without separate authorization.

## 6. Next actionable work package

The next engineering package should be a **read-only workflow/scheduler dependency map and contract-gap review**, not another generic folder move. It should trace:

- current generation entrypoints and their callers;
- n8n workflow -> runner -> shell command -> publishing/generation call graph;
- run tracker persistence and failure recovery boundaries;
- review/approval and publishing authorization sources of truth;
- existing scheduler behavior and missing durable queue semantics;
- canonical P0/P1 documents and any missing owner decisions.

Only after this map is reconciled should the application-owned scheduler/worker package be designed or implemented.
