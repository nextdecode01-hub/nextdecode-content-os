#!/usr/bin/env python3
"""ND-M3-F1: Immutable upload artifact — digest-bound transfer verification.

Synthetic files + mocked network operations only: no credentials are read, no
real uploads occur, no external hosts are contacted.  The only sockets used are
127.0.0.1 test servers replicating the local tunnel handler, which is the
transfer mechanism under test.

Coverage:
* snapshot helper refuses unbound/unmatched bytes (negative, per artifact);
* youtube_short / youtube_longform / facebook transfer digest-bound snapshots;
* instagram's Meta-fetched URL is served from the immutable snapshot;
* externally configured URL mode is explicitly reported, never claimed bound;
* duplicate / ambiguous / dry-run governance outcomes are preserved; and
* orchestration pins its Instagram tunnel to a baseline-bound snapshot.
"""
from __future__ import annotations

import hashlib
import io
import json
import http.client
import os
import shutil
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlparse

V1 = (b"ND-M3-F1 synthetic video payload v1.\x00" * 4100)  # 151,700 bytes
V2 = (b"ND-M3-F1 synthetic video MUTATED v2.\x01" * 4100)  # different bytes, same size


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decision(video_bytes: bytes, *, platform: str, purpose: str = "short") -> dict:
    """A fake authorize_publish receipt binding an authorized digest.

    Mirrors the full WP5 protected-action receipt contract: scope keys, the
    canonical binding fields and the derived authorization_id, so the fake
    satisfies verify_protected_action_decision exactly like a real receipt.
    """
    from app.publish import authorization as authorization_module
    decision = {
        "policy_version": authorization_module.POLICY_VERSION,
        "status": "authorized",
        "action_type": "publish",
        "platform": platform,
        "purpose": purpose,
        "destination": "private",
        "public_release": None,
        "approved_at": "2026-11-06T00:00:00+00:00",
        "reviewer": "test-reviewer",
        "metadata_sha256": _sha(b"{synthetic metadata}"),
        "video_sha256": _sha(video_bytes),
    }
    binding_fields = (
        "policy_version", "action_type", "platform", "purpose", "destination",
        "approved_at", "reviewer", "metadata_sha256", "video_sha256",
    )
    decision["authorization_id"] = hashlib.sha256(
        json.dumps({key: decision[key] for key in binding_fields},
                   sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return decision


class _StubResponse:
    def __init__(self, payload):
        self._payload = payload
        self.ok = True
        self.status_code = 200
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _StubDotenv:
    """Prevents upstream modules from loading the real project .env in tests."""

    def load_dotenv(self, *args, **kwargs):
        return False


def _stub_dotenv():
    return patch.dict(sys.modules, {"dotenv": _StubDotenv()})


def _media_stub(capture: list):
    """Replace MediaFileUpload with a capturing stub (no googleapiclient I/O)."""
    class _MediaStub:
        def __init__(self, filename, **kwargs):
            capture.append({"path": str(filename), "bytes": Path(filename).read_bytes()})
    return _MediaStub


class SnapshotMechanismTests(unittest.TestCase):
    """The helper: authorized bytes in, nothing unbound ever created."""

    def setUp(self):
        stop = _stub_dotenv(); stop.start(); self.addCleanup(stop.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.video = self.root / "outputs" / "output_short.mp4"
        self.video.parent.mkdir(parents=True, exist_ok=True)
        self.video.write_bytes(V1)

    def test_positive_unchanged_artifact_transfers_exact_authorized_bytes(self):
        from app.publish.artifact_snapshot import upload_snapshot
        with upload_snapshot(self.video, _sha(V1), root=self.root) as snapshot:
            self.assertEqual(snapshot.sha256, _sha(V1))
            self.assertEqual(snapshot.size, len(V1))
            self.assertEqual(snapshot.path.read_bytes(), V1)  # byte-exact payload
            self.assertEqual(oct(os.stat(snapshot.path).st_mode & 0o777), oct(0o400))
        self.assertFalse(snapshot.path.exists())  # removed after the transfer
        from app.publish.artifact_snapshot import staging_is_empty
        self.assertTrue(staging_is_empty(self.root))

    def test_descriptor_pinning_survives_staging_path_replacement(self):
        from app.publish.artifact_snapshot import build_upload_snapshot

        snapshot = build_upload_snapshot(self.video, _sha(V1), root=self.root)
        replacement = snapshot.staging_path
        try:
            # Recreate the former staging name with different bytes. The
            # transfer path must still resolve to the original verified inode.
            replacement.write_bytes(V2)
            transferred = snapshot.path.read_bytes()
            self.assertEqual(transferred, V1)
            self.assertEqual(hashlib.sha256(transferred).hexdigest(), _sha(V1))
        finally:
            snapshot.close()
            replacement.unlink(missing_ok=True)

    def test_negative_replacement_after_authorization_is_blocked(self):
        from app.publish.artifact_snapshot import (
            ArtifactIntegrityError, build_upload_snapshot, staging_is_empty)
        self.video.write_bytes(V2)  # artifact replaced between auth and snapshot
        with self.assertRaises(ArtifactIntegrityError) as caught:
            build_upload_snapshot(self.video, _sha(V1), root=self.root)
        self.assertIn("changed after authorization", str(caught.exception))
        self.assertTrue(staging_is_empty(self.root))  # no partial snapshot survives

    def test_negative_swapped_file_under_the_same_name_never_transfers(self):
        from app.publish.artifact_snapshot import (
            ArtifactIntegrityError, build_upload_snapshot, staging_is_empty)
        replacement = self.root / "outputs" / "replacement.mp4"
        replacement.write_bytes(V2)
        os.replace(replacement, self.video)
        with self.assertRaises(ArtifactIntegrityError):
            build_upload_snapshot(self.video, _sha(V1), root=self.root)
        self.assertTrue(staging_is_empty(self.root))

    def test_negative_invalid_expected_digests_are_refused(self):
        from app.publish.artifact_snapshot import (
            ArtifactIntegrityError, build_upload_snapshot)
        for bad in ("", "tooshort", _sha(V2)[:32], "z" * 64, None):
            with self.assertRaises(ArtifactIntegrityError):
                build_upload_snapshot(self.video, bad, root=self.root)

    def test_negative_missing_source_is_refused(self):
        from app.publish.artifact_snapshot import (
            ArtifactIntegrityError, build_upload_snapshot)
        self.video.unlink()
        with self.assertRaises(ArtifactIntegrityError):
            build_upload_snapshot(self.video, _sha(V1), root=self.root)


class _Workspace(unittest.TestCase):
    """Shared synthetic workspace: tmp root + output video + platform copy."""

    def workspace(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "outputs").mkdir(parents=True, exist_ok=True)
        (self.root / "data").mkdir(parents=True, exist_ok=True)
        self.video = self.root / "outputs" / "output_short.mp4"
        self.video.write_bytes(V1)
        metadata = {
            "title": "Synthetic Reel", "content_pillar": "What Changed",
            "voice_text": "synthetic narration", "hook": "synthetic hook",
            "tags": ["#synthetic"],
            "source_urls": ["https://example.invalid/source"],
            "platform_copy": {"facebook_title": "Synthetic Reel",
                              "facebook_description": "synthetic description",
                              "youtube_title": "Synthetic Short",
                              "youtube_description": "synthetic description",
                              "instagram_caption": "synthetic caption"},
            "instagram_hashtags": ["#synthetic"],
        }
        (self.root / "data" / "metadata.json").write_text(json.dumps(metadata),
                                                          encoding="utf-8")
        self.metadata_file = self.root / "data" / "metadata.json"


def _cleanup_snapshot_patch(*_args, **_kwargs):
    """No @patch needed; snapshots live in a tmp staging dir per test root."""


class FacebookUploadBindingTests(_Workspace):
    def setUp(self):
        self.workspace()
        stop = _stub_dotenv(); stop.start(); self.addCleanup(stop.stop)
        from app.publish import facebook_reels_upload as fb
        self.fb = fb
        for name in ("META_GRAPH_API_VERSION", "FACEBOOK_PAGE_ID",
                     "FACEBOOK_PAGE_ACCESS_TOKEN"):
            env_patch = patch.dict(os.environ, {name: "synthetic-test-value"}, clear=False)
            env_patch.start(); self.addCleanup(env_patch.stop)
        for attr, value in (("ROOT", self.root),
                            ("VIDEO", self.video),
                            ("METADATA", self.metadata_file),
                            ("LEDGER", self.root / "data" / "meta_uploads.json")):
            attr_patch = patch.object(fb, attr, value)
            attr_patch.start(); self.addCleanup(attr_patch.stop)
        self.decision = _decision(V1, platform="facebook")

    def test_positive_unchanged_artifact_transfers_bound_bytes(self):
        captured = {}

        def fake_post(url, **kwargs):
            params = kwargs.get("params") or {}
            if params.get("upload_phase") == "start":
                return _StubResponse({"video_id": "fbvid123",
                                      "upload_url": "https://graph-upload.invalid/upl"})
            data = kwargs.get("data")
            if hasattr(data, "read"):
                captured["bytes"] = data.read()
                captured["declared_size"] = int(kwargs["headers"]["file_size"])
                return _StubResponse({"success": True})
            return _StubResponse({"success": True})  # finish phase

        with patch.object(self.fb, "authorize_publish", return_value=self.decision), \
                patch.object(self.fb.requests, "post", side_effect=fake_post):
            outcome = self.fb.publish()
        self.assertEqual(outcome["status"], "published")
        self.assertEqual(captured["bytes"], V1)
        self.assertEqual(hashlib.sha256(captured["bytes"]).hexdigest(),
                         self.decision["video_sha256"])
        self.assertEqual(captured["declared_size"], len(V1))
        from app.publish.artifact_snapshot import staging_is_empty
        self.assertTrue(staging_is_empty(self.root))

    def test_negative_mutation_after_authorization_never_reaches_the_network(self):
        network_calls = []
        from app.publish.artifact_snapshot import ArtifactIntegrityError, staging_is_empty

        def authorize_then_mutate(**kwargs):
            self.video.write_bytes(V2)  # replaced after (fake) authorization
            return self.decision

        def spy_post(url, **kwargs):
            network_calls.append(url)
            return _StubResponse({"success": True})

        with patch.object(self.fb, "authorize_publish", side_effect=authorize_then_mutate), \
                patch.object(self.fb.requests, "post", side_effect=spy_post):
            with self.assertRaises(ArtifactIntegrityError):
                self.fb.publish()
        self.assertEqual(network_calls, [])
        self.assertTrue(staging_is_empty(self.root))


class InstagramServeBindingTests(_Workspace):
    def setUp(self):
        self.workspace()
        stop = _stub_dotenv(); stop.start(); self.addCleanup(stop.stop)
        from app.publish import instagram_reels_upload as ig
        self.ig = ig
        for name in ("META_GRAPH_API_VERSION", "INSTAGRAM_USER_ID",
                     "INSTAGRAM_ACCESS_TOKEN"):
            env_patch = patch.dict(os.environ, {name: "synthetic-test-value"}, clear=False)
            env_patch.start(); self.addCleanup(env_patch.stop)
        video_url_patch = patch.dict(os.environ, {"INSTAGRAM_VIDEO_URL": ""}, clear=False)
        video_url_patch.start(); self.addCleanup(video_url_patch.stop)
        for attr, value in (("ROOT", self.root),
                            ("VIDEO", self.video),
                            ("METADATA", self.metadata_file),
                            ("LEDGER", self.root / "data" / "meta_uploads.json")):
            attr_patch = patch.object(ig, attr, value)
            attr_patch.start(); self.addCleanup(attr_patch.stop)
        self.decision = _decision(V1, platform="instagram")
        self.serve = {"path": None}

    def _fake_tunnel(self):
        """Own-tunnel mode with the module contract: returns URL + cleanup."""
        def public_video_url_fake(*, serve_path=None):
            self.serve["path"] = serve_path
            return "http://127.0.0.1:55555/reel/synthetic.mp4", lambda: None
        return public_video_url_fake

    def test_tunnel_helper_requires_descriptor_pinned_snapshot(self):
        from app.publish.artifact_snapshot import ArtifactIntegrityError
        with self.assertRaises(TypeError):
            self.ig.public_video_url()
        with self.assertRaises(ArtifactIntegrityError):
            self.ig.public_video_url(serve_path=self.video)

    def test_positive_meta_model_serves_snapshot_bytes_over_http(self):
        """Meta's fetch is a GET: the test performs that fetch against a local
        server streaming the module-pinned snapshot, byte-exact.  publish()
        creates its own snapshot; the test only proves the pinned bytes."""
        from app.publish.artifact_snapshot import staging_is_empty

        def fake_post(url, **kwargs):
            if url.endswith("/media") and "media_type" in (kwargs.get("data") or {}):
                # Model Meta's synchronous fetch of video_url (a GET like Meta's
                # downloader) against the local tunnel handler:
                parsed = urlparse(kwargs["data"]["video_url"])
                connection = http.client.HTTPConnection(parsed.hostname, parsed.port)
                connection.request("GET", parsed.path)
                response = connection.getresponse()
                captured = response.read()
                connection.close()
                self.assertEqual(len(captured), len(V1))
                self.assertEqual(hashlib.sha256(captured).hexdigest(),
                                 self.decision["video_sha256"])
                return _StubResponse({"id": "igc1"})
            return _StubResponse({"id": "igm1"})

        def fake_get(url, **kwargs):
            return _StubResponse({"status_code": "FINISHED", "status": "ok"})

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                served = self.server.served_path  # the module-pinned snapshot
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(served.stat().st_size))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                with served.open("rb") as stream:
                    shutil.copyfileobj(stream, self.wfile, length=1024 * 256)

            def log_message(self, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        tunnel_url = f"http://127.0.0.1:{server.server_address[1]}"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)

        def public_video_url_fake(*, serve_path=None):
            server.served_path = serve_path
            self.serve["path"] = serve_path
            self.serve["bytes"] = serve_path.read_bytes()
            return f"{tunnel_url}/reel/synthetic.mp4", lambda: None

        with patch.object(self.ig, "authorize_publish", return_value=self.decision), \
                patch.object(self.ig, "public_video_url",
                             side_effect=public_video_url_fake), \
                patch.object(self.ig.requests, "post", side_effect=fake_post), \
                patch.object(self.ig.requests, "get", side_effect=fake_get):
            outcome = self.ig.publish()
        self.assertEqual(outcome["status"], "published")
        # the served snapshot is a distinct digest-bound file, gone afterwards
        self.assertEqual(self.serve["bytes"], V1)
        self.assertFalse(self.serve["path"].exists())
        self.assertEqual(hashlib.sha256(self.serve["bytes"]).hexdigest(),
                         self.decision["video_sha256"])
        self.assertNotEqual(self.serve["path"], self.video)
        self.assertTrue(staging_is_empty(self.root))

    def test_negative_mutation_after_authorization_prevents_the_tunnel(self):
        from app.publish.artifact_snapshot import ArtifactIntegrityError, staging_is_empty
        network_calls = []

        def authorize_then_mutate(**kwargs):
            self.video.write_bytes(V2)
            return self.decision

        def forbid_tunnel(*, serve_path=None):
            raise AssertionError("no serving may start for a mutated artifact")

        def fake_post(url, **kwargs):
            network_calls.append(url)
            return _StubResponse({"id": "never_created"})

        with patch.object(self.ig, "authorize_publish", side_effect=authorize_then_mutate), \
                patch.object(self.ig, "public_video_url", side_effect=forbid_tunnel), \
                patch.object(self.ig.requests, "post", side_effect=fake_post):
            with self.assertRaises(ArtifactIntegrityError):
                self.ig.publish()
        self.assertEqual(network_calls, [])

    def test_external_url_mode_fails_closed_before_network(self):
        from app.publish.artifact_snapshot import ArtifactIntegrityError
        network_calls = []
        with patch.object(self.ig, "authorize_publish", return_value=self.decision), \
                patch.object(self.ig, "public_video_url") as tunnel, \
                patch.object(self.ig.requests, "post",
                             side_effect=lambda *a, **k: network_calls.append(("POST", a[0]))), \
                patch.object(self.ig.requests, "get",
                             side_effect=lambda *a, **k: network_calls.append(("GET", a[0]))), \
                patch.dict(os.environ,
                           {"INSTAGRAM_VIDEO_URL": "https://external.invalid/video.mp4",
                            "INSTAGRAM_ARTIFACT_PINNED": "1"}, clear=False):
            with self.assertRaises(ArtifactIntegrityError):
                self.ig.publish()
        self.assertEqual(network_calls, [])
        tunnel.assert_not_called()

    def test_empty_external_url_preserves_normal_dry_run(self):
        with (
            patch.object(self.ig, "authorize_publish", return_value=self.decision),
            patch.object(self.ig, "public_video_url") as tunnel,
            patch.object(self.ig.requests, "post") as post,
            patch.object(self.ig.requests, "get") as get,
            patch.dict(os.environ, {"INSTAGRAM_VIDEO_URL": ""}, clear=False),
        ):
            outcome = self.ig.publish(dry_run=True)
        self.assertEqual(outcome, {"status": "dry_run"})
        tunnel.assert_not_called()
        post.assert_not_called()
        get.assert_not_called()

    def test_external_url_rejected_before_dry_run_early_return(self):
        from app.publish.artifact_snapshot import ArtifactIntegrityError
        with (
            patch.object(self.ig, "authorize_publish", return_value=self.decision),
            patch.object(self.ig, "public_video_url") as tunnel,
            patch.object(self.ig.requests, "post") as post,
            patch.object(self.ig.requests, "get") as get,
            patch.dict(os.environ,
                       {"INSTAGRAM_VIDEO_URL": "https://external.invalid/dry-run.mp4"},
                       clear=False),
        ):
            with self.assertRaises(ArtifactIntegrityError):
                self.ig.publish(dry_run=True)
        tunnel.assert_not_called()
        post.assert_not_called()
        get.assert_not_called()

    def test_external_url_rejected_before_duplicate_ledger_early_return(self):
        from app.publish.artifact_snapshot import ArtifactIntegrityError
        with (
            patch.object(self.ig, "authorize_publish", return_value=self.decision),
            patch.object(self.ig, "fingerprint", return_value="synthetic-fingerprint"),
            patch.object(self.ig, "ledger_read",
                         return_value={"instagram": {"synthetic-fingerprint":
                                                     {"media_id": "already-published"}}}) as ledger,
            patch.object(self.ig, "public_video_url") as tunnel,
            patch.object(self.ig.requests, "post") as post,
            patch.object(self.ig.requests, "get") as get,
            patch.dict(os.environ,
                       {"INSTAGRAM_VIDEO_URL": "https://external.invalid/duplicate.mp4"},
                       clear=False),
        ):
            with self.assertRaises(ArtifactIntegrityError):
                self.ig.publish()
        ledger.assert_not_called()
        tunnel.assert_not_called()
        post.assert_not_called()
        get.assert_not_called()

    def test_forged_legacy_marker_cannot_authorize_external_url(self):
        from app.publish.artifact_snapshot import ArtifactIntegrityError, staging_is_empty
        network_calls = []

        with patch.object(self.ig, "authorize_publish", return_value=self.decision), \
                patch.object(self.ig, "public_video_url") as tunnel, \
                patch.object(self.ig.requests, "post",
                             side_effect=lambda *a, **k: network_calls.append(("POST", a[0]))), \
                patch.object(self.ig.requests, "get",
                             side_effect=lambda *a, **k: network_calls.append(("GET", a[0]))), \
                patch.dict(os.environ,
                           {"INSTAGRAM_VIDEO_URL": "https://attacker.invalid/forged.mp4",
                            "INSTAGRAM_ARTIFACT_PINNED": "1"}, clear=False):
            with self.assertRaises(ArtifactIntegrityError):
                self.ig.publish()

        self.assertEqual(network_calls, [])
        tunnel.assert_not_called()
        self.assertTrue(staging_is_empty(self.root))

    def test_existing_duplicate_ledger_entry_skips_tunnel_and_network(self):
        network_calls = []
        with (
            patch.object(self.ig, "authorize_publish", return_value=self.decision),
            patch.object(self.ig, "fingerprint", return_value="synthetic-fingerprint"),
            patch.object(self.ig, "ledger_read",
                         return_value={"instagram": {"synthetic-fingerprint":
                                                     {"media_id": "already-published"}}}),
            patch.object(self.ig, "public_video_url") as tunnel,
            patch.object(self.ig.requests, "post",
                         side_effect=lambda *a, **k: network_calls.append(("POST", a[0]))),
            patch.object(self.ig.requests, "get",
                         side_effect=lambda *a, **k: network_calls.append(("GET", a[0]))),
        ):
            outcome = self.ig.publish()
        self.assertEqual(outcome, {"status": "skipped_duplicate"})
        self.assertEqual(network_calls, [])
        tunnel.assert_not_called()

    def test_ledger_write_failure_returns_ambiguous_after_remote_publish(self):
        from app.publish.artifact_snapshot import staging_is_empty
        cleanup_calls = []
        network_calls = []

        def fake_post(url, **kwargs):
            network_calls.append(("POST", url))
            if url.endswith("/media_publish"):
                return _StubResponse({"id": "published-media"})
            return _StubResponse({"id": "created-container"})

        def fake_get(url, **kwargs):
            network_calls.append(("GET", url))
            return _StubResponse({"status_code": "FINISHED", "status": "ok"})

        def fake_tunnel(*, serve_path):
            self.serve["path"] = serve_path
            return "https://tunnel.invalid/reel/synthetic.mp4", lambda: cleanup_calls.append(True)

        with (
            patch.object(self.ig, "authorize_publish", return_value=self.decision),
            patch.object(self.ig, "fingerprint", return_value="synthetic-fingerprint"),
            patch.object(self.ig, "ledger_read", return_value={"instagram": {}}),
            patch.object(self.ig, "ledger_write",
                         side_effect=OSError("synthetic ledger disk failure")),
            patch.object(self.ig, "public_video_url", side_effect=fake_tunnel),
            patch.object(self.ig.requests, "post", side_effect=fake_post),
            patch.object(self.ig.requests, "get", side_effect=fake_get),
            patch.dict(os.environ, {"INSTAGRAM_VIDEO_URL": ""}, clear=False),
        ):
            outcome = self.ig.publish()

        self.assertEqual(outcome, {"status": "ambiguous", "media_id": "published-media"})
        self.assertEqual([method for method, _ in network_calls], ["POST", "GET", "POST"])
        self.assertEqual(cleanup_calls, [True])
        self.assertIsNotNone(self.serve["path"])
        self.assertFalse(self.serve["path"].exists())
        self.assertTrue(staging_is_empty(self.root))

    def test_snapshot_and_tunnel_cleanup_when_meta_transfer_raises(self):
        from app.publish.artifact_snapshot import staging_is_empty
        cleanup_calls = []

        def fake_tunnel(*, serve_path=None):
            self.serve["path"] = serve_path
            return "https://tunnel.invalid/reel/synthetic.mp4", lambda: cleanup_calls.append(True)

        with patch.object(self.ig, "authorize_publish", return_value=self.decision), \
                patch.object(self.ig, "public_video_url", side_effect=fake_tunnel), \
                patch.object(self.ig.requests, "post",
                             side_effect=RuntimeError("synthetic Meta transfer failure")), \
                patch.dict(os.environ, {"INSTAGRAM_VIDEO_URL": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "synthetic Meta transfer failure"):
                self.ig.publish()

        self.assertEqual(cleanup_calls, [True])
        self.assertIsNotNone(self.serve["path"])
        self.assertFalse(self.serve["path"].exists())
        self.assertTrue(staging_is_empty(self.root))


class YoutubeShortUploadBindingTests(_Workspace):
    def setUp(self):
        self.workspace()
        stop = _stub_dotenv(); stop.start(); self.addCleanup(stop.stop)
        from app.publish import youtube_upload as yt
        self.yt = yt
        patch_SCRIPT_DIR = patch.object(yt, "SCRIPT_DIR", self.root)
        patch_SCRIPT_DIR.start(); self.addCleanup(patch_SCRIPT_DIR.stop)
        self.decision = _decision(V1, platform="youtube")
        self.media_paths = []

    def _actions(self):
        media_paths = self.media_paths
        patcher = patch.object(self.yt, "MediaFileUpload", _media_stub(media_paths))
        patcher.start(); self.addCleanup(patcher.stop)
        return patcher

    def test_positive_unchanged_artifact_uploads_the_snapshot(self):
        self._actions()

        class _Chunk:
            def next_chunk(self_inner):
                return (None, {"id": "ytvid123"})

        class _Videos:
            def insert(self_inner, **kwargs):
                return _Chunk()

        with patch.object(self.yt, "authorize_publish", return_value=self.decision), \
                patch.object(self.yt, "get_authenticated_service",
                             return_value=SimpleNamespace(videos=lambda: _Videos())):
            exit_code = self.yt.main([])
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(self.media_paths), 1)
        media_record = self.media_paths[0]
        media_path = Path(media_record["path"])
        self.assertNotEqual(media_path, self.video)
        self.assertEqual(media_record["bytes"], V1)  # exact authorized bytes captured at media construction
        self.assertEqual(hashlib.sha256(media_record["bytes"]).hexdigest(),
                         self.decision["video_sha256"])
        from app.publish.artifact_snapshot import staging_is_empty
        self.assertTrue(staging_is_empty(self.root))

    def test_negative_replacement_between_authorizations_blocks_the_upload(self):
        self._actions()
        from app.publish.artifact_snapshot import staging_is_empty
        seen = []

        def authorize_adversarial(**kwargs):
            seen.append(1)
            if len(seen) == 2:  # the library-level re-authorization
                self.video.write_bytes(V2)
            return _decision(V1, platform="youtube")

        with patch.object(self.yt, "authorize_publish", side_effect=authorize_adversarial), \
                patch.object(self.yt, "get_authenticated_service",
                             return_value=SimpleNamespace(videos=lambda: None)):
            exit_code = self.yt.main([])
        self.assertEqual(exit_code, 2)
        self.assertEqual(self.media_paths, [])  # no MediaFileUpload session started
        self.assertTrue(staging_is_empty(self.root))


class YoutubeLongformUploadBindingTests(_Workspace):
    def setUp(self):
        self.workspace()
        stop = _stub_dotenv(); stop.start(); self.addCleanup(stop.stop)
        from app.publish import youtube_longform_upload as lg
        self.lg = lg
        self.video = self.root / "outputs" / "output_longform.mp4"
        self.video.write_bytes(V1)
        (self.root / "data" / "longform_metadata.json").write_text(json.dumps({
            "title": "Synthetic Longform", "description": "synthetic description",
            "voice_text": "synthetic narration", "tags": ["#synthetic"],
        }), encoding="utf-8")
        env_patch = patch.dict(os.environ, {"PUBLISH_MODE": "publish",
                                            "AUTO_PUBLISH_APPROVED": "true"}, clear=False)
        env_patch.start(); self.addCleanup(env_patch.stop)
        self.decision = _decision(V1, platform="youtube_longform", purpose="longform")
        self.media_paths = []
        media_patch = patch.object(self.lg, "MediaFileUpload", _media_stub(self.media_paths))
        media_patch.start(); self.addCleanup(media_patch.stop)

    def test_positive_unchanged_longform_artifact_uploads_the_snapshot(self):
        class _Chunk:
            def next_chunk(self_inner):
                return (None, {"id": "lfvid1"})

        class _Videos:
            def insert(self_inner, **kwargs):
                return _Chunk()

        with patch.object(self.lg, "ROOT", self.root), \
                patch.object(self.lg, "authorize_publish", return_value=self.decision), \
                patch.object(self.lg, "get_authenticated_service",
                             return_value=SimpleNamespace(videos=lambda: _Videos())), \
                patch.object(self.lg, "send_status", lambda *_a, **_k: None):
            exit_code = self.lg.main([])
        self.assertEqual(exit_code, 0)
        media_record = self.media_paths[0]
        media_path = Path(media_record["path"])
        self.assertNotEqual(media_path, self.video)
        self.assertEqual(media_record["bytes"], V1)
        self.assertEqual(hashlib.sha256(media_record["bytes"]).hexdigest(),
                         self.decision["video_sha256"])
        from app.publish.artifact_snapshot import staging_is_empty
        self.assertTrue(staging_is_empty(self.root))

    def test_negative_longform_replacement_blocks_the_upload(self):
        from app.publish.artifact_snapshot import staging_is_empty

        def authorize_then_mutate(**kwargs):
            self.video.write_bytes(V2)
            return self.decision

        with patch.object(self.lg, "ROOT", self.root), \
                patch.object(self.lg, "authorize_publish", side_effect=authorize_then_mutate), \
                patch.object(self.lg, "get_authenticated_service",
                             return_value=SimpleNamespace(videos=lambda: None)), \
                patch.object(self.lg, "send_status", lambda *_a, **_k: None):
            exit_code = self.lg.main([])
        self.assertEqual(exit_code, 2)
        self.assertEqual(self.media_paths, [])


class OrchestrationTunnelSnapshotTests(_Workspace):
    """The publish-all runner must pin its Instagram tunnel to a bound snapshot."""

    def setUp(self):
        self.workspace()
        stop = _stub_dotenv(); stop.start(); self.addCleanup(stop.stop)
        from app.publish import orchestration as orch
        self.orch = orch
        self.platform_configured_original = orch.platform_configured
        from app.publish import instagram_reels_upload
        self.ig_module = instagram_reels_upload
        env = {"INSTAGRAM_TUNNEL_FALLBACK": "true", "PUBLISH_MODE": "publish",
               "AUTO_PUBLISH_APPROVED": "true"}
        env["INSTAGRAM_VIDEO_URL"] = ""
        env_patch = patch.dict(os.environ, env, clear=False)
        env_patch.start(); self.addCleanup(env_patch.stop)
        os.environ.pop("INSTAGRAM_VIDEO_URL", None)
        (self.root / "data" / "review_approved.json").write_text("{}", encoding="utf-8")
        self.decision = _decision(V1, platform="instagram")
        self.tunnel_calls = []

        def public_video_url_fake(*, serve_path=None):
            self.tunnel_calls.append(serve_path)
            return "http://127.0.0.1:60000/reel/synthetic.mp4", lambda: None

        patches = [
            patch.object(self.orch, "ROOT", self.root),
            patch.object(self.orch, "authorize_publish", return_value=self.decision),
            patch.object(self.orch, "validate_content", return_value=""),
            patch.object(self.orch, "platform_configured", return_value=(True, "")),
            patch.object(self.orch, "send_status", lambda *_a, **_k: None),
            patch.object(self.ig_module, "public_video_url",
                         side_effect=public_video_url_fake),
            patch.object(self.orch, "subprocess",
                         SimpleNamespace(run=lambda cmd, **kw: SimpleNamespace(
                             returncode=0,
                             stdout=json.dumps({"status": "success", "video_id": "x"}),
                             stderr=""))),
        ]
        for patcher in patches:
            patcher.start(); self.addCleanup(patcher.stop)

    def test_preflight_rejects_configured_external_instagram_url(self):
        with patch.dict(os.environ,
                        {"INSTAGRAM_VIDEO_URL": "https://external.invalid/video.mp4"},
                        clear=False):
            configured, reason = self.platform_configured_original("instagram")
        self.assertFalse(configured)
        self.assertIn("unverified external source", reason)

    def test_orchestrator_leaves_snapshot_and_tunnel_ownership_to_instagram_publisher(self):
        exit_code = self.orch.run(scheduled_approved=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.tunnel_calls, [])
        from app.publish.artifact_snapshot import staging_is_empty
        self.assertTrue(staging_is_empty(self.root))

    def test_external_url_cannot_inherit_orchestrator_trust_marker(self):
        """A stale caller marker must not bless a manually configured URL."""
        child_envs = []

        def capture_run(_cmd, **kwargs):
            child_envs.append(dict(kwargs.get("env") or {}))
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"status": "success", "video_id": "x"}),
                stderr="",
            )

        self.orch.subprocess.run = capture_run
        external_url = "https://external.invalid/unverified.mp4"
        with patch.dict(os.environ,
                        {"INSTAGRAM_VIDEO_URL": external_url,
                         "INSTAGRAM_ARTIFACT_PINNED": "1"}, clear=False):
            exit_code = self.orch.run(scheduled_approved=False)

        self.assertEqual(exit_code, 0)
        self.assertEqual(self.tunnel_calls, [])  # no orchestrator-owned tunnel was created
        self.assertTrue(child_envs)
        for child_env in child_envs:
            self.assertEqual(child_env.get("INSTAGRAM_VIDEO_URL"), external_url)
            self.assertNotIn("INSTAGRAM_ARTIFACT_PINNED", child_env)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
