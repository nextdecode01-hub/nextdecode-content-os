import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from api import main as api_main

ENV_ON = {"TELEGRAM_BOT_TOKEN": "123:secret-token", "TELEGRAM_CHAT_ID": "42"}


class TelegramNotifyTests(unittest.TestCase):
    def test_skips_silently_without_env(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(api_main.requests, "post") as post:
            self.assertFalse(api_main._notify("hello"))
        post.assert_not_called()

    def test_sends_success_message_with_topic_and_path(self):
        job = {"status": "done", "topic": "AI power grids", "video_path": "outputs/run/output_short.mp4"}
        with patch.dict(os.environ, ENV_ON, clear=True), patch.object(api_main.requests, "post") as post:
            post.return_value = MagicMock(status_code=200)
            api_main._notify_job(job)

        self.assertTrue(job["notified"])
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["chat_id"], "42")
        self.assertEqual(payload["text"], "Video ready | AI power grids | outputs/run/output_short.mp4")
        self.assertEqual(post.call_args.kwargs["timeout"], 15)

    def test_sends_failure_message(self):
        job = {"status": "failed", "error": "exit code 1"}
        with patch.dict(os.environ, ENV_ON, clear=True), patch.object(api_main.requests, "post") as post:
            post.return_value = MagicMock(status_code=200)
            api_main._notify_job(job)

        self.assertEqual(post.call_args.kwargs["json"]["text"], "Video failed | exit code 1")

    def test_retries_twice_then_gives_up_without_raising(self):
        with patch.dict(os.environ, ENV_ON, clear=True), \
                patch.object(api_main.requests, "post", side_effect=OSError("boom")) as post, \
                patch.object(api_main.time, "sleep") as sleep:
            self.assertFalse(api_main._notify("hello"))

        self.assertEqual(post.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_http_errors_are_retried(self):
        with patch.dict(os.environ, ENV_ON, clear=True), \
                patch.object(api_main.requests, "post", return_value=MagicMock(status_code=500)) as post, \
                patch.object(api_main.time, "sleep"):
            self.assertFalse(api_main._notify("hello"))

        self.assertEqual(post.call_count, 3)

    def test_token_never_appears_in_output(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer), \
                patch.dict(os.environ, ENV_ON, clear=True), \
                patch.object(api_main.requests, "post", side_effect=OSError("boom")), \
                patch.object(api_main.time, "sleep"):
            self.assertFalse(api_main._notify("hello"))

        self.assertNotIn("secret-token", buffer.getvalue())
        self.assertNotIn("api.telegram.org", buffer.getvalue())


class RunJobNotifyTests(unittest.TestCase):
    def _run(self, job_id, notify_mock):
        job = {"status": "queued", "dry_run": True, "topic": "t", "quality": "standard"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(api_main.jobs, {job_id: job}, clear=True), \
                    patch.object(api_main, "LOG_DIR", Path(tmp)), \
                    patch.object(api_main.subprocess, "run") as run, \
                    patch.object(api_main, "_extract_result", return_value={"video_path": "out.mp4", "title": "T", "quality": "standard"}), \
                    patch.object(api_main, "_notify_job", notify_mock):
                run.return_value = MagicMock(returncode=0)
                api_main.run_job(job_id, True, "t", "standard")
        return job

    def test_run_job_notifies_done_without_failing_job(self):
        with patch.object(api_main, "_notify_job") as notify:
            job = self._run("abc12345", notify)
        self.assertEqual(job["status"], "done")
        notify.assert_called_once_with(job)

    def test_notify_exception_is_contained(self):
        job = self._run("def67890", MagicMock(side_effect=RuntimeError("down")))
        self.assertEqual(job["status"], "done")


if __name__ == "__main__":
    unittest.main()
