from __future__ import annotations
import json
import threading
import uuid
from pathlib import Path
import pytest
from app.autonomy.models import TaskRequest, TaskResult
from app.autonomy.registry import Capability, CapabilityRegistry
from app.autonomy.store import TaskStore
from app.autonomy.worker import TaskWorker

def test_task_contract_rejects_unknown_schema_and_bad_limits():
    with pytest.raises(ValueError):
        TaskRequest("x", schema_version="nextdecode.task.v0")
    with pytest.raises(ValueError):
        TaskRequest("x", max_attempts=0)

def test_enqueue_idempotency_and_priority(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    first = store.enqueue(TaskRequest("test.echo", {"v": 1}, idempotency_key="same"))
    second = store.enqueue(TaskRequest("test.echo", {"v": 1}, idempotency_key="same"))
    assert first["task_id"] == second["task_id"]
    assert json.loads(second["payload_json"]) == {"v": 1}
    with pytest.raises(ValueError, match="idempotency_key_conflict"):
        store.enqueue(TaskRequest("test.echo", {"v": 2}, idempotency_key="same"))

def test_worker_claim_execute_and_persist_evidence(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    registry = CapabilityRegistry()
    registry.register(Capability("test.echo", "test", "zero-default", "MIT",
        lambda request: TaskResult("succeeded", {"echo": request.payload}, evidence={"verified": True})))
    task = store.enqueue(TaskRequest("test.echo", {"hello": "world"}))
    assert TaskWorker(store, registry, "worker-a").run_once()
    final = store.get(task["task_id"])
    assert final["status"] == "succeeded"
    evidence = json.loads(final["result_json"])["evidence"]
    assert evidence["verified"] is True
    assert len(evidence["run_id"]) == 32
    assert evidence["worker_id"] == "worker-a"
    assert evidence["evaluation"]["accepted"] is True
    assert [e["event"] for e in store.events(task["task_id"])] == ["queued", "claimed", "succeeded"]

def test_retryable_failure_requeues_until_attempt_limit(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    registry = CapabilityRegistry()
    registry.register(Capability("test.retry", "test", "zero-default", "MIT",
        lambda request: TaskResult("failed", error_code="temporary", retryable=True)))
    task = store.enqueue(TaskRequest("test.retry", max_attempts=2))
    worker = TaskWorker(store, registry, "worker-a")
    assert worker.run_once()
    assert store.get(task["task_id"])["status"] == "queued"
    # Retry backoff is deliberate; move the retry eligibility clock forward in this test.
    with store._connect() as db:
        db.execute("UPDATE tasks SET not_before='2000-01-01T00:00:00+00:00' WHERE task_id=?",
                   (task["task_id"],))
    assert worker.run_once()
    final = store.get(task["task_id"])
    assert final["status"] == "failed"
    assert final["attempts"] == 2

def test_unknown_capability_is_blocked_not_executed(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    task = store.enqueue(TaskRequest("arbitrary.shell", {"command": "touch /tmp/unsafe"}))
    assert TaskWorker(store, CapabilityRegistry(), "worker-a").run_once()
    assert store.get(task["task_id"])["status"] == "blocked"

def test_stale_worker_cannot_finish_claimed_task(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    task = store.enqueue(TaskRequest("test.echo"))
    store.claim("worker-a")
    with pytest.raises(RuntimeError):
        store.finish(task["task_id"], "worker-b", TaskResult("succeeded"))


def test_generation_capability_blocks_non_dry_run_before_process_start(monkeypatch):
    from app.autonomy.tasks import generate_short
    from app.autonomy.models import TaskRequest
    import app.autonomy.tasks as task_module
    monkeypatch.setattr(task_module, "run_sandboxed", lambda *args, **kwargs: pytest.fail("sandbox must not start"))
    result = generate_short(TaskRequest("content.short.generate", {"topic": "x", "dry_run": False}))
    assert result.status == "blocked"
    assert result.error_code == "non_dry_run_requires_separate_authorization"


def test_task_payload_rejects_secret_fields_recursively():
    with pytest.raises(ValueError, match="sensitive field"):
        TaskRequest("test", {"nested": [{"api_key": "not-allowed"}]})

def test_execution_output_redacts_common_secret_shapes():
    from app.autonomy.tasks import _redact_output
    text = _redact_output("Authorization: Bearer abc.def_123 api_key=secret-value sk-1234567890")
    assert "abc.def_123" not in text
    assert "secret-value" not in text
    assert "sk-1234567890" not in text
    assert "[REDACTED]" in text



def test_sandbox_command_is_allowlisted_credential_masked_and_review_only():
    from app.autonomy.sandbox import build_bwrap_command

    command = build_bwrap_command(
        "app.autonomy.specialist_cli", ["--help"], network_access=False
    )
    assert command[0].endswith("bwrap")
    assert "--unshare-net" in command
    triplets = [command[index:index + 3] for index in range(len(command) - 2)]
    assert ["--ro-bind", "/dev/null", "/workspace/.env"] in triplets or "/workspace/.env" not in command
    assert "--clearenv" in command
    triplets = [command[index:index + 3] for index in range(len(command) - 2)]
    assert ["--setenv", "PUBLISH_MODE", "review"] in triplets
    assert ["--setenv", "DRY_RUN", "1"] in triplets
    assert ["--setenv", "AUTO_PUBLISH_APPROVED", "false"] in [
        command[index:index + 3] for index in range(len(command) - 2)
    ]
    assert ["--setenv", "AI_GENERATION_PROVIDER", "ollama"] in [
        command[index:index + 3] for index in range(len(command) - 2)
    ]
    assert ["--setenv", "GROQ_API_KEY", ""] in [
        command[index:index + 3] for index in range(len(command) - 2)
    ]
    assert ["--tmpfs", "/workspace/data"] in [
        command[index:index + 2] for index in range(len(command) - 1)
    ]
    assert ["--tmpfs", "/workspace/outputs"] in [
        command[index:index + 2] for index in range(len(command) - 1)
    ]
    assert ["--bind", str(Path(__file__).resolve().parents[1] / "outputs" / "autonomy" / "artifacts"),
            "/workspace/outputs/autonomy/artifacts"] == command[
                command.index("--bind"):command.index("--bind") + 3
            ]
    with pytest.raises(ValueError, match="allow-listed"):
        build_bwrap_command("shell.exec", ["-c", "unsafe"], network_access=True)


def test_autonomy_mode_overrides_dotenv_provider_preferences(monkeypatch):
    from app.providers import multi_model_ai

    monkeypatch.setenv("NEXTDECODE_AUTONOMY_MODE", "1")
    monkeypatch.setenv("AI_GENERATION_PROVIDER", "gemini")
    monkeypatch.setenv("AI_PROVIDER_CHAIN", "gemini,groq")
    monkeypatch.setattr(multi_model_ai, "_exhausted_providers", set())
    monkeypatch.setattr(
        multi_model_ai, "call_ollama",
        lambda *args, **kwargs: '{"provider":"ollama"}',
    )
    monkeypatch.setattr(
        multi_model_ai, "call_gemini",
        lambda *args, **kwargs: pytest.fail("hosted Gemini must not be called"),
    )
    monkeypatch.setattr(
        multi_model_ai, "call_groq",
        lambda *args, **kwargs: pytest.fail("hosted Groq must not be called"),
    )

    assert multi_model_ai._provider_order() == ["ollama"]
    assert multi_model_ai.generate_json("test", temperature=0, timeout=1) == {
        "provider": "ollama"
    }



def test_worker_recovers_from_transient_sqlite_database_open_failure(tmp_path, monkeypatch):
    import sqlite3
    from app.autonomy.worker import TaskWorker
    import app.autonomy.worker as worker_module

    worker = TaskWorker(TaskStore(tmp_path / "tasks.db"), worker_id="recovery-worker")
    stop = threading.Event()
    calls = {"count": 0}
    delays = []

    def flaky_run_once():
        calls["count"] += 1
        if calls["count"] <= 3:
            raise sqlite3.OperationalError("unable to open database file")
        return False

    def fake_sleep(seconds):
        delays.append(seconds)
        if len(delays) == 4:
            stop.set()

    monkeypatch.setattr(worker, "run_once", flaky_run_once)
    monkeypatch.setattr(worker_module.time, "sleep", fake_sleep)
    worker.serve(poll_seconds=0.1, stop_event=stop)

    assert calls["count"] == 4
    assert delays == [1.0, 2.0, 4.0, 0.1]
    health = worker.store.health()
    assert health["active_workers"] == 0
    assert health["workers"][0]["state"] == "stopped"


def test_worker_does_not_retry_non_transient_sqlite_errors(tmp_path, monkeypatch):
    import sqlite3
    from app.autonomy.worker import TaskWorker

    worker = TaskWorker(TaskStore(tmp_path / "tasks.db"), worker_id="bad-schema-worker")
    monkeypatch.setattr(worker, "run_once",
                        lambda: (_ for _ in ()).throw(sqlite3.OperationalError("no such table: tasks")))

    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        worker.serve()


def test_queue_health_is_read_only_and_reports_counts(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    store.enqueue(TaskRequest("test.echo"))
    before = store.list()
    health = store.health()
    assert health["database_accessible"] is True
    assert health["queue_counts"] == {"queued": 1}
    assert health["total_tasks"] == 1
    assert health["expired_running_leases"] == 0
    assert health["active_workers"] == 0
    assert health["workers"] == []
    assert store.list() == before


def test_worker_health_reports_fresh_and_stale_heartbeats(tmp_path):
    from datetime import datetime, timedelta, timezone

    store = TaskStore(tmp_path / "tasks.db")
    started = datetime.now(timezone.utc).isoformat()
    store.record_worker_heartbeat("worker-fresh", "host-a", 123, "idle", started)
    store.record_worker_heartbeat("worker-stopped", "host-b", 456, "stopped", started)
    with store._connect() as db:
        stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        db.execute("UPDATE worker_heartbeats SET heartbeat_at=? WHERE worker_id='worker-fresh'", (stale,))
    health = store.health(stale_after_seconds=30)
    assert health["active_workers"] == 0
    assert health["stale_workers"] == 1
    assert health["stopped_workers"] == 1
    assert {item["state"] for item in health["workers"]} == {"idle", "stopped"}


def test_dead_letters_returns_all_terminal_failures_but_not_blocked_tasks(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    exhausted = store.enqueue(TaskRequest("test.exhausted", max_attempts=2))
    non_retryable = store.enqueue(TaskRequest("test.non_retryable", max_attempts=3))
    blocked = store.enqueue(TaskRequest("test.blocked"))
    with store._connect() as db:
        db.execute("UPDATE tasks SET status='failed',attempts=2,error_code='final_failure' WHERE task_id=?",
                   (exhausted["task_id"],))
        db.execute("UPDATE tasks SET status='failed',attempts=1,error_code='permanent_failure' WHERE task_id=?",
                   (non_retryable["task_id"],))
        db.execute("UPDATE tasks SET status='blocked',attempts=1,error_code='dependency_failed' WHERE task_id=?",
                   (blocked["task_id"],))
    letters = store.dead_letters()
    assert {item["task_id"] for item in letters} == {exhausted["task_id"], non_retryable["task_id"]}
    assert all(item["status"] == "failed" for item in letters)
    assert len(store.dead_letters(0)) == 1
    assert len(store.dead_letters(10000)) == 2


def test_recursive_dependency_failure_blocks_all_descendants(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
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
    worker_id = "recursive-failure-worker"
    claimed = store.claim(worker_id)
    assert claimed["task_id"] == first
    store.finish(first, worker_id, TaskResult("failed", error_code="root_failure"))
    assert store.claim("no-eligible-task") is None
    assert store.get(second)["status"] == "blocked"
    assert store.get(third)["status"] == "blocked"
    assert store.get_plan(plan_id)["status"] == "failed"
    assert any(event["event"] == "blocked" for event in store.events(third))


def test_worker_passes_successful_dependency_outputs_as_transient_context(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    registry = CapabilityRegistry()
    seen = {}

    def research(_request):
        return TaskResult("succeeded", {"research_id": "source-1", "evidence_count": 3})

    def draft(request):
        seen["dependencies"] = request.context.get("dependencies", [])
        return TaskResult("succeeded", {"drafted": True})

    registry.register(Capability("test.research", "research", "zero-default", "MIT", research))
    registry.register(Capability("test.draft", "draft", "zero-default", "MIT", draft))
    parent, child = uuid.uuid4().hex, uuid.uuid4().hex
    nodes = [
        {"task_id": parent, "step_id": "research", "task_type": "test.research",
         "payload": {}, "depends_on": []},
        {"task_id": child, "step_id": "draft", "task_type": "test.draft",
         "payload": {}, "depends_on": [parent]},
    ]
    store.enqueue_plan(uuid.uuid4().hex, "dependency context", nodes,
                       {"schema_version": "nextdecode.autonomy.plan.v1", "nodes": nodes})
    worker = TaskWorker(store, registry, "dependency-context-worker")
    assert worker.run_once()
    assert worker.run_once()
    assert seen["dependencies"][0]["task_id"] == parent
    assert seen["dependencies"][0]["output"]["research_id"] == "source-1"
    assert "context" not in TaskRequest("test.draft").to_dict()
