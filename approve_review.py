#!/usr/bin/env python3
"""Approve the current review package after the owner completes its checklist."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from approval_integrity import sha256_file
from visual_quality import has_publishable_visuals

ROOT = Path(__file__).resolve().parent

def main() -> int:
    parser = argparse.ArgumentParser(description="Approve a reviewed Nextdecode package")
    parser.add_argument("package", nargs="?", help="Path shown in review_pending.json")
    parser.add_argument("--interactive", action="store_true", help="Answer each review checklist question before approving")
    args = parser.parse_args()
    pending = ROOT / "review_pending.json"
    if not pending.exists() and not args.package:
        raise SystemExit("No review_pending.json found")
    package_path = Path(args.package) if args.package else Path(json.loads(pending.read_text(encoding="utf-8"))["package"])
    package = json.loads(package_path.read_text(encoding="utf-8"))
    metadata_file = ROOT / "metadata.json"
    video_file = ROOT / "output_short.mp4"
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    current_hashes = {
        "metadata_sha256": sha256_file(metadata_file),
        "video_sha256": sha256_file(video_file),
    }
    if any(package.get(name) != value for name, value in current_hashes.items()):
        raise SystemExit("Review package does not match the current video and metadata; create a fresh review package.")
    if package.get("visuals") != metadata.get("visuals"):
        raise SystemExit("Review package visuals do not match the current video; create a fresh review package.")
    if not has_publishable_visuals(metadata.get("visuals")):
        raise SystemExit("This is a draft with procedural visuals. Add owner-recorded or licensed footage before approval.")
    checks = package.get("checklist", {})
    questions = {
        "two_sources_checked": "Have you checked at least two credible sources?",
        "primary_source_checked": "Have you verified the key claims against a primary source?",
        "real_demo_or_original_visual": "Have you confirmed the visuals are relevant, owner-recorded, or properly licensed?",
        "limitation_stated": "Does the video clearly state important limitations or uncertainty?",
        "captions_audio_and_9x16_checked": "Have you watched the full video and checked audio, captions, and 9:16 framing?",
        "platform_copy_checked": "Have you reviewed the title and copy for each publishing platform?",
    }
    required = tuple(questions)
    if args.interactive:
        checks = package.setdefault("checklist", {})
        for name, question in questions.items():
            answer = input(f"{question} [y/N] ").strip().lower()
            if answer not in {"y", "yes"}:
                raise SystemExit("Approval cancelled; the package remains unapproved.")
            checks[name] = True
    missing = [name for name in required if checks.get(name) is not True]
    if missing:
        raise SystemExit("Review checklist is incomplete: " + ", ".join(missing))
    package["status"] = "approved"
    package["checklist"]["publish_approved"] = True
    package["approved_at"] = datetime.now(timezone.utc).isoformat()
    package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    (ROOT / "review_approved.json").write_text(json.dumps({
        "status": "approved",
        "package": str(package_path),
        "title": package.get("title", ""),
        "approved_at": package["approved_at"],
        **current_hashes,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "approved", "package": str(package_path), "title": package.get("title", "")}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
