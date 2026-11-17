"""Fail-closed local capability policy; not a substitute for canonical WP3/WP5 authority."""
from __future__ import annotations

from dataclasses import dataclass

POLICY_VERSION = "local-worker-policy.v1"

ALLOWED_SCOPES = frozenset({
    "public_web:read",
    "local_model:inference",
    "artifact:write",
    "input:read",
    "document:extract",
    "data:analyze",
    "workspace:read",
    "publishing:readiness-check",
})

ALLOWED_PROFILES = frozenset({
    "bwrap-project-ro-network",
    "in-process-bounded",
    "bwrap-project-ro-output-rw",
    "in-process-readonly",
})


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    policy_version: str = POLICY_VERSION


@dataclass(frozen=True)
class LocalWorkerPolicy:
    """Validate registry-owned capability metadata; task payloads grant no authority."""

    def evaluate(self, capability, payload: dict) -> PolicyDecision:
        if not isinstance(payload, dict):
            return PolicyDecision(False, "invalid_task_payload")
        reserved = {"permission_scopes", "permissions", "network_access", "sandbox_profile"}
        if reserved.intersection(payload):
            return PolicyDecision(False, "task_payload_cannot_set_execution_policy")

        scopes = getattr(capability, "permission_scopes", None)
        if not isinstance(scopes, tuple) or len(scopes) != len(set(scopes)):
            return PolicyDecision(False, "invalid_capability_scopes")
        if any(not isinstance(scope, str) or scope not in ALLOWED_SCOPES for scope in scopes):
            return PolicyDecision(False, "capability_scope_not_allowlisted")

        profile = getattr(capability, "sandbox_profile", None)
        if profile not in ALLOWED_PROFILES:
            return PolicyDecision(False, "sandbox_profile_not_allowlisted")

        network_access = getattr(capability, "network_access", None)
        if not isinstance(network_access, bool):
            return PolicyDecision(False, "invalid_network_policy")
        if network_access and profile != "bwrap-project-ro-network":
            return PolicyDecision(False, "network_requires_restricted_network_profile")
        if not network_access and "public_web:read" in scopes:
            return PolicyDecision(False, "network_scope_without_network_profile")
        if "publishing:readiness-check" in scopes and network_access:
            return PolicyDecision(False, "publishing_readiness_must_be_offline")

        return PolicyDecision(True, "allowed")

import os

MODES = {"assisted", "approve_publish", "fully_auto"}
APPROVAL_POLICIES = {"publish_only", "exceptions", "stage_control"}
FAILURE_POLICIES = {"auto_recover", "ask_on_failure"}
RECOVERABLE_FAILURES = frozenset({
    "provider_unavailable", "provider_rate_limited", "asset_irrelevant",
    "asset_low_quality", "render_failed", "duration_out_of_range",
    "transient_io", "worker_interrupted",
})
NON_BYPASSABLE_GATES = frozenset({
    "unsupported_claim", "unverified_material_claim", "unknown_asset_rights",
    "license_violation", "artifact_integrity_failure", "qa_failed",
    "publish_authorization_missing", "final_publish_approval_missing",
})


@dataclass(frozen=True)
class ExecutionPolicy:
    mode: str = "approve_publish"
    approval: str = "exceptions"
    failure_handling: str = "auto_recover"
    max_stage_attempts: int = 3
    max_provider_attempts: int = 2
    allow_public_auto_publish: bool = False

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"unsupported execution mode: {self.mode}")
        if self.approval not in APPROVAL_POLICIES:
            raise ValueError(f"unsupported approval policy: {self.approval}")
        if self.failure_handling not in FAILURE_POLICIES:
            raise ValueError(f"unsupported failure policy: {self.failure_handling}")
        if not 1 <= self.max_stage_attempts <= 5:
            raise ValueError("max_stage_attempts must be between 1 and 5")
        if not 1 <= self.max_provider_attempts <= 5:
            raise ValueError("max_provider_attempts must be between 1 and 5")
        if self.allow_public_auto_publish:
            raise ValueError("public automatic publishing requires a separate owner authorization")

    def requires_human_approval(self, action: str, *, unresolved_exception: bool = False) -> bool:
        if action in {"publish_public", "publish_any"}:
            return True
        if action == "resolve_exception":
            return unresolved_exception
        if self.mode == "assisted" or self.approval == "stage_control":
            return action in {"script_review", "storyboard_review", "render_review"}
        if self.approval == "exceptions":
            return unresolved_exception
        return False

    def may_auto_recover(self, failure: str, *, attempt: int) -> bool:
        if self.failure_handling != "auto_recover":
            return False
        if failure in NON_BYPASSABLE_GATES or failure not in RECOVERABLE_FAILURES:
            return False
        return 0 <= attempt < self.max_stage_attempts

    def as_dict(self) -> dict:
        return {
            "mode": self.mode,
            "approval": self.approval,
            "failure_handling": self.failure_handling,
            "max_stage_attempts": self.max_stage_attempts,
            "max_provider_attempts": self.max_provider_attempts,
            "allow_public_auto_publish": self.allow_public_auto_publish,
        }


def load_execution_policy(environ=None) -> ExecutionPolicy:
    """Load policy from environment; invalid values fail closed."""
    env = os.environ if environ is None else environ
    return ExecutionPolicy(
        mode=str(env.get("NEXTDECODE_EXECUTION_MODE", "approve_publish")).strip().lower(),
        approval=str(env.get("NEXTDECODE_APPROVAL_POLICY", "exceptions")).strip().lower(),
        failure_handling=str(env.get("NEXTDECODE_FAILURE_HANDLING", "auto_recover")).strip().lower(),
        max_stage_attempts=int(env.get("NEXTDECODE_MAX_STAGE_ATTEMPTS", "3")),
        max_provider_attempts=int(env.get("NEXTDECODE_MAX_PROVIDER_ATTEMPTS", "2")),
        allow_public_auto_publish=False,
    )
