# Dependency Map — NEXTDECODE Autonomous Runtime

Status: current application-owned execution map, 2026-11-07.

## Core task lifecycle

```text
Task request -> TaskPlanner -> nextdecode.plan.v1 DAG -> TaskStore (SQLite WAL) -> CapabilityRegistry -> TaskWorker -> specialist handler -> TaskResult + evidence
```

| Responsibility | Module | Contract / boundary |
|---|---|---|
| Task schema | `app.autonomy.models` | Versioned request/result validation |
| Planning | `app.autonomy.planner` | Deterministic bounded intent routing; capability-only plans |
| Tool qualification | `app.autonomy.tool_catalog` | Ranked primary/fallback candidates; no implicit install or execution |
| Capability discovery | `app.autonomy.registry` | Explicit handlers only; zero-default external cost |
| Durable queue + DAG | `app.autonomy.store` | SQLite WAL, atomic plan persistence, dependency graph, idempotency, priority, leases, backoff and append-only events |
| Worker | `app.autonomy.worker` | Claims jobs and persists terminal/retry state |
| Task adapters | `app.autonomy.tasks` | Fixed local entrypoints; no arbitrary command execution |
| CLI | `app.autonomy.cli` | Plan, enqueue, inspect, run-once, worker and capability listing |
| Run identity/artifacts | `app.tracking.run_tracker` | Existing run manifests and artifact hashes |
| Content generation | `pipelines.short`, `pipelines.longform` | Strong quality pipeline; review-only execution |
| Publishing policy | `app.publish.authorization`, `app.publish.orchestration` | Separate guarded boundary; no autonomous upload capability |

## Initial capabilities

- `content.short.generate`: Strong Short generation; defaults to dry-run/review-only.
- `content.longform.generate`: long-form generation; defaults to dry-run/review-only.
- `publishing.check`: blocked result; no upload or external publication.

## Reliability semantics

- Idempotency keys prevent duplicate enqueue requests.
- Plans are inserted atomically; cyclic/unknown dependencies are rejected.
- DAG tasks become eligible only after every prerequisite succeeds; failed prerequisites block descendants.
- Workers claim with bounded leases; expired leases are recovered while attempts remain.
- Retryable failures use capped exponential backoff and requeue only up to the configured maximum attempts.
- A stale worker cannot overwrite a task after losing its lease.
- Every lifecycle transition is appended to `task_events`.
- Unknown capabilities are blocked; task data is never interpreted as a shell command.

## Local operation

```bash
python -m app.autonomy.cli capabilities
python -m app.autonomy.cli plan "Create a YouTube Short about AI agents"
python -m app.autonomy.cli enqueue content.short.generate --payload '{"topic":"Example","dry_run":true}'
python -m app.autonomy.cli worker
python -m app.autonomy.cli list
```

Default database: `data/autonomy/tasks.sqlite3`; override with `NEXTDECODE_TASK_DB`.

## Replacement strategy

The core uses Python standard library + SQLite rather than another workflow server. Specialist tools plug in behind stable capability contracts. If the queue later becomes insufficient, replace only the TaskStore adapter after restart recovery, idempotency, retry, scheduling, audit and resource acceptance tests pass.
