#!/usr/bin/env python3
"""Upload the approved long-form package to YouTube, with duplicate protection."""
from __future__ import annotations
import hashlib
import json
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from app.publish.youtube_upload import get_authenticated_service, load_upload_ledger, save_upload_ledger
from app.publish.authorization import authorize_publish, authorization_error, verify_protected_action_decision
from app.publish.artifact_snapshot import ArtifactIntegrityError, upload_snapshot
from googleapiclient.http import MediaFileUpload
from app.notifications.notify_status import send_status
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Upload an approved long-form package to YouTube")
    parser.add_argument("--scheduled-approved", action="store_true", help="Restrict this run to the scheduled 20:00 IST window")
    parser.add_argument("--destination", default=None, help="private (default), unlisted, or public with an owner public-release authorization")
    parser.add_argument("--dry-run", action="store_true", help="Validate authorization without uploading")
    args = parser.parse_args(argv)
    metadata_file = ROOT / "data" / "longform_metadata.json"
    video_file = ROOT / "outputs" / "output_longform.mp4"
    # ND-ENG-006-R7 (P0): the owner-release authorization is required for every
    # long-form publish attempt regardless of the scheduling flag; the flag is
    # only a restriction (the 20:00 IST window) and is handled via require_window.
    if os.getenv("PUBLISH_MODE", "review").strip().lower() != "publish" or os.getenv("AUTO_PUBLISH_APPROVED", "false").strip().lower() != "true":
        print(json.dumps({"status": "blocked_approval", "reason": "Long-form publishing is review-only."}))
        return 2
    try:
        decision = authorize_publish(
            platform="youtube_longform", purpose="longform", data_root=ROOT,
            metadata_file=metadata_file, video_file=video_file,
            destination=args.destination, require_window=args.scheduled_approved)
    except Exception as exc:
        code, reason = authorization_error(exc)
        return blocked(reason, args.scheduled_approved, code)
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "uploaded": False,
                          "destination": decision["destination"]}))
        return 0
    data = json.loads(metadata_file.read_text(encoding="utf-8"))
    ledger_file = ROOT / "data" / "uploaded_longform_content.json"
    ledger = load_upload_ledger(ledger_file)
    fingerprint = hashlib.sha256((str(data.get("title", "")) + "\n" + str(data.get("voice_text", ""))).lower().encode("utf-8")).hexdigest()
    if fingerprint in ledger["fingerprints"]:
        print(json.dumps({"status": "skipped_duplicate", "video_url": ledger["fingerprints"][fingerprint].get("video_url", "")}))
        return 0
    # ND-M3-F1: bind the authorized digest to the exact bytes uploaded; the
    # resumable chunks read from the immutable snapshot, not the live path.
    try:
        verify_protected_action_decision(decision, platform="youtube_longform", purpose="longform")
        with upload_snapshot(video_file, decision["video_sha256"], root=ROOT) as snapshot:
            youtube = get_authenticated_service()
            body = {"snippet": {"title": str(data.get("title", ""))[:90], "description": str(data.get("description", ""))[:5000], "tags": data.get("tags", []), "categoryId": "28"}, "status": {"privacyStatus": decision["destination"], "selfDeclaredMadeForKids": False}}
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(snapshot.path), chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4"))
            response = None
            while response is None:
                _, response = request.next_chunk()
    except ArtifactIntegrityError as exc:
        # The video changed after authorization; nothing was uploaded.
        print(json.dumps({"status": "blocked_artifact_integrity", "uploaded": False,
                          "reason": str(exc)}))
        return 2
    video_id = response.get("id", "")
    url = f"https://youtube.com/watch?v={video_id}" if video_id else ""
    ledger["fingerprints"][fingerprint] = {"title": data.get("title", ""), "video_id": video_id, "video_url": url, "uploaded_at": datetime.now(timezone.utc).isoformat()}
    try:
        save_upload_ledger(ledger_file, ledger)
    except OSError as exc:
        print(json.dumps({"status": "ambiguous", "uploaded": True, "video_id": video_id,
                          "reason": "the long-form upload succeeded but the local duplicate ledger could not be written; reconcile before retrying",
                          "error": type(exc).__name__}, ensure_ascii=False))
        return 3
    print(json.dumps({"status": "success", "title": data.get("title", ""), "video_id": video_id,
                      "video_url": url, "destination": decision["destination"]}))
    send_status("Nextdecode Studio: today's owner-approved long-form video was uploaded to YouTube: " + url)
    return 0


def blocked(reason: str, scheduled: bool, status: str = "blocked_approval") -> int:
    print(json.dumps({"status": status, "reason": reason}))
    if scheduled:
        send_status("Nextdecode Studio: long-form upload skipped: " + reason)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
