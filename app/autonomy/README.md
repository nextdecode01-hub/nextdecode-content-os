# NEXTDECODE Autonomous Task Execution Core

This package is the local autonomy execution prototype/runtime for NEXTDECODE. It is application-owned and does not depend on an external workflow server. It does not replace the accepted P0 cloud control-plane ownership or the canonical WP2–WP6 workflow, worker, artifact and authorization contracts. Local PostgreSQL stores this runtime's queue only; SQLite remains the development/test adapter and preserved legacy source.

## A2 — Planner and validated DAGs

- Namespaced internal contracts: nextdecode.autonomy.plan.v1 and nextdecode.autonomy.task.v1; these are not P0 WorkflowTask/Job/JobAttempt contracts.
- Deterministic intent routing for research and editorial script drafts.
- A local Ollama JSON-schema planner is available for explicitly complex workflow requests; deterministic routing is the no-cost offline fallback.
- Model output is only a proposal. The plan contract validates every node against the enabled registry, capability payload validator, permission policy, dependency references and DAG acyclicity.
- Bounds: 1–32 nodes, at most 8 dependencies per node, 64 KiB per payload, 256 KiB total plan, 1–10 attempts, priority -1000..1000.
- Plan idempotency hashes the logical request, not generated UUIDs. Reusing a key with different content is rejected.
- A research step can feed its verified artifact to downstream script tasks. The worker loads successful prerequisite outputs into a transient execution context; that context is not persisted as user payload.

## A3 — Registered specialists

| Capability | Status | Scope |
|---|---|---|
| research.topic.collect | Active | Public, source-backed research; compact local evidence brief |
| content.short.script.draft | Active | Research-backed Short script draft; human review pending |
| content.longform.script.draft | Active | Research-backed long-form script draft; human review pending |
| documents.text.analyze | Active | Bounded inline text analysis; no arbitrary filesystem reads |
| documents.office.extract | Active, direct-task only | Bounded inline DOCX/XLSX extraction using stdlib ZIP/XML; no filesystem/network, macros or formula execution; no canonical WP4 registration |
| data.dataset.profile | Active | Bounded inline dataset profiling; deterministic statistics |
| data.csv.profile | Active, direct-task only | Bounded inline CSV profiling with stdlib parser; no file or network access |
| content.short.generate | Restricted | Local procedural dry-run only; not planner-approved |
| content.longform.generate | Disabled | Existing entrypoint has no verified review-only execution path |
| publishing.check | Blocked-only | Readiness response; no upload or posting |

Browser automation (Playwright/Selenium), coding agents (OpenCode/Aider), PDF extraction (pypdf), and analytics alternatives (DuckDB/pandas) remain ranked candidates; none is installed or invoked. DOCX/XLSX currently use the bounded Python-standard-library extractor. The Office extractor is direct-task only and is not the canonical WP4 artifact-registration system.

## A4 — Sandbox and evaluator

- Process specialists execute only fixed, allow-listed Python modules through Bubblewrap (bwrap); no arbitrary shell or user-supplied command execution.
- Every specialist runs in a private network namespace (`--unshare-net`). Network-enabled research uses a per-execution Unix-socket egress broker; there is no direct IP route from the specialist to the host or internet.
- The public-web broker permits bounded HTTP(S) GET/HEAD only, rejects non-global/private destinations, revalidates redirects, strips authorization/cookie headers, enforces standard ports, request/response bounds and short timeouts. It never forwards credentials or arbitrary POST bodies. Each hostname is resolved once per request/redirect; the selected globally routable address is pinned to the TCP connection while the original hostname remains for Host, TLS SNI and certificate checks. A regression test simulates DNS changing from public to loopback after validation and confirms the connection still uses the pinned public address. Independent security review and production acceptance remain outstanding.
- Local-model inference is a separate capability gate. Only script-draft specialists receive the broker's fixed `127.0.0.1:11434/api/chat` route, only for `gemma3:4b`, bounded prompt messages and non-streaming requests (maximum 180-second request timeout and 512 generated-token ceiling). Script drafting selects two upstream source records while preserving the full research brief artifact, permits one bounded repair only for under-length drafts; over-length drafts are trimmed at whole-sentence boundaries without another model call. This does not expose the host's general loopback network.
- Project source is read-only inside the sandbox. Existing data/ and outputs/ trees are hidden behind temporary filesystems; only outputs/autonomy/artifacts is bind-mounted for persistent writes. Existing review queues, upload ledgers, token-usage files and prior media outputs are not exposed to specialists.
- .env, YouTube tokens, client-secret and credentials files are masked. The environment is cleared and rebuilt with local-model-only, dry-run and no-publish settings.
- Network access is capability-scoped: research/script specialists may access public web; offline/in-process specialists do not receive network access.
- No host-execution fallback exists if bwrap is missing or fails.
- Every task execution receives a UUID run ID, a process-scoped local runtime worker ID, capability version, timestamps and evidence hashes. This is not the canonical P0 WP3 WorkerRegistry identity or trust record.
- The evaluator rejects non-zero process exits, artifacts outside the autonomy artifact store, hash mismatches, invalid artifact schema, missing human-review state or any artifact that enables external actions.
- Local autonomy artifacts are marked human_review_status=pending and external_actions_allowed=false. They are not canonical WP4 Artifact/ArtifactVersion records, and this runtime does not implement the WP5 ApprovalRequest/ApprovalDecision workflow.

