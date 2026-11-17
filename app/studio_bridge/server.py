#!/usr/bin/env python3
"""Local Studio write-server for the NEXTDECODE dashboard.

Bound to 127.0.0.1 only.  Requires the same Bearer key the dashboard uses for
the read API.  It performs a small, explicit set of mutations by shelling out
to the pipeline and to the storyboard approval CLI — the gates stay in the
engine, not in this process.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(Path(os.path.expanduser("~/.config/nextdecode/api.env")), override=False)
load_dotenv(ROOT / ".env", override=False)

JOBS_DIR = ROOT / "data" / "studio_jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_ROOT = ROOT / "outputs" / "runs"

RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TOPIC_RE = re.compile(r"^[^\x00-\x1f]{1,200}$")
REVIEWER_RE = re.compile(r"^[^\x00-\x1f]{1,120}$")

MAX_CONCURRENT_JOBS = 2
TOPIC_MAX_LEN = 200

_jobs: dict[str, subprocess.Popen] = {}
_job_lock = None  # lazy


def _bearer_key() -> str:
    return os.getenv("SHORTS_STUDIO_API_KEY", "").strip()


def _require_auth(headers) -> bool:
    key = _bearer_key()
    if not key:
        # No key configured: refuse rather than run open.
        return False
    auth = headers.get("authorization", "")
    return auth == f"Bearer {key}"


def _job_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def _log_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.log"


def _active_job_count() -> int:
    alive = 0
    for pid in list(_jobs.values()):
        if pid.poll() is None:
            alive += 1
    return alive


def _launch(name: str, command: list[str]) -> dict:
    if _active_job_count() >= MAX_CONCURRENT_JOBS:
        return {"status": "error", "error": "too_many_active_jobs"}
    job_id = f"{int(time.time() * 1000)}-{os.urandom(4).hex()}"
    log_file = _log_path(job_id)
    with log_file.open("w", encoding="utf-8") as log:
        log.write(f"$ {' '.join(command)}\n")
        log.flush()
        process = subprocess.Popen(
            command,
            cwd=str(ROOT),
            stdout=log,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    _jobs[job_id] = process
    meta = {
        "job_id": job_id,
        "name": name,
        "command": command[1:],
        "status": "running",
        "pid": process.pid,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "log_file": str(log_file),
        "run_id": None,
        "exit_code": None,
    }
    _job_path(job_id).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"status": "started", "job_id": job_id, "log_file": str(log_file)}


def _read_job(job_id: str) -> dict:
    path = _job_path(job_id)
    if not path.is_file():
        return {"status": "error", "error": "job_not_found"}
    meta = json.loads(path.read_text(encoding="utf-8"))
    process = _jobs.get(job_id)
    if process is not None:
        code = process.poll()
        if code is None:
            meta["status"] = "running"
        else:
            meta["status"] = "finished"
            meta["exit_code"] = code
    elif meta.get("status") == "running":
        # Process unknown to this server (e.g. restarted): treat as interrupted
        # unless the log shows completion — never fabricate success.
        meta["status"] = "unknown"
    # Try to recover the run directory from the log (line: [*] Run directory:).
    log_file = Path(meta.get("log_file") or "")
    run_id = meta.get("run_id")
    if log_file.is_file():
        try:
            text = log_file.read_text(encoding="utf-8", errors="replace")[-65536:]
        except OSError:
            text = ""
        if not run_id:
            match = re.search(r"Run directory:\s*(\S+)", text)
            if match:
                run_id = Path(match.group(1)).name
        meta["log_tail"] = text[-4000:]
    if run_id:
        meta["run_id"] = run_id
    if meta.get("status") == "finished" and log_file.is_file():
        try:
            text = log_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        lowered = text.lower()
        if "parked as awaiting_review" in lowered:
            meta["outcome"] = "awaiting_review"
        elif "\n[success]" in lowered or '"status": "success"' in lowered:
            meta["outcome"] = "success"
        else:
            meta["outcome"] = "failed"
    path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def _storyboard_path(run_id: str) -> Path | None:
    if not RUN_ID_RE.match(run_id):
        return None
    candidate = (RUNS_ROOT / run_id).resolve()
    try:
        candidate.relative_to(RUNS_ROOT.resolve())
    except ValueError:
        return None
    storyboard = candidate / "storyboard.json"
    # Also check shots subdir for the plan-persisted storyboard layout.
    if not storyboard.is_file():
        alt = candidate / "shots" / "storyboard.json"
        if alt.is_file():
            storyboard = alt
    return storyboard if storyboard.is_file() else None


def _find_storyboard_in_run(run_dir: Path) -> Path | None:
    for candidate in (run_dir / "storyboard.json", run_dir / "shots" / "storyboard.json"):
        if candidate.is_file():
            return candidate
    # Fallback: shallow search for any storyboard.json in the run tree.
    try:
        for path in sorted(run_dir.rglob("storyboard.json")):
            if path.is_file():
                return path
    except OSError:
        return None
    return None


def _run_dir_for(run_id: str) -> Path | None:
    if not RUN_ID_RE.match(run_id):
        return None
    candidate = (RUNS_ROOT / run_id).resolve()
    try:
        candidate.relative_to(RUNS_ROOT.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_dir() else None




def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _library_items() -> list[dict]:
    """Collect every engine-produced artifact descriptor, newest first.

    Pure file reads: manifest + render_context only.  No hashing, no execution,
    no writes — callers can poll this freely.
    """
    if not RUNS_ROOT.is_dir():
        return []
    items: list[dict] = []
    for manifest_path in sorted(RUNS_ROOT.glob('*/manifest.json')):
        run_dir = manifest_path.parent
        manifest = _read_json(manifest_path)
        if not isinstance(manifest, dict):
            continue
        context = _read_json(run_dir / 'render_context.json')
        script = (context or {}).get('script') if isinstance(context, dict) else None
        if not isinstance(script, dict):
            script = {}
        artifacts = manifest.get('artifacts') or {}
        video_entry = artifacts.get('video') if isinstance(artifacts, dict) else None
        storyboard_entry = artifacts.get('storyboard') if isinstance(artifacts, dict) else None
        contact_sheet_entry = artifacts.get('contact_sheet') if isinstance(artifacts, dict) else None
        platform_copy = script.get('platform_copy') if isinstance(script.get('platform_copy'), dict) else {}
        items.append({
            'run_id': run_dir.name,
            'status': manifest.get('status', 'unknown'),
            'topic': manifest.get('topic') or (context or {}).get('topic') or None,
            'title': script.get('title') or None,
            'hook': script.get('hook') or None,
            'word_count': script.get('word_count'),
            'duration_seconds': script.get('duration_seconds') or script.get('seconds'),
            'tags': script.get('youtube_tags') or script.get('tags') or [],
            'platform_copy': {
                'youtube_description': platform_copy.get('youtube_description'),
                'instagram_caption': platform_copy.get('instagram_caption'),
                'facebook_title': platform_copy.get('facebook_title'),
                'facebook_description': platform_copy.get('facebook_description'),
            },
            'artifacts': {
                'video': bool(video_entry),
                'storyboard': bool(storyboard_entry),
                'contact_sheet': bool(contact_sheet_entry),
            },
            'artifacts_count': len(artifacts) if isinstance(artifacts, dict) else 0,
            'started_at': manifest.get('started_at'),
            'finished_at': manifest.get('finished_at'),
        })
    items.sort(key=lambda item: str(item.get('started_at') or ''), reverse=True)
    return items



def _manifest_payload(run_id: str) -> dict | None:
    run_dir = _run_dir_for(run_id)
    if run_dir is None:
        return None
    manifest = _read_json(run_dir / 'manifest.json')
    if isinstance(manifest, dict):
        return {"run_id": run_id, "manifest": manifest}
    return None

def create_app():
    try:
        from fastapi import FastAPI, Header, Request
        from fastapi.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(f"fastapi is required: {exc}")

    app = FastAPI(title="NEXTSTUDIO Bridge", version="1.0.0")

    def auth_ok(authorization: str | None) -> bool:
        key = _bearer_key()
        if not key:
            return False
        return (authorization or "") == f"Bearer {key}"

    @app.get("/studio/health")
    def health() -> dict:
        return {"ok": True, "service": "studio-bridge", "engines": True}

    @app.post("/studio/start")
    def start(payload: dict, authorization: str | None = Header(None)) -> dict:
        if not auth_ok(authorization):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        topic = str(payload.get("topic") or "").strip()
        if not TOPIC_RE.match(topic):
            return JSONResponse(status_code=400, content={"detail": "topic must be 1-200 printable characters"})
        return JSONResponse(status_code=202, content=_launch(
            "start",
            [sys.executable, "pipelines/short.py", "--topic", topic, "--quality", "strong"],
        ))

    @app.get("/studio/jobs/{job_id}")
    def job(job_id: str, authorization: str | None = Header(None)) -> dict:
        if not auth_ok(authorization):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        if not re.match(r"^\d+-[0-9a-f]{8}$", job_id):
            return JSONResponse(status_code=400, content={"detail": "invalid job id"})
        meta = _read_job(job_id)
        if meta.get("status") == "error":
            return JSONResponse(status_code=404, content=meta)
        return meta





    @app.get("/studio/manifest/{run_id}")
    def manifest_route(run_id: str, authorization: str | None = Header(None)) -> dict:
        if not auth_ok(authorization):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        payload = _manifest_payload(run_id)
        if payload is None:
            return JSONResponse(status_code=404, content={"detail": "run not found"})
        return payload

    @app.get("/studio/library")
    def library(authorization: str | None = Header(None)) -> dict:
        if not auth_ok(authorization):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        return {"items": _library_items(), "source": "outputs/runs"}

    @app.get("/studio/jobs")
    def jobs(authorization: str | None = Header(None)) -> dict:
        if not auth_ok(authorization):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        records = []
        for path in sorted(JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return {"jobs": records}

    @app.post("/studio/runs/{run_id}/approve-storyboard")
    def approve(run_id: str, payload: dict, authorization: str | None = Header(None)) -> dict:
        if not auth_ok(authorization):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        reviewer = str(payload.get("reviewer") or "").strip()
        note = str(payload.get("note") or "")[:500]
        if not REVIEWER_RE.match(reviewer):
            return JSONResponse(status_code=400, content={"detail": "reviewer is required (1-120 printable characters)"})
        run_dir = _run_dir_for(run_id)
        if run_dir is None:
            return JSONResponse(status_code=404, content={"detail": "run not found"})
        storyboard = _find_storyboard_in_run(run_dir)
        if storyboard is None:
            return JSONResponse(status_code=404, content={"detail": "storyboard not found in run"})
        try:
            from app.visuals.storyboard import approve_storyboard
            approval = approve_storyboard(storyboard, reviewer, note)
        except RuntimeError as exc:
            return JSONResponse(status_code=409, content={"detail": str(exc)})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"detail": str(exc)})
        return {"status": "approved", "run_id": run_id, "storyboard": str(storyboard), "approval": approval}

    @app.post("/studio/runs/{run_id}/resume")
    def resume(run_id: str, authorization: str | None = Header(None)) -> dict:
        if not auth_ok(authorization):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        run_dir = _run_dir_for(run_id)
        if run_dir is None:
            return JSONResponse(status_code=404, content={"detail": "run not found"})
        plan = run_dir / "render_plan.json"
        if not plan.is_file():
            plan = run_dir / "shots" / "render_plan.json"
        if not plan.is_file():
            return JSONResponse(status_code=409, content={"detail": "no render plan in run; cannot resume"})
        return JSONResponse(status_code=202, content=_launch(
            "resume",
            [sys.executable, "pipelines/short.py", "--resume", str(run_dir)],
        ))

    return app


def main() -> int:
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Local Studio write-server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5181)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        print("studio-bridge: refusing to bind beyond loopback", file=sys.stderr)
        return 2
    if not _bearer_key():
        print("studio-bridge: SHORTS_STUDIO_API_KEY is not configured; refusing to start", file=sys.stderr)
        return 2
    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
