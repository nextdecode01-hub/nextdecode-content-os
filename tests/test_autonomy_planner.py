from __future__ import annotations
import json
import pytest
from app.autonomy.models import TaskResult
from app.autonomy.planner import TaskPlanner
from app.autonomy.registry import Capability, CapabilityRegistry
from app.autonomy.store import TaskStore
from app.autonomy.worker import TaskWorker

def _registry():
    registry = CapabilityRegistry()
    registry.register(Capability("step.first", "first", "zero-default", "MIT",
        lambda request: TaskResult("succeeded", {"step": "first"})))
    registry.register(Capability("step.second", "second", "zero-default", "MIT",
        lambda request: TaskResult("succeeded", {"step": "second"})))
    return registry

def test_plan_dependencies_are_respected_and_plan_completes(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    first, second = "a" * 32, "b" * 32
    store.enqueue_plan("p1", "test goal", [
        {"task_id": first, "task_type": "step.first", "payload": {}, "depends_on": []},
        {"task_id": second, "task_type": "step.second", "payload": {}, "depends_on": [first]},
    ], {"schema_version": "nextdecode.autonomy.plan.v1"})
    worker = TaskWorker(store, _registry(), "dag-worker")
    claimed = store.claim("other-worker")
    assert claimed["task_id"] == first
    assert store.claim("other-worker") is None
    store.finish(first, "other-worker", TaskResult("succeeded", {"ok": True}))
    assert worker.run_once()
    plan = store.get_plan("p1")
    assert plan["status"] == "succeeded"
    assert plan["plan"]["status"] == "succeeded"
    assert [task["status"] for task in plan["tasks"]] == ["succeeded", "succeeded"]

def test_failed_dependency_blocks_descendant(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    first, second = "c" * 32, "d" * 32
    store.enqueue_plan("p2", "blocked goal", [
        {"task_id": first, "task_type": "step.first", "payload": {}, "depends_on": []},
        {"task_id": second, "task_type": "step.second", "payload": {}, "depends_on": [first]},
    ], {"schema_version": "nextdecode.autonomy.plan.v1"})
    claimed = store.claim("worker")
    store.finish(first, "worker", TaskResult("failed", error_code="expected_failure"))
    assert store.claim("worker") is None
    assert store.get(second)["status"] == "blocked"
    assert store.get_plan("p2")["status"] == "failed"

def test_planner_only_emits_registered_nonpublishing_capabilities(tmp_path):
    planner = TaskPlanner(TaskStore(tmp_path / "tasks.db"))
    decision = planner.propose("Create a YouTube Short about AI agents")
    assert decision.accepted
    assert decision.plan["schema_version"] == "nextdecode.autonomy.plan.v1"
    assert [node["task_type"] for node in decision.plan["nodes"]] == [
        "research.topic.collect", "content.short.script.draft"
    ]
    assert decision.plan["nodes"][1]["depends_on"] == [decision.plan["nodes"][0]["task_id"]]
    assert decision.plan["external_actions_allowed"] is False
    assert decision.plan["human_approval_required"] is True

def test_planner_rejects_publication_and_unsupported_requests(tmp_path):
    planner = TaskPlanner(TaskStore(tmp_path / "tasks.db"))
    assert not planner.propose("Publish a video to YouTube").accepted
    research = planner.propose("Research latest AI news")
    assert research.accepted
    assert [node["task_type"] for node in research.plan["nodes"]] == ["research.topic.collect"]
    assert not planner.propose("").accepted


def test_plan_idempotency_replays_identical_request_and_rejects_conflict(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    planner = TaskPlanner(store)
    first = planner.propose("Create a short about AI", idempotency_key="same-plan")
    second = planner.propose("Create a short about AI", idempotency_key="same-plan")
    assert first.accepted and second.accepted
    assert first.plan_id == second.plan_id
    conflict = planner.propose("Create a short about robotics", idempotency_key="same-plan")
    assert not conflict.accepted
    assert conflict.reason == "idempotency_key_conflict"


def test_plan_store_rejects_dependency_cycles_atomically(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    with pytest.raises(ValueError, match="cycle"):
        store.enqueue_plan("cycle", "bad graph", [
            {"task_id": "e" * 32, "task_type": "step.first", "depends_on": ["f" * 32]},
            {"task_id": "f" * 32, "task_type": "step.second", "depends_on": ["e" * 32]},
        ], {"schema_version": "nextdecode.autonomy.plan.v1"})
    assert store.get_plan("cycle") is None
    assert store.list() == []


def test_planner_refuses_non_dry_run(tmp_path):
    decision = TaskPlanner(TaskStore(tmp_path / "tasks.db")).propose(
        "Create a YouTube Short about AI", dry_run=False)
    assert not decision.accepted
    assert decision.reason == "non_dry_run_requires_separate_authorization"


def test_planner_rejects_non_string_topic_without_crashing(tmp_path):
    decision = TaskPlanner(TaskStore(tmp_path / "tasks.db")).propose(
        "Create a YouTube Short", topic={"secret": "bad"})
    assert not decision.accepted
    assert decision.reason == "topic_must_be_a_string"


def test_planner_validates_idempotency_key_type_and_length(tmp_path):
    planner = TaskPlanner(TaskStore(tmp_path / "tasks.db"))
    assert planner.propose("Create a short about AI", idempotency_key=123).reason == "invalid_idempotency_key"
    assert planner.propose("Create a short about AI", idempotency_key="x" * 201).reason == "invalid_idempotency_key"



def test_failed_branch_does_not_mark_plan_terminal_while_independent_work_is_queued(tmp_path):
    store = TaskStore(tmp_path / "tasks.db")
    failed, independent, descendant = "1" * 32, "2" * 32, "3" * 32
    store.enqueue_plan("p3", "mixed outcome", [
        {"task_id": failed, "task_type": "step.first", "payload": {}, "depends_on": []},
        {"task_id": independent, "task_type": "step.second", "payload": {}, "depends_on": []},
        {"task_id": descendant, "task_type": "step.second", "payload": {}, "depends_on": [failed]},
    ], {"schema_version": "nextdecode.autonomy.plan.v1"})

    first = store.claim("worker")
    assert first["task_id"] == failed
    store.finish(failed, "worker", TaskResult("failed", error_code="expected_failure"))

    in_progress = store.get_plan("p3")
    assert in_progress["status"] == "queued"
    assert in_progress["plan"]["status"] == "queued"

    second = store.claim("worker")
    assert second["task_id"] == independent
    store.finish(independent, "worker", TaskResult("succeeded", {"ok": True}))
    assert store.claim("worker") is None  # propagates the failed prerequisite to its child

    terminal = store.get_plan("p3")
    assert terminal["status"] == "failed"
    assert terminal["plan"]["status"] == "failed"
    states = {task["task_id"]: task["status"] for task in terminal["tasks"]}
    assert states == {failed: "failed", independent: "succeeded", descendant: "blocked"}



def test_planner_uses_local_classifier_only_to_select_registered_generation_capability(tmp_path, monkeypatch):
    import app.autonomy.local_planner as local_planner

    monkeypatch.setattr(local_planner, "classify_goal",
                        lambda _goal: ("content.longform.script.draft", "test-local-model"))
    decision = TaskPlanner(TaskStore(tmp_path / "tasks.db")).propose(
        "Make an explainer about AI agents")

    assert decision.accepted
    assert decision.plan["nodes"][0]["task_type"] == "research.topic.collect"
    assert decision.plan["nodes"][1]["task_type"] == "content.longform.script.draft"
    assert decision.plan["human_approval_required"] is True
    assert decision.plan["external_actions_allowed"] is False


def test_planner_falls_back_to_deterministic_routing_when_local_model_unavailable(tmp_path, monkeypatch):
    import app.autonomy.local_planner as local_planner

    def unavailable(_goal):
        raise local_planner.LocalPlannerUnavailable("offline")

    monkeypatch.setattr(local_planner, "classify_goal", unavailable)
    decision = TaskPlanner(TaskStore(tmp_path / "tasks.db")).propose(
        "Create a YouTube Short about local AI")

    assert decision.accepted
    assert decision.plan["nodes"][1]["task_type"] == "content.short.script.draft"


def test_planner_ignores_local_classifier_output_outside_registered_allowlist(tmp_path, monkeypatch):
    import app.autonomy.local_planner as local_planner

    monkeypatch.setattr(local_planner, "classify_goal",
                        lambda _goal: ("shell.exec", "unsafe-test-model"))
    decision = TaskPlanner(TaskStore(tmp_path / "tasks.db")).propose(
        "Create an explainer video about AI")

    assert not decision.accepted
    assert decision.reason == "unsupported_goal_needs_specialist_or_clarification"


def test_research_only_goal_is_supported_without_calling_media_classifier(tmp_path, monkeypatch):
    import app.autonomy.local_planner as local_planner

    monkeypatch.setattr(local_planner, "classify_goal",
                        lambda _goal: pytest.fail("research-only goal must not reach media planner"))
    decision = TaskPlanner(TaskStore(tmp_path / "tasks.db")).propose("Research latest AI news")

    assert decision.accepted
    assert [node["task_type"] for node in decision.plan["nodes"]] == ["research.topic.collect"]


def test_complex_workflow_uses_strict_local_model_plan_and_validates_it(tmp_path, monkeypatch):
    import app.autonomy.local_planner as local_planner

    proposal = {
        "summary": "Research first, then draft a Short",
        "nodes": [
            {"step_id": "research", "task_type": "research.topic.collect",
             "payload": {"topic": "AI", "max_sources": 3}, "depends_on": []},
            {"step_id": "draft", "task_type": "content.short.script.draft",
             "payload": {"topic": "AI"}, "depends_on": ["research"]},
        ],
    }
    monkeypatch.setattr(local_planner, "propose_plan",
                        lambda _goal, _caps: (proposal, "test-model"))
    decision = TaskPlanner(TaskStore(tmp_path / "tasks.db")).propose(
        "Create a multi-step workflow about AI"
    )
    assert decision.accepted
    assert decision.plan["intent"] == "local_model_validated_dag"
    assert decision.plan["nodes"][1]["depends_on"] == [decision.plan["nodes"][0]["task_id"]]


def test_complex_workflow_rejects_model_invented_shell_capability(tmp_path, monkeypatch):
    import app.autonomy.local_planner as local_planner

    monkeypatch.setattr(local_planner, "propose_plan", lambda *_: ({
        "summary": "Unsafe",
        "nodes": [{"step_id": "run", "task_type": "shell.exec",
                   "payload": {"command": "whoami"}, "depends_on": []}],
    }, "test-model"))
    decision = TaskPlanner(TaskStore(tmp_path / "tasks.db")).propose(
        "Create a multi-step workflow about AI"
    )
    assert not decision.accepted
    assert decision.reason == "unsupported plan capability"
