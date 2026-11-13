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

from app.publish.authorization import authorize_publish, authorization_error, verify_protected_action_decision
from app.publish.artifact_snapshot import ArtifactIntegrityError, upload_snapshot

SCRIPT_DIR = Path(__file__).resolve().parents[2]
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

def upload_video(video_path: str, title: str, description: str, tags: list, *,
                 platform: str = "youtube", purpose: str = "short",
                 destination: str | None = None, metadata_file: str | Path | None = None,
                 data_root: str | Path | None = None):
    """Upload one already-approved video.

    Authorization runs here, not only in the CLI, so a direct library call cannot skip
    the shared governance policy.
    """
    decision = authorize_publish(
        platform=platform,
        purpose=purpose,
        data_root=Path(data_root) if data_root else SCRIPT_DIR,
        metadata_file=metadata_file,
        video_file=Path(video_path),
        destination=destination,
    )
    print(f"[*] Starting upload of '{video_path}' to YouTube "
          f"(destination={decision['destination']})...")
    # ND-M3-F1: bind the authorized digest to the exact bytes transferred.  The
    # snapshot is created (and re-verified) before any network session starts,
    # and the resumable chunks are read from it, not from the mutable live
    # path.  Preservation: authorize_publish above still runs and still decides.
    verify_protected_action_decision(decision, platform=platform, purpose=purpose)
    with upload_snapshot(Path(video_path), decision["video_sha256"],
                         root=Path(data_root) if data_root else SCRIPT_DIR) as snapshot:
        print("[*] Upload artifact digest-verified against the authorized sha256.")
        youtube = get_authenticated_service()
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "28"  # Science & Technology
            },
            "status": {
                "privacyStatus": decision["destination"],
                "selfDeclaredMadeForKids": False
            }
        }
        media = MediaFileUpload(str(snapshot.path), chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4")
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


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in arguments
    destination = None
    if "--destination" in arguments:
        try:
            destination = arguments[arguments.index("--destination") + 1]
        except IndexError:
            print("--destination needs a value (private, unlisted or public).", file=sys.stderr)
            return 2
    meta_file = SCRIPT_DIR / "data" / "metadata.json"
    video_file = SCRIPT_DIR / "outputs" / "output_short.mp4"
    ledger_file = SCRIPT_DIR / "data" / "uploaded_content.json"
    if not meta_file.exists() or not video_file.exists() or video_file.stat().st_size < 150_000:
        print("Metadata or a valid rendered video is missing; upload skipped.", file=sys.stderr)
        return 1

    data = json.loads(meta_file.read_text(encoding="utf-8"))
    platform_copy = data.get("platform_copy", {})
    if not isinstance(platform_copy, dict):
        platform_copy = {}
    title = str(platform_copy.get("youtube_title", data.get("title", ""))).strip()
    tags = data.get("tags", ["#Nextdecode", "#AI", "#Tech", "#shorts"])
    if not title or not isinstance(tags, list):
        print("Video metadata is invalid; upload skipped.", file=sys.stderr)
        return 1

    fingerprint = content_fingerprint(data)
    ledger = load_upload_ledger(ledger_file)
    previous = ledger["fingerprints"].get(fingerprint)
    if previous:
        print(json.dumps({"status": "skipped_duplicate", "video_url": previous.get("video_url", "")}))
        return 0

    sources = data.get("source_urls", [])
    description = str(platform_copy.get("youtube_description", "")).strip()
    if not description:
        description = "Subscribe to Nextdecode for practical AI and technology explainers."
    if sources:
        description += "\n\nSources:\n" + "\n".join(str(url) for url in sources[:5])
    description = description[:5000]

    try:
        decision = authorize_publish(platform="youtube", purpose="short", data_root=SCRIPT_DIR,
                                     metadata_file=meta_file, video_file=video_file,
                                     destination=destination)
    except Exception as exc:
        code, reason = authorization_error(exc)
        print(json.dumps({"status": code, "reason": reason}, ensure_ascii=False))
        return 2

    if dry_run:
        print(json.dumps({"status": "dry_run", "uploaded": False,
                          "destination": decision["destination"], "title": title}))
        return 0

    try:
        response = upload_video(str(video_file), title, description, tags,
                                destination=decision["destination"])
    except ArtifactIntegrityError as exc:
        # ND-M3-F1: the bytes on disk stopped matching the authorized digest
        # between authorization and snapshot.  No upload was started.
        print(json.dumps({"status": "blocked_artifact_integrity", "uploaded": False,
                          "reason": str(exc)}, ensure_ascii=False))
        return 2
    video_id = response.get("id")
    ledger["fingerprints"][fingerprint] = {
        "title": title,
        "content_pillar": data.get("content_pillar", ""),
        "hook": data.get("hook", ""),
        "video_id": video_id,
        "video_url": f"https://youtube.com/shorts/{video_id}" if video_id else "",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        save_upload_ledger(ledger_file, ledger)
    except OSError as exc:
        # The remote upload already happened; a retry would duplicate the video.
        print(json.dumps({"status": "ambiguous", "uploaded": True, "video_id": video_id,
                          "reason": "the upload succeeded but the local duplicate ledger could not be "
                                    "written; reconcile before retrying",
                          "error": type(exc).__name__}, ensure_ascii=False))
        return 3
    print(json.dumps({"status": "success", "title": title, "video_id": video_id,
                      "destination": decision["destination"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



