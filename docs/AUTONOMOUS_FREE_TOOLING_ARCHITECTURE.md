# NEXTDECODE Autonomous Task Execution Core

Status: Local autonomy runtime A1–A5 subsystem implementation; not P0 WP2–WP6 acceptance or production release.
Last reviewed: 2026-11-08

## 1. Product requirement and invariants

NEXTDECODE's local autonomy runtime accepts bounded requests, proposes dependency-aware plans, executes local task graphs, records evidence and returns inspectable outcomes. The task lifecycle is application-owned; external workflow servers are not part of this runtime. This local package is not the canonical P0 WorkflowTask/Job/JobAttempt implementation and does not change accepted P0 ownership boundaries.

Governance invariants:
- Zero external spend by default; hosted or metered providers are never invoked merely because a task was enqueued.
- Human approval is mandatory before public publishing or any irreversible external action.
- External publishing, uploads, payments, destructive changes and credential mutation are not enabled autonomous capabilities.
- Unknown intents/capabilities are rejected or blocked; task text is never interpreted as a shell command.
- Preserve source evidence, run IDs, artifact hashes and append-only task event history.
- Tools are replaceable behind versioned capability contracts; qualify alternatives before migration.
- Preserve existing repository work and accepted P0 boundaries. This execution core does not expand the P0 Control Center or change canonical content-domain ownership.

## 2. Storage decision and alternatives

### Local runtime database (not the P0 shared cloud control plane)

PostgreSQL 18 is the authoritative database only for this local WSL autonomy runtime. The service is a local rootless Podman container bound only to 127.0.0.1:54329. The database volume is nextdecode-postgres-data. Credentials and the connection string live outside the repository under ~/.config/nextdecode/ with restrictive file permissions.

PostgresTaskStore implements the local runtime's task-store contract using transactions, row-level locks and FOR UPDATE SKIP LOCKED for concurrent local workers. It persists internal autonomy plans, tasks, dependencies, idempotency keys, events and process heartbeats. DATABASE_URL takes precedence in the local store factory. An explicit CLI --db path selects SQLite for tests and local development.

This local database does not replace the accepted P0 cloud control plane or canonical shared workflow state. SQLite remains the local test/development adapter and a preserved legacy migration source. It is no longer the live local worker's queue. The exact previous WSL/SQLite open-failure root cause remains unknown; the active local worker dependency was moved to PostgreSQL without claiming the filesystem issue itself was diagnosed.

### Ranked database options

| Rank | Candidate | Role | Decision |
|---:|---|---|---|
| 1 | Local PostgreSQL | Local WSL autonomy runtime queue only; not P0 shared state | Active local runtime |
| 2 | SQLite | Unit tests and single-process local development | Fallback only |
| 2 | Supabase Postgres | Managed PostgreSQL alternative | Approval-required |
| 3 | Neon Postgres | Managed/serverless PostgreSQL alternative | Approval-required |
| 4 | CockroachDB | Distributed SQL alternative with PostgreSQL wire compatibility | Candidate; not a drop-in semantic replacement |

Managed alternatives require separate approval for account/network use, data residency, provider terms and possible usage limits.

Workflow execution ranking: the application-owned local autonomy core is rank 1 for this runtime; Temporal is the strongest durable-workflow alternative (rank 2); Celery (rank 3) and Dramatiq (rank 4) are task-queue alternatives that require a separate broker. APScheduler is scheduling-only, not a durable queue or DAG engine. None is enabled alongside the current worker.

### Migration, backup and restore

The non-destructive one-time migration module:
- refuses to run while the local API or worker is active, or when the target schema is non-empty;
- creates a consistent SQLite backup using SQLite's backup API;
- runs source and backup integrity checks;
- imports rows transactionally into an empty PostgreSQL schema;
- verifies exact source/import/target table counts;
- preserves the original SQLite database and the migration backup;
- marks imported legacy worker heartbeats stopped because their original processes cannot be assumed to survive the backend cutover.

Daily PostgreSQL backups use custom format, mode 0600 and a mode-0700 backup directory. A 14-day retention policy is applied only inside the dedicated backup directory. The backup job validates the archive with pg_restore --list. A restore drill was completed against a disposable database and the live database was not overwritten.

## 3. Internal local task and plan lifecycle

The entities below are internal to this local autonomy runtime. They are not substitutes for the canonical P0 WorkflowTask, Job, JobAttempt or shared workflow entities.

    Request
      -> deterministic intent routing / bounded local-model DAG proposal
      -> versioned plan contract
      -> capability and payload validation
      -> atomic plan + task DAG persistence
      -> PostgreSQL task queue
      -> worker claim + lease
      -> allow-listed specialist
      -> evaluator + artifact provenance
      -> task event history + plan status

Task states: queued -> running -> succeeded | failed | blocked.
Retryable failures return to queued with bounded exponential backoff, capped at 300 seconds, until max attempts. Expired leases are recovered. A stale worker cannot overwrite a task after losing its lease. DAG nodes run only after all dependencies succeed. Failed or blocked prerequisites block descendants. Whole plans are inserted atomically.

