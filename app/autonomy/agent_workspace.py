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

from .agent_assignment import (
    AgentAssignmentPlanner, AssignmentRequest, QualificationRecord,
)
from .agent_runtime import AgentReadinessEvidence, agent_runtime_registry

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
MAX_ASSIGNMENT_LEDGER = 4096

# Machine-readable resolution requirement for every assignment denial code
# produced by AgentAssignmentPlanner (presentation lives at this boundary).
_ASSIGNMENT_REQUIREMENTS = {
    "agent_unknown": "register the agent in the local readiness inventory",
    "assignment_planning_not_authorized": "explicit planning authorization for this assignment",
    "assignment_identity_incomplete": "non-empty assignment ID, task ID and correlation ID",
    "assignment_objective_or_capability_missing": "a bounded objective and a declared capability",
    "acceptance_criteria_missing": "at least one explicit acceptance criterion",
    "timeout_out_of_bounds": "a timeout between 1 and 3600 seconds",
    "input_references_invalid": "valid input reference strings",
    "permission_scope_invalid": "valid permission scope strings",
    "capability_not_declared": "declare the requested capability in the agent's role inventory",
    "agent_not_installed": "local installation evidence for the requested agent",
    "agent_configuration_unverified": "non-secret configuration evidence for the agent",
    "readiness_not_available": "a fresh explicit availability observation",
    "readiness_qualification_not_verified_for_capability": "capability-specific qualification evidence",
    "agent_suspended": "explicit evidence that the suspension is lifted",
    "agent_revoked": "explicit evidence that the agent is reinstated",
    "readiness_qualification_reference_missing": "a qualification reference in the readiness evidence",
    "availability_not_confirmed": "explicit availability confirmation",
    "availability_evidence_stale_or_future": "an availability observation within the freshness and clock-skew bounds",
    "qualification_record_missing": "a digest-verifiable qualification record",
    "qualification_subject_or_capability_mismatch": "a qualification record matching the agent and capability",
    "qualification_not_passed": "a passed qualification run",
    "qualification_provenance_incomplete": "qualification ID, test suite and evidence reference",
    "qualification_digest_invalid": "a valid 64-hex qualification evidence digest",
    "qualification_timestamp_invalid": "a parseable, non-future qualification timestamp",
    "qualification_expired": "a qualification record that has not expired",
    "duplicate_assignment": "a new assignment ID for a further assignment",
}


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
        self._assignment_ledger: set[str] = set()

    def plan(self, *, agent_id: str, workspace_id: str, task: str,
             timeout_seconds: int = 900) -> dict:
        """Generate a reviewable invocation plan without starting anything.

        Plan generation is deliberately independent of the invocation gate:
        the default (safe) policy keeps ``invocation_enabled=False`` and this
        method still produces a plan that records that gate explicitly.
        Starting a process is refused separately by :meth:`execute`.
        """
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
        manifest_path = WORKSPACE_ROOT / workspace_id / "manifest.json"
        manifest_bytes = manifest_path.read_bytes()
        return {
            "schema_version": "nextdecode.agent-invocation-plan.v1",
            "plan_id": uuid.uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workspace_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "agent_id": agent_id,
            "executable_path": candidate["executable_path"],
            "workspace_id": workspace_id,
            "workspace_path": str(workspace),
            "task_sha256": hashlib.sha256(task.strip().encode()).hexdigest(),
            "timeout_seconds": timeout_seconds,
            "network_access": False,
            "credential_forwarding": False,
            "direct_repository_write": False,
            "invocation_authorized": bool(self.policy.invocation_enabled),
            "invocation_gate": {
                "invocation_enabled": bool(self.policy.invocation_enabled),
                "reason": ("invocation_enabled_by_policy" if self.policy.invocation_enabled
                           else "invocation_disabled_by_policy"),
            },
            "human_approval_required": True,
            "process_started": False,
            "status": "plan_only",
        }

    def execute(self, plan: dict) -> dict:
        """Fail-closed execution boundary: refuse every attempt to run a plan.

        Planning is the end of this adapter's authority in this phase. No
        policy value, plan field or caller argument can start a process here.
        """
        if not isinstance(plan, dict) or plan.get("schema_version") != "nextdecode.agent-invocation-plan.v1":
            raise ValueError("execute requires a valid adapter invocation plan")
        raise PermissionError("agent process execution is not permitted in this phase")

    def plan_assignment(self, request: AssignmentRequest, *,
                        readiness_evidence: dict[str, "AgentReadinessEvidence"] | None = None,
                        qualification: QualificationRecord | None = None,
                        planning_authorized: bool = False,
                        now: datetime | None = None) -> dict:
        """Readiness-aware, plan-only assignment decision through this boundary.

        Delegates to :class:`AgentAssignmentPlanner` (no duplicate readiness
        logic) and adds idempotent duplicate-assignment detection for accepted
        assignments. The returned decision never reports an executed
        assignment: ``process_started`` is always ``False``.
        """
        decision = AgentAssignmentPlanner().plan(
            request, readiness_evidence=readiness_evidence, qualification=qualification,
            planning_authorized=planning_authorized, now=now,
        )
        if "required_missing_evidence" not in decision:
            decision["required_missing_evidence"] = [
                {"code": code,
                 "requirement": _ASSIGNMENT_REQUIREMENTS.get(code, "resolve the denial reason")}
                for code in decision.get("denial_reason_codes", [])
            ]
        if not decision.get("accepted"):
            return decision
        assignment_id = getattr(request, "assignment_id", "")
        if assignment_id in self._assignment_ledger:
            return {
                "schema_version": decision["schema_version"],
                "plan_id": decision["plan_id"],
                "assignment_id": assignment_id,
                "task_id": decision.get("task_id"),
                "agent_id": decision.get("agent_id"),
                "capability": decision.get("capability"),
                "correlation_id": decision.get("correlation_id"),
                "status": "denied",
                "accepted": False,
                "denial_reason_codes": ["duplicate_assignment"],
                "required_missing_evidence": [{
                    "code": "duplicate_assignment",
                    "requirement": "issue a new assignment ID for a further assignment",
                }],
                "policy_evaluation": decision["policy_evaluation"],
                "process_started": False,
                "network_access": False,
                "credential_forwarding": False,
                "direct_repository_write": False,
                "human_approval_required": True,
                "observed_at": decision["observed_at"],
            }
        if len(self._assignment_ledger) >= MAX_ASSIGNMENT_LEDGER:
            raise WorkspaceError("assignment ledger reached its bounded limit")
        self._assignment_ledger.add(assignment_id)
        return decision


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
