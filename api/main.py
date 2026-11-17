import hmac
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, Response
from app.autonomy.models import TaskRequest
from app.autonomy.registry import build_default_registry
from app.autonomy.store import create_task_store
from app.autonomy.planner import TaskPlanner
from app.autonomy.tool_catalog import list_capabilities as list_tool_capabilities, rank_candidates
from app.brain.api import router as brain_router
from app.providers.api import router as providers_router
from app.content.formats import get_format_capability, list_format_capabilities
from app.review.read_service import (
    ReviewIntegrityError,
    ReviewNotFound,
    ReviewUnavailable,
    get_pending_review,
)

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "outputs" / "api_logs"
AUTONOMY_DB = ROOT / "data" / "autonomy" / "tasks.sqlite3"
LOG_DIR.mkdir(parents=True, exist_ok=True)
MAX_JOBS = 50
TELEGRAM_TIMEOUT = 15
TELEGRAM_RETRIES = 2
# Option A - strict fail-closed: the API is a production entry point, so it only
# starts strong-pipeline jobs.  The legacy path stays available to an operator who
# explicitly enables it in the server environment.
PRODUCTION_QUALITY = "strong"
LEGACY_OPT_IN_ENV = "SHORTS_STUDIO_ALLOW_STANDARD"
API_KEY_ENV = "SHORTS_STUDIO_API_KEY"
TOPIC_MAX_LENGTH = 200
START_FIELDS = frozenset({"dry_run", "topic", "quality", "content_format"})
SUCCESS_MARKERS = (
    re.compile(r"Final Short Ready:\s*(.+)"),
    re.compile(r"\[\+\]\s*Archived Short:\s*(.+)"),
)

app = FastAPI()
jobs = {}
jobs_lock = threading.Lock()


