import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.security.approval_integrity import approved_today, sha256_file, upload_window_open
from app.publish import orchestration as publish_all
from app.publish import scheduler as scheduled_publish
from app.security.approval_integrity import IST


class ApprovalIntegrityTests(unittest.TestCase):
    def test_root_compatibility_shim_preserves_canonical_module_identity(self):
        import app.security.approval_integrity as canonical
        from app.security import approval_integrity as legacy

        self.assertIs(legacy, canonical)

    def test_file_hash_changes_when_file_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "content.mp4"
            target.write_bytes(b"first")
            first = sha256_file(target)
            target.write_bytes(b"second")
            self.assertNotEqual(first, sha256_file(target))

    def test_approval_is_valid_for_same_ist_day_across_utc_boundary(self):
        approved_at = datetime(2026, 2, 10, 8, 0, tzinfo=timezone.utc).isoformat()
        current = datetime(2026, 2, 10, 15, 0, tzinfo=timezone.utc)
        self.assertTrue(approved_today(approved_at, current))

    def test_approval_expires_at_ist_midnight(self):
        approved_at = datetime(2026, 2, 10, 17, 0, tzinfo=timezone.utc).isoformat()
        current = datetime(2026, 2, 10, 18, 30, tzinfo=timezone.utc)
        self.assertFalse(approved_today(approved_at, current))

    def test_invalid_or_timezone_naive_approval_is_rejected(self):
        self.assertFalse(approved_today("not-a-time"))
        self.assertFalse(approved_today("2026-02-10T12:00:00"))

    def test_scheduled_upload_window_is_20_ist_only(self):
        self.assertFalse(upload_window_open(datetime(2026, 2, 10, 19, 59, tzinfo=timezone.utc)))
        self.assertTrue(upload_window_open(datetime(2026, 2, 10, 14, 30, tzinfo=timezone.utc)))
        self.assertFalse(upload_window_open(datetime(2026, 2, 10, 15, 30, tzinfo=timezone.utc)))

    def test_short_approval_is_invalidated_when_video_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            output_dir = root / "outputs"
            data_dir.mkdir()
            output_dir.mkdir()
            metadata_file = data_dir / "metadata.json"
            video_file = output_dir / "output_short.mp4"
            footage = root / "footage.mp4"
            footage.write_bytes(b"licensed-footage")
            visuals = {"mode": "owner_recorded", "asset_count": 1, "asset_path": str(footage)}
            metadata = {
                "title": "A verified demo",
                "hook": "This demo reveals a useful detail.",
                "content_pillar": "How It Works",
                "visuals": visuals,
            }
            metadata_file.write_text(json.dumps(metadata), encoding="utf-8")
            video_file.write_bytes(b"rendered-video")
            approved_at = datetime.now(IST).isoformat()
            hashes = {
                "metadata_sha256": sha256_file(metadata_file),
                "video_sha256": sha256_file(video_file),
            }
            package_path = root / "package.json"
            package_path.write_text(json.dumps({
                "status": "pending_human_review",
                "title": metadata["title"],
                "hook": metadata["hook"],
                "content_pillar": metadata["content_pillar"],
                "visuals": visuals,
                **hashes,
            }), encoding="utf-8")
            decision_path = data_dir / "review_approvals" / "decision.json"
            decision_path.parent.mkdir(parents=True, exist_ok=True)
            decision = {
                "status": "approved",
                "approved_at": approved_at,
                "package": str(package_path),
                "review_package_sha256": sha256_file(package_path),
                "reviewer": "test-reviewer",
                "rationale": "verified test fixture",
                "purpose": "short",
                "platform": "youtube",
                "destination": "private",
                "checklist": {name: True for name in (
                    "two_sources_checked", "primary_source_checked",
                    "real_demo_or_original_visual", "limitation_stated",
                    "captions_audio_and_9x16_checked", "platform_copy_checked",
                    "publish_approved")},
                **hashes,
            }
            decision_path.write_text(json.dumps(decision), encoding="utf-8")
            (data_dir / "review_approved.json").write_text(json.dumps({
                "status": "approved",
                "package": str(package_path),
                "decision_record": str(decision_path),
                "decision_record_sha256": sha256_file(decision_path),
            }), encoding="utf-8")

            with patch.object(publish_all, "ROOT", root):
                self.assertEqual(publish_all.approval_matches_current_content(), "")
                video_file.write_bytes(b"changed-render")
                self.assertIn("does not match", publish_all.approval_matches_current_content())

    def test_missed_upload_window_never_invokes_a_publisher(self):
        with (
            patch.object(scheduled_publish, "datetime") as clock,
            patch.object(scheduled_publish.subprocess, "run") as run,
            patch.object(scheduled_publish, "send_status"),
        ):
            clock.now.return_value = datetime(2026, 2, 10, 19, 59, tzinfo=IST)
            self.assertEqual(scheduled_publish.main(), 2)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
