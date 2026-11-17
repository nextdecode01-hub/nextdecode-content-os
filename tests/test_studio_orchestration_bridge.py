from __future__ import annotations
import pytest
import app.autonomy.tasks as tasks

import json

from fastapi.testclient import TestClient

from api import main as api_main
from app.autonomy.models import TaskRequest, TaskResult
from app.autonomy.registry import build_default_registry
from app.autonomy.store import TaskStore
from app.autonomy.worker import TaskWorker


def _storyboard():
    return {
        "title": "AI Accelerates Research?",
        "target_duration_seconds": 35,
        "scenes": [
            {"id": 1, "name": "Hook", "start": 0, "end": 4, "kind": "Kinetic typography",
             "description": "Open with a sharp question.", "caption": "Does AI speed up research?"},
            {"id": 2, "name": "Evidence", "start": 4, "end": 11, "kind": "B-roll",
             "description": "Show the evidence cards.", "caption": "Evidence before conclusions."},
            {"id": 3, "name": "Caveat", "start": 11, "end": 20, "kind": "Motion graphic",
             "description": "Explain the limitation.", "caption": "A hypothesis is not proof."},
        ],
    }


def test_storyboard_validator_rejects_overlapping_scenes():
    from app.autonomy.tasks import validate_storyboard_payload

    payload = _storyboard()
    payload["scenes"][2]["start"] = 10
    try:
        validate_storyboard_payload(payload)
    except ValueError as exc:
        assert "overlaps" in str(exc)
    else:
        raise AssertionError("overlapping scenes must be rejected")


def test_studio_storyboard_http_to_durable_worker_result(tmp_path, monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "studio-bridge-test-key")
    monkeypatch.setenv("NEXTDECODE_TASK_DB", str(tmp_path / "studio-bridge.sqlite3"))
    monkeypatch.delenv("DATABASE_URL", raising=False)

    client = TestClient(api_main.app)
    headers = {"Authorization": "Bearer studio-bridge-test-key"}
    denied = client.post("/tasks", json={
        "task_type": "studio.storyboard.validate", "payload": _storyboard()
    })
    assert denied.status_code == 401

    queued = client.post("/tasks", headers=headers, json={
        "task_type": "studio.storyboard.validate",
        "payload": _storyboard(),
        "idempotency_key": "studio-storyboard-bridge-001",
    })
    assert queued.status_code == 202
    task_id = queued.json()["task_id"]
    assert queued.json()["status"] == "queued"

    store = TaskStore(tmp_path / "studio-bridge.sqlite3")
    worker = TaskWorker(store, registry=build_default_registry(), worker_id="studio-bridge-test-worker")
    assert worker.run_once() is True

    detail = client.get(f"/tasks/{task_id}", headers=headers)
    assert detail.status_code == 200
    task = detail.json()["task"]
    assert task["status"] == "succeeded"
    assert task["task_type"] == "studio.storyboard.validate"
    result = json.loads(task["result_json"])
    assert result["output"]["scene_count"] == 3
    assert result["output"]["actual_duration_seconds"] == 20.0
    assert result["output"]["human_review_required"] is True
    assert result["output"]["external_actions_allowed"] is False
    assert result["evidence"]["validation"] == "studio.storyboard.v1"
    assert [event["event"] for event in detail.json()["events"]] == [
        "queued", "claimed", "succeeded"
    ]


def test_storyboard_capability_is_offline_and_not_planner_exposed():
    capability = build_default_registry().get("studio.storyboard.validate")
    assert capability.network_access is False
    assert capability.planner_allowed is False
    assert capability.permission_scopes == ("input:read",)
    assert capability.sandbox_profile == "in-process-bounded"


def test_storyboard_validation_binds_immutable_studio_version_and_digest():
    from app.autonomy.models import TaskRequest
    from app.autonomy.tasks import validate_storyboard_payload, validate_storyboard

    payload = _storyboard()
    payload["studio_version_id"] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    payload["studio_content_sha256"] = "b" * 64
    normalized = validate_storyboard_payload(payload)
    assert normalized["studio_version_id"] == "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    assert normalized["studio_content_sha256"] == "b" * 64

    result = validate_storyboard(TaskRequest("studio.storyboard.validate", normalized))
    assert result.status == "succeeded"
    assert result.output["studio_version_id"] == "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    assert result.output["studio_content_sha256"] == "b" * 64
    assert result.evidence["studio_version_id"] == "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    assert result.evidence["studio_content_sha256"] == "b" * 64


def test_storyboard_version_provenance_requires_valid_paired_identity():
    from app.autonomy.tasks import validate_storyboard_payload
    import pytest

    payload = _storyboard()
    payload["studio_version_id"] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    with pytest.raises(ValueError, match="supplied together"):
        validate_storyboard_payload(payload)

    payload["studio_content_sha256"] = "not-a-digest"
    with pytest.raises(ValueError, match="SHA-256 digest"):
        validate_storyboard_payload(payload)


def test_storyboard_validation_remains_compatible_without_studio_provenance():
    from app.autonomy.models import TaskRequest
    from app.autonomy.tasks import validate_storyboard_payload, validate_storyboard
    result = validate_storyboard(TaskRequest("studio.storyboard.validate", validate_storyboard_payload(_storyboard())))
    assert result.status == "succeeded"
    assert result.output["studio_version_id"] is None
    assert result.evidence["studio_content_sha256"] is None


