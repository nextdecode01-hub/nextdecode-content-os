import hashlib
import json

import pytest
from types import SimpleNamespace

from app.providers import video_generation_workflow as workflow


class FakeProvider:
    def create_text_to_video(self, prompt, **kwargs):
        return {"provider": "fake", "task_id": "task-123", "model": "fake-v1", "status": "submitted"}
    def download(self, task, output_path):
        output_path.write_bytes(b"fake-video-bytes")
        return output_path


def test_wait_for_video_task_polls_until_completed(monkeypatch):
    class Poller:
        def __init__(self):
            self.calls = 0
        def get_task(self, task_id):
            self.calls += 1
            return {"task_id": task_id, "status": "processing" if self.calls == 1 else "completed"}
    poller = Poller()
    monkeypatch.setattr(workflow, "_provider", lambda name: poller)
    now = [0.0]
    def clock():
        return now[0]
    def sleep(seconds):
        now[0] += seconds
    result = workflow.wait_for_video_task("kling", {"task_id": "t"}, poll_interval=1,
        max_wait_seconds=10, clock=clock, sleeper=sleep)
    assert result["status"] == "completed"
    assert poller.calls == 2


def test_generate_video_asset_is_denied_before_provider_construction(tmp_path, monkeypatch):
    constructed = []
    monkeypatch.setattr(workflow, "_provider", lambda name: constructed.append(name))
    target = tmp_path / "clip.mp4"
    with pytest.raises(PermissionError, match="disabled"):
        workflow.generate_video_asset("kling", "must not call provider", target)
    assert constructed == []
    assert not target.exists()


def test_generate_video_asset_rejects_provider_not_allowed_on_selected_route(tmp_path, monkeypatch):
    constructed = []
    policy = {"routes": {"direct_provider_apis": {"providers": []}}}
    monkeypatch.setattr(workflow, "load_video_generation_policy", lambda: policy)
    monkeypatch.setattr(workflow, "_provider", lambda name: constructed.append(name))
    with pytest.raises(PermissionError, match="not allowed on route"):
        workflow.generate_video_asset("kling", "fixture", tmp_path / "clip.mp4")
    assert constructed == []


def test_generate_video_asset_uses_provider_specific_approval_route(monkeypatch):
    routes = []
    monkeypatch.setattr(workflow, "authorize_video_generation", lambda route, policy=None: (
        routes.append(route) or SimpleNamespace(route=route, budget_usd=0.0,
            approved=True, policy_status="test_authorized")
    ))
    monkeypatch.setattr(workflow, "_provider", lambda name: FakeProvider())
    monkeypatch.setattr(workflow, "wait_for_video_task", lambda *a, **k: {
        "provider": "fake", "task_id": "task-123", "status": "completed",
        "video_url": "https://media.example/video.mp4"
    })
    monkeypatch.setattr(workflow, "_probe_video", lambda path: {
        "width": 720, "height": 1280, "duration_seconds": 5.0, "fps": "30/1"
    })
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        workflow.generate_video_asset("kling", "fixture", Path(tmp) / "k.mp4")
        workflow.generate_video_asset("runway", "fixture", Path(tmp) / "r.mp4")
    assert routes == ["direct_provider_apis", "unified_gateway"]


def test_generate_video_asset_persists_hash_and_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "authorize_video_generation", lambda route, policy=None: (
        SimpleNamespace(route=route, budget_usd=1.0, approved=True, policy_status="test_authorized")
    ))
    monkeypatch.setattr(workflow, "_provider", lambda name: FakeProvider())
    monkeypatch.setattr(workflow, "wait_for_video_task", lambda *a, **k: {
        "provider": "fake", "task_id": "task-123", "status": "completed",
        "video_url": "https://media.example/video.mp4"
    })
    monkeypatch.setattr(workflow, "_probe_video", lambda path: {
        "width": 720, "height": 1280, "duration_seconds": 5.0, "fps": "30/1"
    })
    target = tmp_path / "clip.mp4"
    record = workflow.generate_video_asset("kling", "cinematic data center", target, run_id="run-1")
    assert record["status"] == "qualified"
    assert record["run_id"] == "run-1"
    assert record["sha256"] == hashlib.sha256(b"fake-video-bytes").hexdigest()
    sidecar = json.loads((tmp_path / "clip.mp4.asset.json").read_text())
    assert sidecar["task_id"] == "task-123"
    assert sidecar["requires_editorial_review"] is True
    assert sidecar["authorization"]["approved"] is True
    assert sidecar["authorization"]["route"] == "direct_provider_apis"


def test_wait_for_video_task_returns_timeout_without_switching_provider(monkeypatch):
    class Poller:
        def get_task(self, task_id):
            return {"task_id": task_id, "status": "processing"}
    monkeypatch.setattr(workflow, "_provider", lambda name: Poller())
    now = [0.0]
    def clock():
        return now[0]
    def sleep(seconds):
        now[0] += seconds
    result = workflow.wait_for_video_task("runway", {"task_id": "t"}, poll_interval=1,
        max_wait_seconds=1, clock=clock, sleeper=sleep)
    assert result["status"] == "timeout"
