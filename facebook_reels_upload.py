#!/usr/bin/env python3
"""Publish the current rendered MP4 as a Facebook Page Reel using Meta's API."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)
VIDEO = ROOT / "output_short.mp4"
METADATA = ROOT / "metadata.json"
LEDGER = ROOT / "meta_uploads.json"


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name} in the project .env; Facebook Reel upload skipped.")
    return value


def api_json(response: requests.Response) -> dict:
    try:
        payload = response.json()
    except ValueError:
        response.raise_for_status()
        raise RuntimeError("Meta returned a response that was not JSON.")
    if not response.ok or "error" in payload:
        error = payload.get("error", {})
        message = error.get("message", "Meta Graph API request failed") if isinstance(error, dict) else str(error)
        raise RuntimeError(f"Meta Graph API error: {message}")
    return payload


def content_fingerprint(metadata: dict) -> str:
    raw = "\n".join((str(metadata.get("title", "")), str(metadata.get("voice_text", ""))))
    return hashlib.sha256(raw.strip().lower().encode("utf-8")).hexdigest()


def read_ledger() -> dict:
    if not LEDGER.exists():
        return {"facebook": {}}
    value = json.loads(LEDGER.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("facebook", {}), dict):
        raise RuntimeError("Meta upload ledger is invalid; refusing a possible duplicate post.")
    value.setdefault("facebook", {})
    return value


def save_ledger(value: dict) -> None:
    temporary = LEDGER.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    os.replace(temporary, LEDGER)


def publish() -> dict:
    graph_version = require_env("META_GRAPH_API_VERSION")
    page_id = require_env("FACEBOOK_PAGE_ID")
    page_token = require_env("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not METADATA.exists() or not VIDEO.exists() or VIDEO.stat().st_size < 150_000:
        raise RuntimeError("A valid generated MP4 and metadata.json are required; Facebook upload skipped.")

    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    platform_copy = metadata.get("platform_copy", {})
    if not isinstance(platform_copy, dict):
        platform_copy = {}
    title = str(platform_copy.get("facebook_title", metadata.get("title", ""))).strip()
    if not title:
        raise RuntimeError("Video title is missing; Facebook upload skipped.")
    description = str(platform_copy.get("facebook_description", "")).strip()
    if not description:
        description = " ".join(str(tag) for tag in metadata.get("tags", [])[:8])
    sources = metadata.get("source_urls", [])
    if sources:
        description += "\n\nSources: " + " ".join(str(url) for url in sources[:5])
    description = description[:5000]

    fingerprint = f"{page_id}:{content_fingerprint(metadata)}"
    ledger = read_ledger()
    if fingerprint in ledger["facebook"]:
        previous = ledger["facebook"][fingerprint]
        print(json.dumps({"status": "skipped_duplicate", "video_id": previous.get("video_id", "")}))
        return {"status": "skipped_duplicate"}

    base = f"https://graph.facebook.com/{graph_version}"
    session = api_json(requests.post(
        f"{base}/{page_id}/video_reels",
        params={"upload_phase": "start"},
        headers={"Authorization": f"Bearer {page_token}"},
        timeout=30,
    ))
    video_id = session.get("video_id")
    upload_url = session.get("upload_url")
    if not video_id or not upload_url:
        raise RuntimeError("Meta did not return a Reel upload session.")

    size = VIDEO.stat().st_size
    with VIDEO.open("rb") as stream:
        uploaded = requests.post(
            upload_url,
            data=stream,
            headers={
                "Authorization": f"OAuth {page_token}",
                "offset": "0",
                "file_size": str(size),
                "Content-Type": "application/octet-stream",
            },
            timeout=(30, 600),
        )
    try:
        upload_result = uploaded.json()
    except ValueError:
        upload_result = {}
    if not uploaded.ok or upload_result.get("success") is not True:
        api_json(uploaded)
        raise RuntimeError("Meta did not confirm the Reel video upload.")

    finished = api_json(requests.post(
        f"{base}/{page_id}/video_reels",
        params={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description,
            "title": title[:100],
        },
        headers={"Authorization": f"Bearer {page_token}"},
        timeout=30,
    ))
    if finished.get("success") is not True:
        raise RuntimeError("Meta did not confirm Reel publishing.")

    ledger["facebook"][fingerprint] = {
        "video_id": video_id,
        "title": title,
        "content_pillar": metadata.get("content_pillar", ""),
        "hook": metadata.get("hook", ""),
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    save_ledger(ledger)
    print(json.dumps({"status": "published", "video_id": video_id, "title": title}))
    return {"status": "published", "video_id": video_id}


if __name__ == "__main__":
    try:
        publish()
    except Exception as exc:
        print(f"Facebook Reel publish failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)




