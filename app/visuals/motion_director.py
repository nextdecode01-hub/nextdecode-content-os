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

from app.visuals import creative_director
from pathlib import Path

SAFE_ZONE_TOP = 0.10
SAFE_ZONE_BOTTOM = 0.18

MIN_SHOT_DURATION = 1.3
MAX_SHOT_DURATION = 2.9
MIN_SHOTS = 8
DEFAULT_DURATION = 30.0

SOURCES = ("coverr", "pixabay", "wikimedia", "ai_image", "procedural", "demo")
SFX_KINDS = ("whoosh", "impact", "riser", "none")

HOOK_KEYWORDS = ("hook", "open", "intro", "attention", "listen")
PAYOFF_KEYWORDS = ("payoff", "close", "outro", "cta", "call to action", "finally", "remember")

ZOOM_PAIRS = ((1.00, 1.14), (1.02, 1.18), (1.00, 1.16), (1.04, 1.12))
PAN_OFFSETS = ((6.0, 0.0), (-6.0, 3.0), (8.0, -2.0), (-4.0, 4.0))
DEFAULT_MUSIC_GAIN_DB = -15.0

# Scene-aware motion.  Amplitudes are deliberately small: a 3–8% push keeps the
# frame alive without cropping the text that the narration is explaining.  The
# renderer alternates direction so the scale at a cut matches the scale the
# previous shot ended on (no visible snap between scenes).
MOTION_PROFILES = {
    "typography": {"mode": "kenburns", "zoom_pct": 4.0, "pan_pct": 0.0},
    "chart": {"mode": "kenburns", "zoom_pct": 3.5, "pan_pct": 0.3},
    "ui_demo": {"mode": "kenburns", "zoom_pct": 5.0, "pan_pct": 0.5},
    "diagram": {"mode": "kenburns", "zoom_pct": 6.0, "pan_pct": 0.8},
    "map": {"mode": "kenburns", "zoom_pct": 6.0, "pan_pct": 1.0},
    "product": {"mode": "kenburns", "zoom_pct": 7.0, "pan_pct": 0.8},
}
PHOTO_PROFILE = {"mode": "kenburns", "zoom_pct": 8.0, "pan_pct": 1.2}
NATIVE_VIDEO_PROFILE = {"mode": "native", "zoom_pct": 0.0, "pan_pct": 0.0}
NATIVE_VIDEO_MAX_SCALE = 1.08
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def sfx_enabled() -> bool:
    """Per-cut transition SFX are opt-in only.

    Phase 6 added a whoosh to every cut.  That is an intentional sound effect,
    not a render artefact, but it reads as an unwanted extra sound.  Keep the
    synthesis path available behind ``SHOT_SFX=on`` and default to silence.
    """
    return os.getenv("SHOT_SFX", "").strip().lower() in {"1", "true", "yes", "on"}

_DEMO_VIDEO_PATH = os.getenv("DEMO_VIDEO_PATH", "").strip()

_AI_IMAGE_ENV_KEYS = ("GEMINI_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN", "OPENAI_API_KEY")


def _image_provider_available() -> bool:
    """True when a hosted image generator is configured."""
    return any(os.getenv(key, "").strip() for key in _AI_IMAGE_ENV_KEYS)


def _beat_text(beat) -> str:
    if isinstance(beat, str):
        return beat
    if isinstance(beat, dict):
        return (beat.get("text") or beat.get("caption") or beat.get("claim")
                or beat.get("visual") or str(beat))
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
    if os.getenv("COVERR_API_KEY", "").strip():
        ordered.append("coverr")
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
    if not sfx_enabled():
        return "none"
    if _has_keyword(text, HOOK_KEYWORDS) or index == 0:
        return "impact"
    if _has_keyword(text, PAYOFF_KEYWORDS):
        return "impact"
    if index > 0:
        return "whoosh"
    return "none"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _asset_kind(detail: dict | None) -> str:
    provider = str((detail or {}).get("provider") or "")
    if provider in {"gradient", "procedural"}:
        return "procedural"
    path = str((detail or {}).get("path") or "").lower()
    suffix = Path(path).suffix if path else ""
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    return "procedural"


def _motion_profile(scene_type: str, asset_kind: str,
                    provider: str = "") -> tuple[str, dict]:
    if provider == "gradient":
        # The fallback is a text card rendered to video; keep the text still.
        return "gradient_text_card", MOTION_PROFILES["typography"]
    if scene_type == "footage":
        if asset_kind == "video":
            return "native_footage", NATIVE_VIDEO_PROFILE
        return "photo_kenburns", PHOTO_PROFILE
    if scene_type in MOTION_PROFILES:
        return f"{scene_type}_kenburns", MOTION_PROFILES[scene_type]
    return "photo_kenburns", PHOTO_PROFILE


