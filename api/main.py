import json
import os
import re
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "outputs" / "api_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
MAX_JOBS = 50
SUCCESS_MARKERS = (
    re.compile(r"Final Short Ready:\s*(.+)"),
    re.compile(r"\[\+\]\s*Archived Short:\s*(.+)"),
)

app = FastAPI()
jobs = {}
jobs_lock = threading.Lock()


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


def run_job(job_id: str, dry_run: bool, topic: str, quality: str):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return
    job["status"] = "running"
    env = os.environ.copy()
    env["DRY_RUN"] = "1" if dry_run else "0"
    cmd = [sys.executable, "-m", "pipelines.short", "--quality", quality]
    if topic:
        cmd += ["--topic", topic]
    log_path = LOG_DIR / f"{job_id}.log"
    job["log_file"] = str(log_path)
    try:
        with open(log_path, "w") as f:
            proc = subprocess.run(
                cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=f, stderr=subprocess.STDOUT, timeout=3600,
            )
        out = log_path.read_text(errors="ignore")
        job["log_tail"] = _redact(out[-1500:])
        result = _extract_result(out)
        if proc.returncode == 0 and result:
            job["status"] = "done"
            job["video_path"] = result["video_path"]
            if result.get("title"):
                job["title"] = result["title"]
        else:
            job["status"] = "failed"
            job["error"] = f"exit code {proc.returncode}" if proc.returncode else "no success marker in output"
    except subprocess.TimeoutExpired:
        job["status"] = "failed"
        job["error"] = "pipeline timed out after 3600s"
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = _redact(exc)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/jobs")
def list_jobs():
    with jobs_lock:
        return {job_id: dict(job) for job_id, job in jobs.items()}


@app.post("/start")
def start(data: Optional[dict] = None):
    dry_run = True if not data else bool(data.get("dry_run", True))
    topic = "" if not data else str(data.get("topic", "")).strip()
    quality = "standard" if not data else str(data.get("quality", "standard")).strip()
    if quality not in ("standard", "strong"):
        quality = "standard"
    with jobs_lock:
        if any(j["status"] in ("queued", "running") for j in jobs.values()):
            return {"error": "another job is running"}
        job_id = uuid.uuid4().hex[:8]
        jobs[job_id] = {"status": "queued", "dry_run": dry_run, "topic": topic, "quality": quality}
        _prune_jobs()
    threading.Thread(
        target=run_job, args=(job_id, dry_run, topic, quality), daemon=True
    ).start()
    return {"job_id": job_id}


@app.get("/status/{job_id}")
def status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        return dict(job) if job else {"status": "not_found"}
