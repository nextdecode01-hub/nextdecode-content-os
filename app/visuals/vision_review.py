"""Optional vision-based relevance review for selected visual assets.

This is disabled by default.  It only runs when ``VISION_REVIEW_PROVIDER`` is
set to a supported provider and the corresponding key is present.  The lexical
validator in :mod:`app.visuals.chain` remains the offline default.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
from pathlib import Path

import requests

SUPPORTED_PROVIDERS = {"gemini"}
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def _provider() -> str:
    return os.getenv("VISION_REVIEW_PROVIDER", "").strip().lower()


def _key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def enabled() -> bool:
    return _provider() in SUPPORTED_PROVIDERS and bool(_key())


def _first_frame(path: Path) -> tuple[bytes, str] | None:
    path = Path(path)
    if not path.is_file():
        return None
    if path.suffix.lower() in IMAGE_SUFFIXES:
        try:
            return path.read_bytes(), "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        except OSError:
            return None
    try:
        completed = subprocess.run(
            [
                "ffmpeg", "-v", "error", "-ss", "0.5", "-i", str(path),
                "-frames:v", "1", "-f", "image2pipe", "-vcodec", "mjpeg", "-",
            ],
            capture_output=True,
            timeout=60,
        )
    except Exception:
        return None
    if completed.returncode != 0 or not completed.stdout:
        return None
    return completed.stdout, "image/jpeg"


def _prompt(scene: dict, asset: dict) -> str:
    return (
        "You are reviewing one visual for a vertical short video.\n"
        f"Narration beat: {scene.get('narration', '')}\n"
        f"Intended purpose: {scene.get('visual_purpose', '')}\n"
        f"Scene type: {scene.get('scene_type', '')}\n"
        f"Provider: {asset.get('provider', '')}\n"
        f"Search query: {asset.get('query', '')}\n"
        f"Title/tags: {asset.get('title', '')} {asset.get('tags', '')}\n\n"
        "Judge only whether the visible image plausibly supports the narration "
        "beat. Ignore style and production quality. Return strict JSON with keys "
        '"relevance" (high/medium/low) and "reason" (short).'
    )


def _parse(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", str(text or "").strip(), flags=re.M).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    relevance = str(payload.get("relevance") or "").lower()
    if relevance not in {"high", "medium", "low"}:
        return {}
    return {"relevance": relevance, "reason": str(payload.get("reason") or "")[:240]}


def review_asset(scene: dict, asset: dict, *, timeout: int = 60) -> dict:
    """Return a vision-review result, or a checked=False reason.

    Providers are opt-in.  Logs must never include the request URL or key.
    """
    provider = _provider()
    if provider in {"", "off", "none"}:
        return {"checked": False, "reason": "vision review disabled"}
    if provider not in SUPPORTED_PROVIDERS:
        return {"checked": False, "reason": f"unsupported vision provider: {provider}"}
    if not _key():
        return {"checked": False, "reason": "vision provider key missing"}
    path = Path(str(asset.get("path") or ""))
    frame = _first_frame(path)
    if not frame:
        return {"checked": False, "reason": "could not extract an image frame"}
    image_bytes, mime_type = frame
    model = os.getenv("VISION_REVIEW_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={_key()}"
    )
    body = {
        "contents": [{
            "parts": [
                {"text": _prompt(scene, asset)},
                {"inline_data": {"mime_type": mime_type,
                                 "data": base64.b64encode(image_bytes).decode("ascii")}},
            ]
        }],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    try:
        response = requests.post(url, json=body, timeout=timeout)
    except Exception as exc:
        return {"checked": False, "reason": f"vision request failed ({type(exc).__name__})"}
    if not (200 <= response.status_code < 300):
        return {"checked": False, "reason": f"vision provider HTTP {response.status_code}"}
    try:
        payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return {"checked": False, "reason": "vision provider returned an unexpected payload"}
    parsed = _parse(text)
    if not parsed:
        return {"checked": False, "reason": "vision provider returned no usable verdict"}
    return {
        "checked": True,
        "provider": provider,
        "model": model,
        "relevance": parsed["relevance"],
        "reason": parsed["reason"],
    }