def assign_motion(shots: list[dict], details: list[dict] | None = None, *,
                  width: int = 1080) -> list[dict]:
    """Attach a scene-aware, continuous motion plan to already-resolved shots.

    Must run after assets are resolved (it needs the asset kind and scene type)
    and before rendering.  The first zoom of every shot equals the last zoom of
    the previous shot, so cuts do not visibly jump in scale.  Real video uses a
    fixed crop and keeps its native motion; stills use an eased Ken Burns move.
    """
    details = details or []
    previous_end_zoom: float | None = None
    previous_end_pan = (0.0, 0.0)
    motions: list[dict] = []
    for position, shot in enumerate(shots):
        detail = details[position] if position < len(details) else {}
        scene_type = str((detail or {}).get("scene_type") or shot.get("scene_type") or "footage")
        asset_kind = _asset_kind(detail)
        profile_name, profile = _motion_profile(
            scene_type, asset_kind, str((detail or {}).get("provider") or "")
        )
        duration = max(0.1, float(shot.get("duration") or 3.0))
        frames = max(1, int(round(duration * 30)))

        if profile["mode"] == "native":
            scale = _clamp(previous_end_zoom or 1.0, 1.0, NATIVE_VIDEO_MAX_SCALE)
            z0 = z1 = round(scale, 3)
            pan0 = pan1 = (0.0, 0.0)
        else:
            low = 1.0
            high = round(1.0 + float(profile["zoom_pct"]) / 100.0, 3)
            if previous_end_zoom is None:
                z0, z1 = low, high
            else:
                z0 = round(_clamp(previous_end_zoom, low, high), 3)
                if abs(z0 - high) <= 1e-3:
                    z1 = low
                elif abs(z0 - low) <= 1e-3:
                    z1 = high
                else:
                    z1 = low if z0 >= (low + high) / 2.0 else high
            amplitude = float(width) * float(profile["pan_pct"]) / 100.0
            if amplitude <= 0.5:
                pan0 = pan1 = (0.0, 0.0)
            else:
                px0 = _clamp(previous_end_pan[0], -amplitude, amplitude)
                py0 = _clamp(previous_end_pan[1], -amplitude / 2.0, amplitude / 2.0)
                px1 = -amplitude if px0 >= 0 else amplitude
                py1 = -amplitude / 2.0 if py0 >= 0 else amplitude / 2.0
                pan0 = (round(px0, 1), round(py0, 1))
                pan1 = (round(px1, 1), round(py1, 1))

            # Execute the creative director's camera movement on still/graphic
            # scenes; native stock video retains its real camera movement.
            camera_move = str(shot.get("camera_movement") or "").lower()
            if camera_move == "locked_off":
                z0 = z1 = 1.0
                pan0 = pan1 = (0.0, 0.0)
            elif camera_move == "slow_push_in":
                z0, z1 = 1.0, max(high, 1.10)
            elif camera_move == "slow_pull_back":
                z0, z1 = max(high, 1.10), 1.0
            elif camera_move == "lateral_dolly":
                z0 = z1 = max(high, 1.06)
                pan0, pan1 = (-amplitude, 0.0), (amplitude, 0.0)
            elif camera_move == "slow_drift":
                z0, z1 = 1.02, max(high, 1.06)
                pan0, pan1 = (0.0, -amplitude / 2.0), (0.0, amplitude / 2.0)
            elif camera_move == "subtle_handheld":
                z0, z1 = 1.02, 1.05
                pan0, pan1 = (-amplitude / 4.0, 0.0), (amplitude / 4.0, 0.0)
            elif camera_move == "rack_focus_simulated":
                z0, z1 = 1.03, max(high, 1.08)

        motion = {
            "profile": profile_name,
            "mode": profile["mode"],
            "scene_type": scene_type,
            "asset_kind": asset_kind,
            "zoom_from": z0,
            "zoom_to": z1,
            "pan": {"x0": pan0[0], "y0": pan0[1], "x1": pan1[0], "y1": pan1[1]},
            "ease": "smoothstep",
            "duration": round(duration, 3),
            "frames": frames,
        }
        shot["motion"] = motion
        # Keep the legacy keys meaningful for existing consumers/metadata.
        shot["scene_type"] = scene_type
        shot["zoom_from"] = z0
        shot["zoom_to"] = z1
        shot["pan"] = {
            "x": pan0[0], "y": pan0[1],
            "x0": pan0[0], "y0": pan0[1], "x1": pan1[0], "y1": pan1[1],
        }
        previous_end_zoom = z1
        previous_end_pan = pan1
        motions.append({
            "index": int(shot.get("index", position) or 0),
            "scene_type": scene_type,
            "asset_kind": asset_kind,
            "profile": profile_name,
            "mode": profile["mode"],
            "zoom_from": z0,
            "zoom_to": z1,
            "pan": dict(motion["pan"]),
            "duration": round(duration, 3),
        })
    return motions


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

    story_format = str(script.get("story_format") or os.getenv("NEXTDECODE_STORY_FORMAT", "auto")).strip().lower()
    visual_style = str(script.get("visual_style") or os.getenv("NEXTDECODE_VISUAL_STYLE", "auto")).strip().lower()
    beats = creative_director.direct_shots(
        beats, topic=str(script.get("topic") or script.get("title") or "short"),
        story_format=story_format, visual_style=visual_style,
    )

    if audio_duration is None:
        audio_duration = _estimate_duration_from_beats(beats)
    try:
        duration = max(5.0, float(audio_duration))
    except (TypeError, ValueError):
        duration = DEFAULT_DURATION

    count = max(MIN_SHOTS, math.ceil(duration / MAX_SHOT_DURATION))
    if len(beats) >= MIN_SHOTS:
        # Prefer one shot per beat: cycling the beat list repeats visuals.
        count = len(beats)
    seg = duration / count
    while seg < MIN_SHOT_DURATION and count > MIN_SHOTS:
        count -= 1
        seg = duration / count
    slots = _schedule(duration, count)

    shots: list[dict] = []
    topic = str(script.get("topic") or script.get("title") or "short").strip()
    previous_query = ""
    for i, (start, end) in enumerate(slots):
        beat = beats[i % len(beats)]
        text = _beat_text(beat)
        caption_text = text
        claim = ""
        beat_label = ""
        if isinstance(beat, dict):
            caption_text = str(beat.get("caption") or text)
            claim = str(beat.get("claim") or beat.get("text") or "")
            beat_label = str(beat.get("label") or beat.get("beat_label") or "")
        query = _visual_query(beat, i) or f"{topic} shot {i + 1}"
        variants = _query_variants(beat)
        if query.lower() == previous_query:
            alternative = next(
                (item for item in variants if item.lower() != previous_query),
                "",
            )
            if alternative:
                query = alternative
        previous_query = query.lower()
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
            "claim": claim or text,
            "beat_label": beat_label,
            "asset_query": query,
            "asset_query_variants": variants,
            "source": _pick_source(i, text),
            "caption": _truncate(caption_text, 42) or f"{topic} part {i + 1}",
            "zoom_from": z_from,
            "zoom_to": z_to,
            "pan": {"x": px, "y": py},
            "transition": "fade" if i in (0, count - 1) else "cut",
            "sfx": _pick_sfx(i, text, count),
            "music_gain_db": gain,
            "story_format": str(beat.get("story_format") or story_format),
            "visual_style": str(beat.get("visual_style") or visual_style),
            "visual_family": str(beat.get("visual_family") or "real_footage"),
            "shot_size": str(beat.get("shot_size") or "medium"),
            "camera_angle": str(beat.get("camera_angle") or "eye_level"),
            "camera_movement": str(beat.get("camera_movement") or "slow_push_in"),
            "camera_instruction": str(beat.get("camera_instruction") or ""),
            "lighting_direction": str(beat.get("lighting_direction") or ""),
            "composition_direction": str(beat.get("composition_direction") or ""),
            "editing_rhythm": str(beat.get("editing_rhythm") or "motivated_fast_cuts"),
            "transition_intent": str(beat.get("transition_intent") or "cut"),
            "continuity_group": str(beat.get("continuity_group") or ""),
            "editorial_reason": str(beat.get("editorial_reason") or ""),
            # Explicitly selected generated clips flow through the normal resolver.
            # Generation itself is never initiated by the renderer.
            **({"generated_video_asset": str(beat.get("generated_video_asset") or "").strip()}
               if isinstance(beat, dict) and str(beat.get("generated_video_asset") or "").strip()
               else {}),
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
        "claim": text,
        "beat_label": "",
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
