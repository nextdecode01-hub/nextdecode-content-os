import hashlib
import json
import os
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import main as api_main


def _manifest(root, run_id, **updates):
    run_dir = root / "outputs" / "runs" / run_id
    run_dir.mkdir(parents=True)
    manifest = {
        "run_id": run_id, "schema_version": 1, "status": "failed",
        "quality": "strong", "topic": "Synthetic fixture only",
        "started_at": "2026-11-07T03:52:11+00:00",
        "finished_at": "2026-11-07T04:00:07+00:00",
        "artifacts": {}, "stages": [],
        "failure": {"stage": "research", "error_type": "RuntimeError", "error_category": "research"},
    }
    manifest.update(updates)
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run_dir


def test_list_production_runs_reads_real_manifests_and_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    _manifest(tmp_path, "20261107-035211-synthetic-fixture")
    result = api_main.list_production_runs(limit=999)
    assert result["source"] == "local_run_tracker"
    assert result["limit"] == 200
    assert len(result["runs"]) == 1
    assert result["runs"][0]["status"] == "failed"
    assert result["runs"][0]["stage_count"] == 0


def test_production_run_detail_returns_only_persisted_stage_and_artifact_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    run_id = "20261107-035211-synthetic-fixture"
    run_dir = _manifest(tmp_path, run_id, stages=[{
        "name": "script", "started_at": "2026-11-07T03:53:00+00:00",
        "finished_at": "2026-11-07T03:54:00+00:00", "status": "ok",
    }])
    artifact = run_dir / "script.json"
    artifact.write_text('{"synthetic":true}', encoding="utf-8")
    manifest_path = run_dir / "manifest.json"
    data = json.loads(manifest_path.read_text())
    data["artifacts"] = {"script": {"path": "script.json", "sha256": "a" * 64, "bytes": artifact.stat().st_size, "stage": "script"}}
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    result = api_main.get_production_run(run_id)
    assert [stage["name"] for stage in result["stages"]] == ["script"]
    assert result["artifacts"][0]["exists"] is True
    assert result["trace_completeness"] == "manifest_only"
    assert result["canonical_workflow_linked"] is False
    assert "Synthetic fixture only" == result["run"]["topic"]


def test_production_run_detail_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    with pytest.raises(HTTPException) as caught:
        api_main.get_production_run("../outside")
    assert caught.value.status_code == 404


