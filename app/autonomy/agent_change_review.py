"""Safety review for isolated coding-agent workspace changes.

This module is advisory and fail-closed: it never imports or applies changes.
"""
from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path
import re
from datetime import datetime, timezone

from .agent_workspace import WORKSPACE_ROOT, _load_manifest, collect_workspace_changes

MAX_DIFF_BYTES = 256 * 1024
MAX_DIFF_LINES = 240
TEXT_SUFFIXES = frozenset({
    ".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".ini",
    ".cfg", ".sh", ".sql", ".html", ".css", ".js", ".jsx", ".ts", ".tsx",
})
PROTECTED_PARTS = frozenset({
    ".git", ".env", "secrets", "credentials", "tokens", "private",
})
PROTECTED_PREFIXES = (
    "app/publish/", "app/autonomy/", "tests/security/", ".github/workflows/",
)
SENSITIVE_NAME = re.compile(
    r"(^|[._-])(secret|credential|token|password|private.?key|oauth)([._-]|$)",
    re.IGNORECASE,
)


def _safe_relative_path(value: str) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = Path(value)
    return not path.is_absolute() and all(
        part not in {"", ".", ".."} for part in value.split("/")
    )


def _risk(path: str, status: str, size: int) -> tuple[str, list[str]]:
    if not _safe_relative_path(path):
        return "blocked", ["unsafe_path"]
    reasons: list[str] = []
    normalized = path.lower()
    parts = normalized.split("/")
    name = parts[-1]
    if any(part in PROTECTED_PARTS for part in parts) or name.startswith(".env"):
        reasons.append("sensitive_or_private_path")
    if SENSITIVE_NAME.search(name):
        reasons.append("sensitive_filename")
    if normalized.startswith(PROTECTED_PREFIXES):
        reasons.append("protected_security_or_publishing_area")
    if Path(name).suffix.lower() not in TEXT_SUFFIXES:
        reasons.append("non_text_or_unreviewable_file")
    if size > MAX_DIFF_BYTES:
        reasons.append("diff_size_limit_exceeded")
    if status == "deleted":
        reasons.append("deletion_requires_explicit_review")
    if reasons:
        blocked_reasons = {
            "unsafe_path", "sensitive_or_private_path", "sensitive_filename",
        }
        return ("blocked" if blocked_reasons.intersection(reasons)
                else "restricted_review"), reasons
    return "review_required", ["human_review_required"]


def _bounded_added_file_diff(target: Path, path: str) -> str | None:
    raw = target.read_bytes()
    if len(raw) > MAX_DIFF_BYTES or b"\x00" in raw:
        return None
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if len(lines) > MAX_DIFF_LINES:
        return None
    return "\n".join(difflib.unified_diff(
        [], lines, fromfile="/dev/null", tofile=path, lineterm=""
    ))[:16000]


def review_workspace_changes(workspace_id: str) -> dict:
    """Produce bounded risk annotations and diffs; never modify/import source."""
    _manifest, workspace = _load_manifest(workspace_id)
    report = collect_workspace_changes(workspace_id)
    reviewed = []
    for change in report["changes"]:
        path = change["path"]
        severity, reasons = _risk(path, change["status"], change["size"])
        item = {**change, "decision": severity, "reasons": reasons, "diff": None}
        if severity == "review_required" and change["status"] == "added":
            try:
                item["diff"] = _bounded_added_file_diff(workspace / path, path)
                if item["diff"] is None:
                    item["decision"] = "restricted_review"
                    item["reasons"].append("diff_not_fully_reviewable")
            except (OSError, UnicodeDecodeError):
                item["decision"] = "restricted_review"
                item["reasons"].append("file_not_safely_decodable")
        elif severity == "review_required" and change["status"] == "modified":
            item["diff"] = "baseline_content_unavailable"
            item["decision"] = "restricted_review"
            item["reasons"] = ["baseline_content_unavailable"]
        reviewed.append(item)

    blocked = sum(item["decision"] == "blocked" for item in reviewed)
    restricted = sum(item["decision"] == "restricted_review" for item in reviewed)
    review = {
        "schema_version": "nextdecode.agent-change-review.v1",
        "workspace_id": workspace_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "change_report_sha256": hashlib.sha256(
            (WORKSPACE_ROOT / workspace_id / "change-report.json").read_bytes()
        ).hexdigest(),
        "change_count": len(reviewed),
        "blocked_count": blocked,
        "restricted_review_count": restricted,
        "review_required_count": len(reviewed) - blocked - restricted,
        "changes": reviewed,
        "status": "blocked_changes_present" if blocked else (
            "restricted_changes_present" if restricted else (
                "pending_human_review" if reviewed else "no_changes"
            )
        ),
        "main_repository_modified": False,
        "automatic_import_allowed": False,
        "approval_granted": False,
    }
    out = WORKSPACE_ROOT / workspace_id / "review-report.json"
    out.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out.chmod(0o600)
    return review
