"""Gap 4: Long-form destination replay and artifact modification after approval.

Validates that:
- Replay after successful upload is skipped (duplicate fingerprint).
- Tampered metadata after approval blocks re-authorization.
- Tampered video after approval blocks re-authorization.
- Destination drift (tampered authorization) blocks upload.
"""
from __future__ import annotations

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from app.publish import youtube_longform_upload as longform
from app.publish.authorization import PublishNotAuthorized, authorize_publish
from test_publish_governance import _Sandbox


class Gap4LongformReplayAndTamperTests(unittest.TestCase):
    """Long-form replay and post-approval tampering must be blocked."""

    def test_longform_replay_after_successful_upload_is_skipped(self):
        with _Sandbox(purpose="longform") as box:
            service = MagicMock()
            service.videos.return_value.insert.return_value.next_chunk.return_value = (
                None, {"id": "vid_longform_123"},
            )
            with patch.object(longform, "ROOT", box.root), \
                 patch.object(longform, "get_authenticated_service", return_value=service), \
                 patch.object(longform, "MediaFileUpload", return_value="media"), \
                 patch.object(longform, "send_status", return_value=True), \
                 patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                # First upload succeeds
                code1 = longform.main([])
                self.assertEqual(code1, 0)
                self.assertEqual(service.videos.return_value.insert.call_count, 1)

                # Replay must detect duplicate fingerprint and skip upload
                service.videos.return_value.insert.reset_mock()
                code2 = longform.main([])
                self.assertEqual(code2, 0)
                service.videos.return_value.insert.assert_not_called()

    def test_longform_metadata_tampered_after_approval_fails_authorization(self):
        with _Sandbox(purpose="longform") as box:
            service = MagicMock()
            metadata = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            metadata["title"] = "Tampered Longform Title"
            box.paths["metadata"].write_text(json.dumps(metadata), encoding="utf-8")

            with patch.object(longform, "ROOT", box.root), \
                 patch.object(longform, "get_authenticated_service", return_value=service), \
                 patch.object(longform, "send_status", return_value=True), \
                 patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                code = longform.main([])
            self.assertEqual(code, 2)
            service.videos.return_value.insert.assert_not_called()

    def test_longform_video_tampered_after_approval_fails_authorization(self):
        with _Sandbox(purpose="longform") as box:
            service = MagicMock()
            box.paths["video"].write_bytes(b"tampered longform video bytes")

            with patch.object(longform, "ROOT", box.root), \
                 patch.object(longform, "get_authenticated_service", return_value=service), \
                 patch.object(longform, "send_status", return_value=True), \
                 patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                code = longform.main([])
            self.assertEqual(code, 2)
            service.videos.return_value.insert.assert_not_called()

    def test_longform_destination_tampered_between_authorizations_fails(self):
        with _Sandbox(purpose="longform") as box:
            service = MagicMock()
            with patch.object(longform, "ROOT", box.root), \
                 patch.object(longform, "get_authenticated_service", return_value=service), \
                 patch.object(longform, "authorize_publish",
                              side_effect=PublishNotAuthorized("tampered", code="blocked_approval")), \
                 patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                code = longform.main([])
            self.assertEqual(code, 2)
            service.videos.return_value.insert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
