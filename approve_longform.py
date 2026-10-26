#!/usr/bin/env python3
"""Approve a long-form YouTube package after the owner completes its checklist."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from approval_integrity import sha256_file
from visual_quality import has_publishable_visuals

ROOT = Path(__file__).resolve().parent
QUESTIONS = {
    "two_sources_checked": "Have you checked at least two credible sources?",
    "primary_source_checked": "Have you verified the key claims against a primary source?",
    "limitations_and_uncertainty_checked": "Does the video clearly explain limitations and uncertainty?",
    "audio_captions_and_16x9_checked": "Have you watched the full video and checked audio, captions, and 16:9 framing?",
    "chapters_and_description_checked": "Have you checked chapters and the YouTube description?",
    "thumbnail_checked": "Have you reviewed the thumbnail and its text?",
    "licensed_or_owner_visuals_checked": "Have you confirmed all footage is owner-recorded or properly licensed?",
}
REQUIRED = tuple(QUESTIONS)

def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Approve a reviewed long-form Nextdecode package")
    parser.add_argument("--interactive", action="store_true", help="Answer each review checklist question before approving")
    args = parser.parse_args(argv)
    pending = ROOT / "longform_review_pending.json"
    if not pending.exists():
        raise SystemExit("No longform_review_pending.json found")
    package = json.loads(pending.read_text(encoding="utf-8"))
    metadata_file = ROOT / "longform_metadata.json"
    video_file = ROOT / "output_longform.mp4"
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    current_hashes = {
        "metadata_sha256": sha256_file(metadata_file),
        "video_sha256": sha256_file(video_file),
    }
    if any(package.get(name) != value for name, value in current_hashes.items()):
        raise SystemExit("Review package does not match the current long-form video and metadata; create a fresh review package.")
    if package.get("visuals") != metadata.get("visuals"):
        raise SystemExit("Review package visuals do not match the current video; create a fresh review package.")
    if not has_publishable_visuals(metadata.get("visuals")):
        raise SystemExit("This is a draft with procedural visuals. Add owner-recorded or licensed footage before approval.")
    checks = package.get("checklist", {})
    if args.interactive:
        checks = package.setdefault("checklist", {})
        for name, question in QUESTIONS.items():
            answer = input(f"{question} [y/N] ").strip().lower()
            if answer not in {"y", "yes"}:
                raise SystemExit("Approval cancelled; the package remains unapproved.")
            checks[name] = True
    missing = [name for name in REQUIRED if checks.get(name) is not True]
    if missing:
        raise SystemExit("Long-form checklist is incomplete: " + ", ".join(missing))
    package["status"] = "approved"
    package["checklist"]["publish_approved"] = True
    package["approved_at"] = datetime.now(timezone.utc).isoformat()
    pending.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    (ROOT / "longform_review_approved.json").write_text(json.dumps({
        "status": "approved",
        "package": str(pending),
        "title": package.get("title", ""),
        "approved_at": package["approved_at"],
        **current_hashes,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "approved", "title": package.get("title", "")}))

if __name__ == "__main__":
    main()
