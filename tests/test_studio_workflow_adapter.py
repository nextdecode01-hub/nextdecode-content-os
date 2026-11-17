from __future__ import annotations

import hashlib
import json

import pytest

from app.autonomy.models import TaskResult
from app.autonomy.planner import TaskPlanner
from app.autonomy.registry import Capability, CapabilityRegistry
from app.autonomy.store import TaskStore
from app.autonomy.studio_workflow import propose_studio_workflow


def _studio_fixture():
    snapshot = {
        "schema": "nextdecode.studio.storyboard.v1",
        "title": "AI Accelerates Research?",
        "beats": [
            {"id": 1, "name": "Hook", "start": 0, "end": 4,
             "kind": "Kinetic typography", "description": "Open with a sharp question.",
             "caption": "Does AI speed up research?"},
            {"id": 2, "name": "Evidence", "start": 4, "end": 11,
             "kind": "B-roll", "description": "Show evidence cards.",
             "caption": "Evidence before conclusions."},
        ],
    }
    digest = hashlib.sha256(
        json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "goal": "Create a YouTube Short about AI agents",
        "studio_version_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "studio_content_sha256": digest,
        "studio_snapshot": snapshot,
    }


def _planner(tmp_path):
    registry = CapabilityRegistry()
    registry.register(Capability(
        "research.topic.collect", "research", "zero-default", "MIT",
        lambda request: TaskResult("succeeded", {"ok": True}),
    ))
    registry.register(Capability(
        "content.short.script.draft", "script", "zero-default", "MIT",
        lambda request: TaskResult("succeeded", {"ok": True}),
    ))
    return TaskPlanner(TaskStore(tmp_path / "tasks.db"), registry=registry)


def test_api_adapter_builds_verified_studio_research_script_plan(tmp_path):
    result = propose_studio_workflow(_studio_fixture(), _planner(tmp_path))
    research, script = result["plan"]["nodes"]
    assert research["payload"]["studio_snapshot"] == _studio_fixture()["studio_snapshot"]
    assert research["payload"]["studio_content_sha256"] == _studio_fixture()["studio_content_sha256"]
    assert script["payload"]["studio_version_id"] == _studio_fixture()["studio_version_id"]
    assert script["payload"]["studio_content_sha256"] == _studio_fixture()["studio_content_sha256"]
    assert script["depends_on"] == [research["task_id"]]
    assert result["plan"]["human_approval_required"] is True
    assert result["plan"]["external_actions_allowed"] is False


@pytest.mark.parametrize("mutation", [
    lambda body: body.update(studio_content_sha256="b" * 64),
    lambda body: body.pop("studio_snapshot"),
    lambda body: body.update(unexpected="field"),
    lambda body: body.update(dry_run=False),
])
def test_api_adapter_fails_closed_for_invalid_studio_plan_requests(tmp_path, mutation):
    body = _studio_fixture()
    mutation(body)
    with pytest.raises(ValueError):
        propose_studio_workflow(body, _planner(tmp_path))
    assert _planner(tmp_path).store.list() == []


def test_api_adapter_requires_authenticated_caller_to_supply_full_contract():
    # Authentication is deliberately not implemented here: the HTTP route owns it.
    with pytest.raises(ValueError, match="requires goal, version ID, digest and snapshot"):
        propose_studio_workflow({"goal": "Create a Short"}, object())

 

