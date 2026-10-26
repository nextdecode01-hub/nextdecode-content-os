import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import n8n_runner


API_KEY = "a" * 64


class TestRunnerEndpoint:
    def setup_method(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), n8n_runner.RunnerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def teardown_method(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, headers=None):
        request = urllib.request.Request(
            self.base_url + path,
            data=b"" if method == "POST" else None,
            headers=headers or {},
            method=method,
        )
        return urllib.request.urlopen(request, timeout=2)

    def test_health_endpoint_returns_checks(self):
        try:
            response = self.request("GET", "/healthz")
        except urllib.error.HTTPError as error:
            assert error.code == 503
            response = error
        with response:
            assert response.status in (200, 503)
            payload = json.load(response)
            assert "status" in payload
            assert "checks" in payload
            checks = payload["checks"]
            assert "ffmpeg" in checks
            assert "ffprobe" in checks
            assert "edge-tts" in checks

    def test_run_endpoint_requires_bearer_key(self):
        with patch.dict(os.environ, {"N8N_RUNNER_API_KEY": API_KEY}):
            with patch("n8n_runner.subprocess.run") as run:
                try:
                    self.request("POST", "/run/generate")
                except urllib.error.HTTPError as error:
                    assert error.code == 401
                    assert json.load(error) == {"status": "unauthorized"}
                else:
                    raise AssertionError("An unauthenticated run request was accepted.")
                run.assert_not_called()

    def test_generation_route_runs_only_review_mode(self):
        project_root = Path("/tmp/shorts-studio-test")
        result = CompletedProcess(args=[], returncode=0, stdout="queued", stderr="")
        with (
            patch.object(n8n_runner, "ROOT", project_root),
            patch.dict(os.environ, {"N8N_RUNNER_API_KEY": API_KEY}),
            patch("n8n_runner.subprocess.run", return_value=result) as run,
        ):
            with self.request(
                "POST",
                "/run/generate",
                headers={"Authorization": f"Bearer {API_KEY}"},
            ) as response:
                payload = json.load(response)

        assert payload["status"] == "completed"
        args, kwargs = run.call_args
        assert args[0] == ["/bin/bash", str(project_root / "run_scheduled_generation.sh")]
        assert kwargs["cwd"] == project_root
        assert kwargs["env"]["PUBLISH_MODE"] == "review"
        assert kwargs["env"]["SHORTS_STUDIO_PYTHON"] == sys.executable
        assert kwargs.get("shell", False) is False
        assert kwargs["timeout"] == n8n_runner.MAX_RUNTIME_SECONDS

    def test_runner_reports_pipeline_errors(self):
        project_root = Path("/tmp/shorts-studio-test")
        result = CompletedProcess(args=[], returncode=3, stdout="", stderr="render failed")
        with (
            patch.object(n8n_runner, "ROOT", project_root),
            patch.dict(os.environ, {"N8N_RUNNER_API_KEY": API_KEY}),
            patch("n8n_runner.subprocess.run", return_value=result),
        ):
            try:
                self.request(
                    "POST",
                    "/run/publish",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                )
            except urllib.error.HTTPError as error:
                assert error.code == 500
                payload = json.load(error)
            else:
                raise AssertionError("A failed pipeline returned a success status.")

        assert payload["status"] == "failed"
        assert payload["exit_code"] == 3
        assert payload["stderr"] == "render failed"