def test_production_run_routes_require_bearer_authentication(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-run-key")
    run_id = "20261107-035211-synthetic-fixture"
    _manifest(tmp_path, run_id)
    client = TestClient(api_main.app)
    assert client.get("/production-runs").status_code == 401
    headers = {"Authorization": "Bearer test-run-key"}
    assert client.get("/production-runs", headers=headers).status_code == 200
    assert client.get(f"/production-runs/{run_id}", headers=headers).status_code == 200


def test_production_run_storyboard_returns_sanitized_scene_qa_and_image_url(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    run_id = "20261107-035211-storyboard-fixture"
    run_dir = _manifest(tmp_path, run_id)
    image = run_dir / "shots" / "storyboard" / "scene_000.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"fake-png-bytes")
    storyboard = image.parent / "storyboard.json"
    storyboard.write_text(json.dumps({
        "title": "Fixture",
        "review_status": "auto_approved",
        "approved": True,
        "review_required": False,
        "review_reasons": [],
        "summary": {"scene_count": 1},
        "scenes": [{
            "index": 0, "start": 0, "end": 3.5,
            "narration": "A router selects an expert.",
            "scene_type": "diagram", "visual_type": "motion_graphic",
            "provider": "motion_graphic", "asset_id": "local:fixture",
            "relevance": "narration_derived", "relevance_confidence": "high",
            "asset_path": str(image), "review_reason": "", "fallback_reason": "",
        }],
    }), encoding="utf-8")

    result = api_main.get_production_run_storyboard(run_id)
    assert result["scene_count"] == 1
    assert result["approved"] is True
    assert result["scenes"][0]["image_url"] == f"/api/production-runs/{run_id}/scenes/0/image"
    assert "asset_path" not in result["scenes"][0]
    response = api_main.get_production_run_scene_image(run_id, 0)
    assert response.media_type == "image/png"
    assert response.body == b"fake-png-bytes"


def test_production_run_scene_image_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    run_id = "20261107-035211-storyboard-traversal"
    run_dir = _manifest(tmp_path, run_id)
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"not allowed")
    storyboard_dir = run_dir / "shots" / "storyboard"
    storyboard_dir.mkdir(parents=True)
    (storyboard_dir / "storyboard.json").write_text(json.dumps({
        "scenes": [{"index": 0, "asset_path": str(outside)}],
    }), encoding="utf-8")
    with pytest.raises(HTTPException) as caught:
        api_main.get_production_run_scene_image(run_id, 0)
    assert caught.value.status_code == 404


def test_storyboard_route_requires_bearer_authentication(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    monkeypatch.setenv(api_main.API_KEY_ENV, "test-run-key")
    run_id = "20261107-035211-storyboard-auth"
    _manifest(tmp_path, run_id)
    client = TestClient(api_main.app)
    assert client.get(f"/production-runs/{run_id}/storyboard").status_code == 401
    headers = {"Authorization": "Bearer test-run-key"}
    assert client.get(f"/production-runs/{run_id}/storyboard", headers=headers).status_code == 404


def test_run_summary_exposes_current_stage_only_when_persisted_active():
    active = api_main._production_run_summary({
        "run_id": "synthetic", "status": "in_progress", "stages": [
            {"name": "research", "status": "ok"},
            {"name": "voice", "status": "in_progress"},
        ],
    })
    assert active["active_stage"] == "voice"

    completed = api_main._production_run_summary({
        "run_id": "synthetic", "status": "ok", "stages": [
            {"name": "research", "status": "ok"},
        ],
    })
    assert completed["active_stage"] is None


def test_production_artifact_integrity_metadata_states(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    run_id = "20261107-035211-integrity-fixture"
    run_dir = _manifest(tmp_path, run_id)
    present = run_dir / "present.bin"
    present.write_bytes(b"current bytes")
    data = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    actual_digest = hashlib.sha256(b"current bytes").hexdigest()
    data["artifacts"] = {
        "consistent": {"path": "present.bin", "sha256": actual_digest, "bytes": len(b"current bytes"), "stage": "render"},
        "size_changed": {"path": "present.bin", "sha256": "b" * 64, "bytes": 999, "stage": "render"},
        "no_digest": {"path": "present.bin", "sha256": "", "bytes": len(b"current bytes"), "stage": "render"},
        "no_size": {"path": "present.bin", "sha256": actual_digest, "stage": "render"},
        "missing": {"path": "gone.bin", "sha256": "c" * 64, "bytes": 10, "stage": "render"},
        "unsafe": {"path": "../outside.bin", "sha256": "d" * 64, "bytes": 10, "stage": "render"},
    }
    (run_dir / "manifest.json").write_text(json.dumps(data), encoding="utf-8")

    artifacts = {item["name"]: item for item in api_main.get_production_run(run_id)["artifacts"]}
    assert artifacts["consistent"]["integrity_status"] == "verified"
    assert artifacts["consistent"]["computed_sha256"] == actual_digest
    assert artifacts["consistent"]["metadata_status"] == "metadata_consistent"
    assert artifacts["consistent"]["actual_bytes"] == len(b"current bytes")
    assert artifacts["size_changed"]["integrity_status"] == "digest_mismatch"
    assert artifacts["size_changed"]["metadata_status"] == "size_mismatch"
    assert artifacts["no_digest"]["integrity_status"] == "digest_missing"
    assert artifacts["no_size"]["integrity_status"] == "verified"
    assert artifacts["no_size"]["metadata_status"] == "size_missing"
    assert artifacts["missing"]["integrity_status"] == "missing_file"
    assert artifacts["unsafe"]["integrity_status"] == "unsafe_path"
    assert artifacts["unsafe"]["path"] is None


def test_run_artifact_digest_verification_refuses_symlink(tmp_path):
    target = tmp_path / "target.bin"
    target.write_bytes(b"trusted target")
    link = tmp_path / "link.bin"
    link.symlink_to(target)
    expected = hashlib.sha256(b"trusted target").hexdigest()

    result = api_main._verify_run_artifact_digest(link, expected)

    assert result["digest_status"] == "verification_unavailable"
    assert result["computed_sha256"] is None


def test_run_artifact_digest_verification_enforces_size_limit(tmp_path, monkeypatch):
    artifact = tmp_path / "large.bin"
    artifact.write_bytes(b"123456789")
    monkeypatch.setattr(api_main, "MAX_RUN_ARTIFACT_VERIFY_BYTES", 4)

    result = api_main._verify_run_artifact_digest(
        artifact, hashlib.sha256(b"123456789").hexdigest()
    )

    assert result["digest_status"] == "verification_limit_exceeded"
    assert result["computed_sha256"] is None



def test_run_artifact_digest_verification_detects_mutation_during_read(tmp_path, monkeypatch):
    artifact = tmp_path / "changing.bin"
    original = b"original data"
    replacement = b"mutated data!"
    assert len(original) == len(replacement)
    artifact.write_bytes(original)
    before = artifact.stat()
    real_read = os.read
    mutated = False

    def mutate_after_first_read(descriptor, size):
        nonlocal mutated
        chunk = real_read(descriptor, size)
        if chunk and not mutated:
            mutated = True
            artifact.write_bytes(replacement)
            os.utime(
                artifact,
                ns=(before.st_atime_ns, before.st_mtime_ns + 5_000_000_000),
            )
        return chunk

    monkeypatch.setattr(api_main.os, "read", mutate_after_first_read)

    result = api_main._verify_run_artifact_digest(
        artifact, hashlib.sha256(original).hexdigest()
    )

    assert mutated is True
    assert result["digest_status"] == "file_changed_during_verification"
    assert result["computed_sha256"] is None


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO creation is unavailable")
def test_run_artifact_digest_verification_rejects_non_regular_file(tmp_path):
    fifo = tmp_path / "artifact.fifo"
    os.mkfifo(fifo)

    result = api_main._verify_run_artifact_digest(
        fifo, hashlib.sha256(b"not a regular file").hexdigest()
    )

    assert result["digest_status"] == "not_regular_file"
    assert result["computed_sha256"] is None



def test_run_artifact_digest_verification_accepts_exact_size_limit(tmp_path, monkeypatch):
    payload = b"exact-limit"
    artifact = tmp_path / "at-limit.bin"
    artifact.write_bytes(payload)
    monkeypatch.setattr(api_main, "MAX_RUN_ARTIFACT_VERIFY_BYTES", len(payload))

    result = api_main._verify_run_artifact_digest(
        artifact, hashlib.sha256(payload).hexdigest()
    )

    assert result["digest_status"] == "verified"
    assert result["computed_sha256"] == hashlib.sha256(payload).hexdigest()


def test_list_production_runs_skips_symlinked_run_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    runs_root = tmp_path / "outputs" / "runs"
    runs_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    run_id = "20261107-035211-synthetic-fixture"
    _manifest(tmp_path, run_id)
    # Move the valid-looking manifest outside the configured runs root, then
    # expose it only through a symlinked run directory.
    (runs_root / run_id).rename(outside / run_id)
    (runs_root / run_id).symlink_to(outside / run_id, target_is_directory=True)

    result = api_main.list_production_runs()

    assert result["runs"] == []


def test_production_run_detail_rejects_symlinked_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ROOT", tmp_path)
    run_id = "20261107-035211-synthetic-fixture"
    run_dir = tmp_path / "outputs" / "runs" / run_id
    run_dir.mkdir(parents=True)
    outside_manifest = tmp_path / "outside-manifest.json"
    outside_manifest.write_text(json.dumps({"run_id": run_id, "artifacts": {}, "stages": []}))
    (run_dir / "manifest.json").symlink_to(outside_manifest)

    with pytest.raises(HTTPException) as caught:
        api_main.get_production_run(run_id)

    assert caught.value.status_code == 503
    assert caught.value.detail == "production_run_manifest_unavailable"