def test_studio_plan_runs_through_real_worker_loop_with_provenance(tmp_path, monkeypatch):
    from app.autonomy import tasks
    from app.autonomy.models import TaskResult
    from app.autonomy.worker import TaskWorker
    from app.autonomy import evaluator

    monkeypatch.setattr(evaluator, "evaluate_result", lambda result: (True, None, {"accepted": True}))
    fixture = _studio_fixture()
    planner = _planner(tmp_path)
    result = propose_studio_workflow(fixture, planner)
    store = planner.store
    registry = CapabilityRegistry()
    registry.register(Capability(
        "research.topic.collect", "offline research fixture", "zero-default", "MIT",
        tasks.research_topic_collect, payload_validator=tasks.validate_topic_payload,
    ))
    registry.register(Capability(
        "content.short.script.draft", "offline script fixture", "zero-default", "MIT",
        tasks.short_script_draft, payload_validator=tasks.validate_script_payload,
    ))
    worker = TaskWorker(store, registry=registry, worker_id="studio-integration-worker")
    invocations = []

    def fake_module(module, args, **kwargs):
        invocations.append((module, list(args)))
        if args[0] == "research":
            return TaskResult("succeeded", {
                "artifact_path": str(tmp_path / "research.json"),
                "artifact_sha256": "d" * 64,
                "studio_version_id": fixture["studio_version_id"],
                "studio_content_sha256": fixture["studio_content_sha256"],
            }, evidence={"artifact_envelope_verified": True})
        return TaskResult("succeeded", {
            "artifact_path": str(tmp_path / "script.json"),
            "studio_version_id": fixture["studio_version_id"],
            "studio_content_sha256": fixture["studio_content_sha256"],
        })

    monkeypatch.setattr(tasks, "_run_module", fake_module)
    assert worker.run_once() is True
    assert worker.run_once() is True
    assert worker.run_once() is False

    completed = store.get_plan(result["plan_id"])
    assert completed["status"] == "succeeded"
    assert [task["status"] for task in completed["tasks"]] == ["succeeded", "succeeded"]
    assert len(invocations) == 2
    script_args = invocations[1][1]
    assert "--research-artifact" in script_args
    assert "--research-sha256" in script_args
    assert "--studio-version-id" in script_args
    assert "--studio-content-sha256" in script_args
    for task in completed["tasks"]:
        events = [event["event"] for event in store.events(task["task_id"])]
        assert events[0] == "queued"
        assert "claimed" in events
        assert events[-1] == "succeeded"


def test_studio_worker_blocks_script_when_research_provenance_is_mismatched(tmp_path, monkeypatch):
    from app.autonomy import tasks
    from app.autonomy.models import TaskResult
    from app.autonomy.worker import TaskWorker
    from app.autonomy import evaluator

    monkeypatch.setattr(evaluator, "evaluate_result", lambda result: (True, None, {"accepted": True}))
    fixture = _studio_fixture()
    planner = _planner(tmp_path)
    result = propose_studio_workflow(fixture, planner)
    store = planner.store
    registry = CapabilityRegistry()
    registry.register(Capability(
        "research.topic.collect", "mismatched research fixture", "zero-default", "MIT",
        tasks.research_topic_collect, payload_validator=tasks.validate_topic_payload,
    ))
    registry.register(Capability(
        "content.short.script.draft", "script fixture", "zero-default", "MIT",
        tasks.short_script_draft, payload_validator=tasks.validate_script_payload,
    ))
    worker = TaskWorker(store, registry=registry, worker_id="studio-mismatch-worker")

    monkeypatch.setattr(tasks, "_run_module", lambda *args, **kwargs: TaskResult(
        "succeeded", {
            "artifact_path": str(tmp_path / "research.json"),
            "artifact_sha256": "d" * 64,
            "studio_version_id": fixture["studio_version_id"],
            "studio_content_sha256": "0" * 64,
        },
        evidence={"artifact_envelope_verified": True},
    ))
    assert worker.run_once() is True
    assert worker.run_once() is False

    completed = store.get_plan(result["plan_id"])
    statuses = {task["task_type"]: task["status"] for task in completed["tasks"]}
    errors = {task["task_type"]: task["error_code"] for task in completed["tasks"]}
    assert statuses["research.topic.collect"] == "failed"
    assert errors["research.topic.collect"] == "studio_artifact_provenance_mismatch"
    assert statuses["content.short.script.draft"] == "blocked"
    assert errors["content.short.script.draft"] == "dependency_failed"
    assert completed["status"] == "failed"
def test_studio_plan_idempotency_replays_same_version_without_duplicate_tasks(tmp_path):
    planner = _planner(tmp_path)
    body = _studio_fixture()
    body["idempotency_key"] = "studio-version-submit-001"

    first = propose_studio_workflow(body, planner)
    second = propose_studio_workflow(body, planner)

    assert first["plan_id"] == second["plan_id"]
    assert first["plan"]["plan_id"] == second["plan"]["plan_id"]
    assert len(planner.store.list()) == 2
    assert len(planner.store.get_plan(first["plan_id"])["tasks"]) == 2


def test_studio_plan_idempotency_rejects_same_key_for_different_version(tmp_path):
    planner = _planner(tmp_path)
    first_body = _studio_fixture()
    first_body["idempotency_key"] = "studio-version-submit-002"
    first = propose_studio_workflow(first_body, planner)

    changed_body = _studio_fixture()
    changed_body["idempotency_key"] = "studio-version-submit-002"
    changed_body["studio_version_id"] = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    with pytest.raises(ValueError, match="idempotency_key_conflict"):
        propose_studio_workflow(changed_body, planner)

    assert len(planner.store.list()) == 2
    assert planner.store.get_plan(first["plan_id"])["status"] == "queued"
