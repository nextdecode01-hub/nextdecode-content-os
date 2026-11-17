"""Read-only, advisory competitor benchmark context for topic selection.

This module never changes a candidate's score. It exposes sample coverage and
repeatable editorial observations so the selector/judge can consider them without
mistaking a small public-view sample for measured audience outcomes.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = ROOT / "data" / "research" / "faceless_video_observations_pilot_2026-11-17.csv"


@lru_cache(maxsize=1)
def load_benchmark_context(path: str | None = None) -> dict:
    source = Path(path) if path else BENCHMARK_PATH
    if not source.exists():
        return {
            "available": False,
            "source": str(source),
            "reason": "benchmark file not found",
            "video_count": 0,
            "channel_count": 0,
            "format_mix": {},
            "recurring_title_patterns": [],
            "score_adjustment": 0.0,
        }
    try:
        with source.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        rows = [row for row in rows if row.get("channel") and row.get("video_title")]
        channels = {row["channel"].strip() for row in rows}
        formats: dict[str, int] = {}
        pattern_channels: dict[str, set[str]] = {}
        pattern_counts: dict[str, int] = {}
        for row in rows:
            fmt = (row.get("format") or "unknown").strip() or "unknown"
            formats[fmt] = formats.get(fmt, 0) + 1
            pattern = (row.get("title_pattern") or "").strip()
            if pattern:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                pattern_channels.setdefault(pattern, set()).add(row["channel"].strip())
        recurring = [
            {"pattern": pattern, "observations": count, "channels": len(pattern_channels[pattern])}
            for pattern, count in sorted(pattern_counts.items())
            if count >= 3 and len(pattern_channels[pattern]) >= 2
        ]
        return {
            "available": True,
            "source": str(source),
            "video_count": len(rows),
            "channel_count": len(channels),
            "format_mix": formats,
            "recurring_title_patterns": recurring,
            "score_adjustment": 0.0,
            "usage": "advisory_only_no_score_adjustment",
        }
    except (OSError, csv.Error, UnicodeError) as exc:
        return {
            "available": False,
            "source": str(source),
            "reason": f"benchmark could not be read: {type(exc).__name__}",
            "video_count": 0,
            "channel_count": 0,
            "format_mix": {},
            "recurring_title_patterns": [],
            "score_adjustment": 0.0,
        }


def clear_benchmark_cache() -> None:
    load_benchmark_context.cache_clear()
