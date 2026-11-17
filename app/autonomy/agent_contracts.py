"""Versioned agent result and independent-verification contracts.

These contracts validate submitted evidence only. They do not execute agents,
read artifact locations, persist results, or authorize protected actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re


_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_RESULT_STATUSES = frozenset({"completed", "failed", "cancelled", "timed_out"})
_VERDICTS = frozenset({
    "accepted", "rejected", "needs_review", "retryable_failure", "permanent_failure",
})


@dataclass(frozen=True)
class ArtifactReference:
    reference: str
    sha256: str
    media_type: str = "application/octet-stream"
    size_bytes: int | None = None


@dataclass(frozen=True)
class AgentResultEnvelope:
    schema_version: str
    assignment_id: str
    task_id: str
    agent_id: str
    execution_id: str
    correlation_id: str
    status: str
    started_at: str
    completed_at: str
    output_references: tuple[str, ...] = ()
    artifacts: tuple[ArtifactReference, ...] = ()
    evidence_references: tuple[str, ...] = ()
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class VerificationDecision:
    schema_version: str
    assignment_id: str
    execution_id: str
    verifier_id: str
    verdict: str
    criteria_checked: tuple[str, ...]
    evidence_references: tuple[str, ...]
    rationale: str
    protected_action_requested: bool = False
    human_approval_reference: str | None = None


def _timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def validate_result_envelope(result: AgentResultEnvelope, *,
                             assignment: dict) -> tuple[str, ...]:
    """Return stable issue codes; empty tuple means the envelope is structurally valid."""
    issues: list[str] = []
    if result.schema_version != "nextdecode.agent-result.v1":
        issues.append("unsupported_result_schema")
    if result.assignment_id != assignment.get("assignment_id"):
        issues.append("assignment_id_mismatch")
    if result.task_id != assignment.get("task_id"):
        issues.append("task_id_mismatch")
    if result.agent_id != assignment.get("agent_id"):
        issues.append("agent_id_mismatch")
    if result.correlation_id != assignment.get("correlation_id"):
        issues.append("correlation_id_mismatch")
    if not result.execution_id.strip():
        issues.append("execution_id_missing")
    if result.status not in _RESULT_STATUSES:
        issues.append("result_status_invalid")
    started = _timestamp(result.started_at)
    completed = _timestamp(result.completed_at)
    if started is None or completed is None:
        issues.append("result_timestamps_invalid")
    elif completed < started:
        issues.append("result_time_order_invalid")
    if result.status == "completed" and result.error_code:
        issues.append("completed_result_has_error")
    if result.status != "completed" and not result.error_code:
        issues.append("failed_result_error_code_missing")
    for artifact in result.artifacts:
        if not artifact.reference.strip():
            issues.append("artifact_reference_missing")
        if not _SHA256_RE.fullmatch(artifact.sha256 or ""):
            issues.append("artifact_digest_invalid")
        if artifact.size_bytes is not None and artifact.size_bytes < 0:
            issues.append("artifact_size_invalid")
    for reference in (*result.output_references, *result.evidence_references):
        if not reference.strip():
            issues.append("result_provenance_reference_empty")
    if result.status == "completed" and not (
        result.output_references or result.artifacts or result.evidence_references
    ):
        issues.append("completed_result_has_no_provenance")
    return tuple(dict.fromkeys(issues))


def evaluate_verification(result: AgentResultEnvelope, *,
                          assignment: dict,
                          decision: VerificationDecision) -> dict:
    """Evaluate an independent verifier decision without granting approval."""
    issues = list(validate_result_envelope(result, assignment=assignment))
    if decision.schema_version != "nextdecode.verification-decision.v1":
        issues.append("unsupported_verification_schema")
    if decision.assignment_id != result.assignment_id:
        issues.append("verification_assignment_mismatch")
    if decision.execution_id != result.execution_id:
        issues.append("verification_execution_mismatch")
    if not decision.verifier_id.strip():
        issues.append("verifier_identity_missing")
    elif decision.verifier_id == result.agent_id:
        issues.append("self_verification_forbidden")
    if decision.verdict not in _VERDICTS:
        issues.append("verification_verdict_invalid")
    if not decision.criteria_checked:
        issues.append("verification_criteria_missing")
    if not decision.rationale.strip():
        issues.append("verification_rationale_missing")
    if not decision.evidence_references or any(not item.strip() for item in decision.evidence_references):
        issues.append("verification_evidence_missing")
    if decision.protected_action_requested and not decision.human_approval_reference:
        issues.append("protected_action_requires_human_approval")
    if result.status != "completed" and decision.verdict == "accepted":
        issues.append("noncompleted_result_cannot_be_accepted")
    unique_issues = list(dict.fromkeys(issues))
    return {
        "schema_version": "nextdecode.verification-evaluation.v1",
        "assignment_id": result.assignment_id,
        "execution_id": result.execution_id,
        "verifier_id": decision.verifier_id,
        "verdict": decision.verdict if not unique_issues else "needs_review",
        "valid": not unique_issues,
        "issue_codes": unique_issues,
        "human_approval_required": decision.protected_action_requested,
        "protected_action_authorized": False,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
