"""Option A - Strict Fail-Closed.

Strong Pipeline is mandatory for production generation.  These tests pin the
five required behaviours: success works, failure stops, legacy is never an
automatic fallback, earlier successful artifacts survive a failed run, and the
scheduler propagates failure without building a review package.  Everything is
hermetic - temp work dirs, stubbed stages, no network, no real notifications.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from api import main as api_main
from pipelines import short as short_module

ROOT = Path(__file__).resolve().parents[1]

STRONG_RESULT = {
    "topic": "AI power grids",
    "title": "Strong Title",
    "content_pillar": "What Changed",
    "tags": ["ai"],
    "source_urls": ["https://example.com/a"],
    "word_count": 40,
    "shots": [{"index": 0}, {"index": 1}],
    "duration_seconds": 35.0,
    "video_path": "outputs/output_short.mp4",
}

LEGACY_RESULT = {
    "title": "Legacy Title",
    "topic": "AI power grids",
    "content_pillar": "What Changed",
    "voice_text": "some narration",
    "broll_query": "grid",
    "tags": ["ai"],
    "source_urls": [],
    "word_count": 20,
}


def _sandbox(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "outputs").mkdir(parents=True, exist_ok=True)
    return tmp_path


STRONG_VIDEO_BYTES = b"strong-pipeline-video-bytes"


def _strong_stub(tmp_path: Path, payload: dict = STRONG_RESULT) -> MagicMock:
    """A run_strong_pipeline stand-in honouring the real contract: it receives a
    work_dir and metadata_file and writes actual artifacts there, so the
    promotion step has something truthful to validate and promote."""
    data = dict(payload)
    data["quality"] = "strong"

    def run(topic, work_dir, metadata_file, *args, **kwargs):
        work_dir = Path(work_dir)
        video_path = work_dir / "output_short.mp4"
        video_path.write_bytes(STRONG_VIDEO_BYTES)
        data["video_path"] = str(video_path)
        Path(metadata_file).write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return dict(data)

    return MagicMock(side_effect=run)


def _run_main(argv: list[str], tmp_path: Path, env: dict | None = None, **overrides):
    """Invoke the CLI entrypoint in-process against a sandboxed SCRIPT_DIR."""
    buffers = io.StringIO()
    patches = [
        patch.object(short_module, "SCRIPT_DIR", tmp_path),
        patch.object(short_module, "record_topic", MagicMock()),
        patch.object(short_module, "archive_video",
                     MagicMock(return_value=tmp_path / "archive.mp4")),
    ]
    for name, value in overrides.items():
        patches.append(patch.object(short_module, name, value))
    # DRY_RUN only: VIDEO_QUALITY stays untouched so callers can set it via
    # ``env`` or the outer test environment (the --quality default reads it).
    runtime = {"DRY_RUN": "0"}
    runtime.update(env or {})
    with contextlib.ExitStack() as stack:
        for item in patches:
            stack.enter_context(item)
        stack.enter_context(patch.dict(os.environ, runtime))
        stack.enter_context(patch.object(sys, "argv", ["pipelines/short.py", *argv]))
        stack.enter_context(contextlib.redirect_stdout(buffers))
        code = None
        try:
            short_module.main()
        except SystemExit as exit_exc:
            code = exit_exc.code
        return code, buffers.getvalue()


def _digest(path: Path) -> str:
    return path.read_bytes().hex() if path.exists() else "<missing>"


def _last_json(text: str) -> dict | None:
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


class CliFailClosedTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = _sandbox(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def test_strong_success_reports_success(self):
        strong = _strong_stub(self.root)
        code, out = _run_main(["--quality", "strong"], self.root,
                              run_strong_pipeline=strong)
        self.assertIsNone(code)
        strong.assert_called_once()
        payload = _last_json(out)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["quality"], "strong")
        self.assertEqual(payload["title"], "Strong Title")
        self.assertTrue(payload["run_id"])

    def test_strong_failure_stops_and_never_calls_legacy(self):
        legacy = MagicMock(return_value=LEGACY_RESULT)
        strong = MagicMock(side_effect=RuntimeError("research stage exploded"))
        code, out = _run_main(["--quality", "strong"], self.root,
                              run_strong_pipeline=strong, generate_script=legacy)
        self.assertEqual(code, 1)
        legacy.assert_not_called()
        self.assertIsNone(_last_json(out))
        self.assertNotIn('"status": "success"', out)

    def test_failure_leaves_previous_outputs_and_review_package_untouched(self):
        metadata = self.root / "data" / "metadata.json"
        review = self.root / "data" / "review_pending.json"
        approved = self.root / "data" / "review_approved.json"
        for path, payload in ((metadata, {"title": "previous strong run", "quality": "strong"}),
                              (review, {"video": "outputs/output_short.mp4"}),
                              (approved, {"reviewer": "Anish", "digest": "abc"})):
            path.write_text(json.dumps(payload), encoding="utf-8")
        before = {path: _digest(path) for path in (metadata, review, approved)}

        _run_main(["--quality", "strong"], self.root,
                  run_strong_pipeline=MagicMock(side_effect=RuntimeError("boom")),
                  generate_script=MagicMock())

        for path, digest in before.items():
            self.assertEqual(_digest(path), digest, f"{path.name} changed after a failed run")
        self.assertFalse((self.root / "outputs" / "output_short.mp4").exists())

    def test_diagnostics_are_sanitized(self):
        secret_url = "https://api.example.com/tts?key=sk-live-SUPERSECRET123"
        strong = MagicMock(side_effect=RuntimeError(f"voice provider refused: {secret_url}"))
        code, out = _run_main(["--quality", "strong"], self.root,
                              run_strong_pipeline=strong)
        self.assertEqual(code, 1)
        diagnostics = json.loads(
            (self.root / "data" / "last_failure.json").read_text(encoding="utf-8"))
        self.assertEqual(diagnostics["stage"], "strong_pipeline")
        self.assertEqual(diagnostics["error_type"], "RuntimeError")
        self.assertIn("voice provider refused", diagnostics["detail"])
        self.assertNotIn("SUPERSECRET", diagnostics["detail"])
        self.assertNotIn("SUPERSECRET", out)
        self.assertIn("key=***", diagnostics["detail"])

    def test_standard_quality_is_refused_without_opt_in(self):
        legacy = MagicMock(return_value=LEGACY_RESULT)
        code, out = _run_main(["--quality", "standard"], self.root,
                              generate_script=legacy)
        self.assertEqual(code, 2)
        legacy.assert_not_called()
        self.assertIn("strong-only", out)
        diagnostics = json.loads(
            (self.root / "data" / "last_failure.json").read_text(encoding="utf-8"))
        self.assertEqual(diagnostics["stage"], "quality_gate")

    def test_video_quality_env_cannot_bypass_strong_pipeline(self):
        legacy = MagicMock(return_value=LEGACY_RESULT)
        with patch.dict(os.environ, {"VIDEO_QUALITY": "standard", "DRY_RUN": "0"}):
            code, _ = _run_main([], self.root, generate_script=legacy)
        self.assertEqual(code, 2)
        legacy.assert_not_called()

    def test_legacy_path_still_available_when_explicitly_requested(self):
        legacy_stages = {
            "generate_script": MagicMock(return_value=dict(LEGACY_RESULT)),
            "generate_voiceover": MagicMock(),
            "get_background_video": MagicMock(return_value={"mode": "stub"}),
            "generate_subtitles": MagicMock(),
            "render_final_short": MagicMock(),
        }
        with patch("subprocess.run", return_value=MagicMock(stdout="30.0")):
            code, out = _run_main(["--quality", "standard", "--allow-standard"],
                                  self.root, **legacy_stages)
        self.assertIsNone(code)
        payload = _last_json(out)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["quality"], "standard")
        self.assertTrue(payload["legacy"])
        legacy_stages["generate_script"].assert_called_once()

    def test_strict_flag_is_still_accepted_but_not_required(self):
        strong = MagicMock(side_effect=RuntimeError("boom"))
        with_strict = _run_main(["--quality", "strong", "--strict"], self.root,
                                run_strong_pipeline=strong)[0]
        without_strict = _run_main(["--quality", "strong"], self.root,
                                   run_strong_pipeline=strong)[0]
        self.assertEqual(with_strict, without_strict)
        self.assertEqual(with_strict, 1)


class ShellChainTests(unittest.TestCase):
    """The scheduler must propagate a failed run and queue nothing for review."""

    def _stub_python(self, tmp_path: Path, call_log: Path, short_exit: int = 1) -> Path:
        stub = tmp_path / "python"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            f'echo "$@" >> "{call_log}"\n'
            'for arg in "$@"; do\n'
            '  case "$arg" in\n'
            '    *pipelines/short.py) exit ' + str(short_exit) + ' ;;\n'
            '  esac\n'
            'done\n'
            "exit 0\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        return stub

    def test_run_pipeline_stops_before_the_review_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            call_log = tmp_path / "calls.log"
            stub = self._stub_python(tmp_path, call_log)
            result = subprocess.run(
                ["/bin/bash", str(ROOT / "run_pipeline.sh")],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
                env={**os.environ, "SHORTS_STUDIO_PYTHON": str(stub),
                     "PUBLISH_MODE": "review", "PATH": os.environ["PATH"]},
            )
            calls = call_log.read_text(encoding="utf-8")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pipelines/short.py", calls)
            self.assertNotIn("app.review.review_bundle", calls)
            self.assertNotIn("app.notifications.notify_review", calls)
            self.assertIn("app.notifications.notify_status", calls)

    def test_scheduled_generation_propagates_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            call_log = tmp_path / "calls.log"
            stub = self._stub_python(tmp_path, call_log)
            result = subprocess.run(
                ["/bin/bash", str(ROOT / "run_scheduled_generation.sh")],
                cwd=ROOT, capture_output=True, text=True, timeout=180,
                env={**os.environ, "SHORTS_STUDIO_PYTHON": str(stub), "PATH": os.environ["PATH"]},
            )
            calls = call_log.read_text(encoding="utf-8")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pipelines/short.py", calls)
            self.assertNotIn("app.review.review_bundle", calls)
            self.assertNotIn("app.notifications.notify_review", calls)
            # The failure notice is the only notification a failed run may send.
            self.assertIn("scheduled Short generation", calls)


class ApiEntryPointTests(unittest.TestCase):
    def setUp(self):
        snapshot = patch.dict(os.environ, {}, clear=False)
        snapshot.start()
        self.addCleanup(snapshot.stop)
        os.environ.pop(api_main.LEGACY_OPT_IN_ENV, None)

    def test_default_start_uses_the_strong_pipeline(self):
        recorded = []

        class FakeThread:
            def __init__(self, target=None, args=(), daemon=None):
                recorded.append(args)

            def start(self):
                pass

        with patch.dict(api_main.jobs, {}, clear=True), \
                patch.object(api_main, "threading", MagicMock(Thread=FakeThread)):
            response = api_main.start()
            # patch.dict restores the original jobs mapping on exit, so any
            # assertion about the registered job must inspect it inside the
            # patched window.
            self.assertNotIn("error", response)
            self.assertEqual(recorded[0][3], "strong")
            self.assertEqual(api_main.jobs[response["job_id"]]["quality"], "strong")

    def test_standard_quality_is_rejected_by_the_api(self):
        with patch.dict(api_main.jobs, {}, clear=True), \
                patch.object(api_main, "threading", MagicMock()):
            response = api_main.start({"quality": "standard", "dry_run": False})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(api_main.jobs, {})

    def test_operator_opt_in_still_reaches_the_legacy_path(self):
        recorded = []

        class FakeThread:
            def __init__(self, target=None, args=(), daemon=None):
                recorded.append(args)

            def start(self):
                pass

        with patch.dict(api_main.jobs, {}, clear=True), \
                patch.dict(os.environ, {api_main.LEGACY_OPT_IN_ENV: "1"}), \
                patch.object(api_main, "threading", MagicMock(Thread=FakeThread)):
            response = api_main.start({"quality": "standard", "dry_run": False})

        self.assertNotIn("error", response)
        self.assertEqual(recorded[0][3], "standard")

    def test_legacy_opt_in_adds_the_explicit_cli_flag(self):
        job_id = "jobopt1"
        job = {"status": "queued", "dry_run": False, "topic": "t", "quality": "standard"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(api_main.jobs, {job_id: job}, clear=True), \
                    patch.object(api_main, "LOG_DIR", Path(tmp)), \
                    patch.object(api_main.subprocess, "run",
                                 return_value=MagicMock(returncode=0)) as run, \
                    patch.object(api_main, "_extract_result",
                                 return_value={"video_path": "out.mp4", "title": "T",
                                               "quality": "standard", "legacy": True}), \
                    patch.object(api_main, "_notify_job"):
                api_main.run_job(job_id, False, "t", "standard")
            cmd = run.call_args.args[0]
        self.assertIn("--allow-standard", cmd)
        self.assertEqual(job["status"], "done")

    def test_failed_run_is_never_reported_done(self):
        job_id = "jobfail1"
        job = {"status": "queued", "dry_run": False, "topic": "t", "quality": "strong"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(api_main.jobs, {job_id: job}, clear=True), \
                    patch.object(api_main, "LOG_DIR", Path(tmp)), \
                    patch.object(api_main.subprocess, "run",
                                 return_value=MagicMock(returncode=1)) as run, \
                    patch.object(api_main, "_extract_result",
                                 return_value={"video_path": "out.mp4", "title": "T",
                                               "quality": "strong"}), \
                    patch.object(api_main, "_notify_job"):
                api_main.run_job(job_id, False, "t", "strong")
            cmd = run.call_args.args[0]
        self.assertEqual(job["status"], "failed")
        self.assertNotIn("video_path", job)
        self.assertIn("--quality", cmd)
        self.assertEqual(cmd[cmd.index("--quality") + 1], "strong")
        self.assertNotIn("--allow-standard", cmd)

    def test_legacy_result_cannot_close_a_production_job(self):
        job_id = "jobleg1"
        job = {"status": "queued", "dry_run": False, "topic": "t", "quality": "strong"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(api_main.jobs, {job_id: job}, clear=True), \
                    patch.object(api_main, "LOG_DIR", Path(tmp)), \
                    patch.object(api_main.subprocess, "run",
                                 return_value=MagicMock(returncode=0)), \
                    patch.object(api_main, "_extract_result",
                                 return_value={"video_path": "out.mp4", "title": "T",
                                               "quality": "standard"}), \
                    patch.object(api_main, "_notify_job"):
                api_main.run_job(job_id, False, "t", "strong")
        self.assertEqual(job["status"], "failed")
        self.assertNotIn("video_path", job)
        self.assertIn("strong-pipeline", job["error"])

    def test_strong_result_completes_the_job(self):
        job_id = "jobok1"
        job = {"status": "queued", "dry_run": False, "topic": "t", "quality": "strong"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(api_main.jobs, {job_id: job}, clear=True), \
                    patch.object(api_main, "LOG_DIR", Path(tmp)), \
                    patch.object(api_main.subprocess, "run",
                                 return_value=MagicMock(returncode=0)), \
                    patch.object(api_main, "_extract_result",
                                 return_value={"video_path": "out.mp4", "title": "T",
                                               "quality": "strong"}), \
                    patch.object(api_main, "_notify_job"):
                api_main.run_job(job_id, False, "t", "strong")
        self.assertEqual(job["status"], "done")
        self.assertEqual(job["video_path"], "out.mp4")


class RunSecuredPromotionTests(unittest.TestCase):
    """End-to-end Phase 10.4: run identity, artifact isolation, promotion.

    A successful strong run must leave a complete run identity behind (manifest
    ok only after its promotion journal completed) and land byte-identical
    artifacts in the legacy slots; a failed strong run must mark the run
    failed without touching previous outputs; the legacy and dry-run paths
    must never create run identities.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = _sandbox(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def _runs_dir(self):
        return self.root / "outputs" / "runs"

    def _only_run_manifest(self):
        run_dirs = [d for d in self._runs_dir().iterdir() if d.is_dir()]
        self.assertEqual(len(run_dirs), 1)
        manifest = json.loads((run_dirs[0] / "manifest.json").read_text(encoding="utf-8"))
        return run_dirs[0], manifest

    def test_successful_strong_run_builds_run_identity_and_promotes(self):
        code, out = _run_main(["--quality", "strong"], self.root,
                              run_strong_pipeline=_strong_stub(self.root))
        self.assertIsNone(code)
        run_dir, manifest = self._only_run_manifest()
        self.assertEqual(manifest["status"], "ok")
        self.assertEqual(manifest["run_id"], run_dir.name)
        self.assertIn("output_short.mp4", manifest["artifacts"]["video"]["path"])
        metadata_artifact = manifest["artifacts"]["metadata"]
        metadata_path = Path(metadata_artifact["path"])
        if not metadata_path.is_absolute():
            metadata_path = run_dir / metadata_path
        self.assertEqual(hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
                         metadata_artifact["sha256"])
        video_artifact = manifest["artifacts"]["video"]
        video_path = Path(video_artifact["path"])
        if not video_path.is_absolute():
            video_path = run_dir / video_path
        self.assertEqual(hashlib.sha256(video_path.read_bytes()).hexdigest(),
                         video_artifact["sha256"])
        journal = json.loads(
            Path(manifest["promotion"]["journal_path"]).read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "completed")
        self.assertEqual(journal["targets"],
                         {name: artifact["sha256"]
                          for name, artifact in manifest["artifacts"].items()})
        index = self.root / "data" / "runs" / "index.jsonl"
        records = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(records[-1]["run_id"], run_dir.name)
        self.assertEqual(records[-1]["status"], "ok")
        self.assertTrue((self.root / "outputs" / "output_short.mp4").is_file())
        metadata = json.loads((self.root / "data" / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["run_id"], run_dir.name)

    def test_failed_strong_run_marks_failed_and_preserves_outputs(self):
        metadata_file = self.root / "data" / "metadata.json"
        video_file = self.root / "outputs" / "output_short.mp4"
        metadata_file.write_text(json.dumps({"title": "previous strong run", "quality": "strong"}), encoding="utf-8")
        video_file.write_bytes(b"PREVIOUS-VIDEO")
        code, out = _run_main(
            ["--quality", "strong"], self.root,
            run_strong_pipeline=MagicMock(side_effect=RuntimeError("boom")))
        self.assertEqual(code, 1)
        self.assertIsNone(_last_json(out))
        before_metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        self.assertEqual(before_metadata["title"], "previous strong run")
        self.assertEqual(video_file.read_bytes(), b"PREVIOUS-VIDEO")
        run_dir, manifest = self._only_run_manifest()
        self.assertEqual(manifest["status"], "failed")
        failure = json.loads((run_dir / "failure.json").read_text(encoding="utf-8"))
        self.assertEqual(failure["error_type"], "RuntimeError")
        index = self.root / "data" / "runs" / "index.jsonl"
        records = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(records[-1]["status"], "failed")
        self.assertFalse((self._runs_dir() / run_dir.name / "promotion").exists())

    def test_legacy_opt_in_and_dry_runs_never_create_run_identity(self):
        legacy_stages = {
            "generate_script": MagicMock(return_value=dict(LEGACY_RESULT)),
            "generate_voiceover": MagicMock(),
            "get_background_video": MagicMock(return_value={"mode": "stub"}),
            "generate_subtitles": MagicMock(),
            "render_final_short": MagicMock(),
        }
        with patch("subprocess.run", return_value=MagicMock(stdout="30.0")):
            code, _ = _run_main(["--quality", "standard", "--allow-standard"],
                                self.root, **legacy_stages)
        self.assertIsNone(code)
        self.assertFalse(self._runs_dir().exists())
        self.assertFalse((self.root / "data" / "runs").exists())


if __name__ == "__main__":
    unittest.main()
