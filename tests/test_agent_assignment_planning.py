"""AEC-01 isolated tests: readiness-aware, plan-only assignment planning.

Every agent, credential and evidence value in this file is a synthetic
test-only fixture; nothing here represents a real installed or qualified
agent. The suite verifies the assignment flow end to end through the
AgentExecutionAdapter planning boundary, including the review-finding
regressions (plan/execute separation) and the security boundary
(no process invocation, no network access, no repository writes).
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.autonomy.agent_assignment import (
    AgentAssignmentPlanner, AssignmentRequest, QualificationRecord,
)
from app.autonomy.agent_runtime import (
    AgentReadinessEvidence, AgentRuntimeRegistry, AgentSpec,
    agent_runtime_registry,
)
from app.autonomy.agent_workspace import (
    AgentExecutionAdapter, AgentExecutionPolicy, prepare_workspace,
)


NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
TEST_ONLY_DIGEST = "b" * 64


def _request(**overrides) -> AssignmentRequest:
    values = {
        "assignment_id": "assignment-test-0001",
        "task_id": "task-test-0001",
        "agent_id": "fixture-agent",
        "capability": "code_review",
        "objective": "Review the bounded change",
        "input_references": ("artifact://input-1",),
        "acceptance_criteria": ("No critical findings",),
        "permission_scope": ("read_only",),
        "correlation_id": "corr-test-0001",
    }
    values.update(overrides)
    return AssignmentRequest(**values)


def _evidence(**overrides) -> dict:
    values = {
        "configured": True,
        "configuration_reference": "test-config",
        "qualification_reference": "qualification-001",
        "qualification_passed": True,
        "qualification_evidence_sha256": TEST_ONLY_DIGEST,
        "qualification_capabilities": ("code_review",),
        "availability_observed_at": NOW.isoformat(),
        "availability": True,
    }
    values.update(overrides)
    return {"fixture-agent": AgentReadinessEvidence(**values)}


def _qualification(**overrides) -> QualificationRecord:
    values = {
        "agent_id": "fixture-agent",
        "capability": "code_review",
        "qualification_id": "qualification-001",
        "status": "passed",
        "test_suite": "fixture-test-suite-v1",
        "evidence_reference": "test://qualification/fixture",
        "evidence_sha256": TEST_ONLY_DIGEST,
        "qualified_at": (NOW - timedelta(minutes=1)).isoformat(),
    }
    values.update(overrides)
    return QualificationRecord(**values)


def _adapter(monkeypatch, installed=True) -> AgentExecutionAdapter:
    """Adapter boundary with a synthetic test-only agent in the shared registry."""
    fixture_registry = AgentRuntimeRegistry([
        AgentSpec("fixture-agent", "Fixture Agent (test-only)", "fixture-cli",
                  ("code_review",), 1, "test-only"),
    ])
    monkeypatch.setattr(agent_runtime_registry, "_specs", fixture_registry._specs)
    monkeypatch.setattr(
        agent_runtime_registry, "_installation_evidence",
        (lambda _spec: [{"kind": "test_fixture", "reference": "test://installed"}])
        if installed else (lambda _spec: []),
    )
    return AgentExecutionAdapter()


_NO_QUALIFICATION = object()


def _plan(monkeypatch, adapter=None, request=None, evidence=None,
          qualification=_NO_QUALIFICATION, planning_authorized=True):
    adapter = adapter or _adapter(monkeypatch)
    return adapter.plan_assignment(
        request or _request(),
        readiness_evidence=_evidence() if evidence is None else evidence,
        qualification=_qualification() if qualification is _NO_QUALIFICATION else qualification,
        planning_authorized=planning_authorized, now=NOW,
    )


# --- Mission scenarios 1-9: readiness-aware denial and acceptance paths -----

def test_unknown_agent_is_denied(monkeypatch):
    decision = _plan(monkeypatch, request=_request(agent_id="unknown-agent"))
    assert decision["accepted"] is False
    assert "agent_unknown" in decision["denial_reason_codes"]


def test_unknown_capability_is_denied(monkeypatch):
    decision = _plan(monkeypatch, request=_request(capability="publishing"))
    assert "capability_not_declared" in decision["denial_reason_codes"]


def test_missing_installation_evidence_is_denied(monkeypatch):
    decision = _plan(monkeypatch, adapter=_adapter(monkeypatch, installed=False))
    assert "agent_not_installed" in decision["denial_reason_codes"]


def test_missing_qualification_is_denied(monkeypatch):
    decision = _plan(monkeypatch, qualification=None)
    assert "qualification_record_missing" in decision["denial_reason_codes"]


def test_stale_availability_is_denied(monkeypatch):
    decision = _plan(monkeypatch, evidence=_evidence(
        availability_observed_at=(NOW - timedelta(hours=1)).isoformat()))
    assert "availability_evidence_stale_or_future" in decision["denial_reason_codes"]


def test_suspended_agent_is_denied(monkeypatch):
    decision = _plan(monkeypatch, evidence=_evidence(suspended=True))
    assert "agent_suspended" in decision["denial_reason_codes"]


def test_revoked_agent_is_denied(monkeypatch):
    decision = _plan(monkeypatch, evidence=_evidence(revoked=True))
    assert "agent_revoked" in decision["denial_reason_codes"]


def test_invocation_is_never_authorized_by_the_planning_boundary(monkeypatch):
    """Even with invocation_authorized=True in evidence, the decision refuses it."""
    decision = _plan(monkeypatch, evidence=_evidence(invocation_authorized=True))
    assert decision["accepted"] is True
    assert decision["policy_evaluation"]["invocation_authorized"] is False
    record = agent_runtime_registry.get_readiness(
        "fixture-agent", evidence=_evidence(invocation_authorized=True), now=NOW)
    assert record["states"]["invocation_authorized"]["value"] is False
    adapter = AgentExecutionAdapter()
    with pytest.raises(PermissionError):
        adapter.execute({
            "schema_version": "nextdecode.agent-invocation-plan.v1",
        })


def test_qualified_available_authorized_agent_produces_plan_only_decision(monkeypatch):
    decision = _plan(monkeypatch)
    assert decision["accepted"] is True
    assert decision["status"] == "plan_only"
    assert decision["process_started"] is False
    assert decision["human_approval_required"] is True


# --- Mission scenario 10: structured, machine-readable denials --------------

def test_denial_decision_is_structured_and_machine_readable(monkeypatch):
    decision = _plan(monkeypatch, request=_request(
        acceptance_criteria=(), assignment_id="assignment-test-0002",
        task_id="task-test-0002", correlation_id="corr-test-0002",
    ), planning_authorized=False)
    assert decision["accepted"] is False
    codes = decision["denial_reason_codes"]
    assert codes == sorted(set(codes)) or len(codes) == len(set(codes))
    assert "assignment_planning_not_authorized" in codes
    assert "acceptance_criteria_missing" in codes
    required = decision["required_missing_evidence"]
    assert all(set(item) == {"code", "requirement"} for item in required)
    assert [item["code"] for item in required] == codes
    assert all(isinstance(item["requirement"], str) and item["requirement"]
               for item in required)
    for key in ("schema_version", "plan_id", "assignment_id", "status",
                "policy_evaluation", "process_started", "observed_at"):
        assert key in decision


# --- Mission scenario 11: duplicate assignment request -----------------------

def test_duplicate_assignment_request_is_denied(monkeypatch):
    adapter = _adapter(monkeypatch)
    first = adapter.plan_assignment(
        _request(), readiness_evidence=_evidence(),
        qualification=_qualification(), planning_authorized=True, now=NOW)
    assert first["accepted"] is True
    duplicate = adapter.plan_assignment(
        _request(), readiness_evidence=_evidence(),
        qualification=_qualification(), planning_authorized=True, now=NOW)
    assert duplicate["accepted"] is False
    assert duplicate["status"] == "denied"
    assert duplicate["denial_reason_codes"] == ["duplicate_assignment"]
    assert duplicate["process_started"] is False


def test_denied_assignment_does_not_reserve_the_assignment_id(monkeypatch):
    adapter = _adapter(monkeypatch)
    stale = adapter.plan_assignment(
        _request(), readiness_evidence=_evidence(
            availability_observed_at=(NOW - timedelta(hours=1)).isoformat()),
        qualification=_qualification(), planning_authorized=True, now=NOW)
    assert stale["accepted"] is False
    retry = adapter.plan_assignment(
        _request(), readiness_evidence=_evidence(),
        qualification=_qualification(), planning_authorized=True, now=NOW)
    assert retry["accepted"] is True


def test_a_fresh_adapter_has_no_assignment_ledger_state(monkeypatch):
    _plan(monkeypatch, adapter=_adapter(monkeypatch))
    assert _adapter(monkeypatch).plan_assignment(
        _request(), readiness_evidence=_evidence(),
        qualification=_qualification(), planning_authorized=True, now=NOW,
    )["accepted"] is True


# --- Mission scenarios 12-15: the security boundary --------------------------

_FORBIDDEN_SOURCE_MARKERS = ("subprocess", "os.system", "socket", "urllib",
                             "Popen", "http.client")


@pytest.mark.parametrize("module_name", [
    "app.autonomy.agent_assignment",
    "app.autonomy.agent_workspace",
    "app.autonomy.agent_runtime",
])
def test_assignment_modules_contain_no_execution_or_network_machinery(module_name):
    source = Path(__import__(module_name, fromlist=["x"]).__file__).read_text(encoding="utf-8")
    for marker in _FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source, f"forbidden machinery in {module_name}: {marker}"


def test_planning_starts_no_process(monkeypatch):
    import os
    import subprocess

    def _no_process(*_args, **_kwargs):
        pytest.fail("assignment planning must never start a process")

    monkeypatch.setattr(subprocess, "Popen", _no_process)
    monkeypatch.setattr(subprocess, "run", _no_process)
    monkeypatch.setattr(os, "system", _no_process)
    decision = _plan(monkeypatch)
    assert decision["process_started"] is False


def test_planning_uses_no_network(monkeypatch):
    import socket

    def _no_network(*_args, **_kwargs):
        pytest.fail("assignment planning must never access the network")

    monkeypatch.setattr(socket, "socket", _no_network)
    monkeypatch.setattr(socket, "create_connection", _no_network)
    decision = _plan(monkeypatch)
    assert decision["network_access"] is False
    assert decision["credential_forwarding"] is False


def test_planning_writes_nothing_to_the_repository(monkeypatch):
    def _no_open(*_args, **_kwargs):
        pytest.fail("assignment planning must not touch the filesystem")

    def _no_write(*_args, **_kwargs):
        pytest.fail("assignment planning must not write files")

    monkeypatch.setattr("builtins.open", _no_open)
    monkeypatch.setattr(Path, "write_text", _no_write)
    monkeypatch.setattr(Path, "write_bytes", _no_write)
    monkeypatch.setattr(Path, "mkdir", _no_write)
    decision = _plan(monkeypatch)
    assert decision["direct_repository_write"] is False


def test_every_decision_reports_process_started_false(monkeypatch):
    variants = [
        {},
        {"agent_id": "unknown-agent"},
        {"capability": "publishing"},
        {"acceptance_criteria": ()},
    ]
    decisions = [_plan(monkeypatch, request=_request(**variant)) for variant in variants]
    decisions.append(_plan(monkeypatch, evidence=_evidence(suspended=True)))
    decisions.append(_plan(monkeypatch, evidence=_evidence(revoked=True)))
    decisions.append(_plan(monkeypatch, evidence=_evidence(
        availability_observed_at=(NOW - timedelta(hours=1)).isoformat())))
    decisions.append(_plan(monkeypatch, qualification=None))
    decisions.append(_plan(monkeypatch, planning_authorized=False))
    assert len(decisions) == 9
    assert all(decision["process_started"] is False for decision in decisions)
    assert all(decision["policy_evaluation"]["invocation_authorized"] is False
               for decision in decisions)
    assert all(decision["network_access"] is False for decision in decisions)
    assert all(decision["credential_forwarding"] is False for decision in decisions)
    assert all(decision["direct_repository_write"] is False for decision in decisions)


# --- Review finding 1: plan generation is separate from process execution ----

def test_invocation_plan_generates_under_the_default_safe_policy(monkeypatch):
    """Regression: plan() no longer refuses the default invocation_enabled=False policy."""
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/fixture-cli")
    workspace = prepare_workspace()
    adapter = AgentExecutionAdapter()
    plan = adapter.plan(
        agent_id="opencode", workspace_id=workspace.workspace_id,
        task="Review the bounded change", timeout_seconds=300,
    )
    assert plan["status"] == "plan_only"
    assert plan["process_started"] is False
    assert plan["invocation_authorized"] is False
    assert plan["invocation_gate"] == {
        "invocation_enabled": False,
        "reason": "invocation_disabled_by_policy",
    }
    assert plan["human_approval_required"] is True


def test_unsafe_execution_policy_still_refuses_plan_generation():
    adapter = AgentExecutionAdapter(AgentExecutionPolicy(
        invocation_enabled=True, network_enabled=True))
    with pytest.raises(PermissionError):
        adapter.plan(agent_id="opencode", workspace_id="any", task="task")


def test_execute_always_refuses_regardless_of_policy(monkeypatch):
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/fixture-cli")
    workspace = prepare_workspace()
    enabled = AgentExecutionAdapter(AgentExecutionPolicy(invocation_enabled=True))
    plan = enabled.plan(agent_id="opencode", workspace_id=workspace.workspace_id,
                        task="Review the bounded change")
    with pytest.raises(PermissionError):
        enabled.execute(plan)
    disabled = AgentExecutionAdapter()
    with pytest.raises(PermissionError):
        disabled.execute(plan)


def test_execute_rejects_a_non_adapter_plan():
    adapter = AgentExecutionAdapter()
    with pytest.raises(ValueError):
        adapter.execute({"schema_version": "not-the-adapter-schema"})


def test_assignment_planning_works_with_invocation_disabled(monkeypatch):
    """Regression: plan-only assignment never requires enabling invocation."""
    adapter = _adapter(monkeypatch)
    assert adapter.policy.invocation_enabled is False
    decision = adapter.plan_assignment(
        _request(), readiness_evidence=_evidence(),
        qualification=_qualification(), planning_authorized=True, now=NOW)
    assert decision["accepted"] is True
    assert decision["process_started"] is False


def test_assignment_planning_module_matches_the_planner_contract(monkeypatch):
    """The adapter boundary delegates to the shared planner without duplication."""
    adapter = _adapter(monkeypatch)
    via_adapter = adapter.plan_assignment(
        _request(), readiness_evidence=_evidence(),
        qualification=_qualification(), planning_authorized=True, now=NOW)
    direct = AgentAssignmentPlanner().plan(
        _request(), readiness_evidence=_evidence(),
        qualification=_qualification(), planning_authorized=True, now=NOW)
    assert via_adapter["denial_reason_codes"] == direct["denial_reason_codes"]
    assert via_adapter["status"] == direct["status"] == "plan_only"
    assert via_adapter["schema_version"] == direct["schema_version"]
