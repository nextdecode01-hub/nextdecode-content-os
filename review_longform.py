#!/usr/bin/env python3
"""Create a review gate for a generated YouTube long-form video."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from approval_integrity import sha256_file
from visual_quality import has_publishable_visuals

ROOT = Path(__file__).resolve().parent

def main() -> int:
    metadata = ROOT / "data" / "longform_metadata.json"
    video = ROOT / "outputs" / "output_longform.mp4"
    if not metadata.exists() or not video.exists() or video.stat().st_size < 500_000:
        raise SystemExit("longform_metadata.json and a rendered output_longform.mp4 are required")
    data = json.loads(metadata.read_text(encoding="utf-8"))
    package = {
        "status": "pending_human_review",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "video_path": str(video),
        "metadata_path": str(metadata),
        "video_sha256": sha256_file(video),
        "metadata_sha256": sha256_file(metadata),
        "title": data.get("title", ""),
        "format": "youtube_longform",
        "word_count": data.get("word_count", 0),
        "chapters": data.get("chapters", []),
        "source_urls": data.get("source_urls", []),
        "visuals": data.get("visuals", {"mode": "unverified", "asset_count": 0}),
        "visual_quality_status": "review_ready" if has_publishable_visuals(data.get("visuals")) else "draft_only",
        "thumbnail_text": data.get("thumbnail_text", ""),
        "checklist": {
            "two_sources_checked": False,
            "primary_source_checked": False,
            "limitations_and_uncertainty_checked": False,
            "audio_captions_and_16x9_checked": False,
            "chapters_and_description_checked": False,
            "thumbnail_checked": False,
            "licensed_or_owner_visuals_checked": False,
            "publish_approved": False,
        },
        "notes": "Review the exact video and complete the checklist before approval. Approval expires at the end of today (Asia/Kolkata)."
    }
    (ROOT / "data" / "longform_review_pending.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": package["status"], "title": package["title"], "package": str(ROOT / "data" / "longform_review_pending.json")}))

if __name__ == "__main__":
    main()
