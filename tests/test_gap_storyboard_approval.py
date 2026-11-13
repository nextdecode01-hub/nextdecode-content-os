"""Gaps 2 & 3: Storyboard blocked status and approval binding integrity.

Gap 2: Storyboard blocked status under STORYBOARD_GATE=require must raise.
Gap 3: Missing, stale and tampered storyboard approval bindings
       (contact sheet, script hash, ledger hash, scene digest) must raise.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.visuals import storyboard

FFMPEG = shutil.which("ffmpeg")


def _run(cmd):
    subprocess.run(
        [FFMPEG, "-y", *cmd],
        check=True, capture_output=True, text=True, timeout=60,
    )


def _png(path: Path) -> Path:
    _run(["-f", "lavfi", "-i", "color=c=0x22d3ee:s=270x480:r=1",
          "-frames:v", "1", str(path)])
    return path


def _detail(index: int, path: Path) -> dict:
    return {
        "path": str(path),
        "provider": "pixabay",
        "visual_type": "broll",
        "scene_type": "footage",
        "asset_id": f"pixabay:{index}",
        "query": "data center servers",
        "relevance": "tag_overlap",
        "relevance_confidence": "medium",
        "semantic_review": True,
        "review_reason": "lexical match needs visual review",
    }


@unittest.skipUnless(FFMPEG, "ffmpeg not available")
class Gap2StoryboardBlockedTests(unittest.TestCase):
    """Blocked storyboard status must prevent render under require gate."""

    def test_storyboard_blocked_status_raises_under_require_gate(self):
        payload = {
            "review_status": "blocked",
            "review_reasons": ["s00: no usable asset"],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            r"storyboard review required before render \(blocked\)",
        ):
            storyboard.enforce_review_gate(payload, "require")


@unittest.skipUnless(FFMPEG, "ffmpeg not available")
class Gap3ApprovalBindingIntegrityTests(unittest.TestCase):
    """Storyboard approval bindings must be validated at enforce time."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_approval_missing_approval_file(self):
        shots = [{"index": 0, "duration": 3.0, "caption": "c"}]
        details = [_detail(0, _png(self.dir / "a.png"))]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        result["approval_path"] = str(self.dir / "non_existent.json")
        with self.assertRaisesRegex(RuntimeError, "storyboard review required before render"):
            storyboard.enforce_review_gate(result, "require")

    def test_approval_missing_contact_sheet(self):
        shots = [{"index": 0, "duration": 3.0, "caption": "c"}]
        details = [_detail(0, _png(self.dir / "a.png"))]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        storyboard.approve_storyboard(result["json_path"], "Anish", "note")
        Path(result["contact_sheet"]).unlink()
        with self.assertRaisesRegex(RuntimeError, "storyboard review required before render"):
            storyboard.enforce_review_gate(result, "require")

    def test_approval_stale_or_tampered_contact_sheet(self):
        shots = [{"index": 0, "duration": 3.0, "caption": "c"}]
        details = [_detail(0, _png(self.dir / "a.png"))]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        storyboard.approve_storyboard(result["json_path"], "Anish", "note")
        _run(["-f", "lavfi", "-i", "color=c=0xff0000:s=270x480:r=1",
              "-frames:v", "1", result["contact_sheet"]])
        with self.assertRaisesRegex(RuntimeError, "storyboard review required before render"):
            storyboard.enforce_review_gate(result, "require")

    def test_approval_tampered_script_hash(self):
        shots = [{"index": 0, "duration": 3.0, "caption": "c"}]
        details = [_detail(0, _png(self.dir / "a.png"))]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        storyboard.approve_storyboard(result["json_path"], "Anish", "note")
        result["script_sha256"] = "a" * 64
        with self.assertRaisesRegex(RuntimeError, "storyboard review required before render"):
            storyboard.enforce_review_gate(result, "require")

    def test_approval_tampered_ledger_hash(self):
        shots = [{"index": 0, "duration": 3.0, "caption": "c"}]
        details = [_detail(0, _png(self.dir / "a.png"))]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        storyboard.approve_storyboard(result["json_path"], "Anish", "note")
        result["ledger_sha256"] = "b" * 64
        with self.assertRaisesRegex(RuntimeError, "storyboard review required before render"):
            storyboard.enforce_review_gate(result, "require")

    def test_approval_tampered_scene_digest(self):
        shots = [{"index": 0, "duration": 3.0, "caption": "c"}]
        details = [_detail(0, _png(self.dir / "a.png"))]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        storyboard.approve_storyboard(result["json_path"], "Anish", "note")
        result["scene_digest"] = "c" * 64
        with self.assertRaisesRegex(RuntimeError, "storyboard review required before render"):
            storyboard.enforce_review_gate(result, "require")


if __name__ == "__main__":
    unittest.main()
