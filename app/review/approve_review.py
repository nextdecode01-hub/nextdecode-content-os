#!/usr/bin/env python3
"""Approve the current review package after the owner completes its checklist.

Trust boundary: --reviewer is a locally asserted label, not an authenticated
identity. Only the accountable human reviewer should have access to invoke this
command and write the local approval state. This record is not non-repudiation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from app.security.approval_integrity import sha256_file
from app.visuals.visual_quality import has_publishable_visuals

ROOT = Path(__file__).resolve().parents[2]

def main() -> int:
    parser = argparse.ArgumentParser(description="Approve a reviewed Nextdecode package")
    parser.add_argument("package", nargs="?", help="Path shown in review_pending.json")
    parser.add_argument("--interactive", action="store_true", help="Answer each review checklist question before approving")
    parser.add_argument("--reviewer", default="", help="locally asserted reviewer label (not authenticated identity)")
    parser.add_argument("--rationale", default="", help="brief reason for the approval decision")
    args = parser.parse_args()
    pending = ROOT / "data" / "review_pending.json"
    if not pending.exists() and not args.package:
        raise SystemExit("No review_pending.json found")
    package_path = Path(args.package) if args.package else Path(json.loads(pending.read_text(encoding="utf-8"))["package"])
    # Parse and attest the exact same byte buffer. A second path read here
    # would permit a concurrent local replacement between review and hashing.
    try:
        package_bytes = package_path.read_bytes()
        package = json.loads(package_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Review package is unreadable or malformed; refusing approval: {type(exc).__name__}")
    package_digest = hashlib.sha256(package_bytes).hexdigest()
    metadata_file = ROOT / "data" / "metadata.json"
    video_file = ROOT / "outputs" / "output_short.mp4"
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
    # Additive run provenance (Phase 10.4): a package tied to a run identity is
    # only approvable when the run manifest says ok, its promotion journal is
    # completed, and BOTH legacy slots still hash-match the run's recorded
    # artifacts.  A mixed pair (metadata from run B, video from run A) or an
    # interrupted promotion therefore cannot be approved.  Packages without a
    # run_id keep the exact legacy behaviour above.
    run_id = str(package.get("run_id") or "")
    if run_id:
        manifest_path = Path(package.get("run_manifest_path") or (
            ROOT / "outputs" / "runs" / run_id / "manifest.json"))
        if not manifest_path.is_file():
            raise SystemExit(f"Run manifest for {run_id} is missing; create a fresh review package from a completed run.")
        if package.get("run_manifest_sha256") and sha256_file(manifest_path) != package["run_manifest_sha256"]:
            raise SystemExit("Run manifest does not match the review package; create a fresh review package.")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise SystemExit(f"Run manifest for {run_id} is corrupt; refusing approval.")
        if manifest.get("status") != "ok":
            raise SystemExit(f"Run {run_id} is {manifest.get('status')!r}, not a completed run; refusing approval.")
        artifacts = manifest.get("artifacts") or {}
        for slot_name, slot_file in (("metadata", metadata_file), ("video", video_file)):
            entry = artifacts.get(slot_name) or {}
            if not entry.get("sha256") or sha256_file(slot_file) != entry["sha256"]:
                raise SystemExit(
                    f"Current {slot_name} does not match run {run_id}'s recorded artifact; "
                    "refusing to approve a mixed or stale pair.")
        journal_path = ROOT / "data" / "runs" / "promotions" / f"{run_id}.json"
        if not journal_path.is_file():
            raise SystemExit(f"No promotion journal for run {run_id}; refusing approval.")
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        if journal.get("status") != "completed":
            raise SystemExit(
                f"Promotion for run {run_id} is {journal.get('status')!r}; "
                "its slots are not a verified success; refusing approval.")
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
    if package.get("status") != "pending_human_review":
        raise SystemExit("Only an immutable pending review package can be approved.")
    if not args.reviewer.strip() or not args.rationale.strip():
        raise SystemExit("A reviewer label and approval rationale are required; the label is not authenticated.")
    approved_at = datetime.now(timezone.utc).isoformat()
    decision = {
        "status": "approved",
        "package": str(package_path),
        "review_package_sha256": package_digest,
        "reviewer": args.reviewer.strip(),
        "rationale": args.rationale.strip(),
        "purpose": "short",
        "platform": "youtube",
        "destination": "private",
        "checklist": {**checks, "publish_approved": True},
        "title": package.get("title", ""),
        "approved_at": approved_at,
        **current_hashes,
    }
    decisions_dir = ROOT / "data" / "review_approvals"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    decision_path = decisions_dir / f"{approved_at.replace(':', '').replace('-', '')}-{package_digest[:16]}.json"
    temporary = decision_path.with_suffix(".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(decision, stream, indent=2)
            stream.write("\n")
            stream.flush()
            import os
            os.fsync(stream.fileno())
        # Atomic no-overwrite publication: hard-link creation fails if this
        # append-only decision path already exists.
        os.link(temporary, decision_path)
        temporary.unlink()
        os.chmod(decision_path, 0o400)
        directory_fd = os.open(decisions_dir, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except FileExistsError:
        temporary.unlink(missing_ok=True)
        raise SystemExit("An approval decision with this identity already exists; refusing to overwrite it.")
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    pointer = {
        "status": "approved",
        "package": str(package_path),
        "decision_record": str(decision_path),
        "decision_record_sha256": sha256_file(decision_path),
    }
    pointer_path = ROOT / "data" / "review_approved.json"
    pointer_tmp = pointer_path.with_suffix(".json.tmp")
    with pointer_tmp.open("w", encoding="utf-8") as stream:
        json.dump(pointer, stream, indent=2)
        stream.write("\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    os.replace(pointer_tmp, pointer_path)
    print(json.dumps({"status": "approved", "package": str(package_path), "decision_record": str(decision_path), "title": package.get("title", "")}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
