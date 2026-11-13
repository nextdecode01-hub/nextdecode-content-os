import hmac
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from app.autonomy.models import TaskRequest
from app.autonomy.registry import build_default_registry
from app.autonomy.store import create_task_store
from app.autonomy.planner import TaskPlanner
from app.autonomy.tool_catalog import list_capabilities as list_tool_capabilities, rank_candidates
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
START_FIELDS = frozenset({"dry_run", "topic", "quality"})
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


def _validated_start_request(data) -> dict:
    """Reject malformed field types instead of coercing them into valid values."""
    if data is None:
        return {"dry_run": True, "topic": "", "quality": PRODUCTION_QUALITY}
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
    return {"dry_run": dry_run, "topic": topic.strip(), "quality": quality.strip()}


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
        if str(payload.get("status", "")).lower() == "success" and payload.get("video_path"):
            return {"video_path": str(payload["video_path"]), "title": payload.get("title", ""), "quality": payload.get("quality", "")}
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


def run_job(job_id: str, dry_run: bool, topic: str, quality: str):
    log_path = LOG_DIR / f"{job_id}.log"
    if not _update_job(job_id, {"status": "running", "log_file": str(log_path)}):
        return

    env = os.environ.copy()
    env["DRY_RUN"] = "1" if dry_run else "0"
    cmd = [sys.executable, "-m", "pipelines.short", "--quality", quality]
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
        if proc.returncode == 0 and result and (
                dry_run or result.get("quality") == quality):
            updates = {"log_tail": log_tail, "video_path": result["video_path"]}
            if result.get("title"):
                updates["title"] = result["title"]
            updates["status"] = "done"
            _update_job(job_id, updates, remove=("error",))
        else:
            if proc.returncode:
                error = f"exit code {proc.returncode}"
            elif not result:
                error = "no success marker in output"
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
        jobs[job_id] = {"status": "queued", "dry_run": dry_run, "topic": topic, "quality": quality}
        _prune_jobs()
    threading.Thread(
        target=run_job, args=(job_id, dry_run, topic, quality), daemon=True
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


@app.get("/tasks", dependencies=[Depends(require_api_key)])
def list_autonomous_tasks():
    return {"tasks": _task_store().list()}


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


@app.get("/tool-catalog", dependencies=[Depends(require_api_key)])
def get_tool_catalog(capability: Optional[str] = None):
    if capability:
        return {"capability": capability, "candidates": rank_candidates(capability)}
    return {"capabilities": list_tool_capabilities()}
