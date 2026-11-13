"""Explicit per-file approval and isolated staging for agent workspace changes.

No function in this module writes to the main repository.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid
from datetime import datetime, timezone

from .agent_workspace import WORKSPACE_ROOT, WorkspaceError, _load_manifest, _sha256
from .agent_change_review import review_workspace_changes, _safe_relative_path

MAX_APPROVALS = 100
STAGING_ROOT = WORKSPACE_ROOT / "staging"


def _read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise WorkspaceError(f"{label} is missing or unreadable") from None
    if not isinstance(value, dict):
        raise WorkspaceError(f"{label} has an invalid structure")
    return value


def approve_added_file(workspace_id: str, relative_path: str, expected_sha256: str,
                       reason: str) -> dict:
    """Record a deliberate human approval for one eligible added text file."""
    if not _safe_relative_path(relative_path):
        raise WorkspaceError("unsafe relative path")
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise WorkspaceError("expected SHA-256 must be 64 hexadecimal characters")
    try:
        int(expected_sha256, 16)
    except ValueError:
        raise WorkspaceError("expected SHA-256 must be hexadecimal") from None
    if not isinstance(reason, str) or not 8 <= len(reason.strip()) <= 500:
        raise ValueError("approval reason must contain 8..500 characters")

    review = review_workspace_changes(workspace_id)
    entry = next((item for item in review["changes"] if item["path"] == relative_path), None)
    if entry is None or entry["status"] != "added":
        raise WorkspaceError("only a currently detected added file can be approved")
    if entry["decision"] != "review_required":
        raise WorkspaceError("blocked or restricted changes cannot be approved by this local gate")
    if entry.get("diff") in (None, "diff_omitted_line_limit"):
        raise WorkspaceError("file does not have a complete reviewable text diff")
    workspace = WORKSPACE_ROOT / workspace_id / "workspace"
    source = workspace / relative_path
    if source.is_symlink() or not source.is_file():
        raise WorkspaceError("candidate is not a regular file")
    actual = _sha256(source)
    if actual != expected_sha256:
        raise WorkspaceError("candidate hash does not match the explicitly supplied hash")

    approvals_path = WORKSPACE_ROOT / workspace_id / "approvals.json"
    approvals = {"schema_version": "nextdecode.agent-change-approvals.v1",
                 "workspace_id": workspace_id, "approvals": []}
    if approvals_path.exists():
        approvals = _read_json(approvals_path, "approval record")
    if approvals.get("schema_version") != "nextdecode.agent-change-approvals.v1" or approvals.get("workspace_id") != workspace_id:
        raise WorkspaceError("approval record identity/schema mismatch")
    rows = approvals.get("approvals")
    if not isinstance(rows, list) or len(rows) >= MAX_APPROVALS:
        raise WorkspaceError("approval record is invalid or has reached its limit")
    if any(row.get("path") == relative_path and row.get("active") for row in rows):
        raise WorkspaceError("an active approval already exists for this path")

    record = {
        "approval_id": uuid.uuid4().hex,
        "path": relative_path,
        "sha256": actual,
        "review_report_sha256": hashlib.sha256(json.dumps(
            review["changes"], sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest(),
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason.strip(),
        "active": True,
        "scope": "stage_only_not_repository_import",
    }
    rows.append(record)
    approvals_path.write_text(json.dumps(approvals, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    approvals_path.chmod(0o600)
    return record


def prepare_approved_staging(workspace_id: str) -> dict:
    """Copy currently approved additions into a private proposal directory only."""
    _manifest, workspace = _load_manifest(workspace_id)
    review = review_workspace_changes(workspace_id)
    approvals_path = WORKSPACE_ROOT / workspace_id / "approvals.json"
    if not approvals_path.is_file():
        raise WorkspaceError("no explicit per-file approvals exist")
    approvals = _read_json(approvals_path, "approval record")
    if approvals.get("workspace_id") != workspace_id:
        raise WorkspaceError("approval record identity mismatch")
    rows = approvals.get("approvals")
    if not isinstance(rows, list):
        raise WorkspaceError("approval record is invalid")

    current = {item["path"]: item for item in review["changes"]}
    selected = []
    for approval in rows:
        if not approval.get("active"):
            continue
        path = approval.get("path")
        entry = current.get(path)
        if not entry or entry["status"] != "added" or entry["decision"] != "review_required":
            raise WorkspaceError(f"approved change is no longer eligible: {path}")
        source = workspace / path
        if source.is_symlink() or not source.is_file() or _sha256(source) != approval.get("sha256"):
            raise WorkspaceError(f"approved file changed after approval: {path}")
        report_hash = hashlib.sha256(json.dumps(
            review["changes"], sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest()
        if report_hash != approval.get("review_report_sha256"):
            raise WorkspaceError(f"review report changed after approval: {path}")
        selected.append((path, source))

    if not selected:
        raise WorkspaceError("there are no active approved additions to stage")

    STAGING_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    STAGING_ROOT.chmod(0o700)
    staging_id = uuid.uuid4().hex
    destination = STAGING_ROOT / staging_id
    destination.mkdir(mode=0o700)
    try:
        staged = []
        for relative, source in selected:
            target = destination / "files" / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            # Recheck the path components before copying; no symlink traversal.
            cursor = target.parent
            while cursor != destination:
                if cursor.is_symlink():
                    raise WorkspaceError("staging path contains a symlink")
                cursor = cursor.parent
            shutil.copyfile(source, target)
            target.chmod(0o600)
            staged.append({"path": relative, "sha256": _sha256(target), "size": target.stat().st_size})
        package = {
            "schema_version": "nextdecode.agent-staging-package.v1",
            "staging_id": staging_id,
            "workspace_id": workspace_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": staged,
            "status": "staged_for_final_human_review",
            "main_repository_modified": False,
            "repository_import_performed": False,
            "publish_or_deploy_performed": False,
        }
        raw = json.dumps(package, indent=2, sort_keys=True) + "\n"
        (destination / "staging-manifest.json").write_text(raw, encoding="utf-8")
        (destination / "staging-manifest.json").chmod(0o600)
        return package
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
