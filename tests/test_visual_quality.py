import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import approve_longform
import approve_review
from approval_integrity import sha256_file
from visual_quality import has_publishable_visuals


class VisualQualityTests(unittest.TestCase):
    def test_procedural_visuals_are_not_publishable(self):
        self.assertFalse(has_publishable_visuals({"mode": "procedural_fallback", "asset_count": 0}))
        self.assertFalse(has_publishable_visuals({"mode": "owner_recorded", "asset_count": 0}))
        self.assertFalse(has_publishable_visuals(None))

    def test_owner_or_licensed_assets_are_publishable_candidates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset = Path(temp_dir) / "footage.mp4"
            asset.write_bytes(b"video")
            self.assertTrue(has_publishable_visuals({
                "mode": "owner_recorded",
                "asset_count": 1,
                "asset_path": str(asset),
            }))
            self.assertTrue(has_publishable_visuals({
                "mode": "pexels_stock",
                "asset_count": 2,
                "asset_path": str(asset),
            }))
            self.assertFalse(has_publishable_visuals({
                "mode": "owner_recorded",
                "asset_count": 1,
                "asset_path": str(asset.with_name("missing.mp4")),
            }))

    def test_stock_assets_require_query_match_coverage_and_unique_images(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first.jpg"
            second = root / "second.jpg"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            assets = [
                {"provider": "wikimedia", "title": "File:Perplexity Page one.png", "license": "CC BY 4.0", "path": str(first), "query_matched": True},
                {"provider": "wikimedia", "title": "File:Perplexity Page two.png", "license": "CC BY 4.0", "path": str(second), "query_matched": True},
            ]
            visuals = {"mode": "multi_shot_stock", "asset_count": 2, "shot_count": 2, "procedural_shot_count": 0, "assets": assets}
            self.assertTrue(has_publishable_visuals(visuals))

            unmatched = {"mode": "multi_shot_stock", "asset_count": 1, "shot_count": 1, "assets": [dict(assets[0], query_matched=False)]}
            self.assertFalse(has_publishable_visuals(unmatched))

            repeated = dict(visuals, assets=[assets[0], dict(assets[1], title=assets[0]["title"])])
            self.assertFalse(has_publishable_visuals(repeated))

            missing_shot = dict(visuals, shot_count=3, asset_count=2, procedural_shot_count=1)
            self.assertFalse(has_publishable_visuals(missing_shot))

    def test_longform_approval_blocks_procedural_visuals(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            visuals = {"mode": "procedural_fallback", "asset_count": 0}
            metadata = root / "longform_metadata.json"
            video = root / "output_longform.mp4"
            metadata.write_text(json.dumps({"visuals": visuals}), encoding="utf-8")
            video.write_bytes(b"video")
            (root / "longform_review_pending.json").write_text(
                json.dumps({
                    "checklist": {name: True for name in approve_longform.REQUIRED},
                    "visuals": visuals,
                    "metadata_sha256": sha256_file(metadata),
                    "video_sha256": sha256_file(video),
                }),
                encoding="utf-8",
            )
            with patch.object(approve_longform, "ROOT", root), patch("sys.argv", ["approve_longform.py"]):
                with self.assertRaisesRegex(SystemExit, "draft with procedural visuals"):
                    approve_longform.main()

    def test_short_approval_blocks_procedural_visuals_even_if_checklist_is_ticked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_path = root / "review_queue" / "package.json"
            package_path.parent.mkdir()
            visuals = {"mode": "procedural_fallback", "asset_count": 0}
            metadata_path = root / "metadata.json"
            video_path = root / "output_short.mp4"
            metadata_path.write_text(json.dumps({"visuals": visuals}), encoding="utf-8")
            video_path.write_bytes(b"video")
            checks = {
                "two_sources_checked": True,
                "primary_source_checked": True,
                "real_demo_or_original_visual": True,
                "limitation_stated": True,
                "captions_audio_and_9x16_checked": True,
                "platform_copy_checked": True,
            }
            package_path.write_text(json.dumps({
                "visuals": visuals,
                "checklist": checks,
                "metadata_sha256": sha256_file(metadata_path),
                "video_sha256": sha256_file(video_path),
            }), encoding="utf-8")
            (root / "review_pending.json").write_text(json.dumps({"package": str(package_path)}), encoding="utf-8")
            with patch.object(approve_review, "ROOT", root), patch("sys.argv", ["approve_review.py"]):
                with self.assertRaisesRegex(SystemExit, "draft with procedural visuals"):
                    approve_review.main()

    def test_longform_approval_accepts_reviewed_owner_footage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset = root / "footage.mp4"
            asset.write_bytes(b"video")
            visuals = {"mode": "owner_recorded", "asset_count": 1, "asset_path": str(asset)}
            metadata = root / "longform_metadata.json"
            video = root / "output_longform.mp4"
            metadata.write_text(json.dumps({"visuals": visuals, "title": "Owner footage video"}), encoding="utf-8")
            video.write_bytes(b"rendered-video")
            (root / "longform_review_pending.json").write_text(
                json.dumps({
                    "title": "Owner footage video",
                    "visuals": visuals,
                    "checklist": {name: True for name in approve_longform.REQUIRED},
                    "metadata_sha256": sha256_file(metadata),
                    "video_sha256": sha256_file(video),
                }),
                encoding="utf-8",
            )
            with (
                patch.object(approve_longform, "ROOT", root),
                patch("sys.argv", ["approve_longform.py"]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = approve_longform.main()

            self.assertIsNone(result)
            approved = json.loads((root / "longform_review_approved.json").read_text(encoding="utf-8"))
            self.assertEqual(approved["status"], "approved")


if __name__ == "__main__":
    unittest.main()
