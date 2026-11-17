"""Explicit single-provider video generation workflow with local asset QA."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .video_generation import KlingVideoProvider, RunwayVideoProvider, GoogleVeoProvider, VideoProviderError
from .video_generation_guard import (
    VideoGenerationNotAuthorized, authorize_video_generation, load_video_generation_policy,
)


def _provider(name: str):
    providers = {
        "kling": KlingVideoProvider,
        "runway": RunwayVideoProvider,
        "google_veo": GoogleVeoProvider,
    }
    try:
        return providers[name]()
    except KeyError as exc:
        raise ValueError(f"unsupported video provider: {name}") from exc


def wait_for_video_task(provider_name: str, task: dict, *, poll_interval: float = 8.0,
                        max_wait_seconds: float = 900.0, clock=time.monotonic,
                        sleeper=time.sleep) -> dict:
    """Poll one submitted task. Never creates another task or switches provider."""
    provider = _provider(provider_name)
    if provider_name == "google_veo":
        return provider.poll(task, interval_seconds=max(1, int(poll_interval)),
                             max_wait_seconds=int(max_wait_seconds))
    deadline = clock() + max(0.0, max_wait_seconds)
    delay = max(1.0, poll_interval)
    latest = dict(task)
    while clock() < deadline:
        latest = provider.get_task(str(task["task_id"]))
        status = str(latest.get("status", "unknown")).lower()
        if status in {"completed", "failed", "cancelled"}:
            return latest
        sleeper(min(delay, max(0.0, deadline - clock())))
        delay = min(delay * 1.5, 30.0)
    return {**latest, "status": "timeout"}


def _probe_video(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise VideoProviderError("ffprobe is required to qualify generated video assets")
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    payload = json.loads(result.stdout or "{}")
    streams = payload.get("streams") or []
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    if not video:
        raise VideoProviderError("generated asset has no video stream")
    return {
        "codec": video.get("codec_name"),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "fps": video.get("avg_frame_rate") or video.get("r_frame_rate"),
        "duration_seconds": float((payload.get("format") or {}).get("duration") or video.get("duration") or 0),
        "format": (payload.get("format") or {}).get("format_name"),
        "size_bytes": path.stat().st_size,
    }


def generate_video_asset(provider_name: str, prompt: str, output_path: str | Path, *,
                         model: str | None = None, duration: int = 5,
                         aspect_ratio: str = "9:16", run_id: str | None = None,
                         poll_interval: float = 8.0, max_wait_seconds: float = 900.0) -> dict:
    """Submit, poll, download and qualify one explicitly authorized provider clip."""
    # Enforce the zero-budget/owner-approval policy at the only generation entry
    # point, before provider construction or any network-capable operation.
    route = "unified_gateway" if provider_name == "runway" else "direct_provider_apis"
    policy = load_video_generation_policy()
    route_policy = (policy.get("routes") or {}).get(route) or {}
    allowed_providers = route_policy.get("providers") or []
    if provider_name not in allowed_providers:
        raise VideoGenerationNotAuthorized(
            f"provider {provider_name!r} is not allowed on route {route!r}"
        )
    authorization = authorize_video_generation(route=route, policy=policy)
    provider = _provider(provider_name)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    run_id = run_id or str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    if provider_name == "kling":
        task = provider.create_text_to_video(prompt, model=model or "kling-2.5-turbo",
            duration=duration, aspect_ratio=aspect_ratio)
    elif provider_name == "runway":
        ratio = "720:1280" if aspect_ratio == "9:16" else ("1280:720" if aspect_ratio == "16:9" else "960:960")
        task = provider.create_text_to_video(prompt, model=model or "gen4.5",
            duration=duration, ratio=ratio)
    else:
        task = provider.create_text_to_video(prompt, model=model or "veo-3.1-generate-001",
            duration=duration, aspect_ratio=aspect_ratio)
    completed = wait_for_video_task(provider_name, task, poll_interval=poll_interval,
                                    max_wait_seconds=max_wait_seconds)
    if completed.get("status") != "completed":
        raise VideoProviderError(f"video task did not complete: {completed.get('status', 'unknown')}")
    provider.download(completed, target)
    metadata = _probe_video(target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if metadata.get('width', 0) <= 0 or metadata.get('height', 0) <= 0:
        raise VideoProviderError('generated video has invalid dimensions')
    if metadata.get('duration_seconds', 0) <= 0:
        raise VideoProviderError('generated video has invalid duration')
    if aspect_ratio == '9:16' and metadata['height'] <= metadata['width']:
        raise VideoProviderError('generated video does not satisfy requested 9:16 orientation')
    if aspect_ratio == '16:9' and metadata['width'] <= metadata['height']:
        raise VideoProviderError('generated video does not satisfy requested 16:9 orientation')
    if metadata['duration_seconds'] > float(duration) + 2.0:
        raise VideoProviderError('generated video exceeds requested duration tolerance')
    record = {
        "schema": "nextdecode.generated-video-asset.v1",
        "run_id": run_id,
        "provider": provider_name,
        "model": task.get("model") or model,
        "task_id": task.get("task_id"),
        "prompt": prompt,
        "source_url": completed.get("video_url"),
        "local_path": str(target.resolve()),
        "sha256": digest,
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": "qualified",
        "metadata": metadata,
        "visual_role": "generated_broll",
        "requires_editorial_review": True,
        "authorization": {
            "route": authorization.route,
            "budget_usd": authorization.budget_usd,
            "approved": authorization.approved,
            "policy_status": authorization.policy_status,
        },
    }
    sidecar = target.with_suffix(target.suffix + ".asset.json")
    temp = sidecar.with_suffix(sidecar.suffix + ".tmp")
    temp.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    temp.replace(sidecar)
    record["sidecar_path"] = str(sidecar)
    return record
