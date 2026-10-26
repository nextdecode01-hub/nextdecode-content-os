#!/usr/bin/env python3
"""
Direct YouTube Uploader for Nextdecode
Uploads generated shorts to YouTube using official Google API client.
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

import google.auth.transport.requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env", override=True)

CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
TOKEN_FILE = SCRIPT_DIR / "youtube_token.json"

def get_authenticated_service():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError("youtube_token.json not found!")
    
    token_data = json.loads(TOKEN_FILE.read_text())
    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    if creds.expired and creds.refresh_token:
        print("[*] Refreshing access token...")
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        # Update token file
        token_data["access_token"] = creds.token
        TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
        print("[+] Token refreshed successfully.")

    return build("youtube", "v3", credentials=creds)

def upload_video(video_path: str, title: str, description: str, tags: list):
    print(f"[*] Starting upload of '{video_path}' to YouTube...")
    youtube = get_authenticated_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28"  # Science & Technology
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(video_path, chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[*] Uploaded {int(status.progress() * 100)}%")
    video_id = response.get("id")
    print(f"\n[SUCCESS] Video Uploaded to YouTube!")
    print(f"Video URL: https://youtube.com/shorts/{video_id}")
    return response

def content_fingerprint(data: dict) -> str:
    content = "\n".join([str(data.get("title", "")), str(data.get("voice_text", ""))]).strip().lower()
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_upload_ledger(path: Path) -> dict:
    if not path.exists():
        return {"fingerprints": {}}
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(ledger, dict) or not isinstance(ledger.get("fingerprints"), dict):
        raise RuntimeError("Upload ledger is invalid; refusing a possibly duplicate upload.")
    return ledger


def save_upload_ledger(path: Path, ledger: dict):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    os.replace(temporary, path)


if __name__ == "__main__":
    meta_file = SCRIPT_DIR / "metadata.json"
    video_file = SCRIPT_DIR / "output_short.mp4"
    ledger_file = SCRIPT_DIR / "uploaded_content.json"
    if not meta_file.exists() or not video_file.exists() or video_file.stat().st_size < 150_000:
        raise SystemExit("Metadata or a valid rendered video is missing; upload skipped.")

    data = json.loads(meta_file.read_text(encoding="utf-8"))
    platform_copy = data.get("platform_copy", {})
    if not isinstance(platform_copy, dict):
        platform_copy = {}
    title = str(platform_copy.get("youtube_title", data.get("title", ""))).strip()
    tags = data.get("tags", ["#Nextdecode", "#AI", "#Tech", "#shorts"])
    if not title or not isinstance(tags, list):
        raise SystemExit("Video metadata is invalid; upload skipped.")

    fingerprint = content_fingerprint(data)
    ledger = load_upload_ledger(ledger_file)
    previous = ledger["fingerprints"].get(fingerprint)
    if previous:
        print(json.dumps({"status": "skipped_duplicate", "video_url": previous.get("video_url", "")}))
        raise SystemExit(0)

    sources = data.get("source_urls", [])
    description = str(platform_copy.get("youtube_description", "")).strip()
    if not description:
        description = "Subscribe to Nextdecode for practical AI and technology explainers."
    if sources:
        description += "\n\nSources:\n" + "\n".join(str(url) for url in sources[:5])
    description = description[:5000]

    response = upload_video(str(video_file), title, description, tags)
    video_id = response.get("id")
    ledger["fingerprints"][fingerprint] = {
        "title": title,
        "content_pillar": data.get("content_pillar", ""),
        "hook": data.get("hook", ""),
        "video_id": video_id,
        "video_url": f"https://youtube.com/shorts/{video_id}" if video_id else "",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    save_upload_ledger(ledger_file, ledger)
    print(json.dumps({"status": "success", "title": title, "video_id": video_id}))



