#!/usr/bin/env python3
"""Run Tracker core (Phase 10.4, Task 1).

Run-identity and manifest layer used by the Shorts Studio generation pipeline.
The short pipeline records run identity, stage/artifact evidence and promotion
state through this module. Its manifest and recovery semantics remain unchanged.

Responsibilities:
    * filesystem-safe, timestamp-based run IDs with a topic slug
    * unique run directories created with exist_ok=False (numeric suffixes on collision)
    * manifest lifecycle: ``in_progress`` → ``ok`` | ``failed``
    * finalized artifact records: path, sha256, size
    * append-only run index at ``data/runs/index.jsonl``
    * sanitized failure records (error type/category only — never raw messages)
    * promotion window: legacy-slot promotion is tracked through the additive
      ``manifest["promotion"]`` field plus an external journal file, and the
      manifest is only marked ``ok`` AFTER the journal reports ``completed``

Failure-recovery rule (owner-approved, documented only — no automatic recovery
is implemented, no old manifests are rewritten, no existing runs are altered):

    * manifest ``in_progress`` without ``failure.json``  → interrupted/unknown run
    * manifest ``in_progress`` WITH ``failure.json``     → failure recorded but
      manifest finalization was incomplete (crash between the two writes)
    * manifest ``failed``                                → terminal failure
    * manifest ``ok``                                    → terminal success

Manifest schema version: newly created manifests carry ``schema_version: 1``.

Explicit non-goals:
    * no automatic deletion of run directories, ever
    * no automatic recovery — interrupted runs stay ``in_progress`` until a human acts
    * no integration with review, approval or publishing code
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_ROOT = ROOT / "outputs" / "runs"
DEFAULT_INDEX_PATH = ROOT / "data" / "runs" / "index.jsonl"

MANIFEST_NAME = "manifest.json"
FAILURE_NAME = "failure.json"

# Closed error-category vocabulary (Phase 10.3 observability alignment).
ERROR_CATEGORIES = frozenset(
    {"topic", "research", "evidence", "script", "voice", "render", "qa", "io", "unknown"}
)
DEFAULT_ERROR_CATEGORY = "unknown"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _slug(topic: str, limit: int = 40) -> str:
    """Filesystem-safe slug, same convention as review_bundle.slug."""
    return re.sub(r"[^a-z0-9]+", "-", str(topic or "").lower()).strip("-")[:limit].strip("-")


def generate_run_id(topic: str = "", *, now: datetime | None = None) -> str:
    """Timestamp-based run ID: ``YYYYMMDD-HHMMSS-<slug>`` (UTC).

    ``now`` is injectable for deterministic tests.  A naive datetime is
    accepted and interpreted as UTC so callers stay tz-agnostic.
    """
    stamp_dt = now or _utcnow()
    if stamp_dt.tzinfo is None:
        stamp_dt = stamp_dt.replace(tzinfo=timezone.utc)
    stamp = stamp_dt.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{_slug(topic) or 'manual'}"


def _sha256_file(path: Path) -> str:
    """Stream a file in 1 MB chunks and return its sha256 hex digest."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_json(path: Path, payload: dict) -> None:
    """Write JSON atomically: temp file in the same directory, then replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def load_manifest(run_dir: Path) -> dict:
    """Load a run manifest, converting malformed JSON into a clear error."""
    path = Path(run_dir) / MANIFEST_NAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RuntimeError(f"manifest not found for run: {path}") from None
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"corrupt manifest for run {path}: {exc.msg}") from None
    if not isinstance(payload, dict) or not payload.get("run_id"):
        raise RuntimeError(f"malformed manifest for run {path}: missing run_id")
    return payload


def append_index_line(index_path: Path, record: dict) -> None:
    """Append one JSONL record to the run index (append-only)."""
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("a", encoding="utf-8") as index:
        index.write(json.dumps(record, ensure_ascii=False) + "\n")


class RunTracker:
    """Lifecycle handle for one run directory.

    Constructed only through :func:`start_run`.  All writes are confined to
    the run directory and the caller-supplied index path.
    """

    def __init__(
        self,
        run_id: str,
        run_dir: Path,
        manifest: dict,
        *,
        index_path: Path,
    ) -> None:
        self.run_id = run_id
        self.run_dir = Path(run_dir)
        self.manifest_path = self.run_dir / MANIFEST_NAME
        self.index_path = Path(index_path)
        self.manifest = manifest

    # -- artifacts ---------------------------------------------------------

    def record_artifact(self, name: str, path: Path | str, *, stage: str = "") -> dict:
        """Hash a finalized artifact file and record it in the manifest.

        The file must live inside the run directory — absolute containment is
        checked on the symlink-resolved path, so neither an external file nor a
        symlink pointing outside is accepted (no traversal escapes).  Only the
        run-relative path is stored, and artifact names are unique: recording
        the same name twice is refused rather than silently overwritten.
        """
        path = Path(path)
        if not path.is_file():
            raise RuntimeError(f"artifact not found for '{name}': {path}")
        artifacts = self.manifest.setdefault("artifacts", {})
        if name in artifacts:
            raise RuntimeError(
                f"artifact '{name}' already recorded for run {self.run_id}; refusing to overwrite"
            )
        resolved = path.resolve()
        run_root = self.run_dir.resolve()
        try:
            stored = str(resolved.relative_to(run_root))
        except ValueError:
            raise RuntimeError(
                f"artifact '{name}' escapes the run directory: {resolved} "
                f"(approved artifacts must live inside {run_root})"
            ) from None
        entry = {
            "path": stored,
            "sha256": _sha256_file(resolved),
            "bytes": resolved.stat().st_size,
            "stage": stage,
        }
        artifacts[name] = entry
        self._write_manifest()
        return entry

    # -- stages ------------------------------------------------------------

    def record_stage(self, name: str, *, started_at: str, finished_at: str, status: str = "ok") -> None:
        """Record a completed (or failed) stage with timestamps."""
        self.manifest.setdefault("stages", []).append(
            {"name": name, "started_at": started_at, "finished_at": finished_at, "status": status}
        )
        self._write_manifest()

    # -- promotion ---------------------------------------------------------

    def begin_promotion(self, targets: dict[str, str], *, journal_path: Path | None = None) -> Path:
        """Open the promotion window and record the promotion journal.

        ``targets`` maps an artifact name to the sha256 the promoted slot must
        carry.  The journal is the cross-process source of truth: while it says
        ``promoting``, no consumer (including approval) may treat the legacy
        slots as a valid successful output.  The manifest stays ``in_progress``
        with only the additive ``promotion`` field updated — Task 1 terminal
        transitions are not touched.
        """
        if self.manifest.get("status") != "in_progress":
            raise RuntimeError(
                f"run {self.run_id} is terminal ({self.manifest.get('status')}); "
                "promotion is only allowed while the run is in_progress"
            )
        if self.manifest.get("promotion", {}).get("status") == "promoting":
            raise RuntimeError(
                f"run {self.run_id} already has an open promotion window "
                f"({self.manifest['promotion'].get('journal_path')})"
            )
        journal = Path(journal_path) if journal_path is not None else (
            self.index_path.parent / "promotions" / f"{self.run_id}.json")
        journal.parent.mkdir(parents=True, exist_ok=True)
        started = _iso(_utcnow())
        _atomic_write_json(journal, {
            "run_id": self.run_id,
            "status": "promoting",
            "started_at": started,
            "targets": dict(targets),
            "finished_at": None,
        })
        self.manifest["promotion"] = {
            "status": "promoting",
            "journal_path": str(journal),
            "targets": dict(targets),
            "started_at": started,
            "finished_at": None,
        }
        self._write_manifest()
        return journal

    def complete_promotion(self) -> dict:
        """Close a successful promotion: journal ``completed``, then caller may ``mark_ok()``."""
        manifest_promotion = self.manifest.get("promotion") or {}
        if manifest_promotion.get("status") != "promoting":
            raise RuntimeError(
                f"run {self.run_id} has no open promotion window to complete"
                f" (status={manifest_promotion.get('status')!r})"
            )
        journal = Path(manifest_promotion["journal_path"])
        entry = json.loads(journal.read_text(encoding="utf-8"))
        if entry.get("status") != "promoting":
            raise RuntimeError(
                f"promotion journal for run {self.run_id} is not open "
                f"(status={entry.get('status')!r})"
            )
        finished = _iso(_utcnow())
        entry["status"] = "completed"
        entry["finished_at"] = finished
        _atomic_write_json(journal, entry)
        manifest_promotion["status"] = "completed"
        manifest_promotion["finished_at"] = finished
        self.manifest["promotion"] = manifest_promotion
        self._write_manifest()
        return entry

    def promote_slots(self, slot_map: dict[str, Path | str]) -> dict[str, Path]:
        """Promote recorded run artifacts into the legacy output slots.

        ``slot_map`` maps an artifact name (as recorded by ``record_artifact``)
        to the destination slot, e.g. ``{"video": outputs/output_short.mp4,
        "metadata": data/metadata.json}``.

        Validation happens before ANY slot is touched: every target artifact
        must be recorded in the manifest, must still live inside the run
        directory, and its sha256 must match the value recorded when it was
        finalized.  The artifacts are then copied next to their destinations
        and swapped in with ``os.replace`` (same-filesystem, atomic per file).
        The promotion journal covers the whole window, so an interrupted or
        mixed promotion is detectable and rejected at approval time — it can
        never be reported as success, and the run manifest is only marked
        ``ok`` by the caller after this method returns and reports completion.
        """
        if self.manifest.get("status") != "in_progress":
            raise RuntimeError(
                f"run {self.run_id} is terminal ({self.manifest.get('status')}); "
                "promotion is only allowed while the run is in_progress"
            )
        artifacts = self.manifest.get("artifacts") or {}
        if not slot_map:
            raise RuntimeError(f"run {self.run_id}: no promotion targets given")
        resolved: dict[str, tuple[Path, Path]] = {}
        for name, dest in slot_map.items():
            entry = artifacts.get(name)
            if not entry:
                raise RuntimeError(
                    f"run {self.run_id}: artifact '{name}' is not recorded; "
                    "refusing promotion of an unvalidated artifact"
                )
            source = self.run_dir / entry["path"]
            if not source.is_file():
                raise RuntimeError(
                    f"run {self.run_id}: artifact '{name}' ({entry['path']}) is missing "
                    "from the run directory; refusing promotion"
                )
            digest = _sha256_file(source)
            if digest != entry.get("sha256"):
                raise RuntimeError(
                    f"run {self.run_id}: artifact '{name}' hash changed after recording "
                    "(expected mismatch-free promotion); refusing promotion"
                )
            resolved[name] = (source, Path(dest))
        targets = {name: artifacts[name]["sha256"] for name in resolved}
        journal = self.begin_promotion(targets)
        staged: list[Path] = []
        try:
            for name, (source, dest) in resolved.items():
                dest.parent.mkdir(parents=True, exist_ok=True)
                tmp = dest.parent / f".{dest.name}.{uuid.uuid4().hex}.tmp"
                shutil.copyfile(source, tmp)
                staged.append(tmp)
                os.replace(tmp, dest)
        except Exception:
            # Best-effort temp cleanup only; any half-promoted slots stay as
            # they are — detectable via the open promotion window, never "ok".
            for tmp in staged:
                try:
                    if tmp.exists():
                        tmp.unlink()
                except OSError:
                    pass
            raise
        self.complete_promotion()
        return {name: dest for name, (_, dest) in resolved.items()}

    # -- lifecycle ---------------------------------------------------------

    def mark_ok(self, *, finished_at: datetime | None = None) -> dict:
        """Transition the manifest to ``ok`` and append the index record."""
        if self.manifest.get("status") not in (None, "in_progress"):
            raise RuntimeError(
                f"run {self.run_id} is already terminal ({self.manifest.get('status')}); "
                "cannot transition to ok"
            )
        self.manifest["status"] = "ok"
        self.manifest["finished_at"] = _iso(finished_at or _utcnow())
        self._write_manifest()
        self._append_index()
        return self.manifest

    def mark_failed(
        self,
        *,
        stage: str,
        exc: BaseException | None = None,
        error_category: str = DEFAULT_ERROR_CATEGORY,
        finished_at: datetime | None = None,
    ) -> dict:
        """Record a sanitized failure: manifest, failure.json and index line.

        Only the exception *type name* is stored — never the message — so
        credentials or URLs embedded in exception text cannot leak into logs.
        """
        if self.manifest.get("status") not in (None, "in_progress"):
            raise RuntimeError(
                f"run {self.run_id} is already terminal ({self.manifest.get('status')}); "
                "cannot transition to failed"
            )
        category = error_category if error_category in ERROR_CATEGORIES else DEFAULT_ERROR_CATEGORY
        failure = {
            "stage": str(stage),
            "error_type": type(exc).__name__ if exc is not None else "UnknownError",
            "error_category": category,
        }
        self.manifest["status"] = "failed"
        self.manifest["failure"] = failure
        self.manifest["finished_at"] = _iso(finished_at or _utcnow())
        # If a promotion window was open, close it as an explicit failure so no
        # downstream consumer can mistake a mixed pair for a completed promotion.
        manifest_promotion = self.manifest.get("promotion") or {}
        if manifest_promotion.get("status") == "promoting":
            journal = Path(manifest_promotion["journal_path"])
            try:
                entry = json.loads(journal.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                entry = {"run_id": self.run_id, "status": "promoting"}
            if entry.get("status") in {"promoting", None}:
                entry["status"] = "failed"
                entry["finished_at"] = self.manifest["finished_at"]
                try:
                    _atomic_write_json(journal, entry)
                except OSError:
                    pass  # manifest failure state is authoritative regardless
            manifest_promotion["status"] = "failed"
            manifest_promotion["finished_at"] = self.manifest["finished_at"]
            self.manifest["promotion"] = manifest_promotion
        _atomic_write_json(self.run_dir / FAILURE_NAME, {
            "run_id": self.run_id,
            **failure,
            "written_at": self.manifest["finished_at"],
        })
        self._write_manifest()
        self._append_index()
        return self.manifest

    # -- internals ---------------------------------------------------------

    def _write_manifest(self) -> None:
        _atomic_write_json(self.manifest_path, self.manifest)

    def _append_index(self) -> None:
        failure = self.manifest.get("failure") or {}
        append_index_line(self.index_path, {
            "run_id": self.run_id,
            "status": self.manifest.get("status", ""),
            "topic": self.manifest.get("topic", ""),
            "started_at": self.manifest.get("started_at"),
            "finished_at": self.manifest.get("finished_at"),
            "failure_stage": failure.get("stage"),
            "error_category": failure.get("error_category"),
        })


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def start_run(
    topic: str = "",
    *,
    runs_root: Path | str | None = None,
    index_path: Path | str | None = None,
    now: datetime | None = None,
    quality: str = "strong",
) -> RunTracker:
    """Create a unique run directory and its ``in_progress`` manifest.

    ``runs_root`` and ``index_path`` are injectable (tests use temporary
    directories only).  Collisions on the same timestamp are resolved with
    numeric suffixes via exist_ok=False directory creation — creation itself
    is the atomic uniqueness check.  Filesystem errors propagate untouched.
    """
    runs_root = Path(runs_root or DEFAULT_RUNS_ROOT)
    index_path = Path(index_path or DEFAULT_INDEX_PATH)
    run_id = generate_run_id(topic, now=now)

    # Atomic uniqueness: exist_ok=False raises FileExistsError on a taken
    # directory, so the suffix loop is the collision handler (suffix -1, -2, ...).
    attempt = 1
    candidate = runs_root / run_id
    while True:
        try:
            run_dir = candidate
            run_dir.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            candidate = runs_root / f"{run_id}-{attempt}"
            attempt += 1
        # Any other OSError (missing parent gone mid-flight, permissions,
        # runs_root path is a file) propagates to the caller untouched.

    stamp_dt = now or _utcnow()
    manifest: dict[str, Any] = {
        "run_id": run_dir.name,
        "schema_version": 1,
        "status": "in_progress",
        "quality": quality,
        "topic": topic or "",
        "started_at": _iso(stamp_dt),
        "finished_at": None,
        "artifacts": {},
        "stages": [],
        "failure": None,
    }
    tracker = RunTracker(run_dir.name, run_dir, manifest, index_path=index_path)
    tracker._write_manifest()
    return tracker
