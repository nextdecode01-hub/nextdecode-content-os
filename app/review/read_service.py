"""Read-only access to the active human-review package."""
from __future__ import annotations
import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PENDING_POINTER = ROOT / "data" / "review_pending.json"
REVIEW_QUEUE = ROOT / "data" / "review_queue"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReviewNotFound(Exception):
    pass


class ReviewUnavailable(Exception):
    pass


class ReviewIntegrityError(Exception):
    pass


def _read_json_object(path: Path, *, max_bytes: int = 1_000_000) -> tuple[dict[str, Any], bytes]:
    try:
        if path.is_symlink() or not path.is_file():
            raise ReviewUnavailable("review_file_unavailable")
        raw = path.read_bytes()
        if not raw or len(raw) > max_bytes:
            raise ReviewUnavailable("review_file_invalid_size")
        value = json.loads(raw)
    except ReviewUnavailable:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ReviewUnavailable("review_file_unreadable") from None
    if not isinstance(value, dict):
        raise ReviewUnavailable("review_file_invalid")
    return value, raw


def _resolve_under(path_value: object, allowed_root: Path) -> Path:
    if not isinstance(path_value, str) or not path_value.strip():
        raise ReviewUnavailable("review_artifact_path_missing")
    try:
        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if candidate.is_symlink():
            raise ReviewUnavailable("review_artifact_path_unsafe")
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(allowed_root.resolve(strict=True))
        if not resolved.is_file():
            raise ReviewUnavailable("review_artifact_unavailable")
        return resolved
    except ReviewUnavailable:
        raise
    except FileNotFoundError:
        raise ReviewUnavailable("review_artifact_unavailable") from None
    except (OSError, RuntimeError, ValueError):
        raise ReviewUnavailable("review_artifact_path_unsafe") from None


def _verify_artifact(package: dict[str, Any], *, path_key: str, digest_key: str, allowed_root: Path, expected_path: Path) -> None:
    expected = package.get(digest_key)
    if not isinstance(expected, str) or not _SHA256_RE.fullmatch(expected):
        raise ReviewIntegrityError("review_artifact_digest_invalid")
    artifact = _resolve_under(package.get(path_key), allowed_root)
    try:
        canonical_path = expected_path.resolve(strict=True)
    except (OSError, RuntimeError):
        raise ReviewUnavailable("review_artifact_unavailable") from None
    if artifact != canonical_path:
        raise ReviewUnavailable("review_artifact_path_unsafe")
    digest = hashlib.sha256()
    try:
        with artifact.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        raise ReviewUnavailable("review_artifact_unavailable") from None
    if not hmac.compare_digest(digest.hexdigest(), expected):
        raise ReviewIntegrityError("review_artifact_hash_mismatch")


def _without_local_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_local_paths(item)
            for key, item in value.items()
            if key != "path" and not key.endswith("_path")
        }
    if isinstance(value, list):
        return [_without_local_paths(item) for item in value]
    return value


def get_pending_review() -> dict[str, Any]:
    try:
        pointer, _ = _read_json_object(PENDING_POINTER, max_bytes=64_000)
    except ReviewUnavailable:
        if not PENDING_POINTER.exists() and not PENDING_POINTER.is_symlink():
            raise ReviewNotFound("no_pending_review") from None
        raise
    if pointer.get("status") != "pending_human_review":
        raise ReviewNotFound("no_pending_review")
    package_path = _resolve_under(pointer.get("package"), REVIEW_QUEUE)
    package, package_bytes = _read_json_object(package_path)
    if package.get("status") != "pending_human_review":
        raise ReviewIntegrityError("review_package_not_pending")
    _verify_artifact(
        package, path_key="video_path", digest_key="video_sha256",
        allowed_root=ROOT / "outputs", expected_path=ROOT / "outputs" / "output_short.mp4",
    )
    _verify_artifact(
        package, path_key="metadata_path", digest_key="metadata_sha256",
        allowed_root=ROOT / "data", expected_path=ROOT / "data" / "metadata.json",
    )
    return {
        "status": "pending_human_review",
        "review_package_sha256": hashlib.sha256(package_bytes).hexdigest(),
        "package": _without_local_paths(package),
    }
