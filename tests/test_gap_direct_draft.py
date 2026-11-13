"""Gap 1: Direct pipeline draft-only artifact rejection.

Validates that every downstream publishing/orchestration path rejects
artifacts produced by the direct pipeline entry point when governance
marks them as non-publishable.

Covers: publish_all, youtube_upload CLI, facebook_reels_upload,
instagram_reels_upload, publish_social.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from app.publish import orchestration as publish_all
from app.publish import social_orchestrator as publish_social
from app.publish import facebook_reels_upload as fb
from app.publish import instagram_reels_upload as ig
from app.publish import youtube_upload as yt
from app.publish.authorization import PublishNotAuthorized
from test_publish_governance import _Sandbox

META_ENV = {
    "FACEBOOK_PAGE_ID": "page-123",
    "FACEBOOK_ACCESS_TOKEN": "token-xyz",
    "INSTAGRAM_ACCOUNT_ID": "ig-123",
    "INSTAGRAM_ACCESS_TOKEN": "token-xyz",
}


class Gap1DraftRejectionTests(unittest.TestCase):
    """Every publisher path must reject draft-only governance artifacts."""

    def test_direct_pipeline_draft_metadata_rejected_by_all_publishers(self):
        with _Sandbox(mutate_metadata=lambda m: m.update({
            "governance": {
                "entry": "direct",
                "publishable": False,
                "reason": "the direct pipeline entry point does not run the approved orchestration",
            }
        })) as box:
            # 1. publish_all
            with patch.object(publish_all, "ROOT", box.root), \
                 patch.object(publish_all, "validate_content", return_value=""), \
                 patch.object(publish_all, "platform_configured", return_value=(True, "")), \
                 patch.object(publish_all, "send_status", return_value=True), \
                 patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}), \
                 patch.object(publish_all.subprocess, "run") as runner:
                code_all = publish_all.run(scheduled_approved=False)
            self.assertEqual(code_all, 2)
            runner.assert_not_called()

            # 2. youtube_upload CLI
            service = MagicMock()
            with patch.object(yt, "SCRIPT_DIR", box.root), \
                 patch.object(yt, "get_authenticated_service", return_value=service):
                code_yt = yt.main([])
            self.assertEqual(code_yt, 2)
            service.videos.return_value.insert.assert_not_called()

            # 3. facebook_reels_upload.publish
            with patch.object(fb, "ROOT", box.root), \
                 patch.object(fb, "METADATA", box.paths["metadata"]), \
                 patch.object(fb, "VIDEO", box.paths["video"]), \
                 patch.dict(os.environ, META_ENV):
                with self.assertRaises(PublishNotAuthorized) as caught_fb:
                    fb.publish(dry_run=True)
            self.assertEqual(caught_fb.exception.code, "blocked_governance")

            # 4. instagram_reels_upload.publish
            with patch.object(ig, "ROOT", box.root), \
                 patch.object(ig, "METADATA", box.paths["metadata"]), \
                 patch.object(ig, "VIDEO", box.paths["video"]), \
                 patch.dict(os.environ, META_ENV):
                with self.assertRaises(PublishNotAuthorized) as caught_ig:
                    ig.publish(dry_run=True)
            self.assertEqual(caught_ig.exception.code, "blocked_governance")

            # 5. publish_social.publish
            with patch.object(publish_social, "ROOT", box.root):
                res = publish_social.publish("telegram", str(box.paths["video"]), "caption", dry_run=True)
            self.assertFalse(res["ok"])
            self.assertIn("blocked_governance", res["error"])


if __name__ == "__main__":
    unittest.main()
