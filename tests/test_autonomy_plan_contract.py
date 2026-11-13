import pytest

from app.autonomy.plan_contract import PlanValidationError, validate_plan_nodes
from app.autonomy.registry import build_default_registry
from app.autonomy.models import TaskRequest


def _proposal(nodes):
    return {"summary": "Research then draft a script", "nodes": nodes}


def test_plan_contract_topologically_orders_and_maps_dependency_ids():
    nodes = validate_plan_nodes(_proposal([
        {"step_id": "draft", "task_type": "content.short.script.draft",
         "payload": {"topic": "AI"}, "depends_on": ["research"]},
        {"step_id": "research", "task_type": "research.topic.collect",
         "payload": {"topic": "AI", "max_sources": 3}, "depends_on": []},
    ]), build_default_registry())
    assert [node["step_id"] for node in nodes] == ["research", "draft"]
    assert nodes[1]["depends_on"] == [nodes[0]["task_id"]]
    assert len(nodes[0]["task_id"]) == 32


def test_plan_contract_rejects_unregistered_or_non_planner_capabilities():
    with pytest.raises(PlanValidationError, match="exactly one upstream research"):
        validate_plan_nodes(_proposal([
            {"step_id": "draft", "task_type": "content.short.script.draft",
             "payload": {"topic": "AI"}, "depends_on": []}
        ]), build_default_registry())
    with pytest.raises(PlanValidationError, match="unsupported plan capability"):
        validate_plan_nodes(_proposal([
            {"step_id": "shell", "task_type": "shell.exec", "payload": {}, "depends_on": []}
        ]), build_default_registry())
    with pytest.raises(PlanValidationError, match="not available to the planner"):
        validate_plan_nodes(_proposal([
            {"step_id": "render", "task_type": "content.short.generate",
             "payload": {"topic": "AI", "dry_run": True}, "depends_on": []}
        ]), build_default_registry())


def test_plan_contract_rejects_duplicate_missing_and_cyclic_dependencies():
    registry = build_default_registry()
    with pytest.raises(PlanValidationError, match="duplicate plan step_id"):
        validate_plan_nodes(_proposal([
            {"step_id": "research", "task_type": "research.topic.collect",
             "payload": {"topic": "AI"}, "depends_on": []},
            {"step_id": "research", "task_type": "research.topic.collect",
             "payload": {"topic": "AI"}, "depends_on": []},
        ]), registry)
    with pytest.raises(PlanValidationError, match="unknown step"):
        validate_plan_nodes(_proposal([
            {"step_id": "draft", "task_type": "content.short.script.draft",
             "payload": {"topic": "AI"}, "depends_on": ["missing"]},
        ]), registry)
    with pytest.raises(PlanValidationError, match="cycle"):
        validate_plan_nodes(_proposal([
            {"step_id": "a", "task_type": "research.topic.collect",
             "payload": {"topic": "AI"}, "depends_on": ["b"]},
            {"step_id": "b", "task_type": "research.topic.collect",
             "payload": {"topic": "AI"}, "depends_on": ["a"]},
        ]), registry)


def test_plan_contract_bounds_node_count_payload_and_attempts():
    registry = build_default_registry()
    too_many = [
        {"step_id": f"r{i}", "task_type": "research.topic.collect",
         "payload": {"topic": "AI"}, "depends_on": []}
        for i in range(33)
    ]
    with pytest.raises(PlanValidationError, match="1..32"):
        validate_plan_nodes(_proposal(too_many), registry)
    with pytest.raises(PlanValidationError, match="unsupported fields"):
        validate_plan_nodes(_proposal([
            {"step_id": "research", "task_type": "research.topic.collect",
             "payload": {"topic": "AI", "shell": "rm -rf"}, "depends_on": []}
        ]), registry)
    with pytest.raises(PlanValidationError, match="max_attempts"):
        validate_plan_nodes(_proposal([
            {"step_id": "research", "task_type": "research.topic.collect",
             "payload": {"topic": "AI"}, "depends_on": [], "max_attempts": 99}
        ]), registry)


def test_task_execution_context_is_not_persisted_as_user_payload():
    request = TaskRequest(
        "test.echo", {"message": "safe"},
        context={"dependencies": [{"task_type": "research.topic.collect", "status": "succeeded"}]},
    )
    assert "context" not in request.to_dict()
    assert request.to_dict()["schema_version"] == "nextdecode.autonomy.task.v1"
    assert request.payload == {"message": "safe"}
