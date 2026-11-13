"""SQLite-backed durable task queue with DAG dependencies, leases and recovery."""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from .models import TaskRequest, TaskResult, utc_now
from .retry_policy import retry_not_before

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
 task_id TEXT PRIMARY KEY, plan_id TEXT, task_type TEXT NOT NULL, payload_json TEXT NOT NULL,
 status TEXT NOT NULL, priority INTEGER NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
 max_attempts INTEGER NOT NULL, idempotency_key TEXT UNIQUE, request_hash TEXT, created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL, not_before TEXT, lease_owner TEXT, lease_until TEXT,
 result_json TEXT, error_code TEXT
);
CREATE INDEX IF NOT EXISTS idx_tasks_ready ON tasks(status, priority DESC, created_at);
CREATE TABLE IF NOT EXISTS task_events (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, at TEXT NOT NULL,
 event TEXT NOT NULL, detail_json TEXT NOT NULL,
 FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);
CREATE TABLE IF NOT EXISTS task_plans (
 plan_id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, plan_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS task_dependencies (
 task_id TEXT NOT NULL, depends_on TEXT NOT NULL,
 PRIMARY KEY(task_id, depends_on),
 FOREIGN KEY(task_id) REFERENCES tasks(task_id),
 FOREIGN KEY(depends_on) REFERENCES tasks(task_id)
);
CREATE TABLE IF NOT EXISTS plan_idempotency (
 idempotency_key TEXT PRIMARY KEY, plan_id TEXT NOT NULL UNIQUE, request_hash TEXT,
 FOREIGN KEY(plan_id) REFERENCES task_plans(plan_id)
);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_parent ON task_dependencies(depends_on);
CREATE TABLE IF NOT EXISTS worker_heartbeats (
 worker_id TEXT PRIMARY KEY, hostname TEXT NOT NULL, pid INTEGER NOT NULL,
 state TEXT NOT NULL, started_at TEXT NOT NULL, heartbeat_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_worker_heartbeats_seen ON worker_heartbeats(heartbeat_at);
"""

class TaskStore:
    """SQLite development/test adapter. Production uses PostgresTaskStore."""

    backend = "sqlite"

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(SCHEMA)
            task_columns = {row["name"] for row in db.execute("PRAGMA table_info(tasks)")}
            if "plan_id" not in task_columns:
                db.execute("ALTER TABLE tasks ADD COLUMN plan_id TEXT")
            if "request_hash" not in task_columns:
                db.execute("ALTER TABLE tasks ADD COLUMN request_hash TEXT")
            plan_key_columns = {row["name"] for row in db.execute("PRAGMA table_info(plan_idempotency)")}
            if "request_hash" not in plan_key_columns:
                db.execute("ALTER TABLE plan_idempotency ADD COLUMN request_hash TEXT")
            db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_plan ON tasks(plan_id)")
            db.execute("PRAGMA journal_mode=WAL")

    @staticmethod
    def is_transient_error(exc: Exception) -> bool:
        return isinstance(exc, sqlite3.OperationalError) and any(
            marker in str(exc).casefold()
            for marker in ("unable to open database file", "database is locked", "disk i/o error")
        )

    @staticmethod
    def _digest(value: object) -> str:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=30000")
        return db

    def _event(self, db, task_id, event, detail=None):
        db.execute("INSERT INTO task_events(task_id,at,event,detail_json) VALUES(?,?,?,?)",
                   (task_id, utc_now(), event, json.dumps(detail or {}, sort_keys=True)))

    def enqueue(self, request: TaskRequest) -> dict:
        now = utc_now()
        payload_json = json.dumps(request.payload, sort_keys=True)
        request_hash = self._digest({"task_type": request.task_type, "payload": request.payload})
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if request.idempotency_key:
                existing = db.execute("SELECT * FROM tasks WHERE idempotency_key=?",
                                       (request.idempotency_key,)).fetchone()
                if existing:
                    existing_hash = existing["request_hash"] or self._digest({
                        "task_type": existing["task_type"],
                        "payload": json.loads(existing["payload_json"]),
                    })
                    if existing_hash != request_hash:
                        raise ValueError("idempotency_key_conflict")
                    db.commit()
                    return dict(existing)
            db.execute("""INSERT INTO tasks(task_id,task_type,payload_json,status,priority,attempts,
                max_attempts,idempotency_key,request_hash,created_at,updated_at,not_before)
                VALUES(?,?,?,'queued',?,0,?,?,?,?,?,?)""",
                (request.task_id, request.task_type, payload_json, request.priority,
                 request.max_attempts, request.idempotency_key, request_hash, now, now, request.not_before))
            self._event(db, request.task_id, "queued", {"task_type": request.task_type})
            db.commit()
        return self.get(request.task_id)

    def enqueue_plan(self, plan_id: str, goal: str, nodes: list[dict], plan_json: dict,
                     idempotency_key: str | None = None) -> dict:
        """Persist an entire validated DAG atomically; no worker sees a partial plan."""
        now = utc_now()
        if not isinstance(nodes, list) or not 1 <= len(nodes) <= 32:
            raise ValueError("plan must contain 1..32 nodes")
        ids_list = [node.get("task_id") for node in nodes]
        ids = set(ids_list)
        if len(ids) != len(nodes) or not ids:
            raise ValueError("plan requires unique task ids")
        graph = {}
        for node in nodes:
            parents = node.get("depends_on", [])
            if not isinstance(parents, list) or len(parents) > 8:
                raise ValueError("each plan node supports at most 8 dependencies")
            if len(set(parents)) != len(parents):
                raise ValueError("duplicate task dependency")
            if not isinstance(node.get("payload", {}), dict):
                raise ValueError("task payload must be an object")
            if len(json.dumps(node.get("payload", {}), sort_keys=True)) > 65536:
                raise ValueError("task payload exceeds 65536 bytes")
            graph[node["task_id"]] = set(parents)
        if any(not parents.issubset(ids) for parents in graph.values()):
            raise ValueError("plan dependency references an unknown task")
        from .plan_contract import canonical_plan_request
        request_hash = self._digest(canonical_plan_request(goal, nodes))
        visiting, visited = set(), set()
        def visit(task_id):
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
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if idempotency_key:
                existing = db.execute("SELECT plan_id,request_hash FROM plan_idempotency WHERE idempotency_key=?",
                                      (idempotency_key,)).fetchone()
                if existing:
                    if existing["request_hash"] and existing["request_hash"] != request_hash:
                        raise ValueError("idempotency_key_conflict")
                    db.commit()
                    return self.get_plan(existing["plan_id"])
            db.execute("INSERT INTO task_plans VALUES(?,?,?,?,?,?)",
                       (plan_id, goal, "queued", now, now, json.dumps(plan_json, sort_keys=True)))
            for node in nodes:
                db.execute("""INSERT INTO tasks(task_id,plan_id,task_type,payload_json,status,priority,attempts,
                    max_attempts,idempotency_key,request_hash,created_at,updated_at)
                    VALUES(?,?,?,?,'queued',?,0,?,NULL,NULL,?,?)""",
                    (node["task_id"], plan_id, node["task_type"], json.dumps(node.get("payload", {}), sort_keys=True),
                     node.get("priority", 100), node.get("max_attempts", 3), now, now))
                self._event(db, node["task_id"], "queued", {"plan_id": plan_id, "task_type": node["task_type"]})
            for node in nodes:
                for parent in node.get("depends_on", []):
                    if parent == node["task_id"]:
                        raise ValueError("task cannot depend on itself")
                    db.execute("INSERT INTO task_dependencies(task_id,depends_on) VALUES(?,?)",
                               (node["task_id"], parent))
            if idempotency_key:
                db.execute("INSERT INTO plan_idempotency(idempotency_key,plan_id,request_hash) VALUES(?,?,?)",
                           (idempotency_key, plan_id, request_hash))
            db.commit()
        return self.get_plan(plan_id)

    def get(self, task_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            return dict(row) if row else None

    def list(self, limit: int = 100) -> list[dict]:
        with self._connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 500)),))]

    def get_plan(self, plan_id: str) -> dict | None:
        with self._connect() as db:
            plan = db.execute("SELECT * FROM task_plans WHERE plan_id=?", (plan_id,)).fetchone()
            if not plan:
                return None
            tasks = db.execute(
                "SELECT * FROM tasks WHERE plan_id=? ORDER BY created_at,task_id",
                (plan_id,),
            ).fetchall()
            if not tasks:
                # Compatibility for plans created before plan_id became a first-class relation.
                tasks = db.execute("""SELECT t.* FROM tasks t JOIN task_events e ON e.task_id=t.task_id
                    WHERE json_extract(e.detail_json,'$.plan_id')=? GROUP BY t.task_id
                    ORDER BY t.created_at,t.task_id""", (plan_id,)).fetchall()
            statuses = [r["status"] for r in tasks]
            # A failed branch does not stop independent branches from draining.
            # Keep the plan active until no queued/running work remains, then expose
            # its terminal failed/blocked state.
            status = ("succeeded" if statuses and all(x == "succeeded" for x in statuses)
                      else "running" if any(x == "running" for x in statuses)
                      else "queued" if any(x == "queued" for x in statuses)
                      else "failed" if any(x == "failed" for x in statuses)
                      else "blocked" if any(x == "blocked" for x in statuses)
                      else "queued")
            updated_at = utc_now()
            db.execute("UPDATE task_plans SET status=?,updated_at=? WHERE plan_id=?",
                       (status, updated_at, plan_id))
            db.commit()
            plan_data = dict(plan)
            plan_data["status"] = status
            plan_data["updated_at"] = updated_at
            task_items = []
            for row in tasks:
                item = dict(row)
                item["depends_on"] = [x["depends_on"] for x in db.execute(
                    "SELECT depends_on FROM task_dependencies WHERE task_id=? ORDER BY depends_on",
                    (row["task_id"],)).fetchall()]
                task_items.append(item)
            return {"plan": plan_data, "status": status, "tasks": task_items}

    def claim(self, worker_id: str, lease_seconds: int = 300) -> dict | None:
        now = utc_now()
        from datetime import datetime, timedelta, timezone
        lease_until = (datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)).isoformat()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            expired = db.execute("SELECT task_id,attempts,max_attempts FROM tasks WHERE status='running' AND lease_until<?", (now,)).fetchall()
            for row in expired:
                status = "queued" if row["attempts"] < row["max_attempts"] else "failed"
                retry_at, retry_delay = retry_not_before(row["attempts"]) if status == "queued" else (None, None)
                db.execute("UPDATE tasks SET status=?,lease_owner=NULL,lease_until=NULL,updated_at=?,error_code=?,not_before=COALESCE(?,not_before) WHERE task_id=?",
                           (status, now, None if status == "queued" else "worker_lease_exhausted", retry_at, row["task_id"]))
                self._event(db, row["task_id"], "lease_expired", {
                    "attempt": int(row["attempts"]), "next_status": status,
                    "retry_delay_seconds": retry_delay, "not_before": retry_at,
                })
            # A terminal unsuccessful prerequisite blocks every queued descendant,
            # not only the first generation of children.
            blocked = db.execute("""WITH RECURSIVE blocked(task_id) AS (
                SELECT t.task_id FROM tasks t
                JOIN task_dependencies d ON d.task_id=t.task_id
                JOIN tasks parent ON parent.task_id=d.depends_on
                WHERE t.status='queued' AND parent.status IN ('failed','blocked')
                UNION
                SELECT child.task_id FROM tasks child
                JOIN task_dependencies d ON d.task_id=child.task_id
                JOIN blocked b ON b.task_id=d.depends_on
                WHERE child.status='queued'
            ) SELECT task_id FROM blocked""").fetchall()
            for row in blocked:
                db.execute("UPDATE tasks SET status='blocked',updated_at=?,error_code='dependency_failed' WHERE task_id=?",
                           (now, row["task_id"]))
                self._event(db, row["task_id"], "blocked", {"reason": "dependency_failed"})
            row = db.execute("""SELECT t.* FROM tasks t WHERE t.status='queued'
                AND (t.not_before IS NULL OR t.not_before<=?)
                AND NOT EXISTS (SELECT 1 FROM task_dependencies d JOIN tasks p ON p.task_id=d.depends_on
                    WHERE d.task_id=t.task_id AND p.status!='succeeded')
                ORDER BY t.priority DESC,t.created_at LIMIT 1""", (now,)).fetchone()
            if not row:
                db.commit()
                return None
            db.execute("""UPDATE tasks SET status='running',attempts=attempts+1,lease_owner=?,
                lease_until=?,updated_at=? WHERE task_id=? AND status='queued'""",
                (worker_id, lease_until, now, row["task_id"]))
            claimed = db.execute("SELECT * FROM tasks WHERE task_id=?", (row["task_id"],)).fetchone()
            self._event(db, row["task_id"], "claimed", {
                "worker_id": worker_id, "attempt": int(claimed["attempts"]),
            })
            db.commit()
            return dict(claimed)

    def renew_lease(self, task_id: str, worker_id: str, attempt: int,
                    lease_seconds: int = 300) -> bool:
        """Extend only the current unexpired attempt; attempts fence stale workers."""
        from datetime import datetime, timedelta, timezone
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        lease_until = (now_dt + timedelta(seconds=max(1, int(lease_seconds)))).isoformat()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cursor = db.execute(
                """UPDATE tasks SET lease_until=?,updated_at=?
                   WHERE task_id=? AND status='running' AND lease_owner=?
                     AND attempts=? AND lease_until>?""",
                (lease_until, now, task_id, worker_id, int(attempt), now),
            )
            if cursor.rowcount == 1:
                self._event(db, task_id, "execution_heartbeat", {
                    "worker_id": worker_id, "attempt": int(attempt),
                    "phase": "handler_running",
                })
            db.commit()
            return cursor.rowcount == 1

    def stuck_tasks(self, stale_after_seconds: int = 120, limit: int = 100) -> list[dict]:
        """List running tasks with no recent fenced lease heartbeat; read-only."""
        from datetime import datetime, timedelta, timezone
        threshold = (datetime.now(timezone.utc) - timedelta(seconds=max(1, int(stale_after_seconds)))).isoformat()
        page = max(1, min(int(limit), 500))
        with self._connect() as db:
            rows = db.execute("""SELECT t.task_id,t.task_type,t.lease_owner,t.lease_until,t.attempts,t.updated_at,
                MAX(CASE WHEN e.event='execution_heartbeat' THEN e.at END) AS last_execution_heartbeat
                FROM tasks t LEFT JOIN task_events e ON e.task_id=t.task_id
                WHERE t.status='running' GROUP BY t.task_id
                HAVING last_execution_heartbeat IS NULL OR last_execution_heartbeat < ?
                ORDER BY t.updated_at LIMIT ?""", (threshold, page)).fetchall()
            return [dict(row) for row in rows]

    def finish(self, task_id: str, worker_id: str, result: TaskResult,
               attempt: int) -> None:
        now = utc_now()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if (not row or row["status"] != "running" or row["lease_owner"] != worker_id
                    or row["lease_until"] <= now
                    or row["attempts"] != int(attempt)):
                db.rollback()
                raise RuntimeError("task lease lost or fenced; refusing stale worker update")
            retry_at = None
            retry_delay = None
            if result.status == "failed" and result.retryable and row["attempts"] < row["max_attempts"]:
                status = "queued"
                retry_at, retry_delay = retry_not_before(row["attempts"])
            else:
                status = result.status
            db.execute("""UPDATE tasks SET status=?,updated_at=?,lease_owner=NULL,lease_until=NULL,
                result_json=?,error_code=?,not_before=COALESCE(?,not_before) WHERE task_id=?""",
                (status, now, json.dumps({"output": result.output, "evidence": result.evidence}, sort_keys=True),
                 result.error_code, retry_at, task_id))
            self._event(db, task_id, status, {
                "attempt": int(attempt), "error_code": result.error_code,
                "retryable": result.retryable,
                "retry_delay_seconds": retry_delay,
                "not_before": retry_at,
            })
            db.commit()

    def events(self, task_id: str) -> list[dict]:
        with self._connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM task_events WHERE task_id=? ORDER BY event_id", (task_id,))]

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
                   FROM task_events WHERE event_id>? ORDER BY event_id LIMIT ?""",
                (cursor, bounded_limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def dependency_results(self, task_id: str) -> list[dict]:
        """Return bounded, successful prerequisite outputs for downstream handlers."""
        with self._connect() as db:
            rows = db.execute(
                """SELECT p.task_id,p.task_type,p.status,p.result_json
                   FROM task_dependencies d JOIN tasks p ON p.task_id=d.depends_on
                   WHERE d.task_id=? ORDER BY p.task_id""",
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
        now = utc_now()
        with self._connect() as db:
            db.execute(
                """INSERT INTO worker_heartbeats(worker_id,hostname,pid,state,started_at,heartbeat_at)
                   VALUES(?,?,?,?,?,?) ON CONFLICT(worker_id) DO UPDATE SET
                   hostname=excluded.hostname,pid=excluded.pid,state=excluded.state,
                   heartbeat_at=excluded.heartbeat_at""",
                (worker_id, hostname, int(pid), state, started_at, now),
            )

    def mark_worker_stopped(self, *, worker_id: str, hostname: str, pid: int,
                            expected_heartbeat_at: str) -> bool:
        """Mark a confirmed-dead local worker stopped without erasing its history."""
        with self._connect() as db:
            cursor = db.execute(
                """UPDATE worker_heartbeats SET state='stopped'
                   WHERE worker_id=? AND hostname=? AND pid=? AND heartbeat_at=?
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
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute(
                """SELECT task_id,attempts,max_attempts,lease_owner,lease_until
                   FROM tasks WHERE status='running' AND lease_until<?
                   ORDER BY lease_until,task_id LIMIT ?""",
                (now, bounded_limit),
            ).fetchall()
            for row in rows:
                status = "queued" if row["attempts"] < row["max_attempts"] else "failed"
                error = None if status == "queued" else "worker_lease_exhausted"
                retry_at, retry_delay = retry_not_before(row["attempts"]) if status == "queued" else (None, None)
                cursor = db.execute(
                    """UPDATE tasks SET status=?,lease_owner=NULL,lease_until=NULL,
                       updated_at=?,error_code=?,not_before=COALESCE(?,not_before) WHERE task_id=? AND status='running'
                       AND lease_until<?""",
                    (status, now, error, retry_at, row["task_id"], now),
                )
                if cursor.rowcount != 1:
                    continue
                detail = {"attempt": int(row["attempts"]), "previous_worker_id": row["lease_owner"],
                          "next_status": status, "reason": "lease_expired",
                          "retry_delay_seconds": retry_delay, "not_before": retry_at}
                self._event(db, row["task_id"], "lease_recovered", detail)
                recovered.append({"task_id": row["task_id"], "status": status, **detail})
            db.commit()
        return recovered

    def health(self, stale_after_seconds: int = 45) -> dict:
        """Return queue counts and worker liveness derived from persisted heartbeats."""
        from datetime import datetime, timedelta, timezone
        threshold = (datetime.now(timezone.utc) - timedelta(
            seconds=max(5, min(int(stale_after_seconds), 3600)))).isoformat()
        with self._connect() as db:
            rows = db.execute("SELECT status,COUNT(*) AS count FROM tasks GROUP BY status").fetchall()
            counts = {row["status"]: row["count"] for row in rows}
            expired = db.execute(
                "SELECT COUNT(*) FROM tasks WHERE status='running' AND lease_until<?",
                (utc_now(),),
            ).fetchone()[0]
            workers = [dict(row) for row in db.execute(
                "SELECT worker_id,hostname,pid,state,started_at,heartbeat_at FROM worker_heartbeats ORDER BY heartbeat_at DESC"
            ).fetchall()]
            for worker in workers:
                worker["alive"] = worker["heartbeat_at"] >= threshold and worker["state"] not in {"stopping", "stopped"}
                worker["stale"] = worker["heartbeat_at"] < threshold and worker["state"] not in {"stopping", "stopped"}
            return {
                "database": str(self.path),
                "database_accessible": True,
                "queue_counts": counts,
                "total_tasks": sum(counts.values()),
                "expired_running_leases": expired,
                "workers": workers,
                "active_workers": sum(1 for worker in workers if worker["alive"]),
                "stale_workers": sum(1 for worker in workers if worker["stale"]),
                "stopped_workers": sum(1 for worker in workers if worker["state"] in {"stopping", "stopped"}),
                "heartbeat_stale_after_seconds": max(5, min(int(stale_after_seconds), 3600)),
            }

    def dead_letters(self, limit: int = 100) -> list[dict]:
        """List terminal failed tasks for operator inspection without mutation."""
        bounded_limit = max(1, min(int(limit), 500))
        with self._connect() as db:
            rows = db.execute(
                """SELECT task_id,task_type,status,attempts,max_attempts,created_at,updated_at,
                          error_code,result_json
                   FROM tasks WHERE status='failed'
                   ORDER BY updated_at DESC LIMIT ?""",
                (bounded_limit,),
            ).fetchall()
            return [dict(row) for row in rows]


def create_task_store(path: str | Path | None = None):
    """Select PostgreSQL for the live control plane; SQLite for tests/local dev.

    An explicit path always selects SQLite. Otherwise DATABASE_URL takes
    precedence; NEXTDECODE_TASK_DB is the local-development fallback.
    """
    if path is None:
        dsn = os.environ.get("DATABASE_URL", "").strip()
        if dsn:
            from .postgres_store import PostgresTaskStore
            return PostgresTaskStore(dsn)
        path = os.environ.get(
            "NEXTDECODE_TASK_DB",
            str(Path(__file__).resolve().parents[2] / "data" / "autonomy" / "tasks.sqlite3"),
        )
    return TaskStore(path)
