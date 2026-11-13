# NEXTDECODE Repository Structure Standard

**Status:** Local engineering standard for repository organization; subordinate to accepted owner decisions and canonical P0/P1 contracts  
**Date:** 2026-11-05  
**Scope:** /home/demon/shorts_studio and future NEXTDECODE Content OS implementation work

## 1. Purpose and governing constraints

This standard keeps the existing Shorts Studio engine maintainable while it evolves toward the Content OS. It is a gradual modular-monolith structure, not a rewrite or permission to expand P0 scope.

- Preserve the existing app/ specialist engine and its working feature boundaries.
- Keep P0-A a narrow vertical slice. Dashboard work in P0 is limited to contract-aligned surfaces and integration scaffolding; a full Control Center is separate scope.
- Backend and frontend may progress feature-by-feature (Option A) only against shared, versioned contracts. Neither side invents the other's private data model.
- Adopt registry/evidence/planner/scoped-adapter patterns only where an accepted contract and concrete use case require them. Do not add competing orchestration engines.
- Local-first/free-first; initial target spend ₹0. No paid provider activation or dependency install is implied.
- Human approval remains a distinct gate. Automatic public publishing remains disabled absent separate explicit authorization.
- The canonical P0 workspace remains D:\MsP\NEXTDECODE_WORKSPACE; docs/nextdecode-workspace/ is a dated mirror, not a substitute source of truth.

## 2. Current canonical repository map

| Location | Owns | Placement rule |
|---|---|---|
| app/research/ | Discovery, sources, evidence, claims, lineage, topic selection | Research acquisition and verification stay here. |
| app/script/ | Short/long-form writing and editorial pipeline | No provider SDK or publishing side effects in editorial logic. |
| app/voice/ | Voice preparation and TTS providers | Speech-specific normalization and provider adapters. |
| app/visuals/ | Shot planning, asset selection, storyboard, rights metadata, visual review | Visual provenance/rights evidence must not be bypassed. |
| app/render/ | Assembly, FFmpeg, subtitles, audio/render QA | Rendering does not own review or publishing authorization. |
| app/review/ | Review artifacts and human approval CLIs | Human decision recording; not publishing authorization. |
| app/publish/ | Publishing orchestration, scheduler window, platform adapters | Every protected action uses the shared authorization boundary. |
| app/providers/ | LLM/provider client, health and OmniRoute adapters | Centralize provider configuration and fallback behavior. |
| app/notifications/ | Outbound notification delivery | Notifications cannot approve, mutate review state or grant permissions. |
| app/operations/ | Analytics, preflight, feedback, monetization, archive/workspace utilities | Operational support, not core domain policy. |
| app/tracking/ | Run identity, manifests, artifacts and promotion journal | One canonical run/artifact ledger. |
| api/ | Existing FastAPI generation transport | Legacy API boundary today; do not treat it as the full Content OS control plane. |
| pipelines/ | Specialist pipeline entrypoints | Compose existing app capabilities; do not duplicate domain logic. |
| 	ests/ | Current regression/acceptance suite and fixtures | Flat legacy tests may be reorganized gradually; no bulk test move. |
| 	ools/dev/ | Manual developer utilities | Never execute implicitly as production pipeline behavior. |
| 	ools/maintenance/ | Future controlled maintenance commands | Explicit operator action, dry-run where possible, auditable side effects. |
| docs/ | Architecture, decisions, runbooks, workspace mirror and historical source archive | Distinguish accepted decisions, proposals and historical evidence. |
| reports/ | Historical agent/audit/verification reports | Reports are evidence only when revalidated against current revision/environment. |
| data/ | Local runtime state and review/job metadata | Not source; preserve schemas and live paths. |
| outputs/ | Generated media, benchmarks, run artifacts and logs | Not source; cleanup requires retention/ownership review. |

## 3. Target locations to introduce only when needed

Do not create empty placeholders. Introduce a target directory with the first approved implementation that needs it.



web/, contracts/, infra/ and integrations/ are target homes, not a mandate to scaffold a full dashboard or service mesh. The application-owned autonomy package is the current task execution boundary.

## 4. File placement rules