def require_api_key(authorization: Optional[str] = Header(default=None)) -> None:
    """Bearer authentication on every route that can read state or start work.

    An unconfigured server key fails closed: the API refuses requests rather than
    silently running open.
    """
    expected = os.getenv(API_KEY_ENV, "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="api_key_not_configured")
    scheme, _, supplied = str(authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied.strip():
        raise HTTPException(status_code=401, detail="unauthorized")
    if not hmac.compare_digest(supplied.strip(), expected):
        raise HTTPException(status_code=401, detail="unauthorized")


# Read-only intelligence and provider inventory inherit the existing API bearer boundary.
app.include_router(brain_router, dependencies=[Depends(require_api_key)])
app.include_router(providers_router, dependencies=[Depends(require_api_key)])


def _validated_start_request(data) -> dict:
    """Reject malformed field types instead of coercing them into valid values."""
    if data is None:
        return {"dry_run": True, "topic": "", "quality": PRODUCTION_QUALITY, "content_format": "youtube_shorts"}
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")
    unknown = sorted(set(data) - START_FIELDS)
    if unknown:
        raise HTTPException(status_code=400, detail="unknown field(s): " + ", ".join(unknown))
    dry_run = data.get("dry_run", True)
    if not isinstance(dry_run, bool):
        raise HTTPException(status_code=400, detail="dry_run must be a boolean")
    topic = data.get("topic", "")
    if not isinstance(topic, str) or len(topic.strip()) > TOPIC_MAX_LENGTH:
        raise HTTPException(
            status_code=400, detail=f"topic must be a string of at most {TOPIC_MAX_LENGTH} characters")
    quality = data.get("quality", PRODUCTION_QUALITY)
    if not isinstance(quality, str):
        raise HTTPException(status_code=400, detail="quality must be a string")
    content_format = data.get("content_format", "youtube_shorts")
    if not isinstance(content_format, str):
        raise HTTPException(status_code=400, detail="content_format must be a string")
    try:
        capability = get_format_capability(content_format.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    if capability.status != "supported":
        raise HTTPException(status_code=422, detail={
            "code": "content_format_not_implemented",
            "content_format": capability.format_id,
            "reason": capability.description,
        })
    return {"dry_run": dry_run, "topic": topic.strip(), "quality": quality.strip(),
            "content_format": capability.format_id}


def _legacy_allowed() -> bool:
    return os.getenv(LEGACY_OPT_IN_ENV, "").strip().lower() in {"1", "true", "yes"}


def _redact(text: str) -> str:
    text = str(text)
    for name, value in os.environ.items():
        if len(value) >= 8 and (name.endswith(("_KEY", "_TOKEN", "_SECRET")) or name.startswith(("CF_", "ELEVENLABS_", "CARTESIA_", "OPENAI_", "GEMINI_", "GROQ_"))):
            text = text.replace(value, "***")
    return re.sub(r"(?i)\b(key|token|api_key|access_token)=([^&\s'\"]+)", r"\1=***", text)


def _extract_result(output: str) -> Optional[dict]:
    """Find the success payload in either pipeline path's stdout."""
    for line in reversed(output.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        video_path = payload.get("video_path") or payload.get("video")
        if str(payload.get("status", "")).lower() == "success" and video_path:
            return {"video_path": str(video_path), "title": payload.get("title", ""),
                    "quality": payload.get("quality", ""), "format": payload.get("format", "")}
    for pattern in SUCCESS_MARKERS:
        matches = pattern.findall(output)
        if matches:
            return {"video_path": matches[-1].strip(), "title": "", "quality": ""}
    return None


def _prune_jobs() -> None:
    if len(jobs) <= MAX_JOBS:
        return
    finished = [job_id for job_id, job in jobs.items() if job.get("status") in ("done", "failed")]
    for job_id in finished[: len(jobs) - MAX_JOBS]:
        jobs.pop(job_id, None)


def _notify(text: str) -> bool:
    """Send a Telegram message. Never logs the request URL (it contains the token)."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for attempt in range(TELEGRAM_RETRIES + 1):
        try:
            response = requests.post(
                url,
                json={"chat_id": chat_id, "text": text[:3900]},
                timeout=TELEGRAM_TIMEOUT,
            )
            if 200 <= response.status_code < 300:
                return True
        except Exception:
            pass
        if attempt < TELEGRAM_RETRIES:
            time.sleep(2)
    return False


def _notify_job(job: dict) -> None:
    status = job.get("status")
    if status == "done":
        topic = str(job.get("topic") or job.get("title") or "untitled")
        text = f"Video ready | {topic} | {job.get('video_path', '')}"
    elif status == "failed":
        text = f"Video failed | {_redact(job.get('error') or 'unknown error')}"
    else:
        return
    job["notified"] = _notify(text)


def _update_job(job_id: str, updates: dict, remove=()) -> bool:
    """Apply one complete job-state update while holding the registry lock."""
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return False
        for field in remove:
            job.pop(field, None)
        job.update(updates)
        return True


def _job_snapshot(job_id: str) -> Optional[dict]:
    """Return a detached snapshot; callers must never mutate the registry record."""
    with jobs_lock:
        job = jobs.get(job_id)
        return dict(job) if job is not None else None


def run_job(job_id: str, dry_run: bool, topic: str, quality: str, content_format: str = "youtube_shorts"):
    log_path = LOG_DIR / f"{job_id}.log"
    if not _update_job(job_id, {"status": "running", "log_file": str(log_path)}):
        return

    env = os.environ.copy()
    env["DRY_RUN"] = "1" if dry_run else "0"
    if dry_run:
        # A dry-run render is an explicit local render-mechanics check with
        # procedural visuals and a permanent draft/not-for-publish governance
        # stamp. The production storyboard gate stays fail-closed: it is only
        # relaxed to `warn` inside the isolated dry-run child process, never for
        # a production render. Direct CLI dry-runs keep the production default.
        env["STORYBOARD_GATE"] = "warn"
    capability = get_format_capability(content_format)
    if capability.status != "supported":
        _update_job(job_id, {"status": "failed", "error": f"content_format_not_implemented: {content_format}"})
        return
    if capability.producer == "long_video":
        cmd = [sys.executable, "-m", "pipelines.longform",
               "--content-format", content_format]
    else:
        cmd = [sys.executable, "-m", "pipelines.short", "--quality", quality,
               "--content-format", content_format]
        if quality != PRODUCTION_QUALITY:
            cmd.append("--allow-standard")
    if topic:
        cmd += ["--topic", topic]

    try:
        with open(log_path, "w") as f:
            proc = subprocess.run(
                cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=f, stderr=subprocess.STDOUT, timeout=3600,
            )
        out = log_path.read_text(errors="ignore")
        log_tail = _redact(out[-1500:])
        result = _extract_result(out)
        # Publish artifact metadata and terminal status in one locked update.
        format_matches = capability.producer != "long_video" or result and result.get("format") == content_format
        quality_matches = capability.producer == "long_video" or dry_run or result and result.get("quality") == quality
        if proc.returncode == 0 and result and format_matches and quality_matches:
            updates = {"log_tail": log_tail, "video_path": result["video_path"], "content_format": content_format}
            if result.get("title"):
                updates["title"] = result["title"]
            updates["status"] = "done"
            _update_job(job_id, updates, remove=("error",))
        else:
            if proc.returncode:
                error = f"exit code {proc.returncode}"
            elif not result:
                error = "no success marker in output"
            elif not format_matches:
                error = f"pipeline did not return the requested {content_format} format"
            else:
                error = f"pipeline did not return a {quality}-pipeline result"
            _update_job(
                job_id,
                {"log_tail": log_tail, "error": error, "status": "failed"},
                remove=("video_path",),
            )
    except subprocess.TimeoutExpired:
        _update_job(
            job_id,
            {"error": "pipeline timed out after 3600s", "status": "failed"},
            remove=("video_path",),
        )
    except Exception as exc:
        _update_job(
            job_id,
            {"error": _redact(exc), "status": "failed"},
            remove=("video_path",),
        )

    # Snapshot under lock; keep notification/network I/O outside the lock.
    notification_snapshot = _job_snapshot(job_id)
    if notification_snapshot is None:
        return
    try:
        _notify_job(notification_snapshot)
        if "notified" in notification_snapshot:
            _update_job(job_id, {"notified": notification_snapshot["notified"]})
    except Exception:
        pass


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/review/pending", dependencies=[Depends(require_api_key)])
def get_pending_review_package():
    """Return the active review package without mutating review state."""
    try:
        return get_pending_review()
    except ReviewNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ReviewIntegrityError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except ReviewUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@app.get("/jobs", dependencies=[Depends(require_api_key)])
def list_jobs():
    with jobs_lock:
        return {job_id: dict(job) for job_id, job in jobs.items()}


@app.post("/start", dependencies=[Depends(require_api_key)])
def start(data: Optional[dict] = None):
    request = _validated_start_request(data)
    dry_run = request["dry_run"]
    topic = request["topic"]
    quality = request["quality"]
    content_format = request["content_format"]
    if quality != PRODUCTION_QUALITY and not _legacy_allowed():
        return JSONResponse(
            status_code=400,
            content={"error": f"production generation is strong-only; rejected quality {quality!r}"},
        )
    with jobs_lock:
        if any(j["status"] in ("queued", "running") for j in jobs.values()):
            running_id = next(k for k, j in jobs.items() if j["status"] in ("queued", "running"))
            return {"job_id": running_id, "already_running": True}
        job_id = uuid.uuid4().hex[:8]
        jobs[job_id] = {"status": "queued", "dry_run": dry_run, "topic": topic, "quality": quality, "content_format": content_format}
        _prune_jobs()
    threading.Thread(
        target=run_job, args=(job_id, dry_run, topic, quality, content_format), daemon=True
    ).start()
    return {"job_id": job_id}


@app.get("/status/{job_id}", dependencies=[Depends(require_api_key)])
def status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        return dict(job) if job else {"status": "not_found"}


def _task_store():
    if os.getenv("DATABASE_URL", "").strip():
        return create_task_store()
    if os.getenv("NEXTDECODE_TASK_DB"):
        return create_task_store(os.getenv("NEXTDECODE_TASK_DB"))
    return create_task_store()


@app.get("/capabilities", dependencies=[Depends(require_api_key)])
def list_capabilities():
    return {"capabilities": build_default_registry().describe()}


@app.get("/content-formats", dependencies=[Depends(require_api_key)])
def content_formats():
    """Expose implemented and planned channel formats without implying readiness."""
    return {"formats": list_format_capabilities()}


@app.post("/tasks", status_code=202, dependencies=[Depends(require_api_key)])
def enqueue_task(data: Optional[dict] = None):
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")
    allowed = {"task_type", "payload", "idempotency_key", "max_attempts", "priority"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise HTTPException(status_code=400, detail="unknown field(s): " + ", ".join(unknown))
    task_type = data.get("task_type")
    if not isinstance(task_type, str):
        raise HTTPException(status_code=400, detail="task_type must be a string")
    try:
        capability = build_default_registry().get(task_type)
        payload = data.get("payload", {})
        if capability.payload_validator:
            payload = capability.payload_validator(payload)
        request = TaskRequest(
            task_type=task_type,
            payload=payload,
            idempotency_key=data.get("idempotency_key"),
            max_attempts=data.get("max_attempts", 3),
            priority=data.get("priority", 100),
        )
        task = _task_store().enqueue(request)
    except KeyError:
        raise HTTPException(status_code=400, detail="unsupported task capability") from None
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return {"task_id": task["task_id"], "status": task["status"], "task_type": task["task_type"]}


@app.get("/autonomy/health", dependencies=[Depends(require_api_key)])
def autonomy_health():
    try:
        return _task_store().health()
    except Exception:
        raise HTTPException(status_code=503, detail="autonomy_storage_unavailable") from None


@app.get("/autonomy/dead-letters", dependencies=[Depends(require_api_key)])
def autonomy_dead_letters(limit: int = 100):
    try:
        return {"dead_letters": _task_store().dead_letters(limit)}
    except Exception:
        raise HTTPException(status_code=503, detail="autonomy_storage_unavailable") from None


@app.get("/autonomy/events", dependencies=[Depends(require_api_key)])
def autonomy_event_feed(after_event_id: int = 0, limit: int = 100):
    """Bounded, read-only local task lifecycle feed; not a canonical event bus."""
    try:
        if after_event_id < 0:
            raise HTTPException(status_code=400, detail="after_event_id_must_be_non_negative")
        bounded_limit = max(1, min(int(limit), 500))
        store = _task_store()
        # Cursor zero is the recent-window view used by dashboards. A nonzero
        # cursor is forward-only polling for consumers that maintain a checkpoint.
        events = store.recent_event_feed(limit=bounded_limit) if after_event_id == 0 else store.event_feed(
            after_event_id=after_event_id, limit=bounded_limit
        )
        return {"events": events, "next_after_event_id": events[-1]["event_id"] if events else after_event_id}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="autonomy_storage_unavailable") from None


@app.get("/autonomy/stuck-tasks", dependencies=[Depends(require_api_key)])
def autonomy_stuck_tasks(stale_after_seconds: int = 120, limit: int = 100):
    """Read-only view of running tasks missing a recent execution heartbeat."""
    try:
        if stale_after_seconds < 1:
            raise HTTPException(status_code=400, detail="stale_after_seconds_must_be_positive")
        bounded_limit = max(1, min(int(limit), 500))
        bounded_stale = max(1, min(int(stale_after_seconds), 3600))
        return {"stuck_tasks": _task_store().stuck_tasks(
            stale_after_seconds=bounded_stale, limit=bounded_limit
        ), "stale_after_seconds": bounded_stale}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="autonomy_storage_unavailable") from None


@app.get("/tasks", dependencies=[Depends(require_api_key)])
def list_autonomous_tasks(limit: int = 200):
    """Return a bounded newest-first page of local autonomy tasks."""
    try:
        bounded_limit = max(1, min(int(limit), 500))
        return {"tasks": _task_store().list(limit=bounded_limit), "limit": bounded_limit}
    except Exception:
        raise HTTPException(status_code=503, detail="autonomy_storage_unavailable") from None


@app.get("/tasks/{task_id}", dependencies=[Depends(require_api_key)])
def get_autonomous_task(task_id: str):
    store = _task_store()
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task_not_found")
    return {"task": task, "events": store.events(task_id)}


@app.post("/plans", status_code=202, dependencies=[Depends(require_api_key)])
def create_autonomous_plan(data: Optional[dict] = None):
    if not isinstance(data, dict) or set(data) - {"goal", "topic", "dry_run", "idempotency_key"}:
        raise HTTPException(status_code=400, detail="invalid plan request fields")
    decision = TaskPlanner(_task_store()).propose(
        data.get("goal"), topic=data.get("topic"), dry_run=data.get("dry_run", True),
        idempotency_key=data.get("idempotency_key"))
    if not decision.accepted:
        raise HTTPException(status_code=422, detail=decision.reason)
    return {"plan_id": decision.plan_id, "plan": decision.plan}


@app.get("/plans/{plan_id}", dependencies=[Depends(require_api_key)])
def get_autonomous_plan(plan_id: str):
    plan = _task_store().get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan_not_found")
    return plan


MAX_RUN_ARTIFACT_VERIFY_BYTES = 2 * 1024 * 1024 * 1024
RUN_ARTIFACT_HASH_CHUNK_BYTES = 1024 * 1024


def _verify_run_artifact_digest(candidate: Path, expected_sha256: str) -> dict:
    """Hash a bounded, regular file through a no-follow descriptor.

    The descriptor pins the opened inode while hashing. Before/after metadata
    checks reject files that visibly change during the read. This is read-only
    observability; it does not authorize or mutate the artifact.
    """
    expected = str(expected_sha256 or "").strip().lower()
    if not re.fullmatch(r"[a-f0-9]{64}", expected):
        return {"digest_status": "digest_missing", "computed_sha256": None}
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = -1
    try:
        descriptor = os.open(candidate, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            return {"digest_status": "not_regular_file", "computed_sha256": None}
        if before.st_size > MAX_RUN_ARTIFACT_VERIFY_BYTES:
            return {"digest_status": "verification_limit_exceeded", "computed_sha256": None}
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, RUN_ARTIFACT_HASH_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_RUN_ARTIFACT_VERIFY_BYTES:
                return {"digest_status": "verification_limit_exceeded", "computed_sha256": None}
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ) or total != after.st_size:
            return {"digest_status": "file_changed_during_verification", "computed_sha256": None}
        computed = digest.hexdigest()
        return {
            "digest_status": "verified" if hmac.compare_digest(computed, expected) else "digest_mismatch",
            "computed_sha256": computed,
        }
    except OSError:
        return {"digest_status": "verification_unavailable", "computed_sha256": None}
    finally:
        if descriptor >= 0:
            os.close(descriptor)


MAX_RUN_MANIFEST_BYTES = 2 * 1024 * 1024


def _read_run_manifest_file(manifest_path: Path, runs_root: Path) -> dict:
    """Read a bounded regular manifest without following symlinks."""
    try:
        root = runs_root.resolve()
        parent = manifest_path.parent.resolve()
        parent.relative_to(root)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(manifest_path, flags)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_RUN_MANIFEST_BYTES:
                raise ValueError("manifest_not_regular_or_too_large")
            chunks = []
            total = 0
            while True:
                chunk = os.read(descriptor, min(65536, MAX_RUN_MANIFEST_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_RUN_MANIFEST_BYTES:
                    raise ValueError("manifest_too_large")
            after = os.fstat(descriptor)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
            ) or total != after.st_size:
                raise ValueError("manifest_changed_during_read")
        finally:
            os.close(descriptor)
        manifest = json.loads(b"".join(chunks).decode("utf-8"))
    except (OSError, RuntimeError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise
    if not isinstance(manifest, dict):
        raise ValueError("manifest_invalid")
    return manifest


def _production_run_manifest(run_id: str) -> dict:
    """Load one local RunTracker manifest without exposing filesystem paths."""
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[a-z0-9-]{1,64}(?:-[0-9]+)?", run_id):
        raise HTTPException(status_code=404, detail="production_run_not_found")
    root = (ROOT / "outputs" / "runs").resolve()
    run_dir = (root / run_id).resolve()
    try:
        run_dir.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=404, detail="production_run_not_found") from None
    manifest_path = run_dir / "manifest.json"
    try:
        manifest = _read_run_manifest_file(manifest_path, root)
    except (OSError, RuntimeError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=503, detail="production_run_manifest_unavailable") from None
    if manifest.get("run_id") != run_id:
        raise HTTPException(status_code=503, detail="production_run_manifest_invalid")
    return manifest


def _production_run_summary(manifest: dict) -> dict:
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    stages = manifest.get("stages") if isinstance(manifest.get("stages"), list) else []
    failure = manifest.get("failure") if isinstance(manifest.get("failure"), dict) else None
    active_stage = next((item for item in reversed(stages)
                         if isinstance(item, dict) and item.get("status") == "in_progress"), None)
    return {
        "run_id": manifest.get("run_id"),
        "topic": str(manifest.get("topic") or "")[:200],
        "quality": manifest.get("quality"),
        "status": manifest.get("status", "unknown"),
        "started_at": manifest.get("started_at"),
        "finished_at": manifest.get("finished_at"),
        "stage_count": len(stages),
        "active_stage": str(active_stage.get("name") or "")[:100] if active_stage else None,
        "artifact_count": len(artifacts),
        "failure_stage": str(failure.get("stage") or "")[:80] if failure else None,
        "error_type": str(failure.get("error_type") or "")[:80] if failure else None,
        "error_category": str(failure.get("error_category") or "")[:40] if failure else None,
    }


@app.get("/production-runs", dependencies=[Depends(require_api_key)])
def list_production_runs(limit: int = 50):
    """Read-only index of local RunTracker manifests; not canonical WP2 runs."""
    bounded_limit = max(1, min(int(limit), 200))
    root = (ROOT / "outputs" / "runs").resolve()
    if not root.is_dir():
        return {"runs": [], "limit": bounded_limit, "source": "local_run_tracker"}
    runs = []
    for manifest_path in root.glob("*/manifest.json"):
        try:
            manifest = _read_run_manifest_file(manifest_path, root)
            if manifest.get("run_id") == manifest_path.parent.name:
                runs.append(_production_run_summary(manifest))
        except (OSError, RuntimeError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
    runs.sort(key=lambda item: str(item.get("started_at") or ""), reverse=True)
    return {"runs": runs[:bounded_limit], "limit": bounded_limit, "source": "local_run_tracker"}


@app.get("/production-runs/{run_id}/video", dependencies=[Depends(require_api_key)])
def stream_production_run_video(run_id: str):
    """Stream only the video artifact whose bytes match this run's manifest."""
    manifest = _production_run_manifest(run_id)
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    video = artifacts.get("video")
    if not isinstance(video, dict):
        raise HTTPException(status_code=404, detail="production_run_video_not_found")
    relative = str(video.get("path") or "")
    run_dir = (ROOT / "outputs" / "runs" / run_id).resolve()
    candidate = (run_dir / relative).resolve()
    try:
        candidate.relative_to(run_dir)
    except ValueError:
        raise HTTPException(status_code=404, detail="production_run_video_not_found") from None
    descriptor = -1
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(candidate, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size <= 0:
            raise ValueError("video_not_regular")
        if before.st_size > MAX_RUN_ARTIFACT_VERIFY_BYTES:
            raise ValueError("video_verification_limit")
        expected = str(video.get("sha256") or "").strip().lower()
        if not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise ValueError("video_digest_missing")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, RUN_ARTIFACT_HASH_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_RUN_ARTIFACT_VERIFY_BYTES:
                raise ValueError("video_verification_limit")
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ) or total != after.st_size:
            raise ValueError("video_changed_during_verification")
        if not hmac.compare_digest(digest.hexdigest(), expected):
            raise ValueError("video_digest_mismatch")
        recorded_bytes = video.get("bytes")
        if type(recorded_bytes) is int and recorded_bytes != total:
            raise ValueError("video_size_mismatch")
        os.lseek(descriptor, 0, os.SEEK_SET)
    except (OSError, ValueError):
        if descriptor >= 0:
            os.close(descriptor)
        raise HTTPException(status_code=409, detail="production_run_video_integrity_failed") from None

    def stream():
        try:
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            os.close(descriptor)

    return StreamingResponse(
        stream(),
        media_type="video/mp4",
        headers={"Content-Length": str(before.st_size), "Cache-Control": "no-store"},
    )


@app.get("/production-runs/{run_id}/storyboard", dependencies=[Depends(require_api_key)])
def get_production_run_storyboard(run_id: str):
    """Return a bounded, path-free scene QA view from the persisted storyboard."""
    _production_run_manifest(run_id)
    run_dir = (ROOT / "outputs" / "runs" / run_id).resolve()
    storyboard_path = (run_dir / "shots" / "storyboard" / "storyboard.json").resolve()
    try:
        storyboard_path.relative_to(run_dir)
        if storyboard_path.is_symlink() or not storyboard_path.is_file():
            raise ValueError("storyboard_unavailable")
        if storyboard_path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("storyboard_too_large")
        payload = json.loads(storyboard_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=404, detail="production_run_storyboard_not_found") from None

    raw_scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
    scenes = []
    for item in raw_scenes[:100]:
        if not isinstance(item, dict):
            continue
        index = item.get("index")
        if type(index) is not int or index < 0 or index > 999:
            continue
        scenes.append({
            "index": index,
            "start": item.get("start"),
            "end": item.get("end"),
            "narration": str(item.get("narration") or "")[:600],
            "scene_type": str(item.get("scene_type") or "")[:40],
            "visual_type": str(item.get("visual_type") or "")[:40],
            "provider": str(item.get("provider") or "")[:40],
            "asset_id": str(item.get("asset_id") or "")[:180],
            "relevance": str(item.get("relevance") or "")[:40],
            "relevance_confidence": str(item.get("relevance_confidence") or "")[:40],
            "review_reason": str(item.get("review_reason") or "")[:500],
            "fallback_reason": str(item.get("fallback_reason") or "")[:500],
            "relevance_reason": str(item.get("relevance_reason") or "")[:500],
            "image_url": f"/api/production-runs/{run_id}/scenes/{index}/image"
                if item.get("asset_path") else None,
        })
    return {
        "run_id": run_id,
        "title": str(payload.get("title") or "")[:200],
        "scene_count": len(scenes),
        "review_status": str(payload.get("review_status") or "unknown")[:60],
        "approved": payload.get("approved") is True,
        "review_required": payload.get("review_required") is True,
        "review_reasons": [str(reason)[:500] for reason in payload.get("review_reasons", [])[:50]],
        "summary": payload.get("summary") if isinstance(payload.get("summary"), dict) else {},
        "scenes": scenes,
    }


@app.get("/production-runs/{run_id}/scenes/{scene_index}/image", dependencies=[Depends(require_api_key)])
def get_production_run_scene_image(run_id: str, scene_index: int):
    """Serve one storyboard frame only from inside its validated run directory."""
    if scene_index < 0 or scene_index > 999:
        raise HTTPException(status_code=404, detail="production_run_scene_not_found")
    _production_run_manifest(run_id)
    run_dir = (ROOT / "outputs" / "runs" / run_id).resolve()
    storyboard_path = (run_dir / "shots" / "storyboard" / "storyboard.json").resolve()
    try:
        storyboard_path.relative_to(run_dir)
        if storyboard_path.is_symlink() or not storyboard_path.is_file() or storyboard_path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("storyboard_unavailable")
        payload = json.loads(storyboard_path.read_text(encoding="utf-8"))
        scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
        scene = next((item for item in scenes if isinstance(item, dict) and item.get("index") == scene_index), None)
        if not scene:
            raise ValueError("scene_missing")
        raw_path = Path(str(scene.get("asset_path") or ""))
        candidate = (run_dir / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()
        candidate.relative_to(run_dir)
        if candidate.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("unsupported_scene_image")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(candidate, flags)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_size <= 0 or info.st_size > 20 * 1024 * 1024:
                raise ValueError("scene_image_unavailable")
            chunks = []
            remaining = info.st_size
            while remaining:
                chunk = os.read(descriptor, min(1024 * 1024, remaining))
                if not chunk:
                    raise ValueError("scene_image_changed")
                chunks.append(chunk)
                remaining -= len(chunk)
            if os.read(descriptor, 1):
                raise ValueError("scene_image_changed")
        finally:
            os.close(descriptor)
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=404, detail="production_run_scene_image_not_found") from None
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[candidate.suffix.lower()]
    return Response(content=b"".join(chunks), media_type=mime, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@app.get("/production-runs/{run_id}", dependencies=[Depends(require_api_key)])
def get_production_run(run_id: str):
    """Read-only detail from a local RunTracker manifest, including real recorded evidence."""
    manifest = _production_run_manifest(run_id)
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    safe_artifacts = []
    for name, item in artifacts.items():
        if not isinstance(item, dict):
            continue
        relative = str(item.get("path") or "")
        candidate = ((ROOT / "outputs" / "runs" / run_id) / relative).resolve()
        run_root = (ROOT / "outputs" / "runs" / run_id).resolve()
        try:
            candidate.relative_to(run_root)
            contained = True
        except ValueError:
            contained = False
        try:
            exists = bool(contained and candidate.is_file())
            actual_bytes = candidate.stat().st_size if exists else None
        except OSError:
            exists = False
            actual_bytes = None
        recorded_bytes = item.get("bytes") if type(item.get("bytes")) is int else None
        digest = str(item.get("sha256") or "")[:64]
        if not contained:
            metadata_status = "unsafe_path"
            digest_result = {"digest_status": "not_checked", "computed_sha256": None}
        elif not exists:
            metadata_status = "missing_file"
            digest_result = {"digest_status": "not_checked", "computed_sha256": None}
        elif recorded_bytes is None:
            metadata_status = "size_missing"
            digest_result = _verify_run_artifact_digest(candidate, digest)
        elif actual_bytes != recorded_bytes:
            metadata_status = "size_mismatch"
            digest_result = _verify_run_artifact_digest(candidate, digest)
        else:
            metadata_status = "metadata_consistent"
            digest_result = _verify_run_artifact_digest(candidate, digest)
        integrity_status = (
            "unsafe_path" if not contained else
            "missing_file" if not exists else
            digest_result["digest_status"]
        )
        safe_artifacts.append({
            "name": str(name)[:100],
            "path": relative[:240] if contained else None,
            "sha256": digest,
            "computed_sha256": digest_result["computed_sha256"],
            "bytes": recorded_bytes,
            "actual_bytes": actual_bytes,
            "stage": str(item.get("stage") or "")[:80],
            "exists": exists,
            "metadata_status": metadata_status,
            "integrity_status": integrity_status,
        })
    stages = manifest.get("stages") if isinstance(manifest.get("stages"), list) else []
    safe_stages = []
    for stage in stages[:200]:
        if isinstance(stage, dict):
            safe_stages.append({
                "name": str(stage.get("name") or "")[:100],
                "started_at": stage.get("started_at"),
                "finished_at": stage.get("finished_at"),
                "status": str(stage.get("status") or "unknown")[:40],
            })
    failure = manifest.get("failure") if isinstance(manifest.get("failure"), dict) else None
    promotion = manifest.get("promotion") if isinstance(manifest.get("promotion"), dict) else None
    return {
        "run": _production_run_summary(manifest),
        "schema_version": manifest.get("schema_version"),
        "stages": safe_stages,
        "artifacts": safe_artifacts,
        "failure": {
            "stage": str(failure.get("stage") or "")[:80],
            "error_type": str(failure.get("error_type") or "")[:80],
            "error_category": str(failure.get("error_category") or "")[:40],
        } if failure else None,
        "promotion": {
            "status": str(promotion.get("status") or "unknown")[:40],
            "started_at": promotion.get("started_at"),
            "finished_at": promotion.get("finished_at"),
        } if promotion else None,
        "evidence_source": "outputs/runs/*/manifest.json",
        "trace_completeness": "manifest_only",
        "canonical_workflow_linked": False,
    }



PRODUCTION_ASSET_FILES = {
    "contact-sheet": ("shots/storyboard/contact_sheet.jpg", "image/jpeg"),
    "motion-sheet": ("shots/storyboard/motion_sheet.jpg", "image/jpeg"),
    "voice-mp3": ("voice.mp3", "audio/mpeg"),
    "voice-wav": ("voice.wav", "audio/wav"),
    "captions-ass": ("subtitles.ass", "text/plain; charset=utf-8"),
    "timeline": ("shots/timeline.json", "application/json"),
    "shot-plan": ("shot_plan.json", "application/json"),
    "storyboard": ("shots/storyboard/storyboard.json", "application/json"),
    "claim-ledger": ("research/claim_ledger.json", "application/json"),
    "word-captions": ("captions.words.json", "application/json"),
    "audio-mix": ("shots/audio_mix.wav", "audio/wav"),
}


@app.get("/production-runs/{run_id}/assets", dependencies=[Depends(require_api_key)])
def get_production_run_assets(run_id: str):
    """Curated read-only production assets. Paths are fixed server-side, never caller supplied."""
    _production_run_manifest(run_id)
    root = (ROOT / "outputs" / "runs" / run_id).resolve()
    metadata_path = root / "metadata.json"
    try:
        metadata_path.resolve().relative_to(root)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
    except (OSError, ValueError, json.JSONDecodeError):
        metadata = {}
    assets = []
    for asset_id, (relative, media_type) in PRODUCTION_ASSET_FILES.items():
        candidate = root / relative
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
            info = resolved.stat()
            available = stat.S_ISREG(info.st_mode) and info.st_size <= 100 * 1024 * 1024
            size = info.st_size if available else None
        except (OSError, ValueError):
            available, size = False, None
        assets.append({
            "id": asset_id, "path": relative, "media_type": media_type,
            "available": available, "bytes": size,
            "url": f"/api/production-runs/{run_id}/assets/{asset_id}" if available else None,
        })
    return {
        "script": {
            "title": str(metadata.get("title") or "")[:200],
            "hook": str(metadata.get("hook") or "")[:500],
            "voice_text": str(metadata.get("voice_text") or "")[:12000],
            "word_count": metadata.get("word_count"),
            "duration_seconds": metadata.get("duration_seconds"),
            "source_urls": [str(x)[:500] for x in metadata.get("source_urls", [])[:20] if isinstance(x, str)],
            "tags": [str(x)[:80] for x in metadata.get("tags", [])[:20] if isinstance(x, str)],
        },
        "assets": assets,
        "evidence_source": "run-local files under outputs/runs",
    }


@app.get("/production-runs/{run_id}/assets/{asset_id}", dependencies=[Depends(require_api_key)])
def get_production_run_asset(run_id: str, asset_id: str):
    """Serve only named, curated run-local assets; reject symlinks and path escapes."""
    entry = PRODUCTION_ASSET_FILES.get(asset_id)
    if not entry:
        raise HTTPException(status_code=404, detail="asset_not_found")
    relative, media_type = entry
    root = (ROOT / "outputs" / "runs" / run_id).resolve()
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        info = resolved.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > 100 * 1024 * 1024:
            raise HTTPException(status_code=404, detail="asset_unavailable")
        descriptor = os.open(str(resolved), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_ino != info.st_ino or opened.st_dev != info.st_dev:
            os.close(descriptor)
            raise HTTPException(status_code=409, detail="asset_changed_during_open")
    except HTTPException:
        raise
    except (OSError, ValueError):
        raise HTTPException(status_code=404, detail="asset_unavailable")

    def stream_asset():
        try:
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            os.close(descriptor)

    return StreamingResponse(
        stream_asset(), media_type=media_type,
        headers={"Content-Length": str(opened.st_size), "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/tool-catalog", dependencies=[Depends(require_api_key)])
def get_tool_catalog(capability: Optional[str] = None):
    if capability:
        return {"capability": capability, "candidates": rank_candidates(capability)}
    return {"capabilities": list_tool_capabilities()}
