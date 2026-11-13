"""Non-destructive one-time migration from the legacy SQLite autonomy queue."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.autonomy.postgres_store import PostgresTaskStore


TABLES = ("task_plans", "tasks", "task_dependencies", "task_events",
          "plan_idempotency", "worker_heartbeats")


def _counts_sqlite(path: Path) -> dict[str, int]:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        return {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in TABLES}


def _backup_sqlite(source: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup_dir.chmod(0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = backup_dir / f"tasks-pre-postgres-{stamp}-{uuid.uuid4().hex[:8]}.sqlite3"
    with sqlite3.connect(source, timeout=30) as src:
        check = src.execute("PRAGMA integrity_check").fetchone()[0]
        if check != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {check}")
        src.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        with sqlite3.connect(target) as dst:
            src.backup(dst)
            backup_check = dst.execute("PRAGMA integrity_check").fetchone()[0]
            if backup_check != "ok":
                raise RuntimeError(f"SQLite backup integrity check failed: {backup_check}")
    target.chmod(0o600)
    return target


def migrate(source: Path, backup_dir: Path, *, schema: str = "public") -> dict:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL must point to the target PostgreSQL database")
    if not source.is_file():
        raise FileNotFoundError(source)
    backup = _backup_sqlite(source, backup_dir)
    before = _counts_sqlite(backup)
    store = PostgresTaskStore(os.environ["DATABASE_URL"], schema=schema)
    with store._connect() as db:
        before_target = {
            table: db.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in TABLES
        }
    if any(before_target.values()):
        raise RuntimeError(
            "migration target is not empty; use a fresh database/schema or reconcile manually"
        )
    imported = store.import_sqlite(backup)
    with store._connect() as db:
        after = {
            table: db.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in TABLES
        }
    mismatches = {
        table: {"source": before[table], "imported": imported[table], "target": after[table]}
        for table in TABLES
        if imported[table] != before[table] or after[table] != before[table]
    }
    if mismatches:
        raise RuntimeError("migration count verification failed: " + json.dumps(mismatches))
    return {
        "status": "verified",
        "source": str(source),
        "backup": str(backup),
        "source_counts": before,
        "imported_counts": imported,
        "target_counts": after,
        "source_preserved": source.is_file(),
        "backup_mode": oct(backup.stat().st_mode & 0o777),
        "target_schema": schema,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=os.environ.get(
        "NEXTDECODE_LEGACY_SQLITE_DB", "data/autonomy/tasks.sqlite3"))
    parser.add_argument("--backup-dir", default="data/autonomy/backups")
    parser.add_argument("--schema", default="public")
    args = parser.parse_args()
    systemctl = shutil.which("systemctl")
    if systemctl:
        for unit in (
            "nextdecode-autonomy-worker.service",
            "nextdecode-autonomy-api.service",
        ):
            state = subprocess.run(
                [systemctl, "--user", "is-active", unit],
                capture_output=True, text=True, check=False,
            )
            if state.returncode == 0 and state.stdout.strip() == "active":
                raise RuntimeError(f"stop {unit} before migration")
    result = migrate(Path(args.source).resolve(), Path(args.backup_dir).resolve(),
                     schema=args.schema)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
