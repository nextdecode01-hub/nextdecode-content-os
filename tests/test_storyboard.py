import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.visuals import storyboard

FFMPEG = shutil.which("ffmpeg")
HAS_FFMPEG = bool(FFMPEG)


def _run(cmd):
    subprocess.run([FFMPEG, "-y", *cmd], check=True, capture_output=True, text=True, timeout=60)


def _png(path: Path) -> Path:
    _run(["-f", "lavfi", "-i", "color=c=0x22d3ee:s=270x480:r=1",
          "-frames:v", "1", str(path)])
    return path


def _video(path: Path) -> Path:
    _run(["-f", "lavfi", "-i", "testsrc2=s=270x480:r=30:d=1",
          "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(path)])
    return path


def _shots(count: int) -> list[dict]:
    return [
        {
            "index": index,
            "start": index * 3.1,
            "end": (index + 1) * 3.1,
            "duration": 3.1,
            "claim": f"claim number {index}",
            "caption": f"caption {index}",
            "asset_query": "data center servers",
            "visual": "data center servers",
        }
        for index in range(count)
    ]


def _detail(index: int, path: Path, provider="motion_graphic", **extra) -> dict:
    detail = {
        "path": str(path),
        "provider": provider,
        "visual_type": "motion_graphic" if provider == "motion_graphic" else "broll",
        "scene_type": "typography" if provider == "motion_graphic" else "footage",
        "asset_id": f"{provider}:{index}",
        "query": "data center servers",
        "relevance": "generated_from_narration" if provider == "motion_graphic" else "tag_overlap",
        "relevance_confidence": "high" if provider == "motion_graphic" else "medium",
        "semantic_review": provider != "motion_graphic",
        "review_reason": "" if provider == "motion_graphic" else "lexical match needs visual review",
    }
    detail.update(extra)
    return detail


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
class StoryboardArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_contact_sheet_and_json_are_written(self):
        shots = _shots(4)
        details = [
            _detail(0, _png(self.dir / "a.png")),
            _detail(1, _video(self.dir / "b.mp4"), provider="pixabay"),
            _detail(2, _video(self.dir / "c.mp4"), provider="gradient",
                    relevance_confidence="none", semantic_review=True,
                    fallback_reason="no stock provider configured"),
            _detail(3, _png(self.dir / "d.png")),
        ]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")

        self.assertTrue(Path(result["json_path"]).is_file())
        self.assertTrue(Path(result["contact_sheet"]).is_file())
        self.assertGreater(Path(result["contact_sheet"]).stat().st_size, 10_000)
        payload = json.loads(Path(result["json_path"]).read_text())
        self.assertEqual(payload["scene_count"], 4)
        self.assertEqual(len(payload["scenes"]), 4)
        self.assertEqual(payload["review_status"], "needs_review")
        self.assertTrue(payload["review_required"])
        self.assertFalse(payload["approved"])
        self.assertTrue(all(scene["thumb"] for scene in payload["scenes"]))
        self.assertTrue(all(scene["narration"] for scene in payload["scenes"]))
        self.assertTrue(all(scene["provenance"]["content_sha256"] for scene in payload["scenes"]))
        self.assertTrue(all(scene["provenance"]["retrieved_at"] for scene in payload["scenes"]))
        probe = subprocess.run(
            [shutil.which("ffprobe"), "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width", "-of", "csv=p=0", result["contact_sheet"]],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(probe.stdout.strip(), "1080")
        self.assertEqual(payload["summary"]["high"], 2)
        self.assertEqual(payload["summary"]["medium"], 1)
        self.assertEqual(payload["summary"]["none"], 1)
        self.assertEqual(payload["summary"]["semantic_review"], 2)
        self.assertEqual(payload["summary"]["fallbacks"], 1)

    def test_explicit_approval_unlocks_require_gate(self):
        shots = _shots(2)
        details = [
            _detail(0, _png(self.dir / "a.png")),
            _detail(1, _video(self.dir / "b.mp4"), provider="pixabay"),
        ]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        self.assertEqual(result["review_status"], "needs_review")
        with self.assertRaises(RuntimeError):
            storyboard.enforce_review_gate(result, "require")
        approval = storyboard.approve_storyboard(result["json_path"], "Anish", "looked good")
        self.assertTrue(approval["approved"])
        self.assertEqual(approval["reviewer"], "Anish")
        storyboard.enforce_review_gate(result, "require")

    def test_blocked_storyboard_cannot_be_approved(self):
        shots = _shots(1)
        result = storyboard.build_storyboard(shots, [{"provider": "", "path": ""}], self.dir / "work")
        with self.assertRaisesRegex(RuntimeError, "blocked"):
            storyboard.approve_storyboard(result["json_path"], "Anish")

    def test_missing_asset_blocks_the_gate(self):
        shots = _shots(2)
        details = [_detail(0, _png(self.dir / "a.png")), {"provider": "", "path": ""}]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        self.assertEqual(result["review_status"], "blocked")
        self.assertIn("no usable selected asset", " ".join(result["review_reasons"]))

    def test_all_high_assets_auto_approve(self):
        shots = _shots(2)
        details = [
            _detail(0, _png(self.dir / "a.png")),
            _detail(1, _png(self.dir / "b.png")),
        ]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        self.assertEqual(result["review_status"], "auto_approved")
        self.assertTrue(result["approved"])
        self.assertFalse(result["review_required"])


class ReviewGateTests(unittest.TestCase):
    def test_require_gate_blocks_needs_review(self):
        payload = {"review_status": "needs_review", "review_reasons": ["s00: low confidence"]}
        with self.assertRaisesRegex(RuntimeError, "storyboard review required"):
            storyboard.enforce_review_gate(payload, "require")

    def test_require_gate_allows_auto_approved(self):
        storyboard.enforce_review_gate(
            {"review_status": "auto_approved", "review_reasons": []}, "require"
        )

    def test_warn_and_off_do_not_raise(self):
        payload = {"review_status": "blocked", "review_reasons": ["s00: no asset"]}
        storyboard.enforce_review_gate(payload, "warn")
        storyboard.enforce_review_gate(payload, "off")


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
class StoryboardApprovalBindingRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.shots = _shots(2)
        self.details = [
            _detail(0, _png(self.root / "a.png")),
            _detail(1, _video(self.root / "b.mp4"), provider="pixabay"),
        ]
        self.result = storyboard.build_storyboard(
            self.shots, self.details, self.root / "work",
            evidence={"script_sha256": "script-v1", "ledger_sha256": "ledger-v1"},
        )
        self.assertEqual(self.result["review_status"], "needs_review")
        storyboard.approve_storyboard(self.result["json_path"], "reviewer", "inspected")
        self.contact = Path(self.result["contact_sheet"])
        self.approval = Path(self.result["approval_path"])

    def tearDown(self):
        self.tmp.cleanup()

    def test_blocked_status_cannot_be_overridden_by_a_previous_approval(self):
        # setUp creates a valid approval for the needs_review storyboard.
        # Changing its status to blocked must invalidate that approval.
        self.result["review_status"] = "blocked"
        with self.assertRaisesRegex(RuntimeError, "storyboard review required"):
            storyboard.enforce_review_gate(self.result, "require")

    def test_missing_storyboard_approval_fails_closed(self):
        self.approval.unlink()
        with self.assertRaisesRegex(RuntimeError, "storyboard review required"):
            storyboard.enforce_review_gate(self.result, "require")

    def test_approval_is_invalidated_by_script_ledger_or_scene_digest_changes(self):
        for field in ("script_sha256", "ledger_sha256", "scene_digest"):
            with self.subTest(field=field):
                changed = dict(self.result)
                changed[field] = str(changed.get(field) or "") + "-tampered"
                with self.assertRaisesRegex(RuntimeError, "storyboard review required"):
                    storyboard.enforce_review_gate(changed, "require")

    def test_approval_is_invalidated_when_contact_sheet_changes(self):
        original = self.contact.read_bytes()
        try:
            self.contact.write_bytes(original + b"tampered")
            with self.assertRaisesRegex(RuntimeError, "storyboard review required"):
                storyboard.enforce_review_gate(self.result, "require")
        finally:
            self.contact.write_bytes(original)

    def test_approval_is_valid_for_unchanged_reviewed_artifacts(self):
        storyboard.enforce_review_gate(self.result, "require")
        self.assertTrue(self.result.get("human_approved"))



@unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
class StoryboardWarnModeCompatibilityRegressionTests(unittest.TestCase):
    def test_warn_and_off_remain_explicit_opt_outs_after_approval_invalidation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shots = _shots(2)
            details = [
                _detail(0, _png(root / "a.png")),
                _detail(1, _video(root / "b.mp4"), provider="pixabay"),
            ]
            result = storyboard.build_storyboard(
                shots, details, root / "work",
                evidence={"script_sha256": "script-v1", "ledger_sha256": "ledger-v1"},
            )
            storyboard.approve_storyboard(result["json_path"], "reviewer")
            result["review_status"] = "blocked"
            storyboard.enforce_review_gate(result, "warn")
            storyboard.enforce_review_gate(result, "off")

