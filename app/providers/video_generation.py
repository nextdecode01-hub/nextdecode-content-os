"""Provider adapters for optional video-generation services.

All generation calls are guarded before network I/O. The module supports the
official Kling API, Google Veo via Vertex AI, and the official Runway API.
It normalizes task creation/status/download while leaving editorial decisions
and FFmpeg assembly to the existing production pipeline.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from .video_generation_guard import authorize_video_generation


class VideoProviderError(RuntimeError):
    pass


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _require_https(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise VideoProviderError("provider returned a non-HTTPS media URL")
    return url


def _save_remote_video(url: str, output_path: str | Path, timeout: int = 120) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(_require_https(url), timeout=timeout, stream=True)
    response.raise_for_status()
    temp = target.with_suffix(target.suffix + ".part")
    with temp.open("wb") as handle:
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                handle.write(chunk)
    if not temp.is_file() or temp.stat().st_size == 0:
        temp.unlink(missing_ok=True)
        raise VideoProviderError("provider video download was empty")
    temp.replace(target)
    return target


class KlingVideoProvider:
    provider = "kling"
    base_url = "https://api-singapore.klingai.com"

    def __init__(self, api_key: str | None = None, session=None):
        self.api_key = (api_key or os.getenv("KLING_API_KEY", "")).strip()
        self.session = session or requests

    def configured(self) -> bool:
        return bool(self.api_key)

    def create_text_to_video(self, prompt: str, *, model: str = "kling-2.5-turbo",
                             duration: int = 5, aspect_ratio: str = "9:16",
                             resolution: str = "1080p", timeout: int = 45) -> dict:
        authorize_video_generation(route="direct_provider_apis")
        if not self.configured():
            raise VideoProviderError("KLING_API_KEY is not configured")
        if not prompt.strip() or duration not in {5, 10} or aspect_ratio not in {"9:16", "16:9", "1:1"}:
            raise ValueError("invalid Kling prompt, duration, or aspect ratio")
        endpoint = f"{self.base_url}/text-to-video/{model}"
        payload = {"prompt": prompt, "settings": {"resolution": resolution, "aspect_ratio": aspect_ratio,
                   "duration": duration, "audio": "off"}}
        response = self.session.post(endpoint, headers=_headers(self.api_key), json=payload, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        data = body.get("data") if isinstance(body, dict) else None
        task_id = (data or {}).get("id") or (data or {}).get("task_id") or body.get("task_id")
        if not task_id:
            raise VideoProviderError("Kling response did not contain task id")
        return {"provider": self.provider, "task_id": str(task_id), "status": (data or {}).get("status", "submitted"),
                "model": model, "request_id": body.get("request_id")}

    def get_task(self, task_id: str, *, timeout: int = 30) -> dict:
        if not self.configured():
            raise VideoProviderError("KLING_API_KEY is not configured")
        from urllib.parse import quote
        response = self.session.get(f"{self.base_url}/tasks?task_ids={quote(str(task_id), safe='')}",
            headers=_headers(self.api_key), timeout=timeout)
        response.raise_for_status()
        body = response.json()
        rows = body.get("data") if isinstance(body, dict) else []
        data = rows[0] if isinstance(rows, list) and rows else {}
        outputs = data.get("outputs") or []
        video = next((item for item in outputs if item.get("type") == "video"), {})
        status = data.get("status", "unknown")
        return {"provider": self.provider, "task_id": task_id,
                "status": "completed" if status == "succeeded" else status,
                "video_url": video.get("url"), "raw_status": data}

    def download(self, task: dict, output_path: str | Path) -> Path:
        url = task.get("video_url")
        if not url:
            raise VideoProviderError("Kling task has no completed video URL")
        return _save_remote_video(url, output_path)


class RunwayVideoProvider:
    provider = "runway"
    base_url = "https://api.dev.runwayml.com"
    api_version = "2024-11-06"

    def __init__(self, api_key: str | None = None, session=None):
        self.api_key = (api_key or os.getenv("RUNWAY_API_KEY", "")).strip()
        self.session = session or requests

    def configured(self) -> bool:
        return bool(self.api_key)

    def create_text_to_video(self, prompt: str, *, model: str = "gen4.5",
                             duration: int = 5, ratio: str = "720:1280",
                             timeout: int = 45) -> dict:
        authorize_video_generation(route="unified_gateway")
        if not self.configured():
            raise VideoProviderError("RUNWAY_API_KEY is not configured")
        if not prompt.strip() or not 2 <= duration <= 10:
            raise ValueError("invalid Runway prompt or duration")
        payload = {"model": model, "promptText": prompt, "duration": duration, "ratio": ratio}
        response = self.session.post(f"{self.base_url}/v1/text_to_video",
            headers={**_headers(self.api_key), "X-Runway-Version": self.api_version},
            json=payload, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        task_id = body.get("id") or body.get("task_id")
        if not task_id:
            raise VideoProviderError("Runway response did not contain task id")
        return {"provider": self.provider, "task_id": str(task_id), "status": "submitted", "model": model}

    def get_task(self, task_id: str, *, timeout: int = 30) -> dict:
        if not self.configured():
            raise VideoProviderError("RUNWAY_API_KEY is not configured")
        response = self.session.get(f"{self.base_url}/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {self.api_key}", "X-Runway-Version": self.api_version},
            timeout=timeout)
        response.raise_for_status()
        body = response.json()
        output = body.get("output") or []
        first = output[0] if isinstance(output, list) and output else None
        url = body.get("video_url") or (first if isinstance(first, str) else (first.get("url") if isinstance(first, dict) else None))
        status = str(body.get("status", "unknown")).lower()
        if status in {"succeeded", "success"}:
            status = "completed"
        return {"provider": self.provider, "task_id": task_id, "status": status,
                "video_url": url, "raw_status": body}

    def download(self, task: dict, output_path: str | Path) -> Path:
        if not task.get("video_url"):
            raise VideoProviderError("Runway task has no completed video URL")
        return _save_remote_video(task["video_url"], output_path)


class GoogleVeoProvider:
    """Veo adapter using Vertex AI credentials; Gemini API key alone is not enough."""

    provider = "google_veo"

    def __init__(self, project: str | None = None, location: str | None = None):
        self.project = (project or os.getenv("GOOGLE_CLOUD_PROJECT", "")).strip()
        self.location = (location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")).strip()

    def configured(self) -> bool:
        return bool(self.project and (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"))

    def create_text_to_video(self, prompt: str, *, model: str = "veo-3.1-generate-001",
                             duration: int = 5, aspect_ratio: str = "9:16") -> dict:
        authorize_video_generation(route="direct_provider_apis")
        if not self.configured():
            raise VideoProviderError("Veo requires Google Vertex AI project and application credentials")
        from google import genai
        from google.genai import types
        client = genai.Client(vertexai=True, project=self.project, location=self.location)
        operation = client.models.generate_videos(model=model,
            source=types.GenerateVideosSource(prompt=prompt),
            config=types.GenerateVideosConfig(number_of_videos=1, duration_seconds=duration, aspect_ratio=aspect_ratio))
        return {"provider": self.provider, "task_id": getattr(operation, "name", ""),
                "status": "submitted", "model": model, "operation": operation, "_client": client}

    def poll(self, task: dict, *, interval_seconds: int = 10, max_wait_seconds: int = 900) -> dict:
        operation, client = task.get("operation"), task.get("_client")
        if operation is None or client is None:
            raise VideoProviderError("Veo operation handle is missing; persist the SDK operation name for recovery")
        deadline = time.monotonic() + max_wait_seconds
        while not operation.done and time.monotonic() < deadline:
            time.sleep(max(1, interval_seconds))
            operation = client.operations.get(operation)
        if not operation.done:
            return {**task, "status": "processing"}
        response = operation.response
        generated = response.generated_videos[0]
        return {**task, "status": "completed", "video": generated.video, "response": response}

    def download(self, task: dict, output_path: str | Path) -> Path:
        video = task.get("video")
        if video is None:
            raise VideoProviderError("Veo task has no completed video object")
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        saver = getattr(video, "save", None)
        if not callable(saver):
            raise VideoProviderError("Veo SDK video object does not expose save(path)")
        saver(str(target))
        if not target.is_file() or target.stat().st_size == 0:
            raise VideoProviderError("Veo video download was empty")
        return target
