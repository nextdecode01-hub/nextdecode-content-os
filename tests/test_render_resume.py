"""Regression tests for the render resume / storyboard-review-pause story.

Covers:
  * StoryboardReviewRequired is a typed, resumable pause (RuntimeError subclass)
    carrying storyboard_path, review_status and reasons.
  * The pre-render gate raises StoryboardReviewRequired (not a bare RuntimeError)
    under STORYBOARD_GATE=require, and passes once a valid approval exists.
  * The render plan is persisted before the gate can stop the run.
  * RunTracker: in_progress -> awaiting_review -> ok (reopen via open_run).
  * pipeline.resume loads render_context.json + render_plan.json.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.visuals import storyboard
from app.tracking import run_tracker as tr
from app.script import pipeline as pp
from app.render import assembly as ra

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
class StoryboardReviewRequiredTypeTests(unittest.TestCase):
    """The gate pause must be typed and carry resume-critical fields."""

    def test_is_runtime_error_subclass(self):
        self.assertTrue(issubclass(storyboard.StoryboardReviewRequired, RuntimeError))

    def test_carries_storyboard_path_review_status_reasons(self):
        exc = storyboard.StoryboardReviewRequired(
            "storyboard review required before render (needs_review): s00: x",
            storyboard_path="/runs/r1/storyboard.json",
            review_status="needs_review",
            reasons=["s00: x"],
        )
        self.assertIsInstance(exc, RuntimeError)
        self.assertEqual(exc.storyboard_path, "/runs/r1/storyboard.json")
        self.assertEqual(exc.review_status, "needs_review")
        self.assertEqual(exc.reasons, ["s00: x"])
        self.assertIn("needs_review", str(exc))


@unittest.skipUnless(FFMPEG, "ffmpeg not available")
class GateRaisesTypedPauseTests(unittest.TestCase):
    """enforce_review_gate must raise StoryboardReviewRequired in require mode."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_require_raises_storyboard_review_required(self):
        payload = {
            "json_path": str(self.dir / "storyboard.json"),
            "review_status": "needs_review",
            "review_reasons": ["s00: external visual has not received a successful visual review"],
        }
        with self.assertRaises(storyboard.StoryboardReviewRequired) as ctx:
            storyboard.enforce_review_gate(payload, "require")
        exc = ctx.exception
        self.assertEqual(exc.review_status, "needs_review")
        self.assertEqual(exc.reasons, payload["review_reasons"])
        self.assertEqual(exc.storyboard_path, str(self.dir / "storyboard.json"))

    def test_valid_approval_passes_gate(self):
        shots = [{"index": 0, "duration": 3.0, "caption": "c"}]
        details = [_detail(0, _png(self.dir / "a.png"))]
        result = storyboard.build_storyboard(shots, details, self.dir / "work")
        storyboard.approve_storyboard(result["json_path"], "Anish", "note")
        # A valid, bound approval must NOT raise.
        storyboard.enforce_review_gate(result, "require")
        self.assertTrue(result.get("human_approved"))


class RenderPlanPersistedBeforeGateTests(unittest.TestCase):
    """_write_render_plan must persist render_plan.json with resume-critical keys."""

    def test_write_render_plan_keys(self):
        self.tmp = tempfile.TemporaryDirectory()
        try:
            work = Path(self.tmp.name)
            path = ra._write_render_plan(
                work,
                shots=[{"index": 0, "title": "t", "start": 0.0, "end": 3.0}],
                resolved_scenes=[
                    {"shot": {"index": 0}, "detail": {"provider": "pixabay"},
                     "asset_path": str(work / "a.mp4")}
                ],
                planner={"stock_cap": 2, "total": 5},
                assets=[{"provider": "pixabay", "title": "x"}],
                motion_plan=[{"index": 0, "profile": "slow_zoom"}],
                evidence={"ledger": {"script_sha256": "abc", "ledger_sha256": "def"},
                        "ledger_present": True},
                storyboard={"json_path": str(work / "storyboard.json"),
                            "review_status": "needs_review",
                            "review_reasons": ["s00: x"]},
                width=1080, height=1920, fps=30,
            )
            self.assertTrue(path.is_file())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 1)
            self.assertEqual(data["width"], 1080)
            self.assertEqual(data["height"], 1920)
            self.assertEqual(data["fps"], 30)
            self.assertEqual(len(data["shots"]), 1)
            self.assertEqual(len(data["resolved_scenes"]), 1)
            self.assertEqual(len(data["assets"]), 1)
            self.assertTrue(data["evidence"]["ledger_present"])
            self.assertEqual(data["storyboard_path"], str(work / "storyboard.json"))
        finally:
            self.tmp.cleanup()


class TrackerAwaitingReviewTests(unittest.TestCase):
    """in_progress -> awaiting_review -> ok, with reopen via open_run."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.runs_root = self.dir / "runs"
        self.index_path = self.dir / "index.jsonl"
        self.tracker = tr.start_run(
            "test topic", runs_root=self.runs_root, index_path=self.index_path,
            quality="strong",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_mark_awaiting_review_parks_run(self):
        self.tracker.start_stage("render")
        self.tracker.finish_stage("render", status="failed")
        manifest = self.tracker.mark_awaiting_review(
            stage="render", detail="storyboard review required: needs_review")
        self.assertEqual(manifest["status"], "awaiting_review")
        self.assertIsNone(manifest.get("finished_at"))
        self.assertEqual(manifest["review"]["stage"], "render")
        # index line appended
        line = json.loads(self.index_path.read_text().strip().splitlines()[-1])
        self.assertEqual(line["status"], "awaiting_review")

    def test_open_run_reopens_parked_run(self):
        self.tracker.mark_awaiting_review(stage="render")
        reopened = tr.open_run(self.tracker.run_dir,
                               runs_root=self.runs_root, index_path=self.index_path)
        self.assertEqual(reopened.run_id, self.tracker.run_id)
        self.assertEqual(reopened.manifest["status"], "awaiting_review")

    def test_mark_ok_from_awaiting_review(self):
        self.tracker.mark_awaiting_review(stage="render")
        # Reopen and close to ok (simulates a successful resumed render).
        reopened = tr.open_run(self.tracker.run_dir,
                               runs_root=self.runs_root, index_path=self.index_path)
        manifest = reopened.mark_ok()
        self.assertEqual(manifest["status"], "ok")
        self.assertIsNotNone(manifest.get("finished_at"))

    def test_mark_failed_from_awaiting_review(self):
        self.tracker.mark_awaiting_review(stage="render")
        reopened = tr.open_run(self.tracker.run_dir,
                               runs_root=self.runs_root, index_path=self.index_path)
        manifest = reopened.mark_failed(stage="render", exc=RuntimeError("boom"))
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["failure"]["error_type"], "RuntimeError")


class PipelineResumeTests(unittest.TestCase):
    """pipeline.resume loads render_context.json + render_plan.json."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_resume_missing_context_raises(self):
        with self.assertRaisesRegex(RuntimeError, "no render context for run"):
            pp.resume(self.dir / "nonexistent")

    def test_resume_missing_plan_raises(self):
        (self.dir / "render_context.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "no render plan for run"):
            pp.resume(self.dir)


if __name__ == "__main__":
    unittest.main()
