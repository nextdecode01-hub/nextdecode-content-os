"""Phase 10.4 — approval-side run provenance verification.

Pins the decision that a review package tied to a run identity is only
approvable when:
  * the run manifest says ``ok``,
  * the promotion journal says ``completed``,
  * BOTH legacy slots still hash-match the run's recorded artifacts.

A mixed pair (metadata from run B, video from run A), an interrupted
promotion, or a failed run can therefore never be approved.  Packages without
a run_id keep the exact legacy behaviour (they are not exercised here — other
suites cover that path hermetically).
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from app.security import approval_integrity as approval_integrity
from app.review.approve_review import main as approve_main

RUN_ID = "20261031-120000-demo-topic"


def _sha(path: Path) -> str:
    return approval_integrity.sha256_file(path)


def _build_run(root: Path, *, manifest_status: str = "ok",
               journal_status: str = "completed") -> tuple[Path, Path]:
    metadata_file = root / "data" / "metadata.json"
    video_file = root / "outputs" / "output_short.mp4"
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    video_file.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.write_text(json.dumps(
        {"title": "T", "quality": "strong", "run_id": RUN_ID,
         "visuals": {"mode": "owner_recorded", "asset_count": 1,
                     "asset_path": str(root / "asset.mp4")}}, indent=2), encoding="utf-8")
    video_file.write_bytes(b"RUN-VIDEO-BYTES")
    (root / "asset.mp4").write_bytes(b"asset")
    run_dir = root / "outputs" / "runs" / RUN_ID
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": RUN_ID,
        "status": manifest_status,
        "artifacts": {
            "metadata": {"path": "metadata.json", "sha256": _sha(metadata_file)},
            "video": {"path": "output_short.mp4", "sha256": _sha(video_file)},
        },
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    journal_path = root / "data" / "runs" / "promotions" / f"{RUN_ID}.json"
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text(json.dumps(
        {"run_id": RUN_ID, "status": journal_status, "targets": {
            "metadata": _sha(metadata_file), "video": _sha(video_file)}}, indent=2),
        encoding="utf-8")
    return metadata_file, video_file


def _package(root: Path, metadata_file: Path, video_file: Path) -> Path:
    from app.visuals.visual_quality import has_publishable_visuals
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    package = {
        "status": "pending_human_review",
        "run_id": RUN_ID,
        "run_manifest_path": str(root / "outputs" / "runs" / RUN_ID / "manifest.json"),
        "run_manifest_sha256": _sha(root / "outputs" / "runs" / RUN_ID / "manifest.json"),
        "video_sha256": _sha(video_file),
        "metadata_sha256": _sha(metadata_file),
        "title": metadata["title"],
        "visuals": metadata["visuals"],
        "visual_quality_status": "review_ready" if has_publishable_visuals(metadata["visuals"]) else "draft_only",
        "checklist": {name: True for name in (
            "two_sources_checked", "primary_source_checked",
            "real_demo_or_original_visual", "limitation_stated",
            "captions_audio_and_9x16_checked", "platform_copy_checked",
            "publish_approved")},
    }
    package_path = root / "data" / "review_queue" / "pkg.json"
    package_path.parent.mkdir(parents=True, exist_ok=True)
    package_path.write_text(json.dumps(package, indent=2), encoding="utf-8")
    return package_path


def _approve(execute_against: Path, package_path: Path | None = None):
    with ExitStack() as stack:
        stack.enter_context(patch("app.review.approve_review.ROOT", execute_against))
        argv = ["approve_review.py", "--reviewer", "test-reviewer", "--rationale", "Verified source and final video"]
        if package_path is not None:
            argv.append(str(package_path))
        stack.enter_context(patch.object(sys, "argv", argv))
        stack.enter_context(patch("builtins.input", return_value="y"))
        return approve_main()


class ReviewProvenanceTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _scenario(self, *, manifest_status: str = "ok", journal_status: str = "completed"):
        metadata_file, video_file = _build_run(
            self.root, manifest_status=manifest_status, journal_status=journal_status)
        return metadata_file, video_file, _package(self.root, metadata_file, video_file)

    def test_completed_run_package_is_approvable(self):
        _, video_file, package = self._scenario()
        result = _approve(self.root, package)
        self.assertEqual(result, 0)
        self.assertTrue(video_file.exists())
        package_payload = json.loads(package.read_text(encoding="utf-8"))
        self.assertEqual(package_payload["status"], "pending_human_review")
        pointer = json.loads((self.root / "data" / "review_approved.json").read_text(encoding="utf-8"))
        decision = json.loads(Path(pointer["decision_record"]).read_text(encoding="utf-8"))
        self.assertEqual(decision["reviewer"], "test-reviewer")
        self.assertEqual(decision["destination"], "private")
        self.assertEqual(decision["platform"], "youtube")

    def test_incomplete_promotion_is_never_approvable(self):
        _, video_file, package = self._scenario(journal_status="promoting")
        with self.assertRaisesRegex(SystemExit, "Promotion for run .* is 'promoting'"):
            _approve(self.root, package)
        # nothing was marked approved
        self.assertFalse((self.root / "data" / "review_approved.json").exists())

    def test_mixed_pair_is_never_approvable(self):
        metadata_file, video_file, package = self._scenario()
        # Replace the video slot with another run's bytes, then rebuild the
        # package's slot hashes so the pre-existing dual-hash gate alone would
        # pass — the provenance cross-check must still catch that the current
        # slot does not match the run's recorded artifact.
        video_file.write_bytes(b"OTHER-RUN-VIDEO")
        refreshed = json.loads(package.read_text(encoding="utf-8"))
        refreshed["video_sha256"] = _sha(video_file)
        package.write_text(json.dumps(refreshed, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "does not match run"):
            _approve(self.root, package)
        self.assertFalse((self.root / "data" / "review_approved.json").exists())

    def test_non_ok_run_is_never_approvable(self):
        _, _, package = self._scenario(manifest_status="failed")
        with self.assertRaisesRegex(SystemExit, "not a completed run"):
            _approve(self.root, package)

    def test_approval_digest_uses_exact_bytes_that_were_parsed(self):
        import hashlib
        from app.publish.authorization import PublishNotAuthorized, _approval_records

        _, _, package = self._scenario()
        original_read_bytes = Path.read_bytes
        captured = {}

        def read_then_replace(path):
            content = original_read_bytes(path)
            if path == package:
                captured["digest"] = hashlib.sha256(content).hexdigest()
                changed = json.loads(content)
                changed["notes"] = "replaced after reviewer read the original bytes"
                package.write_text(json.dumps(changed, indent=2), encoding="utf-8")
            return content

        with patch.object(Path, "read_bytes", new=read_then_replace):
            result = _approve(self.root, package)

        self.assertEqual(result, 0)
        pointer = json.loads((self.root / "data" / "review_approved.json").read_text(encoding="utf-8"))
        decision = json.loads(Path(pointer["decision_record"]).read_text(encoding="utf-8"))
        self.assertEqual(decision["review_package_sha256"], captured["digest"])
        with patch("app.publish.authorization.ROOT", self.root):
            with self.assertRaisesRegex(PublishNotAuthorized, "changed after human approval"):
                _approval_records(data_root=self.root, purpose="short")


if __name__ == "__main__":
    unittest.main()
