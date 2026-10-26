#!/usr/bin/env python3
"""Send a private review reminder with the local preview and approval command."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from notify_status import send_status

ROOT = Path(__file__).resolve().parent


def windows_path(path: Path) -> str:
    distro = os.getenv("WSL_DISTRO_NAME", "Ubuntu")
    return rf"\\wsl.localhost\{distro}" + str(path.resolve()).replace("/", "\\")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a private review reminder")
    parser.add_argument("format", choices=("short", "longform"))
    args = parser.parse_args()

    if args.format == "short":
        pending = json.loads((ROOT / "data" / "review_pending.json").read_text(encoding="utf-8"))
        package = json.loads(Path(pending["package"]).read_text(encoding="utf-8"))
        video = ROOT / "outputs" / "output_short.mp4"
        title = package.get("title", "(untitled)")
        approve = "approve_review.py"
        checklist = "sources, key claims, licensed visuals, limitations, full playback, audio/captions, and platform copy"
    else:
        package = json.loads((ROOT / "data" / "longform_review_pending.json").read_text(encoding="utf-8"))
        video = ROOT / "outputs" / "output_longform.mp4"
        title = package.get("title", "(untitled)")
        approve = "approve_longform.py"
        checklist = "sources, claims, limitations, full playback, audio/captions, chapters, thumbnail, and licensed visuals"

    command = (
        f"wsl.exe -d {os.getenv('WSL_DISTRO_NAME', 'Ubuntu')} --exec "
        f"/home/demon/shorts_studio/venv/bin/python "
        f"/home/demon/shorts_studio/{approve} --interactive"
    )
    message = (
        f"Nextdecode Studio: {args.format} video ready for review\n"
        f"Title: {title}\n"
        f"Preview: {windows_path(video)}\n"
        f"Review: {checklist}\n"
        f"If you approve after watching, run this in PowerShell:\n{command}\n"
        "Procedural/unverified visuals cannot be approved for publishing; use only relevant owner-recorded or licensed footage. "
        "Any 'no' cancels approval. The exact approved files are required; approval is valid only today (Asia/Kolkata). "
        "Scheduled upload check: 20:00 IST. No approval means no upload."
    )
    if not send_status(message):
        print("Review reminder was not delivered; check Telegram setup.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
