from __future__ import annotations

import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import psycopg
from psycopg import sql
import pytest

from app.autonomy.models import TaskRequest, TaskResult
from app.autonomy.postgres_store import PostgresTaskStore
from app.autonomy.store import TaskStore


DSN = os.environ.get("NEXTDECODE_TEST_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="NEXTDECODE_TEST_POSTGRES_DSN is not configured")


@pytest.fixture
def store():
    schema = "autonomy_test_" + uuid.uuid4().hex[:24]
    instance = PostgresTaskStore(DSN, schema=schema)
    try:
        yield instance
    finally:
        with psycopg.connect(DSN) as db:
            db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))


def test_postgres_round_trip_and_idempotency_conflict(store):
    key = "pg-idem-" + uuid.uuid4().hex
    first = store.enqueue(TaskRequest("test.echo", {"message": "hello"}, idempotency_key=key))
    replay = store.enqueue(TaskRequest("test.echo", {"message": "hello"}, idempotency_key=key))
    assert first["task_id"] == replay["task_id"]
    with pytest.raises(ValueError, match="idempotency_key_conflict"):
        store.enqueue(TaskRequest("test.echo", {"message": "different"}, idempotency_key=key))
    worker_id = "pg-worker-" + uuid.uuid4().hex
    claimed = store.claim(worker_id)
    assert claimed is not None
    store.finish(claimed["task_id"], worker_id,
                 TaskResult("succeeded", {"ok": True}, evidence={"run_id": uuid.uuid4().hex}))
    assert store.get(claimed["task_id"])["status"] == "succeeded"


def test_postgres_concurrent_enqueue_same_key_returns_one_task_and_event(store):
    key = "pg-concurrent-idem-" + uuid.uuid4().hex
    barrier = Barrier(12)

    def enqueue_one(_index: int):
        barrier.wait(timeout=10)
        return store.enqueue(TaskRequest(
            "test.concurrent_idempotent", {"shared": "payload"},
            task_id=uuid.uuid4().hex, idempotency_key=key,
        ))

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(enqueue_one, range(12)))

    task_ids = {item["task_id"] for item in results}
    assert len(task_ids) == 1
    task_id = task_ids.pop()
    assert len([event for event in store.events(task_id) if event["event"] == "queued"]) == 1
    assert store.get(task_id)["status"] == "queued"


def test_postgres_concurrent_enqueue_conflicting_payload_has_one_winner(store):
    key = "pg-concurrent-conflict-" + uuid.uuid4().hex
    barrier = Barrier(8)

    def enqueue_conflict(index: int):
        barrier.wait(timeout=10)
        try:
            result = store.enqueue(TaskRequest(
                "test.concurrent_conflict", {"request": index},
                task_id=uuid.uuid4().hex, idempotency_key=key,
            ))
            return ("created", result["task_id"])
        except ValueError as exc:
            return ("conflict", str(exc))

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(enqueue_conflict, range(8)))

    created = [value for kind, value in outcomes if kind == "created"]
    conflicts = [value for kind, value in outcomes if kind == "conflict"]
    assert len(created) == 1
    assert len(conflicts) == 7
    assert set(conflicts) == {"idempotency_key_conflict"}
    assert len([event for event in store.events(created[0]) if event["event"] == "queued"]) == 1


def test_postgres_dag_dependency_context_and_plan_idempotency(store):
    plan_id = uuid.uuid4().hex
    parent_id, child_id = uuid.uuid4().hex, uuid.uuid4().hex
    nodes = [
        {"task_id": parent_id, "step_id": "research", "task_type": "test.research",
         "payload": {"topic": "test"}, "depends_on": [], "priority": 100, "max_attempts": 2},
        {"task_id": child_id, "step_id": "draft", "task_type": "test.draft",
         "payload": {"topic": "test"}, "depends_on": [parent_id], "priority": 100, "max_attempts": 2},
    ]
    plan = {"schema_version": "nextdecode.autonomy.plan.v1", "plan_id": plan_id,
            "human_approval_required": True, "external_actions_allowed": False,
            "nodes": nodes}
    key = "pg-plan-" + uuid.uuid4().hex
    created = store.enqueue_plan(plan_id, "test DAG", nodes, plan, key)
    assert len(created["tasks"]) == 2
    replay = store.enqueue_plan(uuid.uuid4().hex, "test DAG", nodes, plan, key)
    assert replay["plan"]["plan_id"] == plan_id

    parent = store.claim("pg-parent-worker")
    assert parent["task_id"] == parent_id
    store.finish(parent_id, "pg-parent-worker",
                 TaskResult("succeeded", {"artifact_path": "outputs/autonomy/artifacts/test.json"}))
    dependencies = store.dependency_results(child_id)
    assert len(dependencies) == 1
    assert dependencies[0]["task_id"] == parent_id
    child = store.claim("pg-child-worker")
    assert child["task_id"] == child_id

    with pytest.raises(ValueError, match="idempotency_key_conflict"):
        store.enqueue_plan(uuid.uuid4().hex, "different goal", nodes, plan, key)


