from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from api import main as api_main
from app.brain.autonomy_observer import collect_local_autonomy_state
from app.brain.service import build_brain_overview, collect_recent_runs, decide_next_action


def _manifest(root: Path, name: str, status: str, *, failure=None, stages=None):
    run = root / name
    run.mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps({
        "run_id": name, "topic": "Test topic", "status": status,
        "started_at": "2026-11-15T00:00:00+00:00", "finished_at": None,
        "stages": stages or [], "artifacts": {}, "failure": failure,
        "secret_token": "must-never-be-returned",
    }), encoding="utf-8")
    return run


def _autonomy_db(path: Path):
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE tasks (
                task_id TEXT PRIMARY KEY, task_type TEXT, status TEXT,
                attempts INTEGER, max_attempts INTEGER, updated_at TEXT,
                error_code TEXT, lease_until TEXT, payload_json TEXT
            );
            CREATE TABLE worker_heartbeats (
                worker_id TEXT PRIMARY KEY, hostname TEXT, pid INTEGER,
                state TEXT, started_at TEXT, heartbeat_at TEXT
            );
        """)
        db.execute(
            "INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)",
            ("task-failed", "render", "failed", 3, 3, "2026-11-15T00:00:00+00:00",
             "renderer_error", None, '{"secret":"never expose"}'),
        )
        db.execute(
            "INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)",
            ("task-expired", "research", "running", 1, 3, "2026-11-15T00:00:00+00:00",
             None, "2000-01-01T00:00:00+00:00", "{}"),
        )
        db.execute(
            "INSERT INTO worker_heartbeats VALUES(?,?,?,?,?,?)",
            ("worker-old", "private-hostname", 12345, "working",
             "2026-11-14T00:00:00+00:00", "2000-01-01T00:00:00+00:00"),
        )


def test_brain_context_loads_owner_project_direction():
    overview = build_brain_overview(runs_root=Path("/nonexistent-nextdecode-runs"))
    assert overview["mode"] == "deterministic_read_only"
    assert overview["project"]["name"] == "NEXTDECODE"
    assert overview["authority"]["ai_agents"] == "future_extension"
    assert overview["guardrails"]["public_auto_publishing"] is False


def test_brain_reads_only_bounded_manifest_fields_and_recommends_failed_run(tmp_path):
    _manifest(
        tmp_path, "failed-run", "failed",
        failure={"stage": "render", "error_type": "RuntimeError",
                 "error_category": "render", "secret": "x"},
        stages=[{"name": "render", "status": "failed"}],
    )
    runs = collect_recent_runs(tmp_path)
    assert len(runs) == 1
    assert "secret_token" not in json.dumps(runs)
    assert '"secret"' not in json.dumps(runs)
    decision = decide_next_action(runs)
    assert decision["action"] == "diagnose_failed_run"
    assert decision["evidence"][0]["stage"] == "render"
    assert decision["authority"] == "recommendation_only"


def test_brain_recommends_liveness_check_for_in_progress_run(tmp_path):
    _manifest(tmp_path, "running", "in_progress", stages=[{"name": "voice", "status": "in_progress"}])
    overview = build_brain_overview(runs_root=tmp_path, autonomy_db_path=tmp_path / "missing.sqlite3")
    assert overview["next_action"]["action"] == "verify_run_liveness"


def test_brain_recommends_human_review_for_completed_run(tmp_path):
    _manifest(tmp_path, "done", "ok")
    assert build_brain_overview(runs_root=tmp_path, autonomy_db_path=tmp_path / "missing.sqlite3")["next_action"]["action"] == "review_completed_video"


def test_brain_skips_symlinked_and_malformed_manifests(tmp_path):
    _manifest(tmp_path, "valid", "failed")
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "manifest.json").write_text("{", encoding="utf-8")
    external = tmp_path / "external.json"
    external.write_text(json.dumps({"run_id": "linked", "status": "failed"}), encoding="utf-8")
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "manifest.json").symlink_to(external)
    runs = collect_recent_runs(tmp_path)
    assert [item["run_id"] for item in runs] == ["valid"]


def test_autonomy_observer_is_read_only_and_sanitizes_operational_state(tmp_path):
    database = tmp_path / "tasks.sqlite3"
    _autonomy_db(database)
    before = database.read_bytes()
    state = collect_local_autonomy_state(database_path=database)
    after = database.read_bytes()
    assert before == after
    assert state["available"] is True
    assert state["authority"] == "non_canonical_operational_observation"
    assert state["queue_counts"] == {"failed": 1, "running": 1}
    assert state["expired_running_leases"] == 1
    assert state["stale_workers"] == 1
    serialized = json.dumps(state)
    assert "private-hostname" not in serialized
    assert "12345" not in serialized
    assert "payload_json" not in serialized
    assert "never expose" not in serialized


def test_brain_integrates_queue_and_worker_signals_without_mutation(tmp_path):
    database = tmp_path / "tasks.sqlite3"
    _autonomy_db(database)
    overview = build_brain_overview(
        runs_root=tmp_path / "no-runs", autonomy_db_path=database
    )
    assert overview["operations"]["available"] is True
    assert overview["next_action"]["action"] == "inspect_expired_task_leases"
    assert overview["next_action"]["authority"] == "recommendation_only"


def test_pipeline_failure_has_priority_over_local_queue_signals(tmp_path):
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    _manifest(runs_root, "failed-run", "failed", failure={"stage": "render"})
    database = tmp_path / "tasks.sqlite3"
    _autonomy_db(database)
    overview = build_brain_overview(runs_root=runs_root, autonomy_db_path=database)
    assert overview["next_action"]["action"] == "diagnose_failed_run"


def test_autonomy_observer_does_not_create_missing_database(tmp_path):
    missing = tmp_path / "missing.sqlite3"
    state = collect_local_autonomy_state(database_path=missing)
    assert state["available"] is False
    assert missing.exists() is False


def test_autonomy_observer_fails_closed_for_unqualified_postgres(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured-but-not-opened")
    state = collect_local_autonomy_state()
    assert state["available"] is False
    assert state["backend"] == "postgresql"
    assert state["reason"] == "postgres_read_only_observer_not_implemented"
    assert "configured-but-not-opened" not in json.dumps(state)


def test_autonomy_observer_rejects_symlink_database(tmp_path):
    database = tmp_path / "real.sqlite3"
    _autonomy_db(database)
    link = tmp_path / "linked.sqlite3"
    link.symlink_to(database)
    state = collect_local_autonomy_state(database_path=link)
    assert state["available"] is False
    assert state["reason"] == "local_database_missing_or_unsafe"


def test_brain_api_is_authenticated_and_read_only(tmp_path, monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "brain-test-key")
    monkeypatch.setattr(
        "app.brain.api.build_brain_overview",
        lambda **kwargs: build_brain_overview(
            runs_root=tmp_path, autonomy_db_path=tmp_path / "missing.sqlite3", **kwargs
        ),
    )
    client = TestClient(api_main.app)
    assert client.get("/brain/overview").status_code == 401
    headers = {"Authorization": "Bearer brain-test-key"}
    response = client.get("/brain/overview", headers=headers)
    assert response.status_code == 200
    assert response.json()["brain_version"] == "nextdecode.brain.deterministic.v1"
    assert client.get("/brain/context", headers=headers).status_code == 200
    assert client.get("/brain/operations", headers=headers).status_code == 200
    assert client.get("/brain/decision", headers=headers).status_code == 200
    assert client.post("/brain/decision", headers=headers).status_code == 405
