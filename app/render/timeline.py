"""Frame-accurate editorial timeline manifest for NEXTDECODE renders.

The manifest is the renderer-independent edit decision record. It keeps picture,
voice, music, effects, captions and director metadata on one integer frame clock.
It deliberately references media instead of embedding it, so a future editor or
OpenTimelineIO adapter can consume the same edit without reverse-engineering MP4.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

TIMELINE_SCHEMA = "nextdecode.timeline.v1"


def _frame(seconds: float, fps: int) -> int:
    return int(round(float(seconds) * int(fps)))


def _sha256(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _media_ref(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    path = Path(path)
    if not path.is_file():
        return {"path": str(path), "exists": False, "sha256": ""}
    return {
        "path": str(path.resolve()),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def build_timeline(
    shots: list[dict],
    shot_files: list[Path],
    *,
    voice_path: Path,
    mixed_audio_path: Path,
    music_path: Path | None = None,
    sfx_timed: list[tuple[float, Path]] | None = None,
    ass_path: Path | None = None,
    caption_words_path: Path | None = None,
    motion_plan: list[dict] | None = None,
    storyboard: dict | None = None,
    edit_decisions: dict[str, Any] | None = None,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
) -> dict[str, Any]:
    """Build and validate a multi-track timeline using integer frame positions."""
    if fps <= 0 or width <= 0 or height <= 0:
        raise ValueError("timeline dimensions and frame rate must be positive")
    if not shots or len(shots) != len(shot_files):
        raise ValueError("timeline requires one rendered media segment per shot")

    video_clips: list[dict[str, Any]] = []
    edl_by_index = {
        int(item.get("shot_index", -1)): item
        for item in ((edit_decisions or {}).get("clips") or [])
        if isinstance(item, dict)
    }
    cursor = 0
    for position, (shot, media_path) in enumerate(zip(shots, shot_files)):
        start = _frame(float(shot.get("start", 0.0)), fps)
        end = _frame(float(shot.get("end", 0.0)), fps)
        declared_duration = float(shot.get("duration", 0.0))
        duration = end - start
        if end <= start or duration <= 0:
            raise ValueError(f"shot {position} has a non-positive frame duration")
        if start != cursor:
            raise ValueError(
                f"shot timeline discontinuity at shot {position}: "
                f"expected frame {cursor}, got {start}"
            )
        if abs((end - start) / fps - declared_duration) > (1.0 / fps):
            raise ValueError(
                f"shot {position} duration does not match its start/end frame range"
            )
        media = _media_ref(Path(media_path))
        if not media or not media["exists"]:
            raise ValueError(f"rendered shot media is missing: {media_path}")
        edl_clip = edl_by_index.get(int(shot.get("index", position)), {})
        source_decision = edl_clip.get("source") or {}
        video_clips.append({
            "clip_id": str(shot.get("shot_id") or f"shot-{position:03d}"),
            "shot_index": int(shot.get("index", position)),
            "start_frame": start,
            "end_frame": end,
            "duration_frames": duration,
            "start_seconds": round(start / fps, 6),
            "end_seconds": round(end / fps, 6),
            "media": media,
            "source_asset": str(source_decision.get("path") or shot.get("asset_path") or ""),
            "narration": str(shot.get("claim") or shot.get("caption") or ""),
            # Preserve the v1 string field; richer executable details are additive.
            "transition_in": str((edl_clip.get("transition_in") or {}).get("type") or shot.get("transition") or "cut"),
            "transition_in_detail": dict(edl_clip.get("transition_in") or {"type": str(shot.get("transition") or "cut"), "duration_frames": 0}),
            "transition_out": dict(edl_clip.get("transition_out") or {"type": "cut", "duration_frames": 0}),
            "source_range": {"in_seconds": source_decision.get("in_seconds", 0.0),
                             "out_seconds": source_decision.get("out_seconds", duration / fps)},
            "framing": dict(edl_clip.get("framing") or {}),
            "edl_clip_id": str(edl_clip.get("clip_id") or ""),
            "motion": dict(edl_clip.get("motion") or shot.get("motion") or {}),
            "source_qa": dict(source_decision.get("qa") or {}),
            "execution_qa": dict(edl_clip.get("execution_qa") or {"status": "not_recorded"}),
        })
        cursor = end

    motion_by_index = {
        int(item.get("index", -1)): item
        for item in (motion_plan or [])
        if isinstance(item, dict)
    }
    for clip in video_clips:
        clip["director_motion"] = motion_by_index.get(clip["shot_index"], {})

    sfx_clips = []
    for position, (start_seconds, media_path) in enumerate(sfx_timed or []):
        start = _frame(float(start_seconds), fps)
        if start < 0 or start >= cursor:
            raise ValueError(f"SFX event {position} starts outside the picture timeline")
        media = _media_ref(Path(media_path))
        if not media or not media["exists"]:
            raise ValueError(f"SFX media is missing: {media_path}")
        sfx_clips.append({
            "clip_id": f"sfx-{position:03d}",
            "start_frame": start,
            "start_seconds": round(start / fps, 6),
            "media": media,
        })

    voice = _media_ref(Path(voice_path))
    mixed = _media_ref(Path(mixed_audio_path))
    if not voice or not voice["exists"]:
        raise ValueError(f"voice track is missing: {voice_path}")
    if not mixed or not mixed["exists"]:
        raise ValueError(f"mixed audio track is missing: {mixed_audio_path}")

    word_cues: list[dict[str, Any]] = []
    if caption_words_path:
        words_payload = json.loads(Path(caption_words_path).read_text(encoding="utf-8"))
        for position, word in enumerate(words_payload.get("words") or []):
            start = _frame(float(word.get("start", 0.0)), fps)
            end = _frame(float(word.get("end", 0.0)), fps)
            if start < 0 or end <= start or end > cursor + fps:
                raise ValueError(f"caption word {position} has invalid timing")
            word_cues.append({
                "word_index": position,
                "text": str(word.get("word") or ""),
                "start_frame": start,
                "end_frame": end,
                "start_seconds": round(start / fps, 6),
                "end_seconds": round(end / fps, 6),
            })

    return {
        "schema": TIMELINE_SCHEMA,
        "timebase": {"fps_num": fps, "fps_den": 1, "drop_frame": False},
        "canvas": {"width": width, "height": height, "pixel_aspect": "1:1"},
        "duration_frames": cursor,
        "duration_seconds": round(cursor / fps, 6),
        "tracks": [
            {"track_id": "V1", "kind": "video", "clips": video_clips},
            {"track_id": "A1", "kind": "voice", "clips": [{
                "clip_id": "voiceover",
                "start_frame": 0,
                "end_frame": cursor,
                "media": voice,
            }]},
            {"track_id": "A2", "kind": "music", "clips": (
                [{"clip_id": "music-bed", "start_frame": 0,
                  "end_frame": cursor, "media": _media_ref(Path(music_path))}]
                if music_path else []
            )},
            {"track_id": "A3", "kind": "sfx", "clips": sfx_clips},
            {"track_id": "C1", "kind": "captions", "clips": (
                [{"clip_id": "burned-captions", "start_frame": 0,
                  "end_frame": cursor, "format": "ass",
                  "media": _media_ref(Path(ass_path)),
                  "word_cues": word_cues}]
                if ass_path else (
                    [{"clip_id": "word-cues", "start_frame": 0,
                      "end_frame": cursor, "format": "json",
                      "word_cues": word_cues}] if word_cues else []
                )
            )},
        ],
        "rendered_mix": mixed,
        "edit_decisions": {
            "schema": str((edit_decisions or {}).get("schema") or ""),
            "duration_frames": int((edit_decisions or {}).get("duration_frames") or 0),
            "clip_count": len((edit_decisions or {}).get("clips") or []),
        },
        "director": {
            "motion_plan": list(motion_plan or []),
            "storyboard_status": str((storyboard or {}).get("review_status") or "not_generated"),
            "human_approved": bool((storyboard or {}).get("human_approved")),
        },
    }


def write_timeline(path: Path, timeline: dict[str, Any]) -> Path:
    """Atomically persist a validated timeline manifest."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(timeline, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return path