## A5 — PostgreSQL integration and operations

### Local runtime backend (not the P0 shared control plane)

PostgresTaskStore is selected whenever DATABASE_URL is set. An explicit CLI --db path selects SQLite for local testing. The local WSL runtime uses PostgreSQL 18 in rootless Podman, bound to 127.0.0.1:54329; the database password and DSN live outside the repository under ~/.config/nextdecode/ with mode 0600.

PostgreSQL provides transactional persistence for this local runtime's plans/tasks, row-level locks, FOR UPDATE SKIP LOCKED concurrent claims, leases, retries, DAG dependencies, append-only events and process heartbeats. It is not the accepted P0 cloud control plane or canonical shared workflow database. SQLite is no longer the live local worker's queue.

### Non-destructive migration

The migration command is:

    systemctl --user stop nextdecode-autonomy-api.service nextdecode-autonomy-worker.service
    set -a
    . ~/.config/nextdecode/autonomy-db.env
    set +a
    python -m app.autonomy.migrate_sqlite_to_postgres

The one-time migration refuses to run while the API or worker is active or when the target schema is non-empty. It creates a consistent SQLite backup, checks its integrity, imports rows transactionally, compares exact table counts and preserves the original SQLite database. Legacy worker heartbeats are marked stopped during import because the old processes cannot be assumed to survive a backend cutover.

### Operations and backups

- User services: nextdecode-postgres.service, nextdecode-autonomy-worker.service and nextdecode-autonomy-api.service.
- The API binds only to 127.0.0.1:8765; its bearer key is stored outside the repository in ~/.config/nextdecode/api.env.
- Daily backup timer: nextdecode-postgres-backup.timer.
- Backups use PostgreSQL custom format, mode 0600, directory mode 0700, 14-day retention.
- The backup job verifies the archive with pg_restore --list.
- A restore drill was run against a disposable database; the live database was not overwritten.
- Authenticated API inspection: GET /autonomy/health and GET /autonomy/dead-letters.

## CLI

    python -m app.autonomy.cli capabilities
    python -m app.autonomy.cli tool-catalog --capability task-storage
    python -m app.autonomy.cli plan "Research and create a Short script about AI agents"
    python -m app.autonomy.cli enqueue data.dataset.profile --payload '{"rows":[{"views":10},{"views":20}]}'
    python -m app.autonomy.cli enqueue data.csv.profile --payload '{"csv_text":"views,likes\\n10,2\\n20,4\\n"}'
    python -m app.autonomy.cli worker
    python -m app.autonomy.cli list
    python -m app.autonomy.cli show TASK_ID
    python -m app.autonomy.cli show-plan PLAN_ID
    python -m app.autonomy.cli health
    python -m app.autonomy.cli dead-letters --limit 100

Health is read-only. A heartbeat proves process liveness, not task correctness. Dead-letter inspection does not retry or mutate tasks.

## Alternative ranking

- Primary database for this local autonomy runtime: local self-hosted PostgreSQL; zero API/license spend, local operational/backup responsibility. It is not the accepted P0 cloud shared-state database.
- Local fallback: SQLite for tests and single-process development only; PostgreSQL is authoritative only within this local runtime.
- Managed PostgreSQL alternatives: Supabase Postgres and Neon; approval-required because of account, network, provider-limit and data-residency implications.
- Distributed SQL alternative: CockroachDB; candidate only, not a drop-in semantic replacement and excessive complexity for this single-host workload.
- Workflow execution: the application-owned local autonomy core is primary for this runtime. Temporal is the strongest durable-workflow alternative; Celery and Dramatiq are task-queue alternatives that require a separate broker. APScheduler is scheduling-only, not a durable queue or DAG engine. None is enabled alongside the current worker.
- Browser: Playwright primary candidate, Selenium alternative.
- Coding: OpenCode primary candidate, Aider alternative.
- Documents: Python standard-library DOCX/XLSX extractor active for bounded inline bytes; pypdf remains a PDF-only candidate. python-docx/openpyxl are not installed.
- Data: Python standard library active for bounded profiling; DuckDB and pandas candidates.