def _studio_snapshot():
    from app.autonomy.tasks import hashlib, json
    snapshot = {
        "schema": "nextdecode.studio.storyboard.v1",
        "title": "AI Accelerates Research?",
        "beats": [
            {"id": 1, "name": "Hook", "start": 0, "end": 4, "kind": "Kinetic typography",
             "description": "Open with a sharp question.", "caption": "Does AI speed up research?"},
            {"id": 2, "name": "Evidence", "start": 4, "end": 11, "kind": "B-roll",
             "description": "Show the evidence cards.", "caption": "Evidence before conclusions."},
        ],
    }
    canonical = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
    return snapshot, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_research_payload_recomputes_studio_snapshot_digest():
    from app.autonomy.tasks import validate_topic_payload
    snapshot, digest = _studio_snapshot()
    payload = {"topic": "AI research", "studio_version_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
               "studio_content_sha256": digest, "studio_snapshot": snapshot}
    normalized = validate_topic_payload(payload)
    assert normalized["studio_content_sha256"] == digest
    assert normalized["studio_snapshot"] == snapshot
    payload["studio_snapshot"]["beats"][0]["caption"] = "tampered"
    with pytest.raises(ValueError, match="SHA-256 verification failed"):
        validate_topic_payload(payload)


def test_research_payload_requires_full_snapshot_for_studio_provenance():
    from app.autonomy.tasks import validate_topic_payload
    with pytest.raises(ValueError, match="snapshot is required"):
        validate_topic_payload({"topic": "AI", "studio_version_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                                "studio_content_sha256": "b" * 64})


def test_research_task_carries_verified_studio_identity_without_live_network(monkeypatch):
    from app.autonomy.tasks import research_topic_collect
    snapshot, digest = _studio_snapshot()
    payload = {"topic": "AI research", "studio_version_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
               "studio_content_sha256": digest, "studio_snapshot": snapshot}
    monkeypatch.setattr("app.autonomy.tasks._run_module", lambda *a, **k: TaskResult(
        "succeeded", {"artifact_path": "outputs/autonomy/artifacts/research.json",
                       "artifact_sha256": "c" * 64,
                       "studio_version_id": payload["studio_version_id"],
                       "studio_content_sha256": payload["studio_content_sha256"]},
        evidence={"artifact_verified": True}))
    result = research_topic_collect(TaskRequest("research.topic.collect", payload))
    assert result.status == "succeeded"
    assert result.output["studio_version_id"] == payload["studio_version_id"]
    assert result.evidence["studio_snapshot_sha256_verified"] is True


def test_script_draft_blocks_research_from_another_studio_version(monkeypatch):
    payload = {"topic": "AI research", "studio_version_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
               "studio_content_sha256": "b" * 64}
    request = TaskRequest("content.short.script.draft", payload, context={"dependencies": [{
        "task_type": "research.topic.collect", "status": "succeeded",
        "output": {"artifact_path": "outputs/autonomy/artifacts/research.json",
                    "artifact_sha256": "c" * 64,
                    "studio_version_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                    "studio_content_sha256": "e" * 64}}]})
    result = tasks.short_script_draft(request)
    assert result.status == "blocked"
    assert result.error_code == "studio_research_provenance_mismatch"


def test_script_draft_requires_studio_provenance_when_research_is_studio_bound(monkeypatch):
    request = TaskRequest("content.short.script.draft", {"topic": "AI research"},
                          context={"dependencies": [{
        "task_type": "research.topic.collect", "status": "succeeded",
        "output": {"artifact_path": "outputs/autonomy/artifacts/research.json",
                    "artifact_sha256": "c" * 64,
                    "studio_version_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                    "studio_content_sha256": "b" * 64}}]})
    result = tasks.short_script_draft(request)
    assert result.status == "blocked"
    assert result.error_code == "studio_provenance_required_for_research_dependency"


def test_script_draft_accepts_matching_studio_research_and_forwards_identity(monkeypatch):
    version_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    digest = "b" * 64
    request = TaskRequest("content.short.script.draft", {
        "topic": "AI research", "studio_version_id": version_id,
        "studio_content_sha256": digest,
    }, context={"dependencies": [{
        "task_type": "research.topic.collect", "status": "succeeded",
        "output": {"artifact_path": "outputs/autonomy/artifacts/research.json",
                    "artifact_sha256": "c" * 64,
                    "studio_version_id": version_id,
                    "studio_content_sha256": digest}}]})
    captured = {}
    def fake_run(_module, args, **_kwargs):
        captured["args"] = args
        return TaskResult("succeeded", {"artifact_path": "outputs/autonomy/artifacts/script.json",
                                         "artifact_sha256": "d" * 64,
                                         "studio_version_id": version_id,
                                         "studio_content_sha256": digest})
    monkeypatch.setattr(tasks, "_run_module", fake_run)
    result = tasks.short_script_draft(request)
    assert result.status == "succeeded"
    assert "--studio-version-id" in captured["args"]
    assert version_id in captured["args"]
    assert "--studio-content-sha256" in captured["args"]
    assert digest in captured["args"]
    assert result.output["studio_version_id"] == version_id
