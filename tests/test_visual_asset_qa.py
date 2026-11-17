from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.visuals import asset_qa


class VisualAssetQATests(unittest.TestCase):
    def test_video_metadata_reports_duration_and_expected_usable_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clip.mp4"
            path.write_bytes(b"clip")
            probe = {
                "format": {"duration": "8.0"},
                "streams": [{
                    "codec_type": "video", "width": 1080, "height": 1920,
                    "avg_frame_rate": "30/1", "codec_name": "h264",
                }],
            }
            with patch.object(asset_qa, "_probe", return_value=probe), patch.object(
                asset_qa, "_dhash", return_value=0x1234,
            ):
                result = asset_qa.inspect_asset({
                    "scene_id": "s03", "provider": "pixabay", "asset_path": str(path),
                    "duration": 3.6, "visual_purpose": "show server racks",
                }, 3)

            self.assertEqual(result["duration_seconds"], 8.0)
            self.assertEqual(result["usable_duration_seconds"], 3.6)
            self.assertEqual(result["duration_coverage"], 1.0)
            self.assertEqual(result["width"], 1080)
            self.assertEqual(result["fps"], 30.0)
            self.assertEqual(result["visual_intent"], "show server racks")

    def test_report_flags_adjacent_exact_and_composition_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clip = root / "same.mp4"
            clip.write_bytes(b"identical asset bytes")
            probe = {"format": {"duration": "5"}, "streams": [{
                "codec_type": "video", "width": 1080, "height": 1920,
                "avg_frame_rate": "30/1", "codec_name": "h264",
            }]}
            with patch.object(asset_qa, "_probe", return_value=probe), patch.object(
                asset_qa, "_dhash", return_value=0xFFFF,
            ), patch.object(asset_qa, "_thumbnail", return_value=False):
                report = asset_qa.build_asset_qa([
                    {"scene_id": "s01", "provider": "pixabay", "asset_path": str(clip), "duration": 3.6},
                    {"scene_id": "s02", "provider": "pixabay", "asset_path": str(clip), "duration": 3.6},
                ], root / "qa")

            self.assertEqual(report["adjacent_exact_duplicates"], [["s01", "s02"]])
            self.assertEqual(report["adjacent_composition_similarities"][0]["hamming_distance"], 0)
            self.assertTrue(Path(report["report_path"]).is_file())
            saved = json.loads(Path(report["report_path"]).read_text(encoding="utf-8"))
            self.assertEqual(saved["asset_count"], 2)

    def test_missing_assets_are_reported_not_silently_omitted(self):
        result = asset_qa.inspect_asset({
            "scene_id": "s09", "provider": "pexels", "asset_path": "/not/a/real/file.mp4",
        }, 9)
        self.assertFalse(result["exists"])
        self.assertEqual(result["probe_error"], "asset file missing")


if __name__ == "__main__":
    unittest.main()
