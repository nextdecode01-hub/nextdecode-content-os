"""Fail-closed, plan-only agent assignment decisions.

This module never launches processes, accesses the network, forwards credentials,
or writes to a repository. Planning authorization is distinct from invocation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import uuid

from .agent_runtime import AgentReadinessEvidence, AgentRuntimeRegistry, agent_runtime_registry


_DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class QualificationRecord:
    """Structured qualification evidence; a bare reference string is insufficient."""

    agent_id: str
    capability: str
    qualification_id: str
    status: str
    test_suite: str
    evidence_reference: str
    evidence_sha256: str
    qualified_at: str
    expires_at: str | None = None


@dataclass(frozen=True)
class AssignmentRequest:
    assignment_id: str
    task_id: str
    agent_id: str
    capability: str
    objective: str
    input_references: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    permission_scope: tuple[str, ...]
    correlation_id: str
    timeout_seconds: int = 900


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _fresh_timestamp(value: str | None, now: datetime, stale_after_seconds: int,
                     future_skew_seconds: int = 60) -> bool:
    observed = _parse_timestamp(value)
    if observed is None:
        return False
    return now - timedelta(seconds=max(1, stale_after_seconds)) <= observed <= now + timedelta(seconds=future_skew_seconds)


def _valid_qualification(record: QualificationRecord | None, *, agent_id: str,
                         capability: str, now: datetime) -> tuple[bool, str]:
    if record is None:
        return False, "qualification_record_missing"
    if record.agent_id != agent_id or record.capability != capability:
        return False, "qualification_subject_or_capability_mismatch"
    if record.status != "passed":
        return False, "qualification_not_passed"
    if not record.qualification_id.strip() or not record.test_suite.strip() or not record.evidence_reference.strip():
        return False, "qualification_provenance_incomplete"
    if not _DIGEST_RE.fullmatch(record.evidence_sha256 or ""):
        return False, "qualification_digest_invalid"
    qualified_at = _parse_timestamp(record.qualified_at)
    expires_at = _parse_timestamp(record.expires_at) if record.expires_at else None
    if qualified_at is None or qualified_at > now + timedelta(seconds=60):
        return False, "qualification_timestamp_invalid"
    if expires_at is not None and expires_at <= now:
        return False, "qualification_expired"
    return True, "qualification_record_valid"


class AgentAssignmentPlanner:
    """Produces reviewable assignment decisions only; never executes an agent."""

    def __init__(self, registry: AgentRuntimeRegistry | None = None,
                 *, stale_after_seconds: int = 300):
        self.registry = registry or agent_runtime_registry
        self.stale_after_seconds = stale_after_seconds

    def plan(self, request: AssignmentRequest, *,
             readiness_evidence: dict[str, AgentReadinessEvidence] | None = None,
             qualification: QualificationRecord | None = None,
             planning_authorized: bool = False,
             now: datetime | None = None) -> dict:
        observed_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        denials: list[str] = []
        spec = self.registry.get_spec(request.agent_id)
        if spec is None:
            denials.append("agent_unknown")
        if not planning_authorized:
            denials.append("assignment_planning_not_authorized")
        identity_values = (request.assignment_id, request.task_id, request.correlation_id)
        if any(not isinstance(value, str) or not value.strip() for value in identity_values):
            denials.append("assignment_identity_incomplete")
        if (not isinstance(request.capability, str) or not request.capability.strip()
                or not isinstance(request.objective, str) or not request.objective.strip()):
            denials.append("assignment_objective_or_capability_missing")
        if (not request.acceptance_criteria
                or any(not isinstance(item, str) or not item.strip() for item in request.acceptance_criteria)):
            denials.append("acceptance_criteria_missing")
        if (not isinstance(request.timeout_seconds, int) or isinstance(request.timeout_seconds, bool)
                or request.timeout_seconds < 1 or request.timeout_seconds > 3600):
            denials.append("timeout_out_of_bounds")
        for values, reason in ((request.input_references, "input_references_invalid"),
                               (request.permission_scope, "permission_scope_invalid")):
            if not isinstance(values, tuple) or any(not isinstance(item, str) or not item.strip() for item in values):
                denials.append(reason)
        if spec is not None and request.capability not in spec.roles:
            denials.append("capability_not_declared")

        evidence = (readiness_evidence or {}).get(request.agent_id, AgentReadinessEvidence())
        if spec is not None:
            readiness = self.registry.get_readiness(
                request.agent_id, evidence=readiness_evidence, now=observed_now,
                stale_after_seconds=self.stale_after_seconds,
            )
            if readiness is None or not readiness["states"]["installed"]["value"]:
                denials.append("agent_not_installed")
            if readiness is None or readiness["states"]["configured"]["value"] is not True:
                denials.append("agent_configuration_unverified")
            if readiness is None or readiness["states"]["available"]["value"] is not True:
                denials.append("readiness_not_available")
            if not evidence.qualification_passed or request.capability not in evidence.qualification_capabilities:
                denials.append("readiness_qualification_not_verified_for_capability")
            if evidence.suspended:
                denials.append("agent_suspended")
            if evidence.revoked:
                denials.append("agent_revoked")
            if not evidence.qualification_reference:
                denials.append("readiness_qualification_reference_missing")
            if evidence.availability is not True:
                denials.append("availability_not_confirmed")
            if not _fresh_timestamp(evidence.availability_observed_at, observed_now,
                                    self.stale_after_seconds):
                denials.append("availability_evidence_stale_or_future")
            valid_qualification, qualification_reason = _valid_qualification(
                qualification, agent_id=request.agent_id,
                capability=request.capability, now=observed_now,
            )
            if not valid_qualification:
                denials.append(qualification_reason)

        unique_denials = list(dict.fromkeys(denials))
        accepted = not unique_denials
        plan_id = uuid.uuid4().hex
        canonical_payload = json.dumps({
            "task_id": request.task_id,
            "agent_id": request.agent_id,
            "capability": request.capability,
            "objective": request.objective,
            "input_references": list(request.input_references),
            "acceptance_criteria": list(request.acceptance_criteria),
            "permission_scope": list(request.permission_scope),
            "correlation_id": request.correlation_id,
            "timeout_seconds": request.timeout_seconds,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        payload_fingerprint = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
        return {
            "schema_version": "nextdecode.agent-assignment-decision.v1",
            "plan_id": plan_id,
            "assignment_id": request.assignment_id,
            "task_id": request.task_id,
            "agent_id": request.agent_id,
            "capability": request.capability,
            "correlation_id": request.correlation_id,
            "payload_fingerprint": payload_fingerprint,
            "status": "plan_only" if accepted else "denied",
            "accepted": accepted,
            "denial_reason_codes": unique_denials,
            "qualification": {
                "qualification_id": qualification.qualification_id,
                "evidence_reference": qualification.evidence_reference,
            } if accepted and qualification else None,
            "policy_evaluation": {
                "planning_authorized": planning_authorized,
                "invocation_authorized": False,
                "network_access": False,
                "credential_forwarding": False,
                "direct_repository_write": False,
                "protected_actions_permitted": False,
            },
            "process_started": False,
            "network_access": False,
            "credential_forwarding": False,
            "direct_repository_write": False,
            "human_approval_required": True,
            "observed_at": observed_now.isoformat(),
        }
