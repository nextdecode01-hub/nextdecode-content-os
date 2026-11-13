#!/usr/bin/env python3
"""Create a review queue entry without publishing or exposing secrets."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from app.security.approval_integrity import sha256_file
from app.visuals.visual_quality import has_publishable_visuals

ROOT = Path(__file__).resolve().parents[2]
METADATA = ROOT / "data" / "metadata.json"
VIDEO = ROOT / "outputs" / "output_short.mp4"
QUEUE = ROOT / "data" / "review_queue"

def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60] or "untitled"

def main() -> int:
    if not METADATA.exists() or not VIDEO.exists():
        raise SystemExit("metadata.json and output_short.mp4 are required before review packaging")
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    created = str(metadata.get("created_at", ""))
    try:
        stamp = datetime.fromisoformat(created.replace("Z", "+00:00"))
    except ValueError:
        stamp = datetime.now(timezone.utc)
    QUEUE.mkdir(parents=True, exist_ok=True)
    filename = f"{stamp.astimezone(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slug(str(metadata.get('title', 'untitled')))}.json"
    package = {
        "status": "pending_human_review",
        "created_at": stamp.astimezone(timezone.utc).isoformat(),
        "video_path": str(VIDEO),
        "metadata_path": str(METADATA),
        "video_sha256": sha256_file(VIDEO),
        "metadata_sha256": sha256_file(METADATA),
        "title": metadata.get("title", ""),
        "content_pillar": metadata.get("content_pillar", ""),
        "script_profile": metadata.get("script_profile", "standard_35s"),
        "target_duration_seconds": metadata.get("target_duration_seconds", 35),
        "word_count": metadata.get("word_count", 0),
        "word_range": metadata.get("word_range", [72, 92]),
        "hook": metadata.get("hook", ""),
        "source_urls": metadata.get("source_urls", []),
        "visuals": metadata.get("visuals", {"mode": "unverified", "asset_count": 0}),
        "visual_quality_status": "review_ready" if has_publishable_visuals(metadata.get("visuals")) else "draft_only",
        "platform_copy": metadata.get("platform_copy", {}),
        "checklist": {
            "two_sources_checked": False,
            "primary_source_checked": False,
            "real_demo_or_original_visual": False,
            "limitation_stated": False,
            "captions_audio_and_9x16_checked": False,
            "platform_copy_checked": False,
            "publish_approved": False,
        },
        "benchmark_references": ["Matt Wolfe", "AI Explained", "Cleo Abram"],
        "notes": "Review the exact video and complete the checklist before approval. Approval expires at the end of today (Asia/Kolkata).",
    }
    # Additive run provenance (Phase 10.4): when the promoted metadata carries a
    # run identity, the package records which run produced these artifacts so
    # approval can verify the promotion actually completed.
    run_id = str(metadata.get("run_id") or "")
    if run_id:
        package["run_id"] = run_id
        manifest_path = ROOT / "outputs" / "runs" / run_id / "manifest.json"
        if manifest_path.is_file():
            package["run_manifest_path"] = str(manifest_path)
            package["run_manifest_sha256"] = sha256_file(manifest_path)
    target = QUEUE / filename
    target.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    (ROOT / "data" / "review_pending.json").write_text(json.dumps({"status": package["status"], "package": str(target), "created_at": package["created_at"]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": package["status"], "review_package": str(target), "title": package["title"]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
