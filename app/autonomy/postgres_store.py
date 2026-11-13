"""PostgreSQL-backed durable autonomy queue.

The implementation mirrors the TaskStore contract while using row-level locking
and SKIP LOCKED for concurrent local workers. This PostgreSQL database is
only the local autonomy runtime queue, not the canonical P0 shared control plane.
SQLite remains a local/test adapter only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .models import TaskRequest, TaskResult, utc_now
from .retry_policy import retry_not_before


SCHEMA = """
CREATE TABLE IF NOT EXISTS task_plans (
    plan_id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    plan_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    plan_id TEXT REFERENCES task_plans(plan_id),
    task_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL,
    idempotency_key TEXT UNIQUE,
    request_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    not_before TEXT,
    lease_owner TEXT,
    lease_until TEXT,
    result_json TEXT,
    error_code TEXT
);
CREATE INDEX IF NOT EXISTS idx_tasks_ready ON tasks(status, priority DESC, created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_plan ON tasks(plan_id);
CREATE TABLE IF NOT EXISTS task_events (
    event_id BIGSERIAL PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    at TEXT NOT NULL,
    event TEXT NOT NULL,
    detail_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_task_events_task ON task_events(task_id, event_id);
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    depends_on TEXT NOT NULL REFERENCES tasks(task_id),
    PRIMARY KEY(task_id, depends_on),
    CHECK (task_id <> depends_on)
);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_parent ON task_dependencies(depends_on);
CREATE TABLE IF NOT EXISTS plan_idempotency (
    idempotency_key TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL UNIQUE REFERENCES task_plans(plan_id),
    request_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS worker_heartbeats (
    worker_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL,
    pid BIGINT NOT NULL,
    state TEXT NOT NULL,
    started_at TEXT NOT NULL,
    heartbeat_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_worker_heartbeats_seen ON worker_heartbeats(heartbeat_at);
"""


class PostgresTaskStore:
    """TaskStore-compatible adapter for the local autonomy PostgreSQL queue."""

    backend = "postgresql"

    def __init__(self, dsn: str, *, connect_timeout: int = 5, schema: str = "public"):
        if not isinstance(dsn, str) or not dsn.startswith(("postgres://", "postgresql://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection URL")
        if not isinstance(schema, str) or not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", schema):
            raise ValueError("invalid PostgreSQL schema name")
        self.dsn = dsn
        self.schema = schema
        self.connect_timeout = max(1, min(int(connect_timeout), 30))
        if self.schema != "public":
            with psycopg.connect(self.dsn, connect_timeout=self.connect_timeout) as db:
                db.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(self.schema)))
        with self._connect() as db:
            db.execute(SCHEMA)

    def _connect(self):
        db = psycopg.connect(
            self.dsn,
            connect_timeout=self.connect_timeout,
            row_factory=dict_row,
            application_name="nextdecode-autonomy",
        )
        if self.schema != "public":
            db.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
        return db

    @staticmethod
    def is_transient_error(exc: Exception) -> bool:
        return isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError))

    @staticmethod
    def _digest(value: object) -> str:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _event(db, task_id: str, event: str, detail: dict | None = None) -> None:
        db.execute(
            "INSERT INTO task_events(task_id,at,event,detail_json) VALUES(%s,%s,%s,%s)",
            (task_id, utc_now(), event, json.dumps(detail or {}, sort_keys=True)),
        )

    @staticmethod
    def _validate_graph(nodes: list[dict]) -> dict[str, set[str]]:
        if not isinstance(nodes, list) or not 1 <= len(nodes) <= 32:
            raise ValueError("plan must contain 1..32 nodes")
        ids = [node.get("task_id") for node in nodes]
        if any(not isinstance(item, str) or len(item) != 32 for item in ids):
            raise ValueError("each plan node requires a valid task_id")
        if len(set(ids)) != len(ids):
            raise ValueError("plan requires unique task ids")
        graph: dict[str, set[str]] = {}
        for node in nodes:
            parents = node.get("depends_on", [])
            if not isinstance(parents, list) or len(parents) > 8:
                raise ValueError("each plan node supports at most 8 dependencies")
            if len(set(parents)) != len(parents):
                raise ValueError("duplicate task dependency")
            graph[node["task_id"]] = set(parents)
        ids_set = set(ids)
        if any(not parents.issubset(ids_set) for parents in graph.values()):
            raise ValueError("plan dependency references an unknown task")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("plan dependency graph contains a cycle")
            if task_id in visited:
                return
            visiting.add(task_id)
            for parent in graph[task_id]:
                visit(parent)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)
        return graph

    def enqueue(self, request: TaskRequest) -> dict:
        now = utc_now()
        payload_json = json.dumps(request.payload, sort_keys=True)
        request_hash = self._digest({"task_type": request.task_type, "payload": request.payload})
        with self._connect() as db:
            if request.idempotency_key:
                # Match enqueue_plan's transaction-scoped serialization: callers
                # racing on one key observe one committed task and one request hash.
                # The unique constraint remains the final integrity guard.
                db.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                    (request.idempotency_key,),
                )
                existing = db.execute(
                    "SELECT * FROM tasks WHERE idempotency_key=%s",
                    (request.idempotency_key,),
                ).fetchone()
                if existing:
                    existing_hash = existing["request_hash"] or self._digest({
                        "task_type": existing["task_type"],
                        "payload": json.loads(existing["payload_json"]),
                    })
                    if existing_hash != request_hash:
                        raise ValueError("idempotency_key_conflict")
                    return dict(existing)

            inserted = db.execute(
                """INSERT INTO tasks(task_id,task_type,payload_json,status,priority,attempts,
                   max_attempts,idempotency_key,request_hash,created_at,updated_at,not_before)
                   VALUES(%s,%s,%s,'queued',%s,0,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (idempotency_key) DO NOTHING
                   RETURNING *""",
                (request.task_id, request.task_type, payload_json, request.priority,
                 request.max_attempts, request.idempotency_key, request_hash, now, now,
                 request.not_before),
            ).fetchone()
            if inserted:
                self._event(db, request.task_id, "queued", {"task_type": request.task_type})
                return dict(inserted)
            if request.idempotency_key:
                # Defensive fallback for a writer that does not use the advisory lock.
                existing = db.execute(
                    "SELECT * FROM tasks WHERE idempotency_key=%s",
                    (request.idempotency_key,),
                ).fetchone()
                if existing:
                    existing_hash = existing["request_hash"] or self._digest({
                        "task_type": existing["task_type"],
                        "payload": json.loads(existing["payload_json"]),
                    })
                    if existing_hash != request_hash:
                        raise ValueError("idempotency_key_conflict")
                    return dict(existing)
            raise ValueError("task_id_conflict")

    def enqueue_plan(self, plan_id: str, goal: str, nodes: list[dict], plan_json: dict,
                     idempotency_key: str | None = None) -> dict:
        graph = self._validate_graph(nodes)
        from .plan_contract import canonical_plan_request
        request_hash = self._digest(canonical_plan_request(goal, nodes))
        now = utc_now()
        with self._connect() as db:
            if idempotency_key:
                # Serialize same-key plan submissions before checking/inserting the
                # idempotency record. The lock is transaction-scoped and local to
                # PostgreSQL; it does not introduce a new persistent schema object.
                db.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                    (idempotency_key,),
                )
                existing = db.execute(
                    "SELECT plan_id,request_hash FROM plan_idempotency WHERE idempotency_key=%s",
                    (idempotency_key,),
                ).fetchone()
                if existing:
                    if existing["request_hash"] != request_hash:
                        raise ValueError("idempotency_key_conflict")
                    return self.get_plan(existing["plan_id"])
            db.execute(
                "INSERT INTO task_plans(plan_id,goal,status,created_at,updated_at,plan_json) VALUES(%s,%s,'queued',%s,%s,%s)",
                (plan_id, goal, now, now, json.dumps(plan_json, sort_keys=True)),
            )
            for node in nodes:
                payload = node.get("payload", {})
                if not isinstance(payload, dict):
                    raise ValueError("task payload must be an object")
                db.execute(
                    """INSERT INTO tasks(task_id,plan_id,task_type,payload_json,status,priority,
                       attempts,max_attempts,created_at,updated_at)
                       VALUES(%s,%s,%s,%s,'queued',%s,0,%s,%s,%s)""",
                    (node["task_id"], plan_id, node["task_type"],
                     json.dumps(payload, sort_keys=True), node.get("priority", 100),
                     node.get("max_attempts", 3), now, now),
                )
                self._event(db, node["task_id"], "queued",
                            {"plan_id": plan_id, "task_type": node["task_type"]})
            for task_id, parents in graph.items():
                for parent in parents:
                    db.execute(
                        "INSERT INTO task_dependencies(task_id,depends_on) VALUES(%s,%s)",
                        (task_id, parent),
                    )
            if idempotency_key:
                db.execute(
                    "INSERT INTO plan_idempotency(idempotency_key,plan_id,request_hash) VALUES(%s,%s,%s)",
                    (idempotency_key, plan_id, request_hash),
                )
        return self.get_plan(plan_id)

    def get(self, task_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,)).fetchone()
            return dict(row) if row else None

    def list(self, limit: int = 100) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT %s",
                (max(1, min(int(limit), 500)),),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_plan(self, plan_id: str) -> dict | None:
        with self._connect() as db:
            plan = db.execute("SELECT * FROM task_plans WHERE plan_id=%s", (plan_id,)).fetchone()
            if not plan:
                return None
            tasks = db.execute(
                "SELECT * FROM tasks WHERE plan_id=%s ORDER BY created_at,task_id",
                (plan_id,),
            ).fetchall()
            statuses = [row["status"] for row in tasks]
            status = (
                "succeeded" if statuses and all(item == "succeeded" for item in statuses)
                else "running" if any(item == "running" for item in statuses)
                else "queued" if any(item == "queued" for item in statuses)
                else "failed" if any(item == "failed" for item in statuses)
                else "blocked" if any(item == "blocked" for item in statuses)
                else "queued"
            )
            updated_at = utc_now()
            db.execute(
                "UPDATE task_plans SET status=%s,updated_at=%s WHERE plan_id=%s",
                (status, updated_at, plan_id),
            )
            task_items = []
            for row in tasks:
                item = dict(row)
                deps = db.execute(
                    "SELECT depends_on FROM task_dependencies WHERE task_id=%s ORDER BY depends_on",
                    (row["task_id"],),
                ).fetchall()
                item["depends_on"] = [dep["depends_on"] for dep in deps]
                task_items.append(item)
            plan_data = dict(plan)
            plan_data["status"] = status
            plan_data["updated_at"] = updated_at
            return {"plan": plan_data, "status": status, "tasks": task_items}

    def claim(self, worker_id: str, lease_seconds: int = 300) -> dict | None:
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        lease_until = (now_dt + timedelta(seconds=max(1, int(lease_seconds)))).isoformat()
        with self._connect() as db:
            expired = db.execute(
                "SELECT task_id,attempts,max_attempts FROM tasks WHERE status='running' AND lease_until < %s FOR UPDATE",
                (now,),
            ).fetchall()
            for row in expired:
                next_status = "queued" if row["attempts"] < row["max_attempts"] else "failed"
                retry_at, retry_delay = retry_not_before(row["attempts"]) if next_status == "queued" else (None, None)
                db.execute(
                    """UPDATE tasks SET status=%s,lease_owner=NULL,lease_until=NULL,
                       updated_at=%s,error_code=%s,not_before=COALESCE(%s,not_before) WHERE task_id=%s""",
                    (next_status, now, None if next_status == "queued" else "worker_lease_exhausted",
                     retry_at, row["task_id"]),
                )
                self._event(db, row["task_id"], "lease_expired", {
                    "attempt": int(row["attempts"]), "next_status": next_status,
                    "retry_delay_seconds": retry_delay, "not_before": retry_at,
                })
            # Propagate terminal dependency failures through every queued descendant
            # and append a transition event for each blocked node.
            blocked = db.execute(
                """WITH RECURSIVE blocked(task_id) AS (
                     SELECT t.task_id FROM tasks t
                     JOIN task_dependencies d ON d.task_id=t.task_id
                     JOIN tasks p ON p.task_id=d.depends_on
                     WHERE t.status='queued' AND p.status IN ('failed','blocked')
                     UNION
                     SELECT child.task_id FROM tasks child
                     JOIN task_dependencies d ON d.task_id=child.task_id
                     JOIN blocked b ON b.task_id=d.depends_on
                     WHERE child.status='queued'
                   ) SELECT task_id FROM blocked"""
            ).fetchall()
            for blocked_row in blocked:
                db.execute(
                    "UPDATE tasks SET status='blocked',updated_at=%s,error_code='dependency_failed' WHERE task_id=%s AND status='queued'",
                    (now, blocked_row["task_id"]),
                )
                self._event(db, blocked_row["task_id"], "blocked",
                            {"reason": "dependency_failed"})
            row = db.execute(
                """SELECT t.* FROM tasks t WHERE t.status='queued'
                   AND (t.not_before IS NULL OR t.not_before<=%s)
                   AND NOT EXISTS (
                     SELECT 1 FROM task_dependencies d JOIN tasks p ON p.task_id=d.depends_on
                     WHERE d.task_id=t.task_id AND p.status!='succeeded'
                   )
                   ORDER BY t.priority DESC,t.created_at
                   LIMIT 1 FOR UPDATE OF t SKIP LOCKED""",
                (now,),
            ).fetchone()
            if not row:
                return None
            db.execute(
                """UPDATE tasks SET status='running',attempts=attempts+1,lease_owner=%s,
                   lease_until=%s,updated_at=%s WHERE task_id=%s AND status='queued'""",
                (worker_id, lease_until, now, row["task_id"]),
            )
            claimed = db.execute(
                "SELECT * FROM tasks WHERE task_id=%s", (row["task_id"],)
            ).fetchone()
            self._event(db, row["task_id"], "claimed", {
                "worker_id": worker_id, "attempt": int(claimed["attempts"]),
            })
            return dict(claimed)

    def renew_lease(self, task_id: str, worker_id: str, attempt: int,
                    lease_seconds: int = 300) -> bool:
        """Extend only the currently owned, unexpired attempt lease.

        The monotonically increasing attempt number is the fencing generation:
        an expired attempt can never renew a lease after a later claim.
        """
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        lease_until = (now_dt + timedelta(seconds=max(1, int(lease_seconds)))).isoformat()
        with self._connect() as db:
            cursor = db.execute(
                """UPDATE tasks SET lease_until=%s,updated_at=%s
                   WHERE task_id=%s AND status='running' AND lease_owner=%s
                     AND attempts=%s AND lease_until>%s""",
                (lease_until, now, task_id, worker_id, int(attempt), now),
            )
            if cursor.rowcount == 1:
                self._event(db, task_id, "execution_heartbeat", {
                    "worker_id": worker_id, "attempt": int(attempt),
                    "phase": "handler_running",
                })
            return cursor.rowcount == 1

    def stuck_tasks(self, stale_after_seconds: int = 120, limit: int = 100) -> list[dict]:
        """List running tasks with no recent fenced lease heartbeat; read-only."""
        threshold = datetime.now(timezone.utc) - timedelta(seconds=max(1, int(stale_after_seconds)))
        page = max(1, min(int(limit), 500))
        with self._connect() as db:
            rows = db.execute("""SELECT t.task_id,t.task_type,t.lease_owner,t.lease_until,t.attempts,t.updated_at,
                MAX(e.at) FILTER (WHERE e.event='execution_heartbeat') AS last_execution_heartbeat
                FROM tasks t LEFT JOIN task_events e ON e.task_id=t.task_id
                WHERE t.status='running' GROUP BY t.task_id
                HAVING MAX(e.at) FILTER (WHERE e.event='execution_heartbeat') IS NULL
                    OR MAX(e.at) FILTER (WHERE e.event='execution_heartbeat') < %s
                ORDER BY t.updated_at LIMIT %s""", (threshold.isoformat(), page)).fetchall()
            return [dict(row) for row in rows]

    def finish(self, task_id: str, worker_id: str, result: TaskResult,
               attempt: int) -> None:
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM tasks WHERE task_id=%s FOR UPDATE", (task_id,)
            ).fetchone()
            if (not row or row["status"] != "running" or row["lease_owner"] != worker_id
                    or row["lease_until"] <= now
                    or row["attempts"] != int(attempt)):
                raise RuntimeError("task lease lost or fenced; refusing stale worker update")
            retry_at = None
            retry_delay = None
            if result.status == "failed" and result.retryable and row["attempts"] < row["max_attempts"]:
                status = "queued"
                retry_at, retry_delay = retry_not_before(row["attempts"])
            else:
                status = result.status
            db.execute(
                """UPDATE tasks SET status=%s,updated_at=%s,lease_owner=NULL,lease_until=NULL,
                   result_json=%s,error_code=%s,not_before=COALESCE(%s,not_before)
                   WHERE task_id=%s""",
                (status, now, json.dumps({"output": result.output, "evidence": result.evidence},
                                         sort_keys=True),
                 result.error_code, retry_at, task_id),
            )
            self._event(db, task_id, status, {
                "attempt": int(attempt), "error_code": result.error_code,
                "retryable": result.retryable,
                "retry_delay_seconds": retry_delay,
                "not_before": retry_at,
            })

    def events(self, task_id: str) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM task_events WHERE task_id=%s ORDER BY event_id", (task_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def event_feed(self, after_event_id: int = 0, limit: int = 100) -> list[dict]:
        """Read a bounded, globally ordered event page after a numeric cursor.

        Persist the last event_id to resume consumption. This is an inspection
        primitive, not a canonical cross-service event bus.
        """
        cursor = int(after_event_id)
        if cursor < 0:
            raise ValueError("after_event_id must be non-negative")
        bounded_limit = max(1, min(int(limit), 500))
        with self._connect() as db:
            rows = db.execute(
                """SELECT event_id,task_id,at,event,detail_json
                   FROM task_events WHERE event_id>%s ORDER BY event_id LIMIT %s""",
                (cursor, bounded_limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def dependency_results(self, task_id: str) -> list[dict]:
        """Return bounded, successful prerequisite outputs for downstream handlers."""
        with self._connect() as db:
            rows = db.execute(
                """SELECT p.task_id,p.task_type,p.status,p.result_json
                   FROM task_dependencies d JOIN tasks p ON p.task_id=d.depends_on
                   WHERE d.task_id=%s ORDER BY p.task_id""",
                (task_id,),
            ).fetchall()
        results = []
        for row in rows:
            if row["status"] != "succeeded" or not row["result_json"]:
                continue
            try:
                result = json.loads(row["result_json"])
            except (TypeError, ValueError):
                continue
            item = {"task_id": row["task_id"], "task_type": row["task_type"],
                    "status": row["status"], "output": result.get("output", {}),
                    "evidence": result.get("evidence", {})}
            if len(json.dumps(item, ensure_ascii=False).encode("utf-8")) <= 16_384:
                results.append(item)
        return results

    def record_worker_heartbeat(self, worker_id: str, hostname: str, pid: int,
                                 state: str, started_at: str) -> None:
        if state not in {"starting", "idle", "working", "stopping", "stopped"}:
            raise ValueError("invalid worker heartbeat state")
        with self._connect() as db:
            db.execute(
                """INSERT INTO worker_heartbeats(worker_id,hostname,pid,state,started_at,heartbeat_at)
                   VALUES(%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(worker_id) DO UPDATE SET hostname=EXCLUDED.hostname,
                   pid=EXCLUDED.pid,state=EXCLUDED.state,heartbeat_at=EXCLUDED.heartbeat_at""",
                (worker_id, hostname, int(pid), state, started_at, utc_now()),
            )

    def mark_worker_stopped(self, *, worker_id: str, hostname: str, pid: int,
                            expected_heartbeat_at: str) -> bool:
        """Mark a confirmed-dead local worker stopped without erasing its history."""
        with self._connect() as db:
            cursor = db.execute(
                """UPDATE worker_heartbeats SET state='stopped'
                   WHERE worker_id=%s AND hostname=%s AND pid=%s AND heartbeat_at=%s
                   AND state NOT IN ('stopping','stopped')""",
                (worker_id, hostname, int(pid), expected_heartbeat_at),
            )
            return cursor.rowcount == 1

    def recover_expired_leases(self, limit: int = 100) -> list[dict]:
        """Requeue expired attempts or fail exhausted tasks without requiring a claim."""
        bounded_limit = max(1, min(int(limit), 500))
        now = utc_now()
        recovered = []
        with self._connect() as db:
            rows = db.execute(
                """SELECT task_id,attempts,max_attempts,lease_owner,lease_until
                   FROM tasks WHERE status='running' AND lease_until<%s
                   ORDER BY lease_until,task_id LIMIT %s FOR UPDATE SKIP LOCKED""",
                (now, bounded_limit),
            ).fetchall()
            for row in rows:
                status = "queued" if row["attempts"] < row["max_attempts"] else "failed"
                error = None if status == "queued" else "worker_lease_exhausted"
                retry_at, retry_delay = retry_not_before(row["attempts"]) if status == "queued" else (None, None)
                cursor = db.execute(
                    """UPDATE tasks SET status=%s,lease_owner=NULL,lease_until=NULL,
                       updated_at=%s,error_code=%s,not_before=COALESCE(%s,not_before) WHERE task_id=%s AND status='running'
                       AND lease_until<%s""",
                    (status, now, error, retry_at, row["task_id"], now),
                )
                if cursor.rowcount != 1:
                    continue
                detail = {"attempt": int(row["attempts"]), "previous_worker_id": row["lease_owner"],
                          "next_status": status, "reason": "lease_expired",
                          "retry_delay_seconds": retry_delay, "not_before": retry_at}
                self._event(db, row["task_id"], "lease_recovered", detail)
                recovered.append({"task_id": row["task_id"], "status": status, **detail})
        return recovered

    def health(self, stale_after_seconds: int = 45) -> dict:
        threshold = (
            datetime.now(timezone.utc) - timedelta(seconds=max(5, min(int(stale_after_seconds), 3600)))
        ).isoformat()
        with self._connect() as db:
            rows = db.execute("SELECT status,COUNT(*) AS count FROM tasks GROUP BY status").fetchall()
            counts = {row["status"]: row["count"] for row in rows}
            expired = db.execute(
                "SELECT COUNT(*) AS count FROM tasks WHERE status='running' AND lease_until<%s",
                (utc_now(),),
            ).fetchone()["count"]
            workers = [dict(row) for row in db.execute(
                """SELECT worker_id,hostname,pid,state,started_at,heartbeat_at
                   FROM worker_heartbeats ORDER BY heartbeat_at DESC"""
            ).fetchall()]
            for worker in workers:
                worker["alive"] = worker["heartbeat_at"] >= threshold and worker["state"] not in {"stopping", "stopped"}
                worker["stale"] = worker["heartbeat_at"] < threshold and worker["state"] not in {"stopping", "stopped"}
            return {
                "database": "postgresql",
                "database_accessible": True,
                "queue_counts": counts,
                "total_tasks": sum(counts.values()),
                "expired_running_leases": expired,
                "workers": workers,
                "active_workers": sum(1 for item in workers if item["alive"]),
                "stale_workers": sum(1 for item in workers if item["stale"]),
                "stopped_workers": sum(1 for item in workers if item["state"] in {"stopping", "stopped"}),
                "heartbeat_stale_after_seconds": max(5, min(int(stale_after_seconds), 3600)),
            }

    def dead_letters(self, limit: int = 100) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT task_id,task_type,status,attempts,max_attempts,created_at,updated_at,
                          error_code,result_json FROM tasks WHERE status='failed'
                   ORDER BY updated_at DESC LIMIT %s""",
                (max(1, min(int(limit), 500)),),
            ).fetchall()
            return [dict(row) for row in rows]

    def import_sqlite(self, source: str | Path) -> dict:
        """Idempotently copy legacy SQLite queue data; never modifies the source."""
        source_path = Path(source)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        legacy = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
        legacy.row_factory = sqlite3.Row
        counts: dict[str, int] = {}
        try:
            with self._connect() as db:
                for table in ("task_plans", "tasks", "task_dependencies", "task_events",
                              "plan_idempotency", "worker_heartbeats"):
                    rows = [dict(row) for row in legacy.execute(f"SELECT * FROM {table}")]
                    counts[table] = len(rows)
                    if table == "task_plans":
                        for row in rows:
                            db.execute(
                                """INSERT INTO task_plans(plan_id,goal,status,created_at,updated_at,plan_json)
                                   VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(plan_id) DO NOTHING""",
                                tuple(row[key] for key in ("plan_id","goal","status","created_at","updated_at","plan_json")),
                            )
                    elif table == "tasks":
                        for row in rows:
                            db.execute(
                                """INSERT INTO tasks(task_id,plan_id,task_type,payload_json,status,priority,
                                   attempts,max_attempts,idempotency_key,request_hash,created_at,updated_at,
                                   not_before,lease_owner,lease_until,result_json,error_code)
                                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                   ON CONFLICT(task_id) DO NOTHING""",
                                (row["task_id"], row.get("plan_id"), row["task_type"], row["payload_json"],
                                 row["status"], row["priority"], row["attempts"], row["max_attempts"],
                                 row["idempotency_key"], row.get("request_hash"), row["created_at"],
                                 row["updated_at"], row["not_before"], row["lease_owner"], row["lease_until"],
                                 row["result_json"], row["error_code"]),
                            )
                    elif table == "task_dependencies":
                        for row in rows:
                            db.execute(
                                "INSERT INTO task_dependencies(task_id,depends_on) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                                (row["task_id"], row["depends_on"]),
                            )
                    elif table == "task_events":
                        for row in rows:
                            db.execute(
                                """INSERT INTO task_events(event_id,task_id,at,event,detail_json)
                                   VALUES(%s,%s,%s,%s,%s) ON CONFLICT(event_id) DO NOTHING""",
                                (row["event_id"], row["task_id"], row["at"], row["event"], row["detail_json"]),
                            )
                    elif table == "plan_idempotency":
                        for row in rows:
                            db.execute(
                                """INSERT INTO plan_idempotency(idempotency_key,plan_id,request_hash)
                                   VALUES(%s,%s,%s) ON CONFLICT(idempotency_key) DO NOTHING""",
                                (row["idempotency_key"], row["plan_id"], row.get("request_hash") or "legacy"),
                            )
                    elif table == "worker_heartbeats":
                        for row in rows:
                            # A migrated heartbeat cannot prove that its old process
                            # survived the backend cutover. Preserve its history but
                            # mark it stopped; the new worker writes its own live row.
                            imported_state = row["state"] if row["state"] in {"stopped", "stopping"} else "stopped"
                            db.execute(
                                """INSERT INTO worker_heartbeats(worker_id,hostname,pid,state,started_at,heartbeat_at)
                                   VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(worker_id) DO NOTHING""",
                                (row["worker_id"], row["hostname"], row["pid"], imported_state,
                                 row["started_at"], row["heartbeat_at"]),
                            )
                db.execute(
                    "SELECT setval(pg_get_serial_sequence('task_events','event_id'), GREATEST(COALESCE((SELECT MAX(event_id) FROM task_events),1),1), true)"
                )
        finally:
            legacy.close()
        return counts
