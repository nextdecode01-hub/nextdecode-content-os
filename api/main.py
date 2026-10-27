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
app = FastAPI()
jobs = {}


def run_job(job_id: str, dry_run: bool, topic: str):
    job = jobs[job_id]
    job["status"] = "running"
    env = os.environ.copy()
    env["DRY_RUN"] = "1" if dry_run else "0"
    cmd = [sys.executable, "-m", "pipelines.short"]
    if topic:
        cmd += ["--topic", topic]
    try:
        proc = subprocess.run(
            cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=3600
        )
        out = proc.stdout + proc.stderr
        job["log_tail"] = out[-1500:]
        m = re.search(r"Final Short Ready:\s*(.+)", out)
        if proc.returncode == 0 and m:
            job["status"] = "done"
            job["video_path"] = m.group(1).strip()
        else:
            job["status"] = "failed"
            job["error"] = f"exit code {proc.returncode}"
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/start")
def start(data: Optional[dict] = None):
    if any(j["status"] in ("queued", "running") for j in jobs.values()):
        return {"error": "another job is running"}
    dry_run = True if not data else bool(data.get("dry_run", True))
    topic = "" if not data else str(data.get("topic", "")).strip()
    job_id = uuid.uuid4().hex[:8]
    jobs[job_id] = {"status": "queued", "dry_run": dry_run, "topic": topic}
    threading.Thread(
        target=run_job, args=(job_id, dry_run, topic), daemon=True
    ).start()
    return {"job_id": job_id}


@app.get("/status/{job_id}")
def status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})
