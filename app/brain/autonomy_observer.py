from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from .context import ROOT

MAX_TASKS = 8
MAX_WORKERS = 20
DEFAULT_DB = ROOT / "data" / "autonomy" / "tasks.sqlite3"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _database_path() -> Path:
    configured = os.environ.get("NEXTDECODE_TASK_DB", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_DB


def collect_local_autonomy_state(
    *, database_path: Path | str | None = None, stale_after_seconds: int = 45
) -> dict:
    """Observe the local autonomy adapter without initializing or mutating it.

    This is explicitly operational telemetry, not canonical P0 workflow/job/worker
    state. PostgreSQL is intentionally not opened here: the current adapter
    constructor performs schema initialization, while the P0 contracts remain
    unfrozen. A dedicated read-only PostgreSQL observer follows contract closure.
    """
    configured_dsn = os.environ.get("DATABASE_URL", "").strip()
    if configured_dsn and database_path is None:
        return {
            "source": "local_autonomy_runtime",
            "authority": "non_canonical_operational_observation",
            "backend": "postgresql",
            "available": False,
            "reason": "postgres_read_only_observer_not_implemented",
            "queue_counts": {},
            "total_tasks": 0,
            "workers": [],
            "recent_failures": [],
            "expired_running_leases": 0,
        }

    path = Path(database_path).expanduser() if database_path is not None else _database_path()
    base = {
        "source": "local_autonomy_runtime",
        "authority": "non_canonical_operational_observation",
        "backend": "sqlite",
        "available": False,
        "queue_counts": {},
        "total_tasks": 0,
        "workers": [],
        "recent_failures": [],
        "expired_running_leases": 0,
        "active_workers": 0,
        "stale_workers": 0,
    }
    try:
        if path.is_symlink() or not path.is_file():
            return {**base, "reason": "local_database_missing_or_unsafe"}
        resolved = path.resolve(strict=True)
        uri = f"file:{quote(str(resolved), safe='/')}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=0.5) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            tables = {
                row["name"]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "tasks" not in tables:
                return {**base, "reason": "task_table_not_found"}
            rows = db.execute(
                "SELECT status, COUNT(*) AS count FROM tasks GROUP BY status"
            ).fetchall()
            counts = {str(row["status"]): int(row["count"]) for row in rows}
            now = _utcnow()
            expired = 0
            if "lease_until" in {r["name"] for r in db.execute("PRAGMA table_info(tasks)")}:
                expired = int(db.execute(
                    "SELECT COUNT(*) FROM tasks WHERE status='running' AND lease_until IS NOT NULL AND lease_until < ?",
                    (now.isoformat(),),
                ).fetchone()[0])

            failures = []
            task_columns = {r["name"] for r in db.execute("PRAGMA table_info(tasks)")}
            safe_columns = {"task_id", "task_type", "status", "attempts", "max_attempts", "updated_at", "error_code"}
            selected = [name for name in safe_columns if name in task_columns]
            if {"task_id", "status"}.issubset(task_columns):
                projection = ", ".join(selected)
                failure_rows = db.execute(
                    f"SELECT {projection} FROM tasks WHERE status='failed' ORDER BY updated_at DESC LIMIT ?",
                    (MAX_TASKS,),
                ).fetchall()
                failures = [{key: row[key] for key in selected} for row in failure_rows]

            workers = []
            if "worker_heartbeats" in tables:
                worker_columns = {r["name"] for r in db.execute("PRAGMA table_info(worker_heartbeats)")}
                needed = {"worker_id", "state", "heartbeat_at"}
                if needed.issubset(worker_columns):
                    worker_rows = db.execute(
                        "SELECT worker_id, state, heartbeat_at FROM worker_heartbeats ORDER BY heartbeat_at DESC LIMIT ?",
                        (MAX_WORKERS,),
                    ).fetchall()
                    threshold = now - timedelta(seconds=max(5, min(int(stale_after_seconds), 3600)))
                    for row in worker_rows:
                        heartbeat = _parse_time(row["heartbeat_at"])
                        state = str(row["state"])
                        stale = bool(heartbeat and heartbeat < threshold and state not in {"stopping", "stopped"})
                        alive = bool(heartbeat and heartbeat >= threshold and state not in {"stopping", "stopped"})
                        workers.append({
                            "worker_id": str(row["worker_id"])[:120],
                            "state": state[:32],
                            "heartbeat_at": row["heartbeat_at"],
                            "alive": alive,
                            "stale": stale,
                        })

            return {
                **base,
                "available": True,
                "reason": None,
                "queue_counts": counts,
                "total_tasks": sum(counts.values()),
                "workers": workers,
                "recent_failures": failures,
                "expired_running_leases": expired,
                "active_workers": sum(1 for worker in workers if worker["alive"]),
                "stale_workers": sum(1 for worker in workers if worker["stale"]),
                "heartbeat_stale_after_seconds": max(5, min(int(stale_after_seconds), 3600)),
            }
    except (OSError, sqlite3.Error, ValueError):
        return {**base, "reason": "local_autonomy_store_unavailable"}