The catalog records license/cost labels, rank, fallback relationship and qualification status. It does not install tools or grant external access.

## Safety and current limits

- Public publishing, uploads, provider spend and deployment remain disabled unless separately authorized.
- Every script artifact remains pending human review; this local runtime does not implement the canonical P0 ApprovalRequest/ApprovalDecision workflow, and task success is not editorial approval.
- Full Short rendering remains outside planner-approved autonomous execution while the storyboard/review gate is unresolved.
- Full long-form video generation remains disabled until a verified review-only path exists.
- The prior intermittent SQLite database-open failure's exact filesystem/WSL root cause remains unknown. The live worker no longer depends on SQLite; the legacy database and verified backup are preserved for forensics/rollback.
- 2026-11-10 runtime observation: after WSL startup, the PostgreSQL Podman unit entered a repeated restart loop with `newuidmap: write to uid_map failed: Operation not permitted` (restart counter had reached 442). Stopping the failed units, resetting their failed state, and starting PostgreSQL again brought the existing database online; API and worker then started successfully, and all three reported zero restarts after recovery. Existing PostgreSQL data volume was preserved. The transient root cause is not yet proven; monitor the next WSL restart before calling startup reliability closed.
- A full live end-to-end video render and production release acceptance are still separate gates. No release-readiness claim is made by these implementation tests.


### Local worker execution policy

The local worker now evaluates registry-owned capability metadata through
`execution_policy.py` before invoking a handler. Scope names and sandbox
profiles are allowlisted; network-enabled capabilities must declare the
restricted network profile, and offline capabilities cannot claim public-web
read access. Task payloads cannot supply or override permission scopes, network
access, or sandbox profile. Rejected capabilities are marked blocked without
calling their handler, and the policy version/decision is included in execution
evidence.

This is a local fail-closed guardrail only. It does not establish canonical WP3
worker enrollment, trust, eligibility, credentials, isolation guarantees, or
WP5 protected-action authorization. A declared sandbox profile is metadata;
actual process isolation must be enforced by the runtime launcher and verified
separately. Publishing remains readiness-only and external publishing remains
disabled.


### Manual CLI environment

The CLI loads ~/.config/nextdecode/autonomy-db.env when invoked manually, without overriding environment variables explicitly supplied by the caller. Use the project virtual environment (./venv/bin/python) so the PostgreSQL driver installed for the services is available. An explicit --db path still selects SQLite for local development.

### Worker failure diagnostics

Unhandled task exceptions preserve a bounded exception type and sanitized message in task result evidence. Credentials in common key/value and bearer-token forms, plus URL query strings, are redacted. Full tracebacks and environment values are not stored. This is diagnostic context, not a retryability policy change.

### PostgreSQL restart backoff

The local PostgreSQL user service uses a 30-second restart delay and a bounded start rate (10 attempts per 5 minutes) to avoid rapid rootless-Podman restart loops when WSL2 denies user-namespace mapping. This limits restart churn; it does not repair WSL2 namespace configuration by itself.


## PostgreSQL backup integrity

- `backup_postgres.sh` writes a private custom-format dump to a temporary file, checks that PostgreSQL can read its archive catalog, computes SHA-256, then publishes the dump and its `.sha256` sidecar. A sidecar is the completion marker for a new backup.
- The existing 14-day retention rule is preserved; when an expired dump is removed, its matching checksum sidecar is removed too.
- Verify a new backup without restoring it:

  ```bash
  app/autonomy/verify_postgres_backup.sh data/autonomy/postgres-backups/autonomy-YYYYMMDDTHHMMSSZ.dump
  ```

- Verification checks the SHA-256 sidecar and that `pg_restore --list` can read the custom archive catalog. It does **not** prove that a full restore succeeds or establish point-in-time recovery. Legacy dumps without sidecars are intentionally rejected by this verifier rather than being reported as checksum-verified.
- Never restore over the live database as part of routine verification. A restore drill must use a separate isolated PostgreSQL instance and be separately authorized.


## Isolated PostgreSQL restore drill

Run a full restore drill against a selected backup:

```bash
app/autonomy/restore_drill_postgres.sh data/autonomy/postgres-backups/autonomy-YYYYMMDDTHHMMSSZ.dump
```

