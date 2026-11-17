from dataclasses import replace

from app.autonomy.agent_contracts import (
    AgentResultEnvelope, ArtifactReference, VerificationDecision,
    evaluate_verification, validate_result_envelope,
)


ASSIGNMENT = {
    "assignment_id": "as-1", "task_id": "task-1", "agent_id": "agent-a",
    "correlation_id": "corr-1",
}


def _result(**changes):
    result = AgentResultEnvelope(
        schema_version="nextdecode.agent-result.v1",
        assignment_id="as-1", task_id="task-1", agent_id="agent-a",
        execution_id="exec-1", correlation_id="corr-1", status="completed",
        started_at="2026-11-13T10:00:00+00:00",
        completed_at="2026-11-13T10:01:00+00:00",
        output_references=("artifact://output-1",),
        artifacts=(ArtifactReference("artifact://output-1", "a" * 64, size_bytes=12),),
        evidence_references=("evidence://run-log",),
    )
    return replace(result, **changes)


def _decision(**changes):
    decision = VerificationDecision(
        schema_version="nextdecode.verification-decision.v1",
        assignment_id="as-1", execution_id="exec-1", verifier_id="verifier-b",
        verdict="accepted", criteria_checked=("accuracy", "format"),
        evidence_references=("evidence://review",), rationale="All required checks passed",
    )
    return replace(decision, **changes)


def test_valid_result_envelope_is_accepted_structurally():
    assert validate_result_envelope(_result(), assignment=ASSIGNMENT) == ()


def test_result_rejects_assignment_and_correlation_mismatch():
    issues = validate_result_envelope(
        _result(assignment_id="other", correlation_id="other"),
        assignment=ASSIGNMENT,
    )
    assert "assignment_id_mismatch" in issues
    assert "correlation_id_mismatch" in issues


def test_result_rejects_invalid_digest_and_missing_provenance():
    invalid_digest = _result(
        artifacts=(ArtifactReference("artifact://output", "bad-digest"),),
    )
    issues = validate_result_envelope(invalid_digest, assignment=ASSIGNMENT)
    assert "artifact_digest_invalid" in issues
    missing_provenance = _result(artifacts=(), output_references=(), evidence_references=())
    issues = validate_result_envelope(missing_provenance, assignment=ASSIGNMENT)
    assert "completed_result_has_no_provenance" in issues


def test_result_rejects_naive_or_reversed_timestamps():
    result = _result(
        started_at="2026-11-13T10:01:00",
        completed_at="2026-11-13T10:00:00+00:00",
    )
    issues = validate_result_envelope(result, assignment=ASSIGNMENT)
    assert "result_timestamps_invalid" in issues


def test_failed_result_requires_error_code():
    result = _result(status="failed", error_code=None)
    assert "failed_result_error_code_missing" in validate_result_envelope(
        result, assignment=ASSIGNMENT
    )


def test_verifier_cannot_verify_own_result():
    result = _result()
    decision = _decision(verifier_id=result.agent_id)
    evaluation = evaluate_verification(result, assignment=ASSIGNMENT, decision=decision)
    assert evaluation["valid"] is False
    assert "self_verification_forbidden" in evaluation["issue_codes"]


def test_protected_action_needs_human_approval_reference():
    evaluation = evaluate_verification(
        _result(), assignment=ASSIGNMENT,
        decision=_decision(protected_action_requested=True),
    )
    assert "protected_action_requires_human_approval" in evaluation["issue_codes"]
    assert evaluation["protected_action_authorized"] is False


def test_valid_independent_verification_does_not_authorize_protected_action():
    evaluation = evaluate_verification(_result(), assignment=ASSIGNMENT, decision=_decision())
    assert evaluation["valid"] is True
    assert evaluation["verdict"] == "accepted"
    assert evaluation["protected_action_authorized"] is False


def test_noncompleted_result_cannot_receive_accepted_verdict():
    result = _result(status="timed_out", error_code="timeout")
    evaluation = evaluate_verification(result, assignment=ASSIGNMENT, decision=_decision())
    assert evaluation["valid"] is False
    assert "noncompleted_result_cannot_be_accepted" in evaluation["issue_codes"]
