#!/usr/bin/env python3
"""Restricted HTTP bridge from the n8n container to the project pipelines."""
from __future__ import annotations

import hmac
import json
import signal
import os
import subprocess
import sys
import threading
import shutil
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("STUDIO_ROOT", "/home/demon/shorts_studio")).resolve()
MAX_RUNTIME_SECONDS = int(os.environ.get("RUNNER_COMMAND_TIMEOUT_SECONDS", "14400"))
OUTPUT_LIMIT = 8000
EXECUTION_LOCK = threading.Lock()


def _tail(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        output = output.decode("utf-8", errors="replace")
    return output[-OUTPUT_LIMIT:]


class RunnerHandler(BaseHTTPRequestHandler):
    server_version = "NextdecodeRunner"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"runner: {format % args}", flush=True)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _check_dependencies() -> dict:
        """Return a dict of dependency checks for the health endpoint."""
        import importlib.util
        checks = {}

        for cmd in ("ffmpeg", "ffprobe"):
            checks[cmd] = shutil.which(cmd) is not None

        checks["edge-tts"] = shutil.which("edge-tts") is not None

        for mod in ("requests", "dotenv", "faster_whisper"):
            checks[f"py:{mod}"] = importlib.util.find_spec(mod) is not None

        health_file = ROOT / "model_health.json"
        checks["model_health_file"] = health_file.is_file()
        if health_file.is_file():
            import json as _json
            try:
                health = _json.loads(health_file.read_text(encoding="utf-8"))
                providers = health.get("providers", {})
                unhealthy = [n for n, r in providers.items() if not r.get("ok", True)]
                checks["unhealthy_providers"] = unhealthy
                checks["provider_count"] = len(providers)
            except Exception:
                checks["model_health_file"] = False
                checks["unhealthy_providers"] = ["unknown"]

        try:
            usage = shutil.disk_usage(str(ROOT))
            checks["disk_free_gb"] = round(usage.free / (1024 ** 3), 2)
            checks["disk_ok"] = usage.free > 512 * 1024 * 1024
        except Exception:
            checks["disk_ok"] = False

        skip_keys = {"unhealthy_providers", "provider_count", "disk_free_gb"}
        all_ok = all(v for k, v in checks.items() if k not in skip_keys)
        checks["all_ok"] = all_ok
        return checks

    def do_GET(self) -> None:
        if self.path != "/healthz":
            self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found"})
            return
        checks = self._check_dependencies()
        code = HTTPStatus.OK if checks.get("all_ok", False) else HTTPStatus.SERVICE_UNAVAILABLE
        self._send_json(code, {"status": "ok" if checks.get("all_ok") else "degraded", "checks": checks})

    def do_POST(self) -> None:
        commands = {
            "/run/generate": ["/bin/bash", str(ROOT / "run_scheduled_generation.sh")],
            "/run/publish": [sys.executable, str(ROOT / "scheduled_publish.py")],
        }
        command = commands.get(self.path)
        if command is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"status": "not_found"})
            return

        expected_key = os.environ.get("N8N_RUNNER_API_KEY", "")
        authorization = self.headers.get("Authorization", "")
        supplied_key = authorization.removeprefix("Bearer ")
        if not expected_key or not authorization.startswith("Bearer ") or not hmac.compare_digest(
            supplied_key, expected_key
        ):
            self._send_json(HTTPStatus.UNAUTHORIZED, {"status": "unauthorized"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"status": "invalid_content_length"})
            return
        if content_length != 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"status": "request_body_not_supported"})
            return

        if not EXECUTION_LOCK.acquire(blocking=False):
            self._send_json(HTTPStatus.CONFLICT, {"status": "runner_busy"})
            return

        environment = os.environ.copy()
        environment["PUBLISH_MODE"] = "review"
        environment["SHORTS_STUDIO_PYTHON"] = os.environ.get(
            "SHORTS_STUDIO_PYTHON", sys.executable
        )
        environment["TZ"] = "Asia/Kolkata"
        try:
            try:
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=MAX_RUNTIME_SECONDS,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                self._send_json(
                    HTTPStatus.GATEWAY_TIMEOUT,
                    {
                        "status": "timed_out",
                        "error": f"Pipeline exceeded {MAX_RUNTIME_SECONDS} seconds.",
                        "stdout": _tail(exc.stdout),
                        "stderr": _tail(exc.stderr),
                    },
                )
                return
            except OSError as exc:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"status": "failed_to_start", "error": str(exc)},
                )
                return

            payload = {
                "status": "completed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout": _tail(result.stdout),
                "stderr": _tail(result.stderr),
            }
            # If scheduled_publish skipped cleanly because outside window (exit_code 2), return OK to n8n
            status = (
                HTTPStatus.OK
                if (result.returncode == 0 or result.returncode == 2)
                else HTTPStatus.INTERNAL_SERVER_ERROR
            )
            self._send_json(status, payload)
        finally:
            EXECUTION_LOCK.release()


def _signal_handler(signum, frame):
    '''
    Handle SIGTERM/SIGINT gracefully: stop accepting new requests, close server.
    '''
    import signal
    import sys
    print("Received signal", signum, "-- shutting down...", flush=True)
    try:
        server.shutdown()
    except Exception:
        pass
    finally:
        server.server_close()
        EXECUTION_LOCK.acquire()
        EXECUTION_LOCK.release()
    sys.exit(0)


def main() -> int:
    api_key = os.environ.get("N8N_RUNNER_API_KEY", "")
    if len(api_key) < 64:
        print("N8N_RUNNER_API_KEY must be a 64-character random hex value.", file=sys.stderr)
        return 2
    if not ROOT.is_dir():
        print(f"Project directory does not exist: {ROOT}", file=sys.stderr)
        return 2
    for required in ("run_scheduled_generation.sh", "scheduled_publish.py"):
        if not (ROOT / required).is_file():
            print(f"Required project file is missing: {ROOT / required}", file=sys.stderr)
            return 2

    server = ThreadingHTTPServer(("0.0.0.0", 8080), RunnerHandler)
    server.daemon_threads = True

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    print("Runner ready on port 8080.", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        EXECUTION_LOCK.acquire()
        EXECUTION_LOCK.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

