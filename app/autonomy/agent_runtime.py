"""Inventory desktop coding-agent apps and CLI runtimes without launching them.

Desktop discovery is intentionally separate from WSL CLI discovery: Windows GUI
apps are not executable through the project's fixed-module specialist sandbox.
This module is inventory/readiness only, not canonical WP3 worker identity/trust.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import shutil
from typing import Iterable


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    display_name: str
    executable: str
    roles: tuple[str, ...]
    priority: int
    cost_model: str
    requires_approval: bool = True
    enabled: bool = True


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
        if spec.agent_id in self._specs:
            raise ValueError(f"agent already registered: {spec.agent_id}")
        self._specs[spec.agent_id] = spec

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
