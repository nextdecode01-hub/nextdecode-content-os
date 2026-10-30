#!/usr/bin/env python3
"""Motion director - plans edited, multi-shot short-form video rundowns.

Public API:
    plan_shots(script, *, audio_duration=None) -> list[dict]
    director_report(shots) -> str
    estimate_render_plan(shots) -> dict
"""

from __future__ import annotations

import math
import os
from pathlib import Path

SAFE_ZONE_TOP = 0.10
SAFE_ZONE_BOTTOM = 0.18

MIN_SHOT_DURATION = 1.3
MAX_SHOT_DURATION = 2.9
MIN_SHOTS = 8
DEFAULT_DURATION = 30.0

SOURCES = ("pexels", "pixabay", "wikimedia", "ai_image", "procedural", "demo")
SFX_KINDS = ("whoosh", "impact", "riser", "none")

HOOK_KEYWORDS = ("hook", "open", "intro", "attention", "listen")
PAYOFF_KEYWORDS = ("payoff", "close", "outro", "cta", "call to action", "finally", "remember")

ZOOM_PAIRS = ((1.00, 1.14), (1.02, 1.18), (1.00, 1.16), (1.04, 1.12))
PAN_OFFSETS = ((6.0, 0.0), (-6.0, 3.0), (8.0, -2.0), (-4.0, 4.0))
DEFAULT_MUSIC_GAIN_DB = -15.0

_DEMO_VIDEO_PATH = os.getenv("DEMO_VIDEO_PATH", "").strip()

_AI_IMAGE_ENV_KEYS = ("GEMINI_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN", "OPENAI_API_KEY")


def _image_provider_available() -> bool:
    """True when a hosted image generator is configured."""
    return any(os.getenv(key, "").strip() for key in _AI_IMAGE_ENV_KEYS)


def _beat_text(beat) -> str:
    if isinstance(beat, str):
        return beat
    if isinstance(beat, dict):
        return beat.get("text") or beat.get("visual") or beat.get("caption") or str(beat)
    return str(beat)


def _visual_query(beat, index: int = 0) -> str:
    if isinstance(beat, dict):
        variants = beat.get("asset_query_variants")
        if isinstance(variants, list) and variants:
            return str(variants[int(index) % len(variants)])
        return (
            beat.get("asset_query")
            or beat.get("query")
            or beat.get("visual")
            or beat.get("text")
            or ""
        )
    return str(beat)


def _query_variants(beat) -> list[str]:
    """Extra search phrases the asset fetcher can fall back to."""
    if isinstance(beat, dict):
        variants = beat.get("asset_query_variants")
        if isinstance(variants, list):
            return [str(item) for item in variants if str(item).strip()]
    return []


def _has_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    low = (text or "").lower()
    return any(k in low for k in keywords)


def _truncate(text: str, max_len: int = 42) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _estimate_duration_from_beats(beats: list) -> float:
    total = 0.0
    for beat in beats:
        if isinstance(beat, dict) and beat.get("duration"):
            try:
                total += float(beat["duration"])
            except (TypeError, ValueError):
                total += 3.0
        else:
            total += 3.0
    return max(total, DEFAULT_DURATION)


def _schedule(duration: float, count: int) -> list[tuple[float, float]]:
    count = max(1, int(count))
    seg = duration / count
    slots = [(i * seg, (i + 1) * seg) for i in range(count)]
    slots[-1] = (slots[-1][0], duration)
    return slots


def _available_sources() -> list[str]:
    """Visual sources that can actually produce an asset right now."""
    ordered: list[str] = []
    if _DEMO_VIDEO_PATH and Path(_DEMO_VIDEO_PATH).is_file():
        ordered.append("demo")
    if os.getenv("PEXELS_API_KEY", "").strip():
        ordered.append("pexels")
    if os.getenv("PIXABAY_API_KEY", "").strip():
        ordered.append("pixabay")
    ordered.append("wikimedia")
    if _image_provider_available():
        ordered.append("ai_image")
    ordered.append("procedural")
    return ordered


def _pick_source(index: int, beat_text: str) -> str:
    ordered = _available_sources()
    return ordered[index % len(ordered)]


def _pick_sfx(index: int, text: str, total: int) -> str:
    if _has_keyword(text, HOOK_KEYWORDS) or index == 0:
        return "impact"
    if _has_keyword(text, PAYOFF_KEYWORDS):
        return "impact"
    if index > 0:
        return "whoosh"
    return "none"


