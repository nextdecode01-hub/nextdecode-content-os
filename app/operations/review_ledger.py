#!/usr/bin/env python3
"""Maintain a small local quality and feedback ledger for the monthly sprint."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "data" / "feedback_ledger.csv"
FIELDS = ["date", "video_number", "title", "content_pillar", "hook", "sources", "demo", "limitation", "hook_score", "evidence_score", "value_score", "visual_score", "pacing_score", "payoff_score", "originality_score", "youtube_24h_views", "youtube_24h_engaged_views", "youtube_7d_views", "instagram_7d_reach", "facebook_7d_reach", "comments", "shares", "saves", "subscribers_gained", "feedback", "next_hypothesis"]

def ensure() -> None:
    if not LEDGER.exists():
        with LEDGER.open("w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=FIELDS).writeheader()

def rows() -> list[dict]:
    ensure()
    with LEDGER.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def main() -> int:
    parser = argparse.ArgumentParser(description="Review ledger for Nextdecode content")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    add = sub.add_parser("add")
    add.add_argument("--video-number", required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--pillar", default="")
    add.add_argument("--hook", default="")
    add.add_argument("--sources", type=int, default=0)
    add.add_argument("--demo", choices=("yes", "no"), default="no")
    add.add_argument("--limitation", choices=("yes", "no"), default="no")
    add.add_argument("--hook-score", type=int, default=0)
    add.add_argument("--evidence-score", type=int, default=0)
    add.add_argument("--value-score", type=int, default=0)
    add.add_argument("--visual-score", type=int, default=0)
    add.add_argument("--pacing-score", type=int, default=0)
    add.add_argument("--payoff-score", type=int, default=0)
    add.add_argument("--originality-score", type=int, default=0)
    add.add_argument("--feedback", default="")
    add.add_argument("--next-hypothesis", default="")
    summary = sub.add_parser("summary")
    args = parser.parse_args()
    ensure()
    if args.command == "init":
        print(f"Initialized {LEDGER}")
    elif args.command == "add":
        item = {field: "" for field in FIELDS}
        item.update({"date": datetime.now(timezone.utc).date().isoformat(), "video_number": args.video_number, "title": args.title, "content_pillar": args.pillar, "hook": args.hook, "sources": args.sources, "demo": args.demo, "limitation": args.limitation, "hook_score": args.hook_score, "evidence_score": args.evidence_score, "value_score": args.value_score, "visual_score": args.visual_score, "pacing_score": args.pacing_score, "payoff_score": args.payoff_score, "originality_score": args.originality_score, "feedback": args.feedback, "next_hypothesis": args.next_hypothesis})
        with LEDGER.open("a", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=FIELDS).writerow(item)
        print(f"Added video {args.video_number} to {LEDGER}")
    else:
        data = rows()
        scored = []
        for row in data:
            scores = [int(row.get(key) or 0) for key in ("hook_score", "evidence_score", "value_score", "visual_score", "pacing_score", "payoff_score", "originality_score")]
            scored.append(sum(scores) / len(scores) if any(scores) else 0)
        print(f"videos={len(data)}")
        print(f"average_quality={sum(scored) / len(scored):.2f}" if scored else "average_quality=0")
        print("Next review: compare one hook, one visual treatment, and one payoff pattern using 24-hour and 7-day metrics.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

