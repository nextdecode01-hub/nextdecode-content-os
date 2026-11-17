"""Optional vision-based relevance review for selected visual assets.

This is disabled by default.  It only runs when ``VISION_REVIEW_PROVIDER`` is
set to a supported provider and the corresponding key is present.  The lexical
validator in :mod:`app.visuals.chain` remains the offline default.
"""
from __future__ import annotations

import base64
import json
import os
from email.utils import parsedate_to_datetime
import re
import subprocess
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

SUPPORTED_PROVIDERS = {"gemini", "groq"}
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
_GROQ_REVIEW_LOCK = threading.Lock()
_LAST_GROQ_REVIEW_AT = 0.0
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def _provider() -> str:
    return os.getenv("VISION_REVIEW_PROVIDER", "").strip().lower()


def _key() -> str:
    name = "GROQ_API_KEY" if _provider() == "groq" else "GEMINI_API_KEY"
    return os.getenv(name, "").strip()


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
        "You are reviewing one visual asset for a premium vertical technology short.\n"
        f"Narration beat: {scene.get('narration', '')}\n"
        f"Visual intent: {scene.get('visual_intent', scene.get('visual_purpose', ''))}\n"
        f"Intended purpose: {scene.get('visual_purpose', '')}\n"
        f"Scene type: {scene.get('scene_type', '')}\n"
        f"Provider: {asset.get('provider', '')}\n"
        f"Search query: {asset.get('query', '')}\n"
        f"Asset metadata (context only, not proof): {asset.get('title', '')} {asset.get('description', '')} {asset.get('tags', '')}\n\n"
        "Inspect the visible pixels, not the title or search query. Decide whether "
        "the actual subject and action support this exact narration beat. Also judge "
        "whether the frame is usable in a polished short: clear subject, sufficient "
        "detail, sensible exposure, no obvious watermark/UI clutter, and suitable "
        "composition. Do not infer unseen content. Return strict JSON with keys "
        '"relevance" (high/medium/low), "quality" (high/medium/low), and "reason" (short).'
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
    quality = str(payload.get("quality") or "unknown").lower()
    if quality not in {"high", "medium", "low", "unknown"}:
        quality = "unknown"
    return {
        "relevance": relevance,
        "quality": quality,
        "reason": str(payload.get("reason") or "")[:240],
    }




def _post_with_backoff(url: str, *, headers: dict, json_body: dict, timeout: int) -> tuple[object | None, int]:
    """Retry transient vision API failures with bounded exponential backoff.

    429 and transient 5xx responses are retried; permanent 4xx responses are
    returned immediately. The final attempt count is surfaced to callers.
    """
    retries = max(0, min(5, int(os.getenv("VISION_REVIEW_MAX_RETRIES", "3"))))
    base = max(0.1, min(10.0, float(os.getenv("VISION_REVIEW_BACKOFF_SECONDS", "2"))))
    maximum = max(base, min(30.0, float(os.getenv("VISION_REVIEW_MAX_BACKOFF_SECONDS", "20"))))
    attempts = 0
    for attempt in range(retries + 1):
        attempts = attempt + 1
        try:
            response = requests.post(url, headers=headers, json=json_body, timeout=timeout)
        except Exception:
            if attempt >= retries:
                return None, attempts
            time.sleep(min(maximum, base * (2 ** attempt)))
            continue
        status = int(response.status_code)
        if 200 <= status < 300 or (status < 500 and status != 429) or attempt >= retries:
            return response, attempts
        retry_after = response.headers.get("Retry-After") if getattr(response, "headers", None) else None
        delay = base * (2 ** attempt)
        if retry_after:
            try:
                delay = float(retry_after)
            except (TypeError, ValueError):
                try:
                    retry_at = parsedate_to_datetime(str(retry_after))
                    delay = retry_at.timestamp() - time.time()
                except (TypeError, ValueError, OverflowError):
                    delay = base * (2 ** attempt)
        time.sleep(max(0.0, min(maximum, delay)))
    return None, attempts