Plan idempotency hashes the logical request, not generated UUIDs. Reusing an idempotency key with different content is rejected.

## 4. A2 — Planner and validated DAG contract

Package: app/autonomy/

- Internal task contract: nextdecode.autonomy.task.v1.
- Internal plan contract: nextdecode.autonomy.plan.v1.
- These namespaced contracts are local execution proposals, not canonical P0 contracts.
- Deterministic routing handles explicit research and editorial script requests.
- A local Ollama JSON-schema planner is available for explicitly complex workflow requests. It receives only planner-approved capability descriptions and cannot define tools, shell commands, URLs, credentials or external actions.
- The model proposes; the plan contract validates. Unknown capabilities, non-planner capabilities, unknown dependencies, duplicate step IDs, cycles, excessive payloads and invalid retry/priority values are rejected.
- Bounds: 1–32 nodes; at most 8 dependencies per node; 64 KiB per task payload; 256 KiB per plan; 1–10 attempts; priority -1000..1000.
- Deterministic offline fallback is used when the local planner is unavailable.
- Script plans include a research task. Downstream script tasks receive successful prerequisite artifact references through transient worker execution context; this context is not persisted as user payload.

## 5. A3 — Specialist registry

Enabled capabilities:
- research.topic.collect: public source-backed research and a compact local evidence brief.
- content.short.script.draft: research-backed Short script draft for human editorial review.
- content.longform.script.draft: research-backed long-form script draft for human editorial review.
- documents.text.analyze: bounded inline text analysis; no arbitrary local file reads.
- documents.office.extract: bounded inline DOCX/XLSX extraction using Python standard-library ZIP/XML parsing; direct-task only, no filesystem/network, macro execution, formula evaluation, external relationship following or canonical WP4 artifact registration. PDF/legacy Office formats are unsupported.
- data.dataset.profile: deterministic bounded inline dataset profiling.
- data.csv.profile: deterministic bounded inline CSV profiling using Python's standard-library parser; direct-task only until a canonical input-reference contract is approved.
- content.short.generate: restricted local procedural dry-run path; not planner-approved.
- publishing.check: blocked-only readiness response.

Disabled/restricted:
- content.longform.generate remains disabled until the existing pipeline has a verified review-only execution path.
- Public upload/posting is not a registered autonomous action.

Alternative qualification status:
- Browser automation: Playwright, with Selenium as an alternative.
- Coding: OpenCode, with Aider as an alternative.
- Document extraction: Python-standard-library DOCX/XLSX extraction is active for bounded inline bytes; pypdf remains a PDF-only candidate. python-docx/openpyxl are not installed.
- Data analytics: Python standard library active for bounded profiling; DuckDB and pandas remain candidates.
- Research hosted enhancement: Exa is approval-required and not default-on.
- Workflow engine: Temporal is a candidate, not a database replacement.

The tool catalog records rank, capability, deployment mode, license/cost labels, replacement relationships, limitations and qualification status. Catalog entries do not install tools or grant permissions.

## 6. A4 — Sandbox, permissions and evaluator

Process specialists execute fixed, allow-listed Python modules through Bubblewrap (bwrap). There is no arbitrary shell, arbitrary command, user-code or host-execution fallback.

Sandbox boundaries:
- project source is read-only;
- every process uses a private network namespace (`--unshare-net`); specialists have no direct IP route to the host or internet;
- public research GET/HEAD requests are brokered through a per-execution Unix-domain socket; the broker blocks loopback/private/link-local/reserved destinations, revalidates each redirect, strips authorization/cookie headers, rejects nonstandard ports and bounds timeouts and response sizes;
- each public hostname is resolved once per request/redirect; every returned address must be globally routable, and the selected validated IP is pinned at the TCP connection layer so the socket does not perform a second hostname lookup. The original hostname remains in the HTTP pool for Host, TLS SNI and certificate validation. Every redirect is independently resolved, validated and pinned. Unit tests simulate a DNS answer changing from public to loopback after validation and verify the socket still targets the pinned public IP. Independent security review and production acceptance remain outstanding. The broker forwards no credentials and supports only public GET/HEAD requests;
- public egress never forwards arbitrary POST bodies or credentials; no provider API key is passed into a specialist;
- local-model inference is separately gated by the `local_model:inference` capability scope and uses only a fixed local Ollama `/api/chat` endpoint, approved `gemma3:4b` model, bounded messages, non-streaming requests, a 180-second maximum request timeout and a 512-token output ceiling; script drafting passes two selected source records while retaining the full upstream research brief artifact, allows one bounded repair only for under-length drafts and trims over-length drafts at whole-sentence boundaries without another model call;
- existing data/ and outputs/ trees are hidden behind temporary filesystems;
- only outputs/autonomy/artifacts is bind-mounted for persistent writes;
- existing review queues, upload ledgers, token-usage files and prior media outputs are not exposed;
- .env, YouTube tokens, client-secret and credentials files are masked;
- environment is cleared and rebuilt with local-model-only, dry-run and no-publish settings;
- offline/in-process specialists receive no egress broker;
- the WSL resolver file is mounted explicitly without exposing the wider host runtime tree.

