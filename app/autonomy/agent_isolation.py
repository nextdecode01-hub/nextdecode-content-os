"""AEC-02 isolated execution preflight.

This module establishes the two-key approval and immutable-input checks. It
intentionally does not launch a process: an OS sandbox backend must be
independently qualified before execution can be enabled.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
import secrets
import stat
from pathlib import Path, PurePosixPath
import re

from .agent_workspace import WORKSPACE_ROOT, WorkspaceError, _load_manifest

_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_PLAN_TTL_SECONDS = 300
_APPROVAL_TTL_SECONDS = 300


@dataclass(frozen=True)
class OwnerExecutionApproval:
    approval_id: str
    plan_id: str
    workspace_id: str
    task_sha256: str
    approved_at: str
    expires_at: str
    scope: str
    owner_identity: str
    approval_evidence_reference: str
    plan_sha256: str = ""
    signature: str = ""


def _canonical_json(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _approval_payload(approval: OwnerExecutionApproval) -> dict:
    return {
        "schema_version": "nextdecode.owner-execution-approval.v1",
        "approval_id": approval.approval_id,
        "plan_id": approval.plan_id,
        "workspace_id": approval.workspace_id,
        "task_sha256": approval.task_sha256,
        "plan_sha256": approval.plan_sha256,
        "approved_at": approval.approved_at,
        "expires_at": approval.expires_at,
        "scope": approval.scope,
        "owner_identity": approval.owner_identity,
        "approval_evidence_reference": approval.approval_evidence_reference,
    }


def _approval_key_path() -> Path:
    return WORKSPACE_ROOT / ".owner-approval-hmac.key"


def _load_or_create_approval_key() -> bytes:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    if WORKSPACE_ROOT.is_symlink():
        raise PermissionError("approval key directory must not be a symlink")
    WORKSPACE_ROOT.chmod(0o700)
    path = _approval_key_path()
    if not path.exists():
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(secrets.token_bytes(32))
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            pass
    if path.is_symlink():
        raise PermissionError("approval key must not be a symlink")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
        raise PermissionError("approval key must be a private regular file")
    key = path.read_bytes()
    if len(key) != 32:
        raise PermissionError("approval key has an invalid length")
    return key


class OwnerApprovalAuthority:
    """Host-local HMAC authority; key is never included in staged workspaces."""

    SCOPE = "single_plan_single_workspace_no_network_no_credentials"

    def issue(self, plan: dict, *, owner_identity: str,
              approval_evidence_reference: str,
              now: datetime | None = None, ttl_seconds: int = _APPROVAL_TTL_SECONDS) -> OwnerExecutionApproval:
        if not isinstance(plan, dict) or plan.get("schema_version") != "nextdecode.agent-invocation-plan.v1":
            raise ValueError("a valid invocation plan is required")
        if plan.get("status") != "plan_only" or plan.get("process_started") is not False:
            raise ValueError("only an unexecuted plan can be approved")
        if plan.get("invocation_authorized") is not False:
            raise ValueError("plan must not self-authorize invocation")
        if not isinstance(owner_identity, str) or not owner_identity.strip():
            raise ValueError("owner identity is required")
        if not isinstance(approval_evidence_reference, str) or not approval_evidence_reference.strip():
            raise ValueError("approval evidence reference is required")
        if not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= _APPROVAL_TTL_SECONDS:
            raise ValueError("approval TTL must be between 1 and 300 seconds")
        issued = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        plan_digest = hashlib.sha256(_canonical_json(plan)).hexdigest()
        unsigned = OwnerExecutionApproval(
            approval_id=secrets.token_hex(16),
            plan_id=str(plan.get("plan_id", "")),
            workspace_id=str(plan.get("workspace_id", "")),
            task_sha256=str(plan.get("task_sha256", "")),
            approved_at=issued.isoformat(),
            expires_at=(issued + timedelta(seconds=ttl_seconds)).isoformat(),
            scope=self.SCOPE,
            owner_identity=owner_identity.strip(),
            approval_evidence_reference=approval_evidence_reference.strip(),
            plan_sha256=plan_digest,
        )
        signature = hmac.new(_load_or_create_approval_key(), _canonical_json(_approval_payload(unsigned)), hashlib.sha256).hexdigest()
        return OwnerExecutionApproval(**{**unsigned.__dict__, "signature": signature})

    def save(self, approval: OwnerExecutionApproval, plan: dict) -> Path:
        if not isinstance(approval, OwnerExecutionApproval):
            raise TypeError("an owner approval artifact is required")
        if not self.verify(approval, plan):
            raise ValueError("approval signature or plan binding is invalid")
        directory = WORKSPACE_ROOT / "owner-approvals"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if directory.is_symlink():
            raise PermissionError("approval artifact directory must not be a symlink")
        directory.chmod(0o700)
        path = directory / f"{approval.approval_id}.json"
        if path.exists() or path.is_symlink():
            raise FileExistsError("approval artifact already exists")
        document = {**_approval_payload(approval), "signature": approval.signature}
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        return path

    def load(self, path: str | Path, plan: dict) -> OwnerExecutionApproval:
        artifact_path = Path(path)
        directory = (WORKSPACE_ROOT / "owner-approvals").resolve()
        if artifact_path.is_symlink() or not artifact_path.is_file():
            raise PermissionError("approval artifact is missing or unsafe")
        resolved = artifact_path.resolve(strict=True)
        if resolved.parent != directory:
            raise PermissionError("approval artifact must remain in the owner approval directory")
        info = resolved.stat()
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("approval artifact must be a private regular file")
        document = json.loads(resolved.read_text(encoding="utf-8"))
        expected_fields = {
            "schema_version", "approval_id", "plan_id", "workspace_id",
            "task_sha256", "plan_sha256", "approved_at", "expires_at",
            "scope", "owner_identity", "approval_evidence_reference", "signature",
        }
        if not isinstance(document, dict) or set(document) != expected_fields:
            raise ValueError("approval artifact schema is invalid")
        if document["schema_version"] != "nextdecode.owner-execution-approval.v1":
            raise ValueError("unsupported approval artifact schema")
        approval = OwnerExecutionApproval(**{
            key: document[key] for key in expected_fields
            if key != "schema_version"
        })
        if resolved.name != f"{approval.approval_id}.json" or not self.verify(approval, plan):
            raise PermissionError("approval artifact signature or identity is invalid")
        return approval

    def verify(self, approval: OwnerExecutionApproval, plan: dict) -> bool:
        if not isinstance(approval, OwnerExecutionApproval) or not isinstance(plan, dict):
            return False
        if not _SHA256.fullmatch(approval.plan_sha256 or "") or not _SHA256.fullmatch(approval.signature or ""):
            return False
        expected_plan_digest = hashlib.sha256(_canonical_json(plan)).hexdigest()
        if not hmac.compare_digest(expected_plan_digest, approval.plan_sha256):
            return False
        expected = hmac.new(_load_or_create_approval_key(), _canonical_json(_approval_payload(approval)), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, approval.signature)


@dataclass(frozen=True)
class ExecutionPreflight:
    plan: dict
    approval: OwnerExecutionApproval
    readiness_observed_at: str
    readiness_available: bool
    readiness_qualified: bool
    readiness_not_suspended: bool
    readiness_not_revoked: bool
    staged_package_id: str


def _time(value: str) -> datetime | None:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return None
    if result.tzinfo is None:
        return None
    return result.astimezone(timezone.utc)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class AgentIsolationPreflight:
    """Validate every launch prerequisite without starting a child process."""

    def __init__(self, *, plan_ttl_seconds: int = _PLAN_TTL_SECONDS,
                 approval_ttl_seconds: int = _APPROVAL_TTL_SECONDS):
        self.plan_ttl_seconds = plan_ttl_seconds
        self.approval_ttl_seconds = approval_ttl_seconds

    def validate(self, preflight: ExecutionPreflight, *, now: datetime | None = None) -> dict:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        issues: list[str] = []
        plan = preflight.plan if isinstance(preflight.plan, dict) else {}
        approval = preflight.approval

        if plan.get("schema_version") != "nextdecode.agent-invocation-plan.v1":
            issues.append("invocation_plan_invalid")
        if plan.get("status") != "plan_only" or plan.get("process_started") is not False:
            issues.append("invocation_plan_not_unexecuted")
        if plan.get("invocation_authorized") is not False:
            issues.append("planning_must_not_grant_invocation")
        if plan.get("network_access") is not False or plan.get("credential_forwarding") is not False:
            issues.append("plan_exceeds_isolation_policy")
        if plan.get("direct_repository_write") is not False:
            issues.append("repository_write_must_be_disabled")

        plan_time = _time(plan.get("created_at") or plan.get("observed_at"))
        if plan_time is None or not current - timedelta(seconds=self.plan_ttl_seconds) <= plan_time <= current + timedelta(seconds=30):
            issues.append("invocation_plan_stale_or_future")

        if not isinstance(approval, OwnerExecutionApproval):
            issues.append("owner_approval_artifact_invalid")
            approval = OwnerExecutionApproval("", "", "", "", "", "", "", "", "")
        if approval.scope != OwnerApprovalAuthority.SCOPE:
            issues.append("owner_approval_scope_invalid")
        if not approval.approval_id.strip() or not approval.owner_identity.strip() or not approval.approval_evidence_reference.strip():
            issues.append("owner_approval_provenance_missing")
        try:
            if not OwnerApprovalAuthority().verify(approval, plan):
                issues.append("owner_approval_signature_invalid")
        except (OSError, PermissionError):
            issues.append("owner_approval_key_unavailable_or_unsafe")
        if approval.plan_id != plan.get("plan_id") or approval.workspace_id != plan.get("workspace_id"):
            issues.append("owner_approval_binding_mismatch")
        if approval.task_sha256 != plan.get("task_sha256") or not _SHA256.fullmatch(approval.task_sha256 or ""):
            issues.append("owner_approval_task_binding_mismatch")
        approved_at, expires_at = _time(approval.approved_at), _time(approval.expires_at)
        if approved_at is None or expires_at is None or expires_at <= current or expires_at <= approved_at:
            issues.append("owner_approval_expired_or_invalid")
        elif current - approved_at > timedelta(seconds=self.approval_ttl_seconds):
            issues.append("owner_approval_too_old")
        if plan_time and approved_at and approved_at < plan_time:
            issues.append("approval_predates_invocation_plan")

        if not preflight.readiness_available:
            issues.append("agent_no_longer_available")
        if not preflight.readiness_qualified:
            issues.append("agent_no_longer_qualified")
        if not preflight.readiness_not_suspended:
            issues.append("agent_suspended")
        if not preflight.readiness_not_revoked:
            issues.append("agent_revoked")
        readiness_time = _time(preflight.readiness_observed_at)
        if readiness_time is None or not current - timedelta(seconds=60) <= readiness_time <= current + timedelta(seconds=30):
            issues.append("readiness_evidence_stale_or_future")

        workspace_check = self._validate_workspace_snapshot(plan)
        issues.extend(workspace_check["issue_codes"])
        staged = self._validate_staged_package(preflight.staged_package_id, plan)
        issues.extend(staged["issue_codes"])
        unique = list(dict.fromkeys(issues))
        return {
            "schema_version": "nextdecode.agent-execution-preflight.v1",
            "plan_id": plan.get("plan_id"),
            "workspace_id": plan.get("workspace_id"),
            "staging_id": preflight.staged_package_id,
            "accepted": not unique,
            "status": "preflight_passed_not_executed" if not unique else "denied",
            "issue_codes": unique,
            "process_started": False,
            "network_access": False,
            "credential_forwarding": False,
            "direct_repository_write": False,
            "human_approval_required": True,
            "execution_backend": "disabled_pending_os_sandbox_qualification",
            "evaluated_at": current.isoformat(),
        }

    @staticmethod
    def _validate_workspace_snapshot(plan: dict) -> dict:
        issues: list[str] = []
        workspace_id = plan.get("workspace_id")
        if not isinstance(workspace_id, str) or not re.fullmatch(r"[a-f0-9]{32}", workspace_id):
            return {"issue_codes": ["workspace_id_invalid"]}
        base = WORKSPACE_ROOT / workspace_id
        manifest_path = base / "manifest.json"
        workspace = base / "workspace"
        try:
            for path in (WORKSPACE_ROOT, base, manifest_path, workspace):
                if path.is_symlink():
                    issues.append("workspace_path_symlink")
            if issues:
                return {"issue_codes": issues}
            manifest_raw = manifest_path.read_bytes()
            manifest = json.loads(manifest_raw)
        except (OSError, ValueError):
            return {"issue_codes": ["workspace_manifest_unreadable"]}
        if hashlib.sha256(manifest_raw).hexdigest() != plan.get("workspace_manifest_sha256"):
            issues.append("workspace_manifest_digest_mismatch")
        if manifest.get("schema_version") != "nextdecode.agent-workspace.v1":
            issues.append("workspace_manifest_schema_invalid")
        if manifest.get("workspace_id") != workspace_id:
            issues.append("workspace_manifest_identity_mismatch")
        if manifest.get("agent_execution_enabled") is not False:
            issues.append("workspace_execution_not_disabled")
        if manifest.get("network_access") is not False or manifest.get("credentials_included") is not False:
            issues.append("workspace_security_baseline_invalid")
        expected = manifest.get("files")
        if not isinstance(expected, list):
            return {"issue_codes": list(dict.fromkeys(issues + ["workspace_file_inventory_invalid"]))}
        expected_paths: set[str] = set()
        for item in expected:
            rel = item.get("path") if isinstance(item, dict) else None
            if (not isinstance(rel, str) or not rel or "\\" in rel
                    or PurePosixPath(rel).is_absolute()
                    or any(part in {"", ".", ".."} for part in rel.split("/"))):
                issues.append("workspace_manifest_path_invalid")
                continue
            if rel in expected_paths:
                issues.append("workspace_manifest_duplicate_path")
                continue
            expected_paths.add(rel)
            candidate = workspace.joinpath(*rel.split("/"))
            try:
                cursor = candidate
                while cursor != workspace:
                    if cursor.is_symlink():
                        issues.append("workspace_file_symlink")
                        break
                    cursor = cursor.parent
                if not candidate.is_file() or candidate.is_symlink():
                    issues.append("workspace_file_missing_or_unsafe")
                elif _sha256_file(candidate) != item.get("sha256"):
                    issues.append("workspace_file_digest_mismatch")
            except OSError:
                issues.append("workspace_file_unreadable")
        observed_paths: set[str] = set()
        for current, dirs, files in os.walk(workspace, topdown=True, followlinks=False):
            current_path = Path(current)
            for name in list(dirs):
                child = current_path / name
                if child.is_symlink():
                    issues.append("workspace_directory_symlink")
                    dirs.remove(name)
            for name in files:
                child = current_path / name
                if child.is_symlink() or not child.is_file():
                    issues.append("workspace_unexpected_unsafe_entry")
                    continue
                observed_paths.add(child.relative_to(workspace).as_posix())
        if observed_paths != expected_paths:
            issues.append("workspace_file_inventory_mismatch")
        expected_path = str(workspace)
        if plan.get("workspace_path") != expected_path:
            issues.append("workspace_path_binding_mismatch")
        return {"issue_codes": list(dict.fromkeys(issues))}

    @staticmethod
    def _validate_staged_package(staging_id: str, plan: dict) -> dict:
        issues: list[str] = []
        if not isinstance(staging_id, str) or not re.fullmatch(r"[a-f0-9]{32}", staging_id):
            return {"issue_codes": ["staging_id_invalid"]}
        staging_root = WORKSPACE_ROOT / "staging"
        root = staging_root / staging_id
        manifest_path = root / "staging-manifest.json"
        try:
            if staging_root.is_symlink() or root.is_symlink() or manifest_path.is_symlink():
                return {"issue_codes": ["staging_path_symlink"]}
            raw_manifest = manifest_path.read_bytes()
            package = json.loads(raw_manifest)
        except (OSError, ValueError):
            return {"issue_codes": ["staging_manifest_unreadable"]}
        if package.get("schema_version") != "nextdecode.agent-staging-package.v1":
            issues.append("staging_schema_invalid")
        if package.get("staging_id") != staging_id or package.get("workspace_id") != plan.get("workspace_id"):
            issues.append("staging_identity_mismatch")
        if package.get("main_repository_modified") is not False or package.get("repository_import_performed") is not False:
            issues.append("staging_package_exceeds_boundary")
        files = package.get("files")
        if not isinstance(files, list) or not files:
            issues.append("staging_package_empty")
            files = []
        expected_paths: set[str] = set()
        for item in files:
            rel = item.get("path") if isinstance(item, dict) else None
            if (not isinstance(rel, str) or not rel or "\\" in rel
                    or PurePosixPath(rel).is_absolute()
                    or any(part in {"", ".", ".."} for part in rel.split("/"))):
                issues.append("staged_path_invalid")
                continue
            if rel in expected_paths:
                issues.append("staged_duplicate_path")
                continue
            expected_paths.add(rel)
            candidate = root / "files" / Path(*rel.split("/"))
            cursor = candidate
            while cursor != root:
                if cursor.is_symlink():
                    issues.append("staged_file_symlink")
                    break
                cursor = cursor.parent
            if candidate.is_symlink() or not candidate.is_file():
                issues.append("staged_file_missing_or_unsafe")
                continue
            if not isinstance(item.get("sha256"), str) or not _SHA256.fullmatch(item["sha256"]):
                issues.append("staged_digest_format_invalid")
            elif _sha256_file(candidate) != item["sha256"]:
                issues.append("staged_file_digest_mismatch")
        observed_paths: set[str] = set()
        files_root = root / "files"
        if files_root.is_symlink():
            issues.append("staged_files_root_symlink")
        elif files_root.is_dir():
            for current, dirs, names in os.walk(files_root, topdown=True, followlinks=False):
                current_path = Path(current)
                for name in list(dirs):
                    child = current_path / name
                    if child.is_symlink():
                        issues.append("staged_directory_symlink")
                        dirs.remove(name)
                for name in names:
                    child = current_path / name
                    if child.is_symlink() or not child.is_file():
                        issues.append("staged_unexpected_unsafe_entry")
                        continue
                    observed_paths.add(child.relative_to(files_root).as_posix())
        if observed_paths != expected_paths:
            issues.append("staged_file_inventory_mismatch")
        return {"issue_codes": list(dict.fromkeys(issues))}


class AgentIsolationExecutor:
    """Execution remains disabled until an OS sandbox backend is qualified."""

    def __init__(self, preflight: AgentIsolationPreflight | None = None):
        self.preflight = preflight or AgentIsolationPreflight()

    def execute(self, request: ExecutionPreflight, *, now: datetime | None = None) -> dict:
        decision = self.preflight.validate(request, now=now)
        if not decision["accepted"]:
            raise PermissionError("agent execution preflight denied: " + ",".join(decision["issue_codes"]))
        raise PermissionError(
            "execution backend is disabled pending OS sandbox qualification; "
            "preflight passed but no process was started"
        )
