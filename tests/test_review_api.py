from __future__ import annotations
import hashlib
import json
from fastapi.testclient import TestClient
from api import main as api_main
from app.review import read_service


def _write_review(root, *, video=b"video-v1", metadata=b'{"title": "Test"}'):
    data, outputs = root / "data", root / "outputs"
    queue = data / "review_queue"
    queue.mkdir(parents=True)
    outputs.mkdir(parents=True)
    video_path, metadata_path = outputs / "output_short.mp4", data / "metadata.json"
    video_path.write_bytes(video)
    metadata_path.write_bytes(metadata)
    package = {
        "status": "pending_human_review",
        "title": "Test review",
        "video_path": str(video_path),
        "metadata_path": str(metadata_path),
        "video_sha256": hashlib.sha256(video).hexdigest(),
        "metadata_sha256": hashlib.sha256(metadata).hexdigest(),
        "visuals": {"mode": "test", "asset_path": str(outputs / "private-asset.png")},
    }
    package_path = queue / "review-1.json"
    package_bytes = json.dumps(package, sort_keys=True).encode()
    package_path.write_bytes(package_bytes)
    pointer = {"status": "pending_human_review", "package": str(package_path), "created_at": "2026-11-12T00:00:00+00:00"}
    (data / "review_pending.json").write_text(json.dumps(pointer), encoding="utf-8")
    return package_path, package_bytes, package


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv(api_main.API_KEY_ENV, "review-test-key")
    monkeypatch.setattr(read_service, "ROOT", tmp_path)
    monkeypatch.setattr(read_service, "PENDING_POINTER", tmp_path / "data" / "review_pending.json")
    monkeypatch.setattr(read_service, "REVIEW_QUEUE", tmp_path / "data" / "review_queue")
    return TestClient(api_main.app)