def _review_groq(scene: dict, asset: dict, image_bytes: bytes, mime_type: str, timeout: int) -> dict:
    """Use Groq's free-tier Qwen vision model through its OpenAI-compatible API."""
    global _LAST_GROQ_REVIEW_AT
    model = os.getenv("VISION_REVIEW_MODEL", "").strip() or DEFAULT_GROQ_MODEL
    image_data = base64.b64encode(image_bytes).decode("ascii")
    body = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": _prompt(scene, asset)},
                {"type": "image_url", "image_url": {
                    "url": f"data:{mime_type};base64,{image_data}"
                }},
            ],
        }],
        "temperature": 0,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {_key()}",
        "Content-Type": "application/json",
    }
    try:
        with _GROQ_REVIEW_LOCK:
            minimum_interval = max(0.0, float(os.getenv("GROQ_VISION_MIN_INTERVAL_SECONDS", "20")))
            wait = minimum_interval - (time.monotonic() - _LAST_GROQ_REVIEW_AT)
            if _LAST_GROQ_REVIEW_AT and wait > 0:
                time.sleep(wait)
            response, attempts = _post_with_backoff(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json_body=body, timeout=timeout,
            )
            _LAST_GROQ_REVIEW_AT = time.monotonic()
    except Exception as exc:
        return {"checked": False, "status": "unavailable", "attempts": 0,
                "reason": f"vision request failed ({type(exc).__name__})"}
    if response is None:
        return {"checked": False, "status": "unavailable", "attempts": attempts,
                "reason": "vision request failed after bounded retries"}
    if not (200 <= response.status_code < 300):
        status = "rate_limited" if response.status_code == 429 else "unavailable"
        return {"checked": False, "status": status, "attempts": attempts,
                "reason": f"vision provider HTTP {response.status_code}"}
    try:
        payload = response.json()
        text = payload["choices"][0]["message"]["content"]
    except Exception:
        return {"checked": False, "status": "invalid_response", "attempts": attempts,
                "reason": "vision provider returned an unexpected payload"}
    parsed = _parse(text)
    if not parsed:
        return {"checked": False, "status": "invalid_response", "attempts": attempts,
                "reason": "vision provider returned no usable verdict"}
    return {
        "checked": True,
        "status": "reviewed",
        "attempts": attempts,
        "provider": "groq",
        "model": model,
        "relevance": parsed["relevance"],
        "quality": parsed["quality"],
        "reason": parsed["reason"],
    }


def review_asset(scene: dict, asset: dict, *, timeout: int = 60) -> dict:
    """Return a vision-review result, or a checked=False reason.

    Providers are opt-in.  Logs must never include the request URL or key.
    """
    provider = _provider()
    if provider in {"", "off", "none"}:
        return {"checked": False, "status": "disabled", "attempts": 0, "reason": "vision review disabled"}
    if provider not in SUPPORTED_PROVIDERS:
        return {"checked": False, "status": "unsupported", "attempts": 0, "reason": f"unsupported vision provider: {provider}"}
    if not _key():
        return {"checked": False, "status": "unavailable", "attempts": 0, "reason": "vision provider key missing"}
    path = Path(str(asset.get("path") or ""))
    frame = _first_frame(path)
    if not frame:
        return {"checked": False, "status": "unavailable", "attempts": 0, "reason": "could not extract an image frame"}
    image_bytes, mime_type = frame
    if provider == "groq":
        return _review_groq(scene, asset, image_bytes, mime_type, timeout)
    model = os.getenv("VISION_REVIEW_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={_key()}"
    )
    body = {
        "contents": [{
            "parts": [
                {"text": _prompt(scene, asset)},
                {"inlineData": {"mimeType": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii")}},
            ]
        }],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    try:
        response, attempts = _post_with_backoff(
            url, headers={}, json_body=body, timeout=timeout,
        )
    except Exception as exc:
        return {"checked": False, "status": "unavailable", "attempts": 0,
                "reason": f"vision request failed ({type(exc).__name__})"}
    if response is None:
        return {"checked": False, "status": "unavailable", "attempts": attempts,
                "reason": "vision request failed after bounded retries"}
    if not (200 <= response.status_code < 300):
        status = "rate_limited" if response.status_code == 429 else "unavailable"
        detail = re.sub(r"\s+", " ", str(getattr(response, "text", "") or ""))[:360]
        return {"checked": False, "status": status, "attempts": attempts,
                "reason": f"vision provider HTTP {response.status_code}: {detail}"}
    try:
        payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return {"checked": False, "status": "invalid_response", "attempts": attempts,
                "reason": "vision provider returned an unexpected payload"}
    parsed = _parse(text)
    if not parsed:
        return {"checked": False, "status": "invalid_response", "attempts": attempts,
                "reason": "vision provider returned no usable verdict"}
    return {
        "checked": True,
        "status": "reviewed",
        "attempts": attempts,
        "provider": provider,
        "model": model,
        "relevance": parsed["relevance"],
        "quality": parsed["quality"],
        "reason": parsed["reason"],
    }