Every task execution receives a UUID run ID, a process-scoped local runtime worker ID, capability version, timestamps, exit status and evidence hashes. The runtime worker ID is not the canonical WP3 WorkerRegistry identity or trust record. The evaluator checks process exit, artifact path confinement, size, SHA-256, local artifact schema, pending-review marker and external-action policy. Local script artifacts remain human_review_status=pending and external_actions_allowed=false; they are not canonical WP4 Artifact/ArtifactVersion registrations. Artifact paths and hashes are checked before the task is marked succeeded.

In-process data/document specialists accept bounded structured input only; they do not read arbitrary filesystem paths.

## 7. A5 — Integration, operations and acceptance

Local services:
- nextdecode-postgres.service: local PostgreSQL container.
- nextdecode-autonomy-worker.service: worker using DATABASE_URL and waiting for database readiness.
- nextdecode-autonomy-api.service: bearer-authenticated API bound only to 127.0.0.1:8765.
- nextdecode-postgres-backup.timer: daily verified backup.

Authenticated API:
- GET /capabilities
- GET /tool-catalog
- POST /tasks, GET /tasks, GET /tasks/{task_id}
- POST /plans, GET /plans/{plan_id}
- GET /autonomy/health
- GET /autonomy/dead-letters

CLI inspection:
- capabilities, tool-catalog, plan, enqueue, worker, list, show, show-plan, health and dead-letters.

Acceptance evidence includes:
- PostgreSQL integration tests for idempotency, transactional DAG dependencies, dependency result context, concurrent SKIP LOCKED claims, dead-letter inspection and SQLite import.
- Bubblewrap smoke test of the allow-listed specialist CLI with all IP networking disabled.
- Egress broker unit/integration tests for public destination checks, private-address rejection, redirect policy, credential stripping, method restrictions, Unix-socket request forwarding, DNS answer validation, pinned TCP destination, preserved hostname/TLS identity and simulated public-to-loopback DNS rebinding (11 focused tests pass).
- Live broker smoke tests over both HTTP and HTTPS returned 200; the HTTPS request completed normal certificate validation while connecting through the pinned-IP adapter.
- Live public research smoke test inside the network-isolated sandbox through the per-run egress broker.
- Live PostgreSQL planner DAG: research (four-source brief) -> Short script (110 words); the script used the separately scoped local Ollama route, passed artifact evaluation, remained pending human review and kept external actions disabled.
- Live authenticated API-to-worker execution of data.csv.profile with a three-row/two-column numeric dataset.
- Live authenticated API-to-PostgreSQL-to-worker execution of documents.office.extract using inline DOCX bytes; task succeeded with extracted text (45 characters, 5 words). XLSX extraction is covered by local fixtures. The capability remains direct-task only and does not register a canonical WP4 Artifact/ArtifactVersion.
- Live PostgreSQL worker health: one active worker, zero expired running leases and two historical stale heartbeat records from older stopped worker processes; no active stale worker. The three systemd services reported zero restarts after recovery.
- PostgreSQL backup archive verification and restore drill into a disposable database.

These results verify the local autonomy subsystem only. They do not satisfy P0 WP2 durable workflow, WP3 canonical worker identity/trust, WP4 artifact registration/transfer, WP5 approval/authorization or WP6 vertical-slice acceptance. Those remain governed by their versioned P0 contracts and owner acceptance gates. A full live end-to-end video render and release acceptance remain separate gates. Script drafting permits one bounded model repair only for under-length output and uses deterministic whole-sentence trimming for over-length output. The live draft passed the local artifact evaluator, but remains pending human editorial review.

## 8. Security, release and human gates

- Task payloads reject credential-shaped keys recursively.
- Captured stdout/stderr are bounded and redacted before persistence.
- Capability payload validators reject unknown fields and enforce bounds.
- No public publishing, uploads, provider spend or deployment is authorized by this architecture.
- Every script artifact remains pending human review; this local runtime does not implement the canonical P0 approval workflow, and task success is not editorial approval.
- Full Short rendering remains outside planner-approved autonomous execution while the storyboard/review gate is unresolved.
- Full long-form video generation remains disabled until a verified review-only path exists.
- API bearer authentication is an application control, not a substitute for TLS, rate limiting, network exposure review or production security acceptance.
- The prior SQLite open-failure root cause remains an open forensic item, but the live queue no longer depends on that backend.
- Release readiness is not claimed by hermetic or subsystem integration tests alone.

## 9. Operational commands

    python -m app.autonomy.cli health
    python -m app.autonomy.cli dead-letters --limit 100
    systemctl --user status nextdecode-postgres.service
    systemctl --user status nextdecode-autonomy-worker.service
    systemctl --user list-timers --all

The migration command requires DATABASE_URL and preserves the source database:

    set -a
    . ~/.config/nextdecode/autonomy-db.env
    set +a
    python -m app.autonomy.migrate_sqlite_to_postgres

No public publishing, external provider spend, push or deployment is authorized by this document.
