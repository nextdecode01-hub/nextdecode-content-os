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
