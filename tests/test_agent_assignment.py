from datetime import datetime, timedelta, timezone

import pytest

from app.autonomy.agent_runtime import AgentReadinessEvidence, AgentRuntimeRegistry, AgentSpec
from app.autonomy.agent_assignment import (
    AgentAssignmentPlanner, AssignmentRequest, QualificationRecord,
)


NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


def _setup(monkeypatch):
    registry = AgentRuntimeRegistry([
        AgentSpec("test-agent", "Test Agent", "test-agent", ("code_review",), 1, "test-only")
    ])
    monkeypatch.setattr(registry, "_installation_evidence",
                        lambda _spec: [{"kind": "test_fixture", "reference": "test://installed"}])
    planner = AgentAssignmentPlanner(registry, stale_after_seconds=300)
    request = AssignmentRequest(
        assignment_id="assignment-001", task_id="task-001",
        agent_id="test-agent", capability="code_review",
        objective="Review the bounded change", input_references=("artifact://input-1",),
        acceptance_criteria=("No critical findings",), permission_scope=("read_only",),
        correlation_id="corr-001",
    )
    evidence = {"test-agent": AgentReadinessEvidence(
        configured=True, configuration_reference="test-config",
        qualification_reference="qualification-001", qualification_passed=True,
        qualification_evidence_sha256="a" * 64,
        qualification_capabilities=("code_review",),
        availability_observed_at=NOW.isoformat(), availability=True,
    )}
    qualification = QualificationRecord(
        agent_id="test-agent", capability="code_review",
        qualification_id="qualification-001", status="passed",
        test_suite="test-suite-v1", evidence_reference="test://qualification",
        evidence_sha256="a" * 64, qualified_at=(NOW - timedelta(minutes=1)).isoformat(),
    )
    return planner, request, evidence, qualification


def test_unknown_agent_is_denied(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    request = AssignmentRequest(**{**request.__dict__, "agent_id": "unknown"})
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW, planning_authorized=True)
    assert "agent_unknown" in result["denial_reason_codes"]


def test_missing_planning_authorization_is_denied(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW)
    assert "assignment_planning_not_authorized" in result["denial_reason_codes"]


def test_undeclared_capability_is_denied(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    request = AssignmentRequest(**{**request.__dict__, "capability": "publishing"})
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW, planning_authorized=True)
    assert "capability_not_declared" in result["denial_reason_codes"]


def test_missing_qualification_record_is_denied(monkeypatch):
    planner, request, evidence, _ = _setup(monkeypatch)
    result = planner.plan(request, readiness_evidence=evidence, now=NOW, planning_authorized=True)
    assert "qualification_record_missing" in result["denial_reason_codes"]


def test_arbitrary_qualification_reference_is_not_sufficient(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    qualification = QualificationRecord(**{**qualification.__dict__, "evidence_sha256": "not-a-digest"})
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW, planning_authorized=True)
    assert "qualification_digest_invalid" in result["denial_reason_codes"]


def test_future_availability_timestamp_is_denied(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    evidence["test-agent"] = AgentReadinessEvidence(
        configured=True, qualification_reference="qualification-001",
        availability=True, availability_observed_at=(NOW + timedelta(hours=1)).isoformat(),
    )
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW, planning_authorized=True)
    assert "availability_evidence_stale_or_future" in result["denial_reason_codes"]


@pytest.mark.parametrize("flag,expected", [
    ("suspended", "agent_suspended"),
    ("revoked", "agent_revoked"),
])
def test_suspension_and_revocation_deny(monkeypatch, flag, expected):
    planner, request, evidence, qualification = _setup(monkeypatch)
    original = evidence["test-agent"].__dict__.copy()
    original[flag] = True
    evidence["test-agent"] = AgentReadinessEvidence(**original)
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW, planning_authorized=True)
    assert expected in result["denial_reason_codes"]


def test_stale_availability_is_denied(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    evidence["test-agent"] = AgentReadinessEvidence(
        configured=True, qualification_reference="qualification-001",
        availability=True, availability_observed_at=(NOW - timedelta(hours=1)).isoformat(),
    )
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW, planning_authorized=True)
    assert "availability_evidence_stale_or_future" in result["denial_reason_codes"]


def test_valid_plan_is_plan_only_and_never_authorizes_invocation(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW, planning_authorized=True)
    assert result["accepted"] is True
    assert result["status"] == "plan_only"
    assert result["process_started"] is False
    assert result["policy_evaluation"]["invocation_authorized"] is False
    assert result["network_access"] is False
    assert result["credential_forwarding"] is False
    assert result["direct_repository_write"] is False


def test_missing_installation_is_denied(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    monkeypatch.setattr(planner.registry, "_installation_evidence", lambda _spec: [])
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW, planning_authorized=True)
    assert "agent_not_installed" in result["denial_reason_codes"]


def test_denial_reasons_are_machine_readable_and_deduplicated(monkeypatch):
    planner, request, evidence, qualification = _setup(monkeypatch)
    request = AssignmentRequest(**{**request.__dict__, "acceptance_criteria": ()})
    result = planner.plan(request, readiness_evidence=evidence, qualification=qualification, now=NOW)
    assert result["accepted"] is False
    assert len(result["denial_reason_codes"]) == len(set(result["denial_reason_codes"]))
    assert "assignment_planning_not_authorized" in result["denial_reason_codes"]
    assert "acceptance_criteria_missing" in result["denial_reason_codes"]



def test_assignment_plan_cli_is_read_only_and_does_not_open_task_store(capsys, monkeypatch):
    from app.autonomy import cli

    monkeypatch.setattr(cli, "_store", lambda *_: pytest.fail("assignment planning must not initialize task storage"))
    request_json = (
        '{"assignment_id":"cli-a1","task_id":"task-a1","agent_id":"opencode",'
        '"capability":"code_review","objective":"Review a bounded change",'
        '"input_references":[],"acceptance_criteria":["No critical findings"],'
        '"permission_scope":["read_only"],"correlation_id":"cli-c1"}'
    )
    assert cli.main(["agent-assignment-plan", "--request", request_json]) == 2
    output = capsys.readouterr().out
    assert '"status": "denied"' in output
    assert '"process_started": false' in output
    assert "qualification_record_missing" in output
