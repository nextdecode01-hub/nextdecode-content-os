"""Versioned specialist registry with explicit capability and permission contracts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .execution_policy import LocalWorkerPolicy, PolicyDecision

from .models import TaskRequest, TaskResult


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    cost: str
    licence: str
    handler: Callable[[TaskRequest], TaskResult]
    enabled: bool = True
    planner_allowed: bool = True
    version: str = "1.0"
    permission_scopes: tuple[str, ...] = ("workspace:read", "artifact:write")
    network_access: bool = False
    # Default must satisfy the fail-closed LocalWorkerPolicy allowlist: handlers
    # execute in-process, so the bounded in-process profile is the honest
    # default. Networked or bwrap profiles must be declared explicitly.
    sandbox_profile: str = "in-process-bounded"
    payload_validator: Callable[[dict], dict] | None = None


@dataclass(frozen=True)
class CapabilitySelection:
    capability: Capability | None
    normalized_payload: dict
    policy_decision: PolicyDecision
    route: str
    reason: str


class CapabilityRegistry:
    def __init__(self):
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.name in self._items:
            raise ValueError(f"capability already registered: {capability.name}")
        if capability.cost != "zero-default":
            raise ValueError("default capabilities must have zero external cost")
        if not capability.name or len(capability.name) > 100:
            raise ValueError("capability name must be 1..100 characters")
        if not capability.version or len(capability.version) > 32:
            raise ValueError("capability version must be 1..32 characters")
        if len(set(capability.permission_scopes)) != len(capability.permission_scopes):
            raise ValueError("capability permission scopes must be unique")
        self._items[capability.name] = capability

    def get(self, name: str) -> Capability:
        capability = self._items.get(name)
        if capability is None or not capability.enabled:
            raise KeyError(f"unsupported capability: {name}")
        return capability

    def select(self, task_type: str, payload: dict,
               policy: LocalWorkerPolicy | None = None) -> CapabilitySelection:
        """Resolve one exact task route, validate its input, then apply local policy.

        No fuzzy matching, alias fallback, or payload-granted authority is allowed.
        This is an in-process routing aid, not WP3 worker enrollment or trust.
        """
        capability = self._items.get(task_type)
        if capability is None:
            return CapabilitySelection(None, {}, PolicyDecision(False, "capability_unavailable"),
                                       "none", "no_exact_task_type_match")
        if not capability.enabled:
            return CapabilitySelection(None, {}, PolicyDecision(False, "capability_disabled"),
                                       capability.name, "capability_disabled")
        if not isinstance(payload, dict):
            return CapabilitySelection(capability, {}, PolicyDecision(False, "invalid_task_payload"),
                                       capability.name, "payload_not_object")
        normalized = payload
        validator = capability.payload_validator
        if validator is not None:
            try:
                normalized = validator(payload)
            except (TypeError, ValueError) as exc:
                reason = str(exc)[:160]
                return CapabilitySelection(capability, {}, PolicyDecision(False, "payload_validation_failed"),
                                           capability.name, reason)
        decision = (policy or LocalWorkerPolicy()).evaluate(capability, normalized)
        return CapabilitySelection(
            capability, normalized, decision, capability.name,
            "exact_match" if decision.allowed else decision.reason,
        )

    def planner_capabilities(self) -> list[Capability]:
        return [
            item for item in self._items.values()
            if item.enabled and item.planner_allowed
        ]

    def describe(self) -> list[dict]:
        return [{
            "name": c.name,
            "description": c.description,
            "cost": c.cost,
            "licence": c.licence,
            "enabled": c.enabled,
            "planner_allowed": c.planner_allowed,
            "version": c.version,
            "permission_scopes": list(c.permission_scopes),
            "network_access": c.network_access,
            "sandbox_profile": c.sandbox_profile,
            "payload_validation": c.payload_validator is not None,
        } for c in sorted(self._items.values(), key=lambda x: x.name)]


def _unavailable(_request: TaskRequest) -> TaskResult:
    return TaskResult("blocked", error_code="specialist_not_qualified")


def build_default_registry() -> CapabilityRegistry:
    """Load only local, zero-default specialists; hosted/metered tools stay gated."""
    from .office_extract import extract_office, validate_office_payload
    from .tasks import (
        csv_dataset_profile,
        dataset_profile,
        document_text_analyze,
        generate_longform,
        generate_short,
        longform_script_draft,
        publish_check,
        research_topic_collect,
        short_script_draft,
        validate_csv_payload,
        validate_dataset_payload,
        validate_document_payload,
        validate_storyboard_payload,
        validate_storyboard,
        validate_generation_payload,
        validate_script_payload,
        validate_topic_payload,
    )

    registry = CapabilityRegistry()
    capabilities = (
        Capability(
            "studio.storyboard.validate",
            "Validate a Studio storyboard timeline locally without provider or render side effects",
            "zero-default", "project", validate_storyboard,
            planner_allowed=False, version="1.0",
            permission_scopes=("input:read",), network_access=False,
            sandbox_profile="in-process-bounded",
            payload_validator=validate_storyboard_payload,
        ),
        Capability(
            "research.topic.collect",
            "Collect source-backed public research and a compact evidence brief",
            "zero-default", "project", research_topic_collect,
            version="1.0", permission_scopes=("public_web:read", "artifact:write"),
            network_access=True, sandbox_profile="bwrap-project-ro-network",
            payload_validator=validate_topic_payload,
        ),
        Capability(
            "content.short.script.draft",
            "Draft a research-backed Short script for human editorial review",
            "zero-default", "project", short_script_draft,
            version="1.0", permission_scopes=("public_web:read", "local_model:inference", "artifact:write"),
            network_access=True, sandbox_profile="bwrap-project-ro-network",
            payload_validator=validate_script_payload,
        ),
        Capability(
            "content.longform.script.draft",
            "Draft a source-checked long-form script for human editorial review",
            "zero-default", "project", longform_script_draft,
            version="1.0", permission_scopes=("public_web:read", "local_model:inference", "artifact:write"),
            network_access=True, sandbox_profile="bwrap-project-ro-network",
            payload_validator=validate_script_payload,
        ),
        Capability(
            "documents.text.analyze",
            "Analyze supplied text without reading arbitrary local files",
            "zero-default", "project", document_text_analyze,
            version="1.0", permission_scopes=("input:read",),
            sandbox_profile="in-process-bounded",
            payload_validator=validate_document_payload,
        ),
        Capability(
            "documents.office.extract",
            "Extract bounded text from inline DOCX/XLSX bytes without filesystem or network access",
            "zero-default", "PSF License", extract_office,
            planner_allowed=False, version="1.0",
            permission_scopes=("input:read", "document:extract"),
            network_access=False, sandbox_profile="in-process-bounded",
            payload_validator=validate_office_payload,
        ),
        Capability(
            "data.dataset.profile",
            "Profile a bounded inline dataset with deterministic local statistics",
            "zero-default", "project", dataset_profile,
            version="1.0", permission_scopes=("input:read", "data:analyze"),
            sandbox_profile="in-process-bounded",
            payload_validator=validate_dataset_payload,
        ),
        Capability(
            "data.csv.profile",
            "Profile a bounded inline CSV payload without filesystem or network access",
            "zero-default", "PSF License", csv_dataset_profile,
            planner_allowed=False, version="1.0",
            permission_scopes=("input:read", "data:analyze"),
            network_access=False, sandbox_profile="in-process-bounded",
            payload_validator=validate_csv_payload,
        ),
        Capability(
            "content.short.generate",
            "Run the local procedural Short render check; not a publishable content run",
            "zero-default", "project", generate_short,
            planner_allowed=False, version="1.0",
            permission_scopes=("workspace:read", "artifact:write"),
            network_access=False, sandbox_profile="bwrap-project-ro-output-rw",
            payload_validator=validate_generation_payload,
        ),
        Capability(
            "content.longform.generate",
            "Full long-form video generation; disabled until a verified review-only path exists",
            "zero-default", "project", generate_longform,
            enabled=False, planner_allowed=False, version="1.0",
            permission_scopes=("workspace:read", "artifact:write"),
            network_access=False, sandbox_profile="disabled",
            payload_validator=validate_generation_payload,
        ),
        Capability(
            "publishing.check",
            "Readiness-only publishing check; external upload and posting are disabled",
            "zero-default", "project", publish_check,
            planner_allowed=False, version="1.0",
            permission_scopes=("publishing:readiness-check",),
            network_access=False, sandbox_profile="in-process-readonly",
        ),
    )
    for capability in capabilities:
        registry.register(capability)
    return registry