The script verifies the SHA-256 sidecar, starts a disposable PostgreSQL 18 container with `--network none`, no published ports, and a temporary in-memory filesystem, restores the custom archive, then compares exact row counts for `task_plans`, `tasks`, `task_dependencies`, `task_events`, `plan_idempotency`, and `worker_heartbeats` against the live database. It removes only the uniquely named temporary container on exit. It does not mount or modify the live PostgreSQL volume. A successful row-count comparison is a restore smoke test, not a complete application-level recovery or point-in-time recovery certification.

## Rootless Podman systemd compatibility

The PostgreSQL and PostgreSQL-backup user units must not set `NoNewPrivileges=true`: rootless Podman needs its setuid `newuidmap`/`newgidmap` helpers to establish the user namespace. Blocking those helpers causes container startup/exec to fail with `newuidmap: write to uid_map failed: Operation not permitted`. Keep the service `UMask=0077` and private backup permissions; do not re-add `NoNewPrivileges=true` to these Podman units without replacing the namespace setup with a verified compatible design.


## Stale worker lifecycle reconciliation

Inspect stale worker records without changing the database:

```bash
./venv/bin/python -m app.autonomy.cli reconcile-workers --stale-after-seconds 45
```

Apply conservative reconciliation:

```bash
./venv/bin/python -m app.autonomy.cli reconcile-workers --stale-after-seconds 45 --apply
```

Only stale workers recorded on the current hostname are eligible. A worker is marked `stopped` only when the operating system conclusively reports its PID does not exist. A live PID, permission ambiguity, OS error, or remote hostname is left unchanged. The update is conditional on the same worker ID, hostname, PID and observed heartbeat timestamp, preventing an old inspection from overwriting a fresh heartbeat. The original PID and last heartbeat timestamp are retained; no worker rows or history are deleted. This is a local runtime liveness check, not canonical WP3 worker trust or enrollment.


## Automatic worker supervision and lease recovery

The worker is supervised by `nextdecode-autonomy-worker.service`. systemd restarts it after an unexpected failure, with a 15-second delay and a bounded start rate (maximum 6 starts in 5 minutes). A clean intentional stop is not treated as a crash.

Expired task leases are recovered by `nextdecode-autonomy-recovery.timer`, which starts `nextdecode-autonomy-recovery.service` every 30 seconds after its initial boot delay. The service waits for PostgreSQL and runs:

```bash
./venv/bin/python -m app.autonomy.cli recover-expired --limit 100
```

A crashed worker's task is not requeued immediately: its 180-second lease must expire first. The recovery service then requeues the task if attempts remain, or marks it failed when its retry budget is exhausted. Attempt fencing prevents an old worker from completing a newer attempt. This is local queue recovery and systemd process supervision, not canonical WP2 job orchestration or a distributed worker control plane.

Inspect the timer and recent recovery runs:

```bash
systemctl --user list-timers nextdecode-autonomy-recovery.timer
systemctl --user status nextdecode-autonomy-recovery.service
journalctl --user -u nextdecode-autonomy-recovery.service -n 50 --no-pager
```


## Execution timeouts and graceful shutdown

Sandboxed specialist execution uses explicit per-handler wall-clock limits: research collection is capped at 600 seconds and script drafting at 1,800 seconds. The sandbox terminates a timed-out subprocess and the task is recorded as `sandbox_timeout` with timeout evidence. Timeout failures are terminal by default (`retryable=false`) because a timed-out process may have left partial artifacts; automatic retry is not assumed safe.

When the worker receives SIGINT or SIGTERM, the CLI sets a shutdown event. The worker finishes its current attempt and exits the polling loop without claiming another task. The service manager's stop timeout remains a hard upper bound; if the worker is forcibly killed, lease expiry and the recovery timer handle the abandoned attempt. This is graceful drain, not mid-handler cooperative cancellation. In-process handlers cannot currently be forcibly interrupted safely.


## Task execution heartbeat and stuck-task inspection

While a handler is running, the worker's lease-renewal loop records a durable `execution_heartbeat` event after each successful fenced lease renewal. The event includes the worker ID, attempt generation and coarse phase (`handler_running`); it deliberately does not store payloads or handler output.

Inspect running tasks whose last execution heartbeat is older than the chosen threshold:

```bash
./venv/bin/python -m app.autonomy.cli stuck-tasks --stale-after-seconds 120 --limit 100
```