| New item | Canonical home | Must not do |
|---|---|---|
| New research/evidence capability | app/research/ | Duplicate provider, approval or run-state authority. |
| Editorial/script feature | app/script/ | Invoke platform uploads or bypass evidence requirements. |
| Voice/TTS feature | app/voice/ | Couple editorial rules to a specific vendor SDK. |
| Visual planning/asset feature | app/visuals/ | Treat unverified rights as cleared. |
| Rendering/encoding feature | app/render/ | Approve or publish artifacts. |
| Human review/decision flow | app/review/ | Treat notification receipt or AI confidence as approval. |
| Platform upload/publish | app/publish/ | Bypass publish_authorization or artifact approval binding. |
| Provider SDK client | app/providers/ | Scatter keys, fallback policy or provider selection across domains. |
| Outbound alert/reminder | app/notifications/ | Accept chat replies as owner approval. |
| HTTP route/schema transport | api/ and approved contracts/ | Put business rules in handlers or let UI access local files directly. |
| Future dashboard page/component | web/ | Read worker files or mutate approval/job records outside authenticated APIs. |
| Vendor/external automation adapter | integrations/<vendor>/ | Own core lifecycle, approval, rights or authorization state. |
| Docker/systemd/deployment files | infra/ | Contain committed secrets or change live services implicitly. |
| One-off developer utility | tools/dev/ | Run implicitly in production. |
| Controlled operator/repair utility | tools/maintenance/ | Hide destructive side effects; require explicit target and backup plan. |
| Dormant/obsolete source awaiting disposition | _holding/ | Require manifest, SHA-256, caller scan and restore path; never store secrets/runtime data or import from here. |
| Reusable operational command | scripts/ | Become a dumping ground for Python domain modules. |
| Test | Existing tests/; gradually tests/<layer>/<domain>/ | Use real credentials, external upload or shared production data by default. |
| Runtime state | Existing data/ | Move into app/, contracts/ or source control. |
| Rendered/generated artifact | Existing outputs/ | Mix generated files with source modules. |
| Historical audit/report | reports/<provenance>/ | Present as current acceptance without revalidation. |
| Architecture decision/runbook | docs/decisions/, docs/architecture/, docs/runbooks/ | Promote a proposal or mirror into an owner decision. |

## 5. Dependency direction



- Domain packages do not import FastAPI, frontend code or vendor SDKs directly.
- API handlers validate transport and delegate; they do not become workflow engines.
- Frontend and backend share versioned contracts, not private implementation imports.
- External adapters depend inward on defined interfaces; core domain code does not depend outward on adapters.
- No circular imports, duplicate ledgers or second approval/authorization source of truth.
- The existing app/publish/scheduler.py is only the publishing-window checker; app/tracking/ is not a durable queue. Do not mislabel either as a general workflow engine.

## 6. Root policy and compatibility

Root may contain README/project metadata, dependency and environment examples, required tool configs, service entrypoints, stable CLI commands and temporary compatibility facades. New business logic, prototypes, vendor-specific configs and generated artifacts do not belong there.

Every root Python file must be classified as one of:
- canonical root entrypoint/shared primitive with a named owner and caller;
- temporary compatibility facade with canonical target and retirement gate;
- hybrid adapter with explicitly documented legacy behavior.

A facade is not dead merely because it is short. Retire individually only after internal imports, tests, shell scripts, systemd, Docker/Compose, scheduled tasks, docs, external/manual and agent callers migrate; identity/CLI compatibility is replaced; focused and full tests pass; rollback is available.

## 7. Tests, migration and cleanup gates

- Unit tests: deterministic domain logic.
- Integration tests: package/storage/adapter interactions with controlled fakes.
- Contract tests: versioned API/event schemas and compatibility.
- End-to-end tests: bounded user workflows against isolated state, with publishing disabled.
- Keep legacy flat test paths stable during unrelated migrations; reorganize tests only as a dedicated mechanical package.
- Before a move/delete: inventory imports, dynamic imports, shell calls, Docker/Compose, systemd/timers/cron, workflow nodes, docs, tests, agent tasks and external/manual commands. Record the old/new path map and hashes for stateful or historical files.
- Use a reversible move, compatibility bridge and focused regression test; remove a bridge only after caller evidence is clear.
- For data/generated files, establish owner, reproducibility, retention and backup before deletion. Age or file size alone is not justification.

## 8. Autonomous execution boundary

`app/autonomy/` owns task planning, capability allow-listing, durable task/DAG state, worker leases, retry/recovery and task events. API routes validate/authenticate transport and delegate to this package. Specialist handlers are replaceable adapters; they do not own the durable task lifecycle or publishing authorization. The tool catalogue ranks alternatives but never installs or invokes them automatically.

The former external workflow bridge, deployment assets, dedicated environment file, workflow export, systemd services and user data directory were retired on 2026-11-07. Do not recreate this dependency. Any future scheduler or specialist integration must use the versioned task/plan contracts and pass restart, idempotency, recovery, audit and resource acceptance tests.

## 9. Governance

This is a repository-organization standard, not a product-scope, physical-schema or P0/P1 contract approval. Preserve accepted owner decisions, P0-A scope, versioned contract dependencies, human approval, rights/quality checks and protected publishing authorization. No commit/push/merge/deploy/service restart/public publishing is authorized by this document.

## 10. Approved scope and future workflow boundary

The current production engine remains under app/; do not establish competing workflow engines or move runtime data during source organization. The application-owned autonomy package now provides the durable local queue/worker baseline; any future distributed replacement requires measured scale evidence and an explicit architecture decision.
