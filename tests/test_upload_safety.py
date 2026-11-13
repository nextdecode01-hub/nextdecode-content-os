"""Upload-path safety tests - mocked only.

Nothing here contacts YouTube or any social platform.  These tests pin request
construction, completion handling, failure propagation, duplicate prevention and
the dry-run no-op, so the upload path can be exercised without a public upload.
"""
from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.publish import social_orchestrator as publish_social
from app.publish import authorization as publish_authorization
from app.publish import youtube_upload as yt
from governance_fixtures import build_sandbox


class _AuthorizedSandbox:
    """Point the shared authorization boundary at a throwaway approved package."""

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.paths = build_sandbox(self.root)
        self._patcher = patch.object(publish_authorization, "ROOT", self.root)
        self._patcher.__enter__()
        return self

    def __exit__(self, *exc_info):
        self._patcher.__exit__(*exc_info)
        self._tmp.cleanup()
        return False


class MockedYouTubeUploadTests(unittest.TestCase):
    def test_request_is_built_and_waits_for_completion(self):
        service = MagicMock()
        request = service.videos.return_value.insert.return_value
        progress = MagicMock()
        progress.progress.return_value = 0.5
        request.next_chunk.side_effect = [(progress, None), (None, {"id": "vid123"})]

        with _AuthorizedSandbox() as box, \
                patch.object(yt, "get_authenticated_service", return_value=service), \
                patch.object(yt, "MediaFileUpload", return_value="media-handle"):
            response = yt.upload_video(str(box.paths["video"]), "Title", "Desc", ["ai"],
                                       data_root=box.root)

        self.assertEqual(response["id"], "vid123")
        insert = service.videos.return_value.insert
        body = insert.call_args.kwargs["body"]
        self.assertEqual(body["snippet"]["title"], "Title")
        self.assertEqual(body["snippet"]["categoryId"], "28")
        self.assertEqual(body["status"]["selfDeclaredMadeForKids"], False)
        self.assertEqual(insert.call_args.kwargs["part"], "snippet,status")
        self.assertEqual(insert.call_args.kwargs["media_body"], "media-handle")
        self.assertEqual(request.next_chunk.call_count, 2)

    def test_upload_request_uses_private_privacy(self):
        service = MagicMock()
        request = service.videos.return_value.insert.return_value
        request.next_chunk.side_effect = [(None, {"id": "vid-private"})]

        with _AuthorizedSandbox() as box, \
                patch.object(yt, "get_authenticated_service", return_value=service), \
                patch.object(yt, "MediaFileUpload", return_value="media-handle") as media:
            yt.upload_video(str(box.paths["video"]), "Title", "Desc", ["ai"],
                            data_root=box.root)

        body = service.videos.return_value.insert.call_args.kwargs["body"]
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertEqual(body["status"]["selfDeclaredMadeForKids"], False)
        self.assertTrue(media.call_args.kwargs["resumable"])
        self.assertEqual(media.call_args.kwargs["chunksize"], 8 * 1024 * 1024)

    def test_direct_library_upload_refuses_without_approval(self):
        service = MagicMock()
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(publish_authorization, "ROOT", Path(tmp)), \
                patch.object(yt, "get_authenticated_service", return_value=service), \
                patch.object(yt, "MediaFileUpload"):
            with self.assertRaises(publish_authorization.PublishNotAuthorized):
                yt.upload_video("clip.mp4", "Title", "Desc", ["ai"])
        service.videos.return_value.insert.assert_not_called()

    def test_upload_failure_propagates_without_success(self):
        service = MagicMock()
        request = service.videos.return_value.insert.return_value
        request.next_chunk.side_effect = RuntimeError("quota exceeded")

        with _AuthorizedSandbox() as box, \
                patch.object(yt, "get_authenticated_service", return_value=service), \
                patch.object(yt, "MediaFileUpload"):
            with self.assertRaises(RuntimeError):
                yt.upload_video(str(box.paths["video"]), "T", "D", [], data_root=box.root)

    def test_missing_token_refuses_before_any_network_call(self):
        missing = Path(tempfile.gettempdir()) / "no-such-youtube-token.json"
        with patch.object(yt, "TOKEN_FILE", missing), patch.object(yt, "build") as build:
            with self.assertRaises(FileNotFoundError):
                yt.get_authenticated_service()
        build.assert_not_called()

    def test_fingerprint_is_stable_and_content_sensitive(self):
        first = yt.content_fingerprint({"title": "A", "voice_text": "x"})
        self.assertEqual(first, yt.content_fingerprint({"voice_text": "x", "title": "A"}))
        self.assertNotEqual(first, yt.content_fingerprint({"title": "B", "voice_text": "x"}))

    def test_invalid_ledger_refuses_the_duplicate_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            path.write_text(json.dumps({"fingerprints": []}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                yt.load_upload_ledger(path)

    def test_known_fingerprint_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            fingerprint = yt.content_fingerprint({"title": "T", "voice_text": "v"})
            path.write_text(json.dumps({"fingerprints": {fingerprint: {"video_url": "u"}}}),
                            encoding="utf-8")
            ledger = yt.load_upload_ledger(path)
        self.assertIn(fingerprint, ledger["fingerprints"])


class SocialUploadTests(unittest.TestCase):
    def _platform(self):
        return publish_social.PLATFORMS["telegram"]

    def test_dry_run_is_blocked_by_destination_policy_before_adapter(self):
        adapter = MagicMock()
        with _AuthorizedSandbox() as box, \
                patch.object(publish_social, "_record") as record, \
                patch.dict(self._platform(), {"configured": lambda: True, "publish": adapter}):
            result = publish_social.publish("telegram", str(box.paths["video"]), "caption",
                                            dry_run=True)
        self.assertFalse(result["ok"])
        self.assertIn("blocked_public_policy", str(result["error"]))
        adapter.assert_not_called()
        record.assert_not_called()

    def test_dry_run_still_validates_governance(self):
        adapter = MagicMock()
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(publish_authorization, "ROOT", Path(tmp)), \
                patch.dict(self._platform(), {"configured": lambda: True, "publish": adapter}):
            result = publish_social.publish("telegram", "clip.mp4", "caption", dry_run=True)
        self.assertFalse(result["ok"])
        self.assertIn("blocked", str(result["error"]))
        adapter.assert_not_called()

    def test_adapter_is_not_called_when_destination_policy_blocks_telegram(self):
        adapter = MagicMock(return_value={"ok": True, "post_id": "p1", "url": None})
        with _AuthorizedSandbox() as box, \
                patch.object(publish_social, "_already", return_value=False), \
                patch.object(publish_social, "_record") as record, \
                patch.dict(self._platform(), {"configured": lambda: True, "publish": adapter}):
            result = publish_social.publish("telegram", str(box.paths["video"]), "caption",
                                            title="T", dry_run=False)
        self.assertFalse(result["ok"])
        self.assertIn("blocked_public_policy", str(result["error"]))
        adapter.assert_not_called()
        record.assert_not_called()

    def test_policy_block_precedes_adapter_and_ledger_write(self):
        adapter = MagicMock(return_value={"ok": True, "post_id": "p1", "url": None})
        with _AuthorizedSandbox() as box, \
                patch.object(publish_social, "_already", return_value=False), \
                patch.object(publish_social, "_record", side_effect=OSError("disk full")) as record, \
                patch.dict(self._platform(), {"configured": lambda: True, "publish": adapter}):
            result = publish_social.publish("telegram", str(box.paths["video"]), "caption",
                                            dry_run=False)
        self.assertFalse(result["ok"])
        self.assertIn("blocked_public_policy", str(result["error"]))
        adapter.assert_not_called()
        record.assert_not_called()

    def test_missing_approval_blocks_every_platform(self):
        adapter = MagicMock()
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(publish_authorization, "ROOT", Path(tmp)), \
                patch.dict(self._platform(), {"configured": lambda: True, "publish": adapter}):
            result = publish_social.publish_all_social(
                "clip.mp4", "caption", platforms=["telegram"])
        self.assertEqual(result["published"], 0)
        self.assertIn("blocked", str(result["results"][0]["error"]))
        adapter.assert_not_called()

    def test_stale_approval_hash_blocks_before_any_adapter(self):
        adapter = MagicMock()
        with _AuthorizedSandbox() as box:
            box.paths["video"].write_bytes(b"rendered-after-approval")
            with patch.dict(self._platform(), {"configured": lambda: True, "publish": adapter}):
                result = publish_social.publish_all_social(
                    str(box.paths["video"]), "caption", platforms=["telegram"])
        self.assertEqual(result["published"], 0)
        self.assertIn("does not match", str(result["results"][0]["error"]))
        adapter.assert_not_called()

    def test_cli_execute_flag_cannot_disable_authorization(self):
        # The require_approval bypass no longer exists on the publishing API.
        signature = inspect.signature(publish_social.publish_all_social)
        self.assertNotIn("require_approval", signature.parameters)
        with self.assertRaises(TypeError):
            publish_social.publish_all_social("clip.mp4", "caption", require_approval=False)

    def test_dry_run_does_not_resolve_a_public_url(self):
        with _AuthorizedSandbox() as box, \
                patch.object(publish_social, "resolve_public_url") as resolver, \
                patch.dict(self._platform(), {"configured": lambda: True,
                                              "publish": MagicMock()}):
            publish_social.publish_all_social(str(box.paths["video"]), "caption",
                                              platforms=["telegram"], dry_run=True)
        resolver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
