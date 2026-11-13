import json
import threading
from types import SimpleNamespace

from api import main as api_main


def test_worker_publishes_done_and_artifact_metadata_atomically(monkeypatch, tmp_path):
    job_id = "r13-atomic-test"
    with api_main.jobs_lock:
        api_main.jobs[job_id] = {"status": "queued", "dry_run": True, "topic": "atomic lifecycle test", "quality": api_main.PRODUCTION_QUALITY}
    monkeypatch.setattr(api_main, "LOG_DIR", tmp_path)
    monkeypatch.setattr(api_main, "_notify", lambda _message: False)

    def fake_pipeline_run(_cmd, *, stdout, **_kwargs):
        stdout.write(json.dumps({"status": "success", "video_path": "outputs/test/final.mp4", "title": "Atomic test artifact", "quality": api_main.PRODUCTION_QUALITY}) + chr(10))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(api_main.subprocess, "run", fake_pipeline_run)
    update_ready = threading.Event()
    allow_update = threading.Event()
    original_update = api_main._update_job

    def pause_before_terminal_commit(target_job_id, updates, remove=()):
        if target_job_id == job_id and updates.get("status") == "done":
            assert updates.get("video_path") == "outputs/test/final.mp4"
            assert updates.get("title") == "Atomic test artifact"
            update_ready.set()
            assert allow_update.wait(timeout=5), "test did not release terminal update"
        return original_update(target_job_id, updates, remove=remove)

    monkeypatch.setattr(api_main, "_update_job", pause_before_terminal_commit)
    worker = threading.Thread(target=api_main.run_job, args=(job_id, True, "atomic lifecycle test", api_main.PRODUCTION_QUALITY))
    worker.start()
    try:
        assert update_ready.wait(timeout=5), "worker did not reach terminal commit"
        during_commit = api_main.status(job_id)
        assert during_commit["status"] == "running"
        assert "video_path" not in during_commit
        assert "title" not in during_commit
        allow_update.set()
        worker.join(timeout=5)
        assert not worker.is_alive(), "worker did not finish"
        completed = api_main.status(job_id)
        assert completed["status"] == "done"
        assert completed["video_path"] == "outputs/test/final.mp4"
        assert completed["title"] == "Atomic test artifact"
        assert "log_tail" in completed
        assert completed["notified"] is False
    finally:
        allow_update.set()
        worker.join(timeout=5)
        with api_main.jobs_lock:
            api_main.jobs.pop(job_id, None)
