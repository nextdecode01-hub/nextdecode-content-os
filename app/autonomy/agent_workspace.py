"""Sanitized workspaces and fail-closed coding-agent execution planning."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

from .agent_runtime import agent_runtime_registry

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = ROOT / "outputs" / "autonomy" / "agent-workspaces"
EXCLUDED_DIRS = frozenset({
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "outputs", "data", "media", "shots",
    "videos", "secrets", "credentials",
})
EXCLUDED_FILES = frozenset({
    ".env", ".env.local", "youtube_token.json", "client_secret.json",
    "credentials.json", "token.json", "token_usage.json",
})
MAX_FILES = 6000
MAX_TOTAL_BYTES = 300 * 1024 * 1024
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_RESULT_FILES = 6000
MAX_RESULT_BYTES = 300 * 1024 * 1024
MAX_TIMEOUT_SECONDS = 3600


class WorkspaceError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkspaceSnapshot:
    workspace_id: str
    path: str
    source_root: str
    created_at: str
    file_count: int
    total_bytes: int
    manifest_sha256: str
    status: str = "prepared_not_executed"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _workspace_paths(workspace_id: str) -> tuple[Path, Path]:
    if (not isinstance(workspace_id, str) or len(workspace_id) != 32
            or any(ch not in "0123456789abcdef" for ch in workspace_id)):
        raise WorkspaceError("invalid workspace ID")
    base = WORKSPACE_ROOT / workspace_id
    manifest_path = base / "manifest.json"
    workspace_path = base / "workspace"
    if not manifest_path.is_file() or not workspace_path.is_dir():
        raise WorkspaceError("workspace or manifest does not exist")
    return workspace_path, manifest_path


def _load_manifest(workspace_id: str) -> tuple[dict, Path]:
    workspace, manifest_path = _workspace_paths(workspace_id)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkspaceError("workspace manifest is unreadable") from None
    if manifest.get("schema_version") != "nextdecode.agent-workspace.v1":
        raise WorkspaceError("unsupported workspace manifest")
    if manifest.get("workspace_id") != workspace_id:
        raise WorkspaceError("workspace identity mismatch")
    return manifest, workspace


def prepare_workspace(source_root: str | Path = ROOT) -> WorkspaceSnapshot:
    """Copy a bounded snapshot; never modify the source repository."""
    source = Path(source_root).resolve(strict=True)
    if not source.is_dir() or source != ROOT.resolve():
        raise WorkspaceError("workspace source must be the configured project root")
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    WORKSPACE_ROOT.chmod(0o700)
    workspace_id = uuid.uuid4().hex
    destination = WORKSPACE_ROOT / workspace_id / "workspace"
    destination.parent.mkdir(mode=0o700)
    entries: list[dict] = []
    total_bytes = 0
    try:
        for current, dirs, files in os.walk(source, topdown=True, followlinks=False):
            current_path = Path(current)
            relative_dir = current_path.relative_to(source)
            dirs[:] = [
                name for name in sorted(dirs)
                if name not in EXCLUDED_DIRS and not (current_path / name).is_symlink()
            ]
            (destination / relative_dir).mkdir(parents=True, exist_ok=True)
            for filename in sorted(files):
                src = current_path / filename
                if filename in EXCLUDED_FILES or src.is_symlink() or not src.is_file():
                    continue
                size = src.stat().st_size
                if size > MAX_FILE_BYTES:
                    continue
                total_bytes += size
                if total_bytes > MAX_TOTAL_BYTES or len(entries) >= MAX_FILES:
                    raise WorkspaceError("project snapshot exceeds configured size/file bounds")
                rel = src.relative_to(source).as_posix()
                dst = destination / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                dst.chmod(0o700 if src.stat().st_mode & 0o111 else 0o600)
                entries.append({"path": rel, "size": size, "sha256": _sha256(dst)})
        entries.sort(key=lambda item: item["path"])
        created_at = datetime.now(timezone.utc).isoformat()
        manifest = {
            "schema_version": "nextdecode.agent-workspace.v1",
            "workspace_id": workspace_id,
            "source_root": str(source),
            "created_at": created_at,
            "file_count": len(entries),
            "total_bytes": total_bytes,
            "excluded_directories": sorted(EXCLUDED_DIRS),
            "excluded_files": sorted(EXCLUDED_FILES),
            "files": entries,
            "agent_execution_enabled": False,
            "network_access": False,
            "credentials_included": False,
        }
        raw = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
        manifest_path = destination.parent / "manifest.json"
        manifest_path.write_bytes(raw)
        manifest_path.chmod(0o600)
        return WorkspaceSnapshot(
            workspace_id, str(destination), str(source), created_at, len(entries),
            total_bytes, hashlib.sha256(raw).hexdigest(),
        )
    except Exception:
        shutil.rmtree(destination.parent, ignore_errors=True)
        raise


def list_workspaces() -> list[dict]:
    if not WORKSPACE_ROOT.exists():
        return []
    result = []
    for manifest_path in sorted(WORKSPACE_ROOT.glob("*/manifest.json")):
        try:
            raw = manifest_path.read_bytes()
            manifest = json.loads(raw)
            result.append({
                "workspace_id": manifest.get("workspace_id"),
                "path": str(manifest_path.parent / "workspace"),
                "created_at": manifest.get("created_at"),
                "file_count": manifest.get("file_count"),
                "total_bytes": manifest.get("total_bytes"),
                "manifest_sha256": hashlib.sha256(raw).hexdigest(),
                "status": "prepared_not_executed",
            })
        except (OSError, ValueError):
            result.append({"path": str(manifest_path), "status": "invalid_manifest"})
    return result


@dataclass(frozen=True)
class AgentExecutionPolicy:
    invocation_enabled: bool = False
    network_enabled: bool = False
    credential_forwarding: bool = False
    direct_repository_write: bool = False


class AgentExecutionAdapter:
    """Builds a reviewable invocation plan; never starts a process in this phase."""

    def __init__(self, policy: AgentExecutionPolicy | None = None):
        self.policy = policy or AgentExecutionPolicy()

    def plan(self, *, agent_id: str, workspace_id: str, task: str,
             timeout_seconds: int = 900) -> dict:
        if not self.policy.invocation_enabled:
            raise PermissionError("agent invocation is disabled by local execution policy")
        if self.policy.network_enabled or self.policy.credential_forwarding or self.policy.direct_repository_write:
            raise PermissionError("requested execution policy exceeds the safe local boundary")
        if not isinstance(task, str) or not 1 <= len(task.strip()) <= 8000:
            raise ValueError("task instruction must contain 1..8000 characters")
        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise ValueError("timeout must be between 1 and 3600 seconds")
        manifest, workspace = _load_manifest(workspace_id)
        if manifest.get("agent_execution_enabled") is not False:
            raise WorkspaceError("workspace manifest does not explicitly deny agent execution")
        if manifest.get("network_access") is not False or manifest.get("credentials_included") is not False:
            raise WorkspaceError("workspace violates the no-network/no-credentials baseline")
        candidates = {item["agent_id"]: item for item in agent_runtime_registry.discover()}
        candidate = candidates.get(agent_id)
        if not candidate or not candidate.get("available"):
            raise WorkspaceError("requested local agent CLI is not installed")
        return {
            "schema_version": "nextdecode.agent-invocation-plan.v1",
            "plan_id": uuid.uuid4().hex,
            "agent_id": agent_id,
            "executable_path": candidate["executable_path"],
            "workspace_id": workspace_id,
            "workspace_path": str(workspace),
            "task_sha256": hashlib.sha256(task.strip().encode()).hexdigest(),
            "timeout_seconds": timeout_seconds,
            "network_access": False,
            "credential_forwarding": False,
            "direct_repository_write": False,
            "human_approval_required": True,
            "process_started": False,
            "status": "plan_only",
        }


def collect_workspace_changes(workspace_id: str) -> dict:
    """Report added/modified/deleted workspace files without importing them."""
    manifest, workspace = _load_manifest(workspace_id)
    baseline = {item["path"]: item for item in manifest.get("files", [])}
    observed: dict[str, dict] = {}
    total_bytes = 0
    for current, dirs, files in os.walk(workspace, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(name for name in dirs if not (current_path / name).is_symlink())
        for filename in sorted(files):
            path = current_path / filename
            if path.is_symlink() or not path.is_file():
                raise WorkspaceError("workspace contains a symlink or non-regular file")
            relative = path.relative_to(workspace).as_posix()
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                raise WorkspaceError("workspace result contains an oversized file")
            total_bytes += size
            if total_bytes > MAX_RESULT_BYTES or len(observed) >= MAX_RESULT_FILES:
                raise WorkspaceError("workspace result exceeds configured bounds")
            observed[relative] = {"size": size, "sha256": _sha256(path)}
    added = sorted(path for path in observed if path not in baseline)
    deleted = sorted(path for path in baseline if path not in observed)
    modified = sorted(
        path for path in observed.keys() & baseline.keys()
        if observed[path]["sha256"] != baseline[path]["sha256"]
    )
    changes = []
    for status, paths in (("added", added), ("modified", modified), ("deleted", deleted)):
        for path in paths:
            changes.append({
                "path": path,
                "status": status,
                "size": observed[path]["size"] if path in observed else baseline[path]["size"],
                "sha256": observed[path]["sha256"] if path in observed else None,
            })
    report = {
        "schema_version": "nextdecode.agent-change-report.v1",
        "workspace_id": workspace_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "baseline_manifest_sha256": hashlib.sha256(
            (WORKSPACE_ROOT / workspace_id / "manifest.json").read_bytes()
        ).hexdigest(),
        "added_count": len(added),
        "modified_count": len(modified),
        "deleted_count": len(deleted),
        "changes": changes,
        "main_repository_modified": False,
        "automatic_import_allowed": False,
        "status": "changes_detected" if changes else "no_changes",
    }
    report_path = WORKSPACE_ROOT / workspace_id / "change-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.chmod(0o600)
    return report
