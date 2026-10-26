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
from approval_integrity import approved_today, sha256_file, upload_window_open
from youtube_upload import get_authenticated_service, load_upload_ledger, save_upload_ledger
from googleapiclient.http import MediaFileUpload
from visual_quality import has_publishable_visuals
from notify_status import send_status

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Upload an approved long-form package to YouTube")
    parser.add_argument("--scheduled-approved", action="store_true", help="Allow scheduled publishing only with a current, matching owner approval")
    args = parser.parse_args(argv)
    if args.scheduled_approved and not upload_window_open():
        reason = "Scheduled publishing is restricted to the 20:00 IST hour."
        print(json.dumps({"status": "blocked_schedule", "reason": reason}))
        send_status("Nextdecode Studio: the long-form upload was skipped because it ran outside the 20:00 IST hour.")
        return 2
    approved = ROOT / "longform_review_approved.json"
    pending = ROOT / "longform_review_pending.json"
    metadata_file = ROOT / "longform_metadata.json"
    video_file = ROOT / "output_longform.mp4"
    if not args.scheduled_approved and (os.getenv("PUBLISH_MODE", "review").strip().lower() != "publish" or os.getenv("AUTO_PUBLISH_APPROVED", "false").strip().lower() != "true"):
        print(json.dumps({"status": "blocked_approval", "reason": "Long-form publishing is review-only."}))
        return 2
    if not approved.exists() or not pending.exists() or not metadata_file.exists() or not video_file.exists():
        return blocked("Approved long-form package or video is missing.", args.scheduled_approved)
    data = json.loads(metadata_file.read_text(encoding="utf-8"))
    approval = json.loads(approved.read_text(encoding="utf-8"))
    package = json.loads(pending.read_text(encoding="utf-8"))
    if (
        approval.get("status") != "approved"
        or package.get("status") != "approved"
        or approval.get("package") != str(pending)
        or approval.get("title") != data.get("title")
        or package.get("title") != data.get("title")
    ):
        return blocked("Approved package does not match current long-form metadata.", args.scheduled_approved)
    if approval.get("approved_at") != package.get("approved_at") or not approved_today(package.get("approved_at")):
        reason = "Approval is missing or expired for today (Asia/Kolkata); review and approve today's video before the upload time."
        return blocked(reason, args.scheduled_approved)
    current_hashes = {
        "metadata_sha256": sha256_file(metadata_file),
        "video_sha256": sha256_file(video_file),
    }
    if any(
        package.get(name) != value or approval.get(name) != value
        for name, value in current_hashes.items()
    ):
        reason = "Approved package does not match the current video and metadata."
        return blocked(reason, args.scheduled_approved)
    if package.get("visuals") != data.get("visuals") or not has_publishable_visuals(data.get("visuals")):
        return blocked("Procedural or unverified visuals are draft-only.", args.scheduled_approved, "blocked_quality")
    ledger_file = ROOT / "uploaded_longform_content.json"
    ledger = load_upload_ledger(ledger_file)
    fingerprint = hashlib.sha256((str(data.get("title", "")) + "\n" + str(data.get("voice_text", ""))).lower().encode("utf-8")).hexdigest()
    if fingerprint in ledger["fingerprints"]:
        print(json.dumps({"status": "skipped_duplicate", "video_url": ledger["fingerprints"][fingerprint].get("video_url", "")}))
        return 0
    youtube = get_authenticated_service()
    body = {"snippet": {"title": str(data.get("title", ""))[:90], "description": str(data.get("description", ""))[:5000], "tags": data.get("tags", []), "categoryId": "28"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(video_file), chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4"))
    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = response.get("id", "")
    url = f"https://youtube.com/watch?v={video_id}" if video_id else ""
    ledger["fingerprints"][fingerprint] = {"title": data.get("title", ""), "video_id": video_id, "video_url": url, "uploaded_at": datetime.now(timezone.utc).isoformat()}
    save_upload_ledger(ledger_file, ledger)
    print(json.dumps({"status": "success", "title": data.get("title", ""), "video_id": video_id, "video_url": url}))
    send_status("Nextdecode Studio: today's owner-approved long-form video was uploaded to YouTube: " + url)
    return 0


def blocked(reason: str, scheduled: bool, status: str = "blocked_approval") -> int:
    print(json.dumps({"status": status, "reason": reason}))
    if scheduled:
        send_status("Nextdecode Studio: long-form upload skipped: " + reason)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