This command is read-only. A stale heartbeat is an alert signal, not proof that a handler is dead; it does not cancel, retry, requeue or alter a lease. Lease expiry and the existing recovery timer remain the only automatic recovery path. A durable cancellation-request contract and safe cooperative handler cancellation are intentionally deferred until the relevant workflow/control-plane contracts are approved.


## Coding-agent workspaces and result collection

Windows desktop agent applications and WSL command-line runtimes are inventoried separately with:

```bash
./venv/bin/python -m app.autonomy.cli agent-workspace readiness
./venv/bin/python -m app.autonomy.cli agents
```

The readiness report detects supported Windows desktop applications through mounted Windows user profiles under `/mnt/c/Users`. A detected desktop application is not treated as a WSL CLI and is not launched automatically. Desktop-to-workspace control is a separate integration boundary and remains disabled until isolation, handoff, and result-collection behavior are implemented and reviewed. Absence of a WSL CLI does not mean the corresponding Windows desktop app is absent.

Prepare a sanitized project snapshot without changing the source repository:

```bash
./venv/bin/python -m app.autonomy.cli agent-workspace prepare
./venv/bin/python -m app.autonomy.cli agent-workspace list
```

Each snapshot is stored under `outputs/autonomy/agent-workspaces/<workspace_id>/`. Its manifest records the copied file paths, sizes and SHA-256 hashes. The snapshot excludes Git metadata, virtual environments, local databases, generated outputs, common credential files and symlinks. Snapshot creation is bounded by file-count and byte limits.

Inspect changes made inside a snapshot:

```bash
./venv/bin/python -m app.autonomy.cli agent-workspace collect <workspace_id>
```

The collector reports added, modified and deleted files with hashes. It does not import changes into the main repository. Its report explicitly records `automatic_import_allowed=false`.

A future invocation plan can be requested with:

```bash
./venv/bin/python -m app.autonomy.cli agent-workspace plan <workspace_id> --agent opencode --task "Describe the bounded task"
```

This currently fails closed because `AgentExecutionPolicy.invocation_enabled` defaults to false. No coding-agent process launcher is active. Local discovery does not install or invoke OpenCode, Aider, Qoder or Kilo; availability, provider authentication and costs must be assessed separately. Network access, credential forwarding and direct writes to the main repository remain disabled. This workspace mechanism is a local preparation/result-inspection facility, not canonical WP2/WP3 worker orchestration or a WP5 authorization service.


## Isolated workspace change review

Use `nextdecode-task agent-workspace review <workspace_id>` after collecting a
workspace. The review report annotates each added, modified, or deleted path
with a conservative risk classification. Sensitive names and protected
publishing/security areas are blocked; binary, oversized, and deletion changes
are restricted for explicit review. Small added text files may include a
bounded diff. Modified-file diffs are intentionally omitted because the
workspace manifest stores hashes, not a second copy of baseline file contents.

The review is advisory, not an authorization service. Every change remains
pending human review. No file is copied into the main repository, no approval
is inferred, and automatic import remains disabled. This is a local safety
boundary only; it does not claim canonical WP5 approval or WP3 worker trust.


## Explicit approval and isolated staging

The local agent-change flow has three separate steps:

1. `agent-workspace review WORKSPACE_ID` creates the current risk report.
2. `agent-workspace approve WORKSPACE_ID --path PATH --sha256 HASH --reason "..." `
   records explicit per-file approval for an eligible **added text file only**.
3. `agent-workspace stage-approved WORKSPACE_ID` rechecks the review report,
   exact file hash, path and approval before copying approved additions into a
   private proposal directory under `outputs/autonomy/agent-workspaces/staging/`.

The approval command requires the operator to supply the exact current SHA-256
and a reason. Modified files and deletions cannot pass this staging gate because
the current workspace snapshot does not retain immutable baseline file bytes
for a trustworthy comparison. Protected, sensitive, binary and oversized
changes remain blocked or restricted.

Staging is not repository integration. It does not overwrite project files,
run code, install dependencies, publish, deploy, or grant an agent execution
permission. The proposal manifest explicitly records that repository import
was not performed. A separate future integration step must independently
inspect and validate the staged proposal before any repository write.


### Coding-agent execution readiness

Inspect prerequisites without launching or installing an agent:

\`\`\`bash
./venv/bin/python -m app.autonomy.cli agent-workspace readiness
\`\`\`

The report checks whether a supported agent CLI is on PATH, Bubblewrap is
available, the project virtualenv is executable, and an isolated workspace
root exists. It does not execute candidate binaries, install tools, grant
network or credentials, or enable invocation. A green prerequisite report
would still not authorize agent execution; invocation remains disabled until
the execution boundary and human approval requirements are separately accepted.
