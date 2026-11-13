"""Phase 10.4 Task 2 — promotion-window tests for the Run Tracker.

Pins the promotion consistency decisions agreed with the owner:

* the manifest stays ``in_progress`` during promotion; ``promotion.status``
  (additive field) tracks the promotion window, and ``mark_ok()`` happens only
  after the journal reports ``completed``;
* a mixed/stale slot pair can exist mid-promotion but is always detectable via
  the journal + manifest → slot cross-check, and never reaches ``ok``;
* promotion validation refuses unrecorded or hash-changed artifacts before any
  slot is touched;
* no automatic recovery: a failed run never gets silently resurrected.

Everything is hermetic: temporary run roots and index paths only.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.tracking import run_tracker as rt


VIDEO_BYTES = b"promoted-video-bytes"
METADATA_BYTES = b"{\"title\": \"run artifact\"}\n"


def _new_tracker(root: Path) -> rt.RunTracker:
    return rt.start_run(
        "demo topic",
        runs_root=root / "outputs" / "runs",
        index_path=root / "data" / "runs" / "index.jsonl",
    )


class PromotionWindowTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _seed_artifacts(self, tracker: rt.RunTracker):
        video = tracker.run_dir / "output_short.mp4"
        metadata = tracker.run_dir / "metadata.json"
        video.write_bytes(VIDEO_BYTES)
        metadata.write_bytes(METADATA_BYTES)
        tracker.record_artifact("video", video, stage="render")
        tracker.record_artifact("metadata", metadata, stage="strong_pipeline")
        return video, metadata

    def test_full_promotion_marks_ok_only_after_journal_completed(self):
        tracker = _new_tracker(self.root)
        video, metadata = self._seed_artifacts(tracker)
        slots = tracker.promote_slots({
            "video": self.root / "outputs" / "output_short.mp4",
            "metadata": self.root / "data" / "metadata.json",
        })
        # journal says completed BEFORE mark_ok is allowed to run
        journal_path = tracker.manifest["promotion"]["journal_path"]
        journal = json.loads(Path(journal_path).read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "completed")
        self.assertEqual(tracker.manifest.get("status"), "in_progress")
        tracker.mark_ok()
        self.assertEqual(tracker.manifest["status"], "ok")
        # promoted slots are byte-identical to the run artifacts
        self.assertEqual((self.root / "outputs" / "output_short.mp4").read_bytes(), VIDEO_BYTES)
        self.assertEqual((self.root / "data" / "metadata.json").read_bytes(), METADATA_BYTES)
        self.assertEqual(list(slots), ["video", "metadata"])

    def test_promotion_refuses_unrecorded_artifact_before_touching_slots(self):
        tracker = _new_tracker(self.root)
        self._seed_artifacts(tracker)
        with self.assertRaisesRegex(RuntimeError, "not recorded"):
            tracker.promote_slots({"ghost": self.root / "data" / "metadata.json"})
        self.assertIsNone(tracker.manifest.get("promotion"))
        self.assertFalse((self.root / "data" / "runs" / "promotions").exists())

    def test_promotion_refuses_hash_changed_artifact_before_touching_slots(self):
        tracker = _new_tracker(self.root)
        video, _ = self._seed_artifacts(tracker)
        video.write_bytes(b"tampered-after-recording")
        with self.assertRaisesRegex(RuntimeError, "hash changed"):
            tracker.promote_slots({"video": self.root / "outputs" / "output_short.mp4"})
        self.assertFalse((self.root / "outputs" / "output_short.mp4").exists())
        self.assertIsNone(tracker.manifest.get("promotion"))

    def test_partial_promotion_stays_detectable_never_ok(self):
        tracker = _new_tracker(self.root)
        self._seed_artifacts(tracker)
        payloads = [
            (self.root / "data" / "metadata.json", METADATA_BYTES),
            (self.root / "outputs" / "output_short.mp4", VIDEO_BYTES),
        ]
        placed: set[int] = set()

        def flaky_copyfile(src, dst, *args, **kwargs):
            if len(placed) >= 1:
                raise OSError("simulated video promotion failure")
            placed.add(1)
            return real_copyfile(src, dst, *args, **kwargs)

        real_copyfile = shutil.copyfile
        with patch.object(rt.shutil, "copyfile", flaky_copyfile):
            with self.assertRaisesRegex(OSError, "simulated"):
                tracker.promote_slots({
                    "metadata": payloads[0][0],
                    "video": payloads[1][0],
                })
        # metadata slot replaced, video slot never written: a mixed pair.
        self.assertEqual(payloads[0][0].read_bytes(), METADATA_BYTES)
        self.assertFalse(payloads[1][0].exists())
        # not terminal, not ok: manifest still in_progress, journal window open
        self.assertEqual(tracker.manifest.get("status"), "in_progress")
        self.assertEqual(tracker.manifest["promotion"]["status"], "promoting")
        journal = json.loads(Path(tracker.manifest["promotion"]["journal_path"]).read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "promoting")
        temp_junk = [p.name for p in payloads[1][0].parent.iterdir() if p.name.startswith(".")]
        self.assertEqual(temp_junk, [])
        # the operator's only fallback is an explicit terminal failure
        tracker.mark_failed(stage="promotion", exc=OSError("simulated"), error_category="io")
        self.assertEqual(tracker.manifest["status"], "failed")
        journal = json.loads(Path(tracker.manifest["promotion"]["journal_path"]).read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "failed")
        self.assertEqual(tracker.manifest["promotion"]["status"], "failed")

    def test_mark_failed_closes_open_promotion_window(self):
        tracker = _new_tracker(self.root)
        self._seed_artifacts(tracker)
        tracker.begin_promotion({"video": "abc123"})
        tracker.mark_failed(stage="promotion", exc=RuntimeError("disk went away"))
        journal = json.loads(Path(tracker.manifest["promotion"]["journal_path"]).read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "failed")
        self.assertEqual(tracker.manifest["promotion"]["status"], "failed")

    def test_double_promotion_window_is_refused(self):
        tracker = _new_tracker(self.root)
        self._seed_artifacts(tracker)
        tracker.begin_promotion({"video": "abc123"})
        with self.assertRaisesRegex(RuntimeError, "already has an open promotion window"):
            tracker.begin_promotion({"video": "abc123"})

    def test_no_promotion_until_artifacts_recorded(self):
        tracker = _new_tracker(self.root)
        (tracker.run_dir / "output_short.mp4").write_bytes(VIDEO_BYTES)
        with self.assertRaisesRegex(RuntimeError, "not recorded"):
            tracker.promote_slots({"video": self.root / "outputs" / "output_short.mp4"})

    def test_index_lines_record_start_and_finish(self):
        tracker = _new_tracker(self.root)
        self._seed_artifacts(tracker)
        tracker.promote_slots({"metadata": self.root / "data" / "metadata.json"})
        tracker.mark_ok()
        lines = (self.root / "data" / "runs" / "index.jsonl").read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "ok")
        self.assertEqual(records[0]["topic"], "demo topic")


if __name__ == "__main__":
    unittest.main()
