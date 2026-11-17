"""Inventory desktop coding-agent apps and CLI runtimes without launching them.

Desktop discovery is intentionally separate from WSL CLI discovery: Windows GUI
apps are not executable through the project's fixed-module specialist sandbox.
This module is inventory/readiness only, not canonical WP3 worker identity/trust.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import re
import shutil
from typing import Iterable


# Qualification evidence must be digest-verifiable: an arbitrary non-empty
# reference string does not establish that an agent ever passed a recorded
# qualification test run.
_QUALIFICATION_DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    display_name: str
    executable: str
    roles: tuple[str, ...]
    priority: int
    cost_model: str
    execution_type: str = "cli"
    configuration_evidence_env: tuple[str, ...] = ()
    requires_approval: bool = True
    enabled: bool = True


@dataclass(frozen=True)
class AgentReadinessEvidence:
    """Non-secret, externally supplied observations; absence means unknown."""

    configured: bool | None = None
    configuration_reference: str | None = None
    version: str | None = None
    qualification_reference: str | None = None
    qualification_passed: bool = False
    qualification_capabilities: tuple[str, ...] = ()
    availability_observed_at: str | None = None
    availability: bool | None = None
    suspended: bool = False
    revoked: bool = False
    invocation_authorized: bool = False
    qualification_evidence_sha256: str | None = None


DEFAULT_AGENTS = (
    AgentSpec("opencode", "OpenCode", "opencode",
              ("code_implementation", "code_review", "repository_analysis"),
              10, "provider_dependent"),
    AgentSpec("aider", "Aider", "aider",
              ("code_implementation", "code_review", "repository_analysis"),
              20, "provider_dependent"),
    AgentSpec("qoder", "Qoder", "qoder",
              ("code_implementation", "repository_analysis"),
              30, "provider_dependent"),
    AgentSpec("kilo", "Kilo", "kilocode",
              ("security_review", "code_review", "repository_analysis"),
              40, "provider_dependent"),
    AgentSpec("continue", "Continue", "continue",
              ("code_implementation", "code_review"), 50, "unknown", "desktop"),
    AgentSpec("deepseek", "DeepSeek", "ollama",
              ("reasoning", "research", "architecture", "audit"), 60, "model_license_and_local_availability_unknown", "local_model"),
    AgentSpec("github-copilot", "GitHub Copilot", "copilot",
              ("code_review", "regression_review"), 70, "subscription_and_entitlement_unknown", "desktop"),
    AgentSpec("antigravity", "Antigravity", "antigravity",
              ("product", "ui_engineering", "visual_engineering"), 80, "provider_dependent", "desktop"),
    AgentSpec("hermes-agent", "Hermes Agent", "hermes-agent",
              ("operator", "repository_analysis"), 90, "unknown", "manual_operator"),
)

# Paths are discovered under Windows user profiles mounted by WSL. No user
# profile name is hard-coded, and no candidate executable is ever run.
DESKTOP_CANDIDATES = {
    "qoder": ("Qoder", "AppData/Local/Programs/Qoder/Qoder.exe",
              ("code_implementation", "repository_analysis")),
    "opencode": ("OpenCode", "AppData/Local/Programs/ai.opencode.desktop/OpenCode.exe",
                 ("code_implementation", "code_review", "repository_analysis")),
    "antigravity": ("Antigravity", "AppData/Local/Programs/antigravity/Antigravity.exe",
                    ("code_implementation", "repository_analysis")),
    "cursor": ("Cursor", "AppData/Local/Programs/cursor/Cursor.exe",
               ("code_implementation", "code_review", "repository_analysis")),
    "vscode": ("Visual Studio Code", "AppData/Local/Programs/Microsoft VS Code/Code.exe",
               ("code_implementation", "code_review", "repository_analysis")),
}


class AgentRuntimeRegistry:
    """Small deterministic inventory of candidate WSL CLI runtimes."""

    def __init__(self, specs: Iterable[AgentSpec] = DEFAULT_AGENTS):
        self._specs: dict[str, AgentSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: AgentSpec) -> None:
        if not spec.agent_id or len(spec.agent_id) > 80:
            raise ValueError("agent_id must be 1..80 characters")
        if not spec.executable or len(spec.executable) > 120:
            raise ValueError("agent executable must be 1..120 characters")
        if spec.priority < 0 or not spec.roles:
            raise ValueError("agent priority and roles are required")
        if spec.execution_type not in {"cli", "desktop", "local_model", "manual_operator"}:
            raise ValueError("agent execution type is invalid")
        if any(not name or "=" in name for name in spec.configuration_evidence_env):
            raise ValueError("configuration evidence names are invalid")
        if spec.agent_id in self._specs:
            raise ValueError(f"agent already registered: {spec.agent_id}")
        self._specs[spec.agent_id] = spec

    def get_spec(self, agent_id: str) -> AgentSpec | None:
        """Return immutable candidate metadata without probing or executing it."""
        if not isinstance(agent_id, str):
            return None
        return self._specs.get(agent_id)

    def discover(self) -> list[dict]:
        """Inspect PATH only; do not execute candidate binaries."""
        result = []
        for spec in sorted(self._specs.values(), key=lambda item: (item.priority, item.agent_id)):
            path = shutil.which(spec.executable) if spec.enabled else None
            result.append({
                **asdict(spec),
                "roles": list(spec.roles),
                "available": bool(path),
                "executable_path": path,
                "state": "available_requires_approval" if path and spec.requires_approval
                         else "available_not_approved" if path
                         else "not_installed" if spec.enabled
                         else "disabled",
                "invocation_enabled": False,
                "runtime_type": "wsl_cli",
            })
        return result

    def rank(self, role: str) -> list[dict]:
        candidates = [
            item for item in self.discover()
            if role in item["roles"] and item["available"] and item["enabled"]
        ]
        return sorted(candidates, key=lambda item: (item["priority"], item["agent_id"]))

    def _installation_evidence(self, spec: AgentSpec) -> list[dict]:
        """Return filesystem/PATH observations only; never launch a candidate."""
        evidence = []
        path = shutil.which(spec.executable) if spec.enabled else None
        if path:
            evidence.append({"kind": "path_executable", "reference": path})
        for desktop in discover_windows_desktop_agents():
            if desktop["agent_id"] == spec.agent_id and desktop["available"]:
                evidence.append({"kind": "desktop_application", "reference": desktop["executable_path"]})
        return evidence

    @staticmethod
    def _fresh_observation(value: str | None, now: datetime, stale_after_seconds: int) -> bool:
        if not value:
            return False
        try:
            observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if observed.tzinfo is None:
                return False
            return (now - timedelta(seconds=max(1, stale_after_seconds))
                    <= observed <= now + timedelta(seconds=60))
        except ValueError:
            return False

    def get_readiness(self, agent_id: str, *, evidence: dict[str, AgentReadinessEvidence] | None = None,
                      now: datetime | None = None, stale_after_seconds: int = 300) -> dict | None:
        """Build a non-executing record; positive states require explicit evidence."""
        spec = self._specs.get(agent_id)
        if spec is None:
            return None
        observed_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        item = (evidence or {}).get(agent_id, AgentReadinessEvidence())
        installations = self._installation_evidence(spec)
        installed = bool(installations)
        if item.configured is not None:
            configured = item.configured
            config_reason = "explicit_configuration_evidence"
        elif spec.configuration_evidence_env:
            configured = all(bool(os.getenv(name, "").strip()) for name in spec.configuration_evidence_env)
            config_reason = "configuration_evidence_present" if configured else "configuration_evidence_missing"
        else:
            configured = None
            config_reason = "configuration_evidence_not_recorded"
        qualified = bool(
            item.qualification_reference and item.qualification_passed
            and item.qualification_evidence_sha256
            and _QUALIFICATION_DIGEST_RE.fullmatch(item.qualification_evidence_sha256)
        )
        if qualified:
            qualified_reason = "qualification_evidence_recorded"
        elif item.qualification_reference or item.qualification_passed or item.qualification_evidence_sha256:
            qualified_reason = "qualification_evidence_not_verifiable"
        else:
            qualified_reason = "qualification_evidence_missing"
        qualification_pending = installed and not qualified and not item.revoked
        observation_fresh = self._fresh_observation(item.availability_observed_at, observed_at, stale_after_seconds)
        if item.revoked:
            available, availability_reason = False, "revoked"
        elif item.suspended:
            available, availability_reason = False, "suspended"
        elif not installed:
            available, availability_reason = False, "not_installed"
        elif configured is not True:
            available, availability_reason = False, "configuration_not_verified"
        elif not qualified:
            available, availability_reason = False, "qualification_not_verified"
        elif item.availability is not True:
            available, availability_reason = False, "availability_not_observed"
        elif not observation_fresh:
            available, availability_reason = False, "availability_evidence_stale"
        else:
            available, availability_reason = True, "fresh_explicit_observation"
        invocation_reason = "invocation_not_implemented"
        if item.revoked:
            invocation_reason = "revoked"
        elif item.suspended:
            invocation_reason = "suspended"
        elif not available:
            invocation_reason = "agent_not_available"
        return {
            "schema_version": "nextdecode.agent-readiness.v1",
            "agent_id": spec.agent_id,
            "display_name": spec.display_name,
            "provider": spec.display_name,
            "execution_type": spec.execution_type,
            "capability_declarations": list(spec.roles),
            "cost_classification": spec.cost_model,
            "cost_uncertainty": spec.cost_model in {"unknown", "provider_dependent", "subscription_and_entitlement_unknown", "model_license_and_local_availability_unknown"},
            "version": item.version,
            "installation_evidence": installations,
            "configuration_reference": item.configuration_reference,
            "qualification_reference": item.qualification_reference,
            "last_observed_availability": item.availability_observed_at,
            "states": {
                "discovered": {"value": True, "reason": "registered_inventory_candidate"},
                "installed": {"value": installed, "reason": "local_installation_evidence" if installed else "no_local_installation_evidence"},
                "configured": {"value": configured, "reason": config_reason},
                "qualification_pending": {"value": qualification_pending, "reason": "qualification_evidence_missing" if qualification_pending else "not_pending"},
                "qualified": {"value": qualified, "reason": qualified_reason},
                "available": {"value": available, "reason": availability_reason},
                "suspended": {"value": bool(item.suspended), "reason": "explicit_suspension_evidence" if item.suspended else "no_suspension_evidence"},
                "revoked": {"value": bool(item.revoked), "reason": "explicit_revocation_evidence" if item.revoked else "no_revocation_evidence"},
                "invocation_authorized": {"value": False, "reason": invocation_reason},
            },
            "transition_requirements": {
                "installed": "local executable or desktop application discovery evidence",
                "configured": "non-secret configuration/authentication evidence",
                "qualified": "digest-verifiable recorded qualification test evidence (64-hex evidence_sha256)",
                "available": "fresh explicit availability observation after installation, configuration and qualification",
                "invocation_authorized": "separate owner-approved execution bridge and assignment authorization; absent in AR-01",
            },
            "network_access": False,
            "credential_forwarding": False,
            "direct_repository_write": False,
            "invocation_enabled": False,
            "worker_trust": "not_represented",
            "wp5_authorization": "not_represented",
            "observed_at": observed_at.isoformat(),
        }

    def readiness(self, *, evidence: dict[str, AgentReadinessEvidence] | None = None,
                  now: datetime | None = None, stale_after_seconds: int = 300) -> dict:
        records = [self.get_readiness(agent_id, evidence=evidence, now=now,
                                      stale_after_seconds=stale_after_seconds)
                   for agent_id in sorted(self._specs)]
        return {
            "schema_version": "nextdecode.agent-readiness-report.v1",
            "mode": "read_only_local_inspection",
            "agents": records,
            "invocation_enabled": False,
            "network_access": False,
            "credential_forwarding": False,
            "direct_repository_write": False,
            "canonical_worker_trust": False,
            "canonical_wp5_authorization": False,
        }


agent_runtime_registry = AgentRuntimeRegistry()


def discover_windows_desktop_agents() -> list[dict]:
    """Find installed Windows desktop applications visible through WSL mounts."""
    users_root = Path("/mnt/c/Users")
    profiles = []
    if users_root.is_dir():
        profiles = [
            path for path in users_root.iterdir()
            if path.is_dir() and path.name.lower() not in {"public", "default", "default user", "all users"}
        ]
    results = []
    for agent_id, (name, relative, roles) in DESKTOP_CANDIDATES.items():
        matches = [profile / relative for profile in profiles if (profile / relative).is_file()]
        results.append({
            "agent_id": agent_id,
            "display_name": name,
            "roles": list(roles),
            "available": bool(matches),
            "executable_path": str(matches[0]) if matches else None,
            "matching_installations": len(matches),
            "runtime_type": "windows_desktop_app",
            "state": "installed_desktop_bridge_required" if matches else "not_detected",
            "launch_enabled": False,
            "workspace_bridge": "not_configured",
            "network_access": False,
            "credential_forwarding": False,
            "direct_repository_write": False,
        })
    return results


def execution_readiness_report() -> dict:
    """Report desktop and CLI prerequisites without launching or configuring agents."""
    import os

    cli_agents = agent_runtime_registry.discover()
    desktop_agents = discover_windows_desktop_agents()
    bwrap_path = shutil.which("bwrap")
    project_root = Path(__file__).resolve().parents[2]
    python_path = project_root / "venv" / "bin" / "python"
    workspace_root = project_root / "outputs" / "autonomy" / "agent-workspaces"
    desktop_found = any(item["available"] for item in desktop_agents)
    checks = [
        {
            "name": "windows_desktop_agent_apps",
            "status": "detected_bridge_required" if desktop_found else "not_detected",
            "detail": "Windows desktop applications detected; a controlled desktop/workspace bridge is still required."
            if desktop_found else "No supported Windows desktop agent application was detected under mounted user profiles.",
        },
        {
            "name": "wsl_cli_agents",
            "status": "available" if any(item["available"] for item in cli_agents) else "not_used_for_desktop_apps",
            "detail": "CLI inventory is separate; absence of WSL CLIs does not mean Windows desktop apps are absent.",
        },
        {
            "name": "bubblewrap",
            "status": "ready" if bwrap_path else "blocked",
            "detail": bwrap_path or "bwrap is not installed; no execution fallback is permitted.",
        },
        {
            "name": "project_virtualenv",
            "status": "ready" if python_path.is_file() and os.access(python_path, os.X_OK) else "blocked",
            "detail": str(python_path),
        },
        {
            "name": "isolated_workspace_root",
            "status": "ready" if workspace_root.is_dir() else "not_prepared",
            "detail": str(workspace_root),
        },
    ]
    blockers = [item["name"] for item in checks if item["status"] == "blocked"]
    return {
        "schema_version": "nextdecode.agent-execution-readiness.v2",
        "status": "desktop_bridge_required" if desktop_found and not blockers
                  else "blocked" if blockers else "no_desktop_agent_detected",
        "checks": checks,
        "desktop_agents": desktop_agents,
        "cli_agents": cli_agents,
        "invocation_enabled": False,
        "desktop_launch_enabled": False,
        "network_access": False,
        "credential_forwarding": False,
        "direct_repository_write": False,
        "human_approval_required": True,
        "automatic_installation_performed": False,
        "process_started": False,
        "blockers": blockers,
        "next_boundary": "Implement a Windows desktop-to-isolated-workspace bridge; do not treat GUI apps as WSL CLI binaries.",
    }
