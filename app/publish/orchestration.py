#!/usr/bin/env python3
"""Preflight and publish one generated Short to every configured destination."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
from app.security.approval_integrity import upload_window_open
from app.publish.authorization import (authorize_publish, authorization_error,
                                   verify_approval_binding)
from app.notifications.notify_status import send_status
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)
PUBLISHERS = {
    "youtube": "app.publish.youtube_upload",
    "facebook": "app.publish.facebook_reels_upload",
    "instagram": "app.publish.instagram_reels_upload",
}
SCRIPT_RANGES = {
    "micro_20s": (42, 58),
    "standard_30s": (62, 78),
    "standard_35s": (72, 92),
    "deep_45s": (96, 118),
    "deep_60s": (170, 210),
}
GENERIC_HOOK_PREFIXES = (
    "today we",
    "in this video",
    "welcome back",
    "did you know",
    "let's talk about",
    "here's what you need to know",
)


def validate_content() -> str:
    metadata_path = ROOT / "data" / "metadata.json"
    video_path = ROOT / "outputs" / "output_short.mp4"
    if not metadata_path.is_file() or not video_path.is_file() or video_path.stat().st_size < 150_000:
        return "Fresh metadata or a rendered video is missing; regenerate before publishing"
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "Generated metadata is invalid; refusing to publish"
    title = str(data.get("title", "")).strip()
    script = str(data.get("voice_text", "")).strip()
    pillar = str(data.get("content_pillar", "")).strip()
    platform_copy = data.get("platform_copy")
    instagram_hashtags = data.get("instagram_hashtags")
    words = len(script.split())
    sources = data.get("source_urls")
    created = data.get("created_at")
    profile = str(data.get("script_profile", "standard_35s")).strip().lower()
    low, high = SCRIPT_RANGES.get(profile, (72, 92))
    if not title or len(title) > 60 or not (low <= words <= high):
        return f"Generated content failed quality checks (title or {words} spoken words; expected {low}-{high} for {profile}); refusing to publish"
    if pillar not in {"AI You Can Use", "Hype Check", "What Changed", "How It Works", "Startup Breakdown"}:
        return "Generated content has no valid Nextdecode series; refusing to publish"
    if not isinstance(platform_copy, dict) or not all(str(platform_copy.get(key, "")).strip() for key in ("youtube_description", "instagram_caption", "facebook_title", "facebook_description")):
        return "Platform-specific captions are missing; refusing to publish"
    if not isinstance(instagram_hashtags, list) or not instagram_hashtags:
        return "Instagram-specific hashtags are missing; refusing to publish"
    if not isinstance(sources, list) or not sources or not all(isinstance(url, str) and url.startswith("https://") for url in sources):
        return "Research source links are missing or invalid; refusing to publish"
    hook = str(data.get("hook", "")).strip()
    hook_words = hook.split()
    if not 3 <= len(hook_words) <= 28 or hook.lower().startswith(GENERIC_HOOK_PREFIXES) or not script.startswith(hook):
        return "Opening hook failed quality checks; refusing to publish"
    if not isinstance(created, str):
        return "Metadata has no generation timestamp; refusing to publish stale output"
    try:
        generated_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)
    except ValueError:
        return "Metadata generation timestamp is invalid; refusing to publish"
    age = datetime.now(timezone.utc) - generated_at.astimezone(timezone.utc)
    if age < -timedelta(minutes=5) or age > timedelta(hours=24):
        return "Generated video is stale; create a fresh Short before publishing"
    return ""

def approval_matches_current_content() -> str:
    """Does the current approval still describe the current artifact?

    Approval binding only - the full governance decision lives in
    ``publish_authorization.authorize_publish``, which ``run()`` calls per destination.
    """
    return verify_approval_binding(data_root=ROOT)


def instagram_tunnel_allowed() -> bool:
    return os.getenv("INSTAGRAM_TUNNEL_FALLBACK", "false").strip().lower() == "true"


def platform_configured(platform: str) -> tuple[bool, str]:
    if platform == "youtube":
        required = os.getenv("YOUTUBE_CLIENT_ID", "").strip() and os.getenv("YOUTUBE_CLIENT_SECRET", "").strip() and (ROOT / "youtube_token.json").is_file()
        if not required:
            return False, "YouTube OAuth setup is incomplete"
    elif platform == "facebook":
        names = ("META_GRAPH_API_VERSION", "FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN")
        missing = [name for name in names if not os.getenv(name, "").strip()]
        if missing:
            return False, "Missing Meta Facebook settings: " + ", ".join(missing)
    elif platform == "instagram":
        names = ("META_GRAPH_API_VERSION", "INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN")
        missing = [name for name in names if not os.getenv(name, "").strip()]
        if os.getenv("INSTAGRAM_VIDEO_URL", "").strip():
            return False, (
                "INSTAGRAM_VIDEO_URL is an unverified external source; unset it and use "
                "the publisher-owned digest-pinned tunnel")
        if not (instagram_tunnel_allowed() and shutil.which("cloudflared")):
            missing.append("INSTAGRAM_TUNNEL_FALLBACK=true with cloudflared")
        if missing:
            return False, "Missing Meta Instagram settings: " + ", ".join(missing)
    module = PUBLISHERS[platform]
    try:
        import importlib.util
        if importlib.util.find_spec(module) is None:
            return False, f"Publisher module is missing: {module}"
    except (ImportError, ModuleNotFoundError, ValueError):
        return False, f"Publisher module is unavailable: {module}"
    return True, ""


def run(scheduled_approved: bool = False) -> int:
    if scheduled_approved and not upload_window_open():
        reason = "Scheduled publishing is restricted to the 20:00 IST hour"
        print(json.dumps({"status": "blocked_schedule", "reason": reason}, ensure_ascii=False))
        send_status("Nextdecode Shorts Studio: " + reason + ". No upload was started.")
        return 2
    if not scheduled_approved and (os.getenv("PUBLISH_MODE", "review").strip().lower() != "publish" or os.getenv("AUTO_PUBLISH_APPROVED", "false").strip().lower() != "true"):
        reason = "Publishing is review-only. Set PUBLISH_MODE=publish and AUTO_PUBLISH_APPROVED=true only after the owner approves the review package."
        print(json.dumps({"status": "blocked_approval", "reason": reason}, ensure_ascii=False))
        send_status("Nextdecode Shorts Studio: a review package is ready; publishing is waiting for explicit owner approval.")
        return 2
    approval_file = ROOT / "data" / "review_approved.json"
    if not approval_file.is_file():
        reason = "No approved review package exists; run python -m app.review.approve_review after completing the checklist."
        print(json.dumps({"status": "blocked_approval", "reason": reason}, ensure_ascii=False))
        send_status("Nextdecode Shorts Studio: publishing is waiting for the approved review package.")
        return 2
    try:
        baseline = authorize_publish(platform="youtube", purpose="short", data_root=ROOT)
    except Exception as exc:
        code, reason = authorization_error(exc)
        print(json.dumps({"status": code, "reason": reason}, ensure_ascii=False))
        send_status("Nextdecode Shorts Studio: publishing was stopped before any upload — " + reason)
        return 2
    content_issue = validate_content()
    if content_issue:
        print(json.dumps({"status": "blocked_quality", "reason": content_issue}, ensure_ascii=False))
        send_status("Nextdecode Shorts Studio: publishing blocked because the generated video failed its freshness or quality checks. No platform upload was started.")
        return 2

    # This studio's contract is all destinations: don't create partial cross-posts.
    setup_issues = []
    for platform in PUBLISHERS:
        configured, reason = platform_configured(platform)
        if not configured:
            setup_issues.append({"platform": platform, "status": "needs_setup", "reason": reason})
    if setup_issues:
        print(json.dumps({"status": "blocked_setup", "platforms": setup_issues}, ensure_ascii=False))
        blocked = ", ".join(item["platform"] for item in setup_issues)
        send_status(f"Nextdecode Shorts Studio: publishing is waiting for setup on {blocked}. No platform upload was started.")
        return 2

    lock = ROOT / ".publish_all.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            pid = int(lock.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
        except (OSError, ValueError):
            try:
                lock.unlink()
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except (FileNotFoundError, FileExistsError):
                print(json.dumps({"status": "blocked", "reason": "Another publish run is already starting"}))
                send_status("Nextdecode Shorts Studio: a publish run is already starting; this duplicate run was stopped.")
                return 1
        else:
            print(json.dumps({"status": "blocked", "reason": "Another publish run is already active"}))
            send_status("Nextdecode Shorts Studio: a publish run is already active; this duplicate run was stopped.")
            return 1
    os.write(fd, str(os.getpid()).encode("ascii"))
    os.close(fd)

    child_env = dict(os.environ)
    # Strip the retired marker defensively. The Instagram publisher no longer
    # accepts any environment value as proof that a remote URL is trustworthy.
    child_env.pop("INSTAGRAM_ARTIFACT_PINNED", None)
    # Prepend workspace to PATH for cloudflared discovery both in main and sub-processes
    ws_path = str(ROOT)
    if ws_path not in child_env.get("PATH", ""):
        child_env["PATH"] = ws_path + ":" + child_env.get("PATH", "")
    if ws_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ws_path + ":" + os.environ.get("PATH", "")
    results = []
    try:
        for platform, module in PUBLISHERS.items():
            # Re-authorize immediately before each destination: a crosspost is not
            # one transaction, so drift between platforms must stop the remaining uploads.
            try:
                decision = authorize_publish(platform=platform, purpose="short", data_root=ROOT)
            except Exception as exc:
                code, reason = authorization_error(exc)
                results.append({"platform": platform, "status": "blocked", "code": code, "reason": reason})
                break
            if (decision["metadata_sha256"], decision["video_sha256"]) != (
                    baseline["metadata_sha256"], baseline["video_sha256"]):
                results.append({"platform": platform, "status": "blocked_drift",
                                "reason": "the approved video or metadata changed after preflight; "
                                          "remaining destinations were stopped"})
                break
            proc = subprocess.run([sys.executable, "-m", module], cwd=ROOT, text=True, capture_output=True, env=child_env)
            if proc.stdout.strip():
                print(proc.stdout.strip())
            if proc.returncode == 0:
                results.append({"platform": platform, "status": "completed",
                                "destination": decision["destination"]})
            elif proc.returncode == 3:
                results.append({"platform": platform, "status": "ambiguous", "exit_code": 3,
                                "reason": "the destination may hold content the local ledger did not record; "
                                          "reconcile manually before retrying"})
                # The remote outcome is unknown. Stop cross-posting until an
                # operator reconciles this destination; never continue blindly.
                break
            else:
                if proc.stderr.strip():
                    print(f"{platform} error: {proc.stderr.strip()}", file=sys.stderr)
                results.append({"platform": platform, "status": "failed", "exit_code": proc.returncode})
        incomplete = [item["platform"] for item in results
                      if item["status"] in {"failed", "ambiguous", "blocked", "blocked_drift"}]
        status = "completed_with_errors" if incomplete else "completed"
        print(json.dumps({"status": status, "platforms": results}))
        if incomplete:
            detail = ", ".join(
                f"{item['platform']} ({item['status']})" for item in results
                if item["status"] in {"failed", "ambiguous", "blocked", "blocked_drift"})
            send_status("Nextdecode Shorts Studio: publishing did not complete cleanly on " + detail
                        + ". Crossposting is not atomic, so check each destination before retrying.")
            # Preserve actionable uploader outcomes for callers: 3 means the
            # destination may have accepted the upload (reconcile before retry),
            # 2 means authorization/drift blocked continuation, and ordinary
            # uploader failures retain their non-zero exit code.
            exit_codes = []
            for item in results:
                status = item["status"]
                if status == "ambiguous":
                    exit_codes.append(3)
                elif status in {"blocked", "blocked_drift"}:
                    exit_codes.append(2)
                elif status == "failed":
                    code = item.get("exit_code")
                    exit_codes.append(code if isinstance(code, int) and code != 0 else 1)
            return max(exit_codes, default=1)
        send_status("Nextdecode Shorts Studio: the video was published successfully to YouTube, Instagram, and Facebook.")
        return 0
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preflight and publish approved Shorts to all configured destinations")
    parser.add_argument("--scheduled-approved", action="store_true", help="Allow the scheduled uploader to proceed only with a current, matching owner approval")
    arguments = parser.parse_args()
    raise SystemExit(run(scheduled_approved=arguments.scheduled_approved))
