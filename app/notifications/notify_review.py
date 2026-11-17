#!/usr/bin/env python3
"""Send a private review reminder with the local preview and approval command.

Outbound notification only. The reviewer must still run the local approval
command; this message never approves anything and never contacts a publisher.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from app.notifications.notify_status import send_status

ROOT = Path(__file__).resolve().parents[2]


def windows_path(path: Path) -> str:
    distro = os.getenv("WSL_DISTRO_NAME", "Ubuntu")
    return rf"\\wsl.localhost\{distro}" + str(path.resolve()).replace("/", "\\")


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a private review reminder")
    parser.add_argument("format", choices=("short", "longform"))
    args = parser.parse_args()

    if args.format == "short":
        pending = _load_json(ROOT / "data" / "review_pending.json")
        if pending is None:
            print("No readable review_pending.json found — nothing to send.", file=sys.stderr)
            return 1
        package_path = Path(pending.get("package",""))
        package = _load_json(package_path) if package_path else None
        if package is None:
            print("Pending review package could not be read — nothing to send.", file=sys.stderr)
            return 1
        video = ROOT / "outputs" / "output_short.mp4"
        title = package.get("title", "(untitled)")
        digest = str(pending.get("review_package_sha256") or package.get("review_package_sha256") or "")
        approve = "app.review.approve_review"
        checklist = "sources, key claims, licensed visuals, limitations, full playback, audio/captions, and platform copy"
    else:
        package = _load_json(ROOT / "data" / "longform_review_pending.json")
        if package is None:
            print("No readable longform_review_pending.json found — nothing to send.", file=sys.stderr)
            return 1
        video = ROOT / "outputs" / "output_longform.mp4"
        title = package.get("title", "(untitled)")
        digest = str(package.get("review_package_sha256") or "")
        approve = "app.review.approve_longform"
        checklist = "sources, claims, limitations, full playback, audio/captions, chapters, thumbnail, and licensed visuals"

    video_ok = video.is_file()
    digest_line = f"Package SHA-256: {digest[:16]}{'…' if len(digest) > 16 else ''}\n" if digest else ""
    video_note = "Preview file present." if video_ok else "Preview file MISSING on disk — inspect before approving."

    command = (
        f"wsl.exe -d {os.getenv('WSL_DISTRO_NAME', 'Ubuntu')} --exec "
        f"/home/demon/shorts_studio/venv/bin/python "
        f"-m {approve} --interactive"
    )
    message = (
        f"Nextdecode Studio: {args.format} video ready for YOUR review (owner gate)\n"
        f"Title: {title}\n"
        f"{digest_line}"
        f"Preview: {windows_path(video)}\n"
        f"{video_note}\n"
        f"Review before approving:\n{checklist}\n\n"
        f"If you approve after watching, run this in PowerShell:\n{command}\n\n"
        "Approval binds to the exact files reviewed — it is NOT approval to publish, upload or post. "
        "Publishing stays blocked without a separate, explicit owner authorization step. "
        "Any 'no' cancels approval. Approval is valid only today (Asia/Kolkata). "
        "No approval = no upload. This message contains no authorization to act."
    )
    if not send_status(message):
        print("Review reminder was not delivered; check Telegram setup.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