def test_pending_review_requires_bearer_authentication(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    assert client.get("/review/pending").status_code == 401


def test_pending_review_returns_verified_package_digest_without_local_paths(monkeypatch, tmp_path):
    _, package_bytes, _ = _write_review(tmp_path)
    response = _client(monkeypatch, tmp_path).get(
        "/review/pending", headers={"Authorization": "Bearer review-test-key"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending_human_review"
    assert body["review_package_sha256"] == hashlib.sha256(package_bytes).hexdigest()
    assert body["package"]["title"] == "Test review"
    assert "video_path" not in body["package"]
    assert "metadata_path" not in body["package"]
    assert "asset_path" not in body["package"]["visuals"]


def test_pending_review_returns_not_found_when_pointer_is_absent(monkeypatch, tmp_path):
    response = _client(monkeypatch, tmp_path).get(
        "/review/pending", headers={"Authorization": "Bearer review-test-key"})
    assert response.status_code == 404
    assert response.json()["detail"] == "no_pending_review"


def test_pending_review_fails_closed_when_video_hash_changes(monkeypatch, tmp_path):
    _write_review(tmp_path)
    (tmp_path / "outputs" / "output_short.mp4").write_bytes(b"replaced-video")
    response = _client(monkeypatch, tmp_path).get(
        "/review/pending", headers={"Authorization": "Bearer review-test-key"})
    assert response.status_code == 409
    assert response.json()["detail"] == "review_artifact_hash_mismatch"


def test_pending_review_rejects_package_path_outside_review_queue(monkeypatch, tmp_path):
    _write_review(tmp_path)
    outside = tmp_path / "data" / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    pointer = tmp_path / "data" / "review_pending.json"
    pointer.write_text(json.dumps({"status": "pending_human_review", "package": str(outside)}), encoding="utf-8")
    response = _client(monkeypatch, tmp_path).get(
        "/review/pending", headers={"Authorization": "Bearer review-test-key"})
    assert response.status_code == 503


def test_pending_review_route_is_registered_as_protected():
    route = next(route for route in api_main.app.routes if getattr(route, "path", None) == "/review/pending")
    assert any(dependency.call is api_main.require_api_key for dependency in route.dependant.dependencies)

def test_pending_review_fails_closed_when_metadata_hash_changes(monkeypatch, tmp_path):
    _write_review(tmp_path)
    (tmp_path / "data" / "metadata.json").write_text('{"title": "changed"}', encoding="utf-8")
    response = _client(monkeypatch, tmp_path).get(
        "/review/pending", headers={"Authorization": "Bearer review-test-key"})
    assert response.status_code == 409
    assert response.json()["detail"] == "review_artifact_hash_mismatch"


def test_pending_review_does_not_mutate_pointer_or_package(monkeypatch, tmp_path):
    package_path, package_bytes, _ = _write_review(tmp_path)
    pointer_path = tmp_path / "data" / "review_pending.json"
    pointer_bytes = pointer_path.read_bytes()
    response = _client(monkeypatch, tmp_path).get(
        "/review/pending", headers={"Authorization": "Bearer review-test-key"})
    assert response.status_code == 200
    assert package_path.read_bytes() == package_bytes
    assert pointer_path.read_bytes() == pointer_bytes

def test_pending_review_rejects_noncanonical_artifact_path_even_with_matching_hash(monkeypatch, tmp_path):
    _, _, package = _write_review(tmp_path)
    alternate = tmp_path / "outputs" / "other.mp4"
    alternate.write_bytes(b"other-video")
    package["video_path"] = str(alternate)
    package["video_sha256"] = hashlib.sha256(b"other-video").hexdigest()
    package_path = tmp_path / "data" / "review_queue" / "review-1.json"
    package_path.write_text(json.dumps(package, sort_keys=True), encoding="utf-8")
    response = _client(monkeypatch, tmp_path).get(
        "/review/pending", headers={"Authorization": "Bearer review-test-key"})
    assert response.status_code == 503
    assert response.json()["detail"] == "review_artifact_path_unsafe"


# Independent-review hardening: exercise fail-closed branches and the HTTP boundary.
import pytest


def _authorized_get(client):
    return client.get("/review/pending", headers={"Authorization": "Bearer review-test-key"})


def test_pending_review_missing_canonical_artifact_is_unavailable(monkeypatch, tmp_path):
    _write_review(tmp_path)
    (tmp_path / "outputs" / "output_short.mp4").unlink()
    response = _authorized_get(_client(monkeypatch, tmp_path))
    assert response.status_code == 503
    assert response.json()["detail"] == "review_artifact_unavailable"


@pytest.mark.parametrize("target", ["pointer", "package"])
def test_pending_review_rejects_malformed_json(monkeypatch, tmp_path, target):
    package_path, _, _ = _write_review(tmp_path)
    path = (tmp_path / "data" / "review_pending.json") if target == "pointer" else package_path
    path.write_text("{not-json", encoding="utf-8")
    response = _authorized_get(_client(monkeypatch, tmp_path))
    assert response.status_code == 503
    assert response.json()["detail"] == "review_file_unreadable"


@pytest.mark.parametrize("target", ["pointer", "package"])
def test_pending_review_rejects_oversized_json(monkeypatch, tmp_path, target):
    package_path, _, _ = _write_review(tmp_path)
    path = (tmp_path / "data" / "review_pending.json") if target == "pointer" else package_path
    path.write_bytes(b" " * (64_001 if target == "pointer" else 1_000_001))
    response = _authorized_get(_client(monkeypatch, tmp_path))
    assert response.status_code == 503
    assert response.json()["detail"] == "review_file_invalid_size"


def test_pending_review_rejects_non_pending_pointer(monkeypatch, tmp_path):
    _write_review(tmp_path)
    pointer_path = tmp_path / "data" / "review_pending.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer["status"] = "completed"
    pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
    response = _authorized_get(_client(monkeypatch, tmp_path))
    assert response.status_code == 404
    assert response.json()["detail"] == "no_pending_review"


def test_pending_review_rejects_non_pending_package(monkeypatch, tmp_path):
    package_path, _, package = _write_review(tmp_path)
    package["status"] = "completed"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    response = _authorized_get(_client(monkeypatch, tmp_path))
    assert response.status_code == 409
    assert response.json()["detail"] == "review_package_not_pending"


def test_pending_review_rejects_malformed_artifact_digest(monkeypatch, tmp_path):
    package_path, _, package = _write_review(tmp_path)
    package["video_sha256"] = "not-a-sha256"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    response = _authorized_get(_client(monkeypatch, tmp_path))
    assert response.status_code == 409
    assert response.json()["detail"] == "review_artifact_digest_invalid"


def test_pending_review_rejects_symlinked_package(monkeypatch, tmp_path):
    package_path, _, _ = _write_review(tmp_path)
    outside = tmp_path / "data" / "outside.json"
    outside.write_bytes(package_path.read_bytes())
    package_path.unlink()
    try:
        package_path.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this platform")
    response = _authorized_get(_client(monkeypatch, tmp_path))
    assert response.status_code == 503
    assert response.json()["detail"] == "review_artifact_path_unsafe"


def test_pending_review_rejects_symlinked_artifact(monkeypatch, tmp_path):
    _write_review(tmp_path)
    video = tmp_path / "outputs" / "output_short.mp4"
    alternate = tmp_path / "outputs" / "alternate.mp4"
    video.rename(alternate)
    try:
        video.symlink_to(alternate)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this platform")
    response = _authorized_get(_client(monkeypatch, tmp_path))
    assert response.status_code == 503
    assert response.json()["detail"] == "review_artifact_path_unsafe"


@pytest.mark.parametrize("authorization", ["Bearer wrong-key", "Basic review-test-key", "Bearer "])
def test_pending_review_rejects_invalid_credentials_at_http_boundary(monkeypatch, tmp_path, authorization):
    _write_review(tmp_path)
    client = _client(monkeypatch, tmp_path)
    monkeypatch.setattr(api_main, "get_pending_review", lambda: pytest.fail("review service called before auth"))
    response = client.get("/review/pending", headers={"Authorization": authorization})
    assert response.status_code == 401


def test_pending_review_fails_closed_when_server_key_is_unconfigured(monkeypatch, tmp_path):
    _write_review(tmp_path)
    client = _client(monkeypatch, tmp_path)
    monkeypatch.delenv(api_main.API_KEY_ENV)
    monkeypatch.setattr(api_main, "get_pending_review", lambda: pytest.fail("review service called without server key"))
    response = client.get("/review/pending", headers={"Authorization": "Bearer review-test-key"})
    assert response.status_code == 503
    assert response.json()["detail"] == "api_key_not_configured"


def test_pending_review_get_and_unsupported_write_method_preserve_all_review_bytes(monkeypatch, tmp_path):
    package_path, _, _ = _write_review(tmp_path)
    data, outputs = tmp_path / "data", tmp_path / "outputs"
    paths = [data / "review_pending.json", package_path, data / "metadata.json", outputs / "output_short.mp4"]
    approval_record = data / "review_approved.json"
    if approval_record.exists():
        paths.append(approval_record)
    before = {path: path.read_bytes() for path in paths}
    client = _client(monkeypatch, tmp_path)
    assert _authorized_get(client).status_code == 200
    assert client.post("/review/pending", headers={"Authorization": "Bearer review-test-key"}).status_code == 405
    assert {path: path.read_bytes() for path in paths} == before