def test_postgres_concurrent_claims_are_unique(store):
    task_ids = {
        store.enqueue(TaskRequest("test.concurrent", {"n": index}))["task_id"]
        for index in range(12)
    }
    barrier = Barrier(12)

    def claim_one(index: int):
        barrier.wait(timeout=5)
        return store.claim(f"pg-parallel-{index}-{uuid.uuid4().hex}")

    with ThreadPoolExecutor(max_workers=12) as pool:
        claimed = list(pool.map(claim_one, range(12)))
    claimed_ids = [item["task_id"] for item in claimed if item]
    assert len(claimed_ids) == 12
    assert len(set(claimed_ids)) == 12
    assert set(claimed_ids) == task_ids


def test_postgres_recursive_dependency_failure_blocks_all_descendants(store):
    first, second, third = (uuid.uuid4().hex for _ in range(3))
    nodes = [
        {"task_id": first, "step_id": "first", "task_type": "test.one",
         "payload": {}, "depends_on": []},
        {"task_id": second, "step_id": "second", "task_type": "test.two",
         "payload": {}, "depends_on": [first]},
        {"task_id": third, "step_id": "third", "task_type": "test.three",
         "payload": {}, "depends_on": [second]},
    ]
    plan_id = uuid.uuid4().hex
    store.enqueue_plan(plan_id, "recursive failure", nodes,
                       {"schema_version": "nextdecode.autonomy.plan.v1", "nodes": nodes})
    worker_id = "pg-recursive-failure"
    claimed = store.claim(worker_id)
    assert claimed["task_id"] == first
    store.finish(first, worker_id, TaskResult("failed", error_code="root_failure"))
    assert store.claim("pg-no-eligible-task") is None
    assert store.get(second)["status"] == "blocked"
    assert store.get(third)["status"] == "blocked"
    assert store.get_plan(plan_id)["status"] == "failed"
    assert any(event["event"] == "blocked" for event in store.events(third))


def test_postgres_store_runs_task_worker_end_to_end(store):
    from app.autonomy.registry import Capability, CapabilityRegistry
    from app.autonomy.worker import TaskWorker

    registry = CapabilityRegistry()
    registry.register(Capability(
        "test.pg_worker", "Postgres worker test", "zero-default", "MIT",
        lambda request: TaskResult("succeeded", {"echo": request.payload.get("value")}),
    ))
    task = store.enqueue(TaskRequest("test.pg_worker", {"value": "postgres"}))
    worker = TaskWorker(store, registry, "pg-worker-integration")
    assert worker.run_once() is True
    assert store.get(task["task_id"])["status"] == "succeeded"
    assert json.loads(store.get(task["task_id"])["result_json"])["output"]["echo"] == "postgres"
    assert any(event["event"] == "succeeded" for event in store.events(task["task_id"]))


def test_postgres_health_and_dead_letters_are_read_only(store):
    task = store.enqueue(TaskRequest("test.dead", {"reason": "integration"}))
    worker_id = "pg-fail-" + uuid.uuid4().hex
    claimed = store.claim(worker_id)
    assert claimed is not None
    store.finish(claimed["task_id"], worker_id,
                 TaskResult("failed", error_code="integration_failure"))
    health = store.health()
    assert health["database_accessible"] is True
    assert health["total_tasks"] >= 1
    assert any(row["task_id"] == task["task_id"] for row in store.dead_letters())


def test_sqlite_migration_is_non_destructive_and_count_verified(store, tmp_path, monkeypatch):
    from app.autonomy.migrate_sqlite_to_postgres import migrate
    source = tmp_path / "legacy.sqlite3"
    legacy = TaskStore(source)
    task = legacy.enqueue(TaskRequest("test.legacy", {"topic": "legacy"}))
    legacy.record_worker_heartbeat(
        "legacy-worker", "test-host", 1234, "idle", "2026-11-08T00:00:00+00:00"
    )
    monkeypatch.setenv("DATABASE_URL", DSN)
    result = migrate(source, tmp_path / "backups", schema=store.schema)
    assert result["status"] == "verified"
    assert result["source_counts"]["tasks"] == 1
    assert result["target_counts"]["worker_heartbeats"] == 1
    assert result["backup_mode"] == "0o600"
    assert store.get(task["task_id"])["task_type"] == "test.legacy"
    assert store.health()["stopped_workers"] == 1
    assert source.is_file()
    assert legacy.get(task["task_id"])["task_type"] == "test.legacy"


def test_task_store_factory_prefers_postgres_when_configured(monkeypatch, tmp_path):
    from app.autonomy.store import create_task_store
    monkeypatch.setenv("DATABASE_URL", DSN)
    monkeypatch.setenv("NEXTDECODE_TASK_DB", "/tmp/legacy-should-not-win.sqlite3")
    store = create_task_store()
    assert store.backend == "postgresql"
    explicit = create_task_store(tmp_path / "explicit-sqlite-override.sqlite3")
    assert explicit.backend == "sqlite"


def test_authenticated_api_health_uses_postgresql_backend(monkeypatch):
    from fastapi.testclient import TestClient
    from api import main as api_main
    monkeypatch.setenv("DATABASE_URL", DSN)
    monkeypatch.delenv("NEXTDECODE_TASK_DB", raising=False)
    monkeypatch.setenv(api_main.API_KEY_ENV, "postgres-api-test-key")
    client = TestClient(api_main.app)
    response = client.get("/autonomy/health", headers={
        "Authorization": "Bearer postgres-api-test-key"
    })
    assert response.status_code == 200
    assert response.json()["database"] == "postgresql"
    assert response.json()["database_accessible"] is True