def plan_shots(script: dict, *, audio_duration: float | None = None) -> list[dict]:
    """Plan edited shots for a short.

    Reads script['shots'] when present, otherwise derives one shot per
    beat_sheet entry, otherwise falls back to a single procedural shot.
    Never raises.
    """
    try:
        script = script or {}
    except Exception:
        script = {}

    explicit = script.get("shots")
    beats = []
    if isinstance(explicit, list) and explicit:
        beats = explicit
    else:
        sheet = script.get("beat_sheet")
        beats = sheet if isinstance(sheet, list) else []

    if not beats:
        duration = float(audio_duration or DEFAULT_DURATION)
        return [_single_shot(0, 0.0, duration, script)]

    if audio_duration is None:
        audio_duration = _estimate_duration_from_beats(beats)
    try:
        duration = max(5.0, float(audio_duration))
    except (TypeError, ValueError):
        duration = DEFAULT_DURATION

    count = max(MIN_SHOTS, math.ceil(duration / MAX_SHOT_DURATION))
    seg = duration / count
    while seg < MIN_SHOT_DURATION and count > MIN_SHOTS:
        count -= 1
        seg = duration / count
    slots = _schedule(duration, count)

    shots: list[dict] = []
    topic = str(script.get("topic") or script.get("title") or "short").strip()
    for i, (start, end) in enumerate(slots):
        beat = beats[i % len(beats)]
        text = _beat_text(beat)
        z_from, z_to = ZOOM_PAIRS[i % len(ZOOM_PAIRS)]
        px, py = PAN_OFFSETS[i % len(PAN_OFFSETS)]
        gain = round(DEFAULT_MUSIC_GAIN_DB - 0.5 * (i % 4), 2)
        gain = max(-18.0, min(-13.0, gain))
        shots.append({
            "index": i,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "visual": text,
            "asset_query": _visual_query(beat, i) or f"{topic} shot {i + 1}",
            "asset_query_variants": _query_variants(beat),
            "source": _pick_source(i, text),
            "caption": _truncate(text, 42) or f"{topic} part {i + 1}",
            "zoom_from": z_from,
            "zoom_to": z_to,
            "pan": {"x": px, "y": py},
            "transition": "fade" if i in (0, count - 1) else "cut",
            "sfx": _pick_sfx(i, text, count),
            "music_gain_db": gain,
        })
    return shots


def _single_shot(index: int, start: float, end: float, script: dict) -> dict:
    text = str(script.get("text") or script.get("caption") or script.get("topic") or "short")
    return {
        "index": index,
        "start": round(start, 3),
        "end": round(end, 3),
        "duration": round(end - start, 3),
        "visual": text,
        "asset_query": text,
        "source": "demo" if (_DEMO_VIDEO_PATH and Path(_DEMO_VIDEO_PATH).is_file()) else "procedural",
        "caption": _truncate(text, 42),
        "zoom_from": 1.00,
        "zoom_to": 1.12,
        "pan": {"x": 0.0, "y": 0.0},
        "transition": "fade",
        "sfx": "none",
        "music_gain_db": DEFAULT_MUSIC_GAIN_DB,
    }


def director_report(shots: list[dict]) -> str:
    lines = ["motion director report", "-" * 44, f"shots: {len(shots)}"]
    total = shots[-1]["end"] if shots else 0.0
    lines.append(f"total_duration: {total:.2f}s")
    for s in shots:
        lines.append(
            "  {i:02d} [{start:6.2f}-{end:6.2f}] {dur:4.2f}s "
            "{caption:<44s} src={source:<10s} sfx={sfx:<7s} "
            "zoom={zf}->{zt} pan=({px},{py}) trans={trans} gain={gain}".format(
                i=s["index"], start=s["start"], end=s["end"], dur=s["duration"],
                caption=s["caption"], source=s["source"], sfx=s["sfx"],
                zf=s["zoom_from"], zt=s["zoom_to"], px=s["pan"]["x"], py=s["pan"]["y"],
                trans=s["transition"], gain=s["music_gain_db"],
            )
        )
    return "\n".join(lines)


def estimate_render_plan(shots: list[dict]) -> dict:
    total = float(shots[-1]["end"]) if shots else 0.0
    count = len(shots)
    avg = total / count if count else 0.0
    cut_rate = (count / total * 60.0) if total else 0.0
    asset_counts: dict[str, int] = {}
    for s in shots:
        src = s.get("source", "procedural")
        asset_counts[src] = asset_counts.get(src, 0) + 1
    return {
        "total_duration": round(total, 3),
        "shot_count": count,
        "avg_shot": round(avg, 3),
        "cut_rate_per_min": round(cut_rate, 1),
        "asset_counts": asset_counts,
    }


def main() -> None:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Motion director demo")
    ap.add_argument("--demo", action="store_true", help="run a synthetic demo plan")
    args = ap.parse_args()
    if args.demo:
        script = {
            "topic": "why most short videos get skipped",
            "beat_sheet": [
                {"text": "Hook: the first 3 seconds decide everything", "visual": "thumb stopping scroll"},
                {"text": "Most creators post one static clip and hope", "visual": "boring looping footage"},
                {"text": "Viewers swipe away because it looks unedited", "visual": "hand swiping up fast"},
                {"text": "Hook them with motion, not just a message", "visual": "fast zoom on eyes"},
                {"text": "Every shot needs a purpose and a cut", "visual": "film splice marks"},
                {"text": "Ken Burns adds life to still images", "visual": "slow zoom on photo"},
                {"text": "Kinetic captions keep eyes glued to screen", "visual": "moving text captions"},
                {"text": "Sound effects punctuate each scene change", "visual": "speaker icon pulse"},
                {"text": "The payoff lands only if pacing holds", "visual": "payoff beat visual"},
                {"text": "Now go edit like you mean it", "visual": "final call to action", "duration": 3.0},
            ],
        }
        shots = plan_shots(script, audio_duration=30.0)
        print(director_report(shots))
        print(json.dumps(estimate_render_plan(shots), indent=2))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
