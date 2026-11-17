"""Deterministic, renderer-facing edit decisions for the existing timeline.

M1 adds a pre-render decision layer without replacing nextdecode.timeline.v1.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from app.render.ffmpeg_tools import (
    _black_intervals,
    _probe_duration,
    _run,
)


def _frame(seconds: float, fps: int) -> int:
    return int(round(float(seconds) * fps))


def _probe_video(path: Path) -> dict[str, Any]:
    """Read rendered video stream duration, dimensions, rate and frame count."""
    completed = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration",
        "-show_entries", "format=duration", "-of", "json", str(path),
    ], capture_output=True, text=True, timeout=30, check=True)
    payload = json.loads(completed.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        raise RuntimeError(f"EDL execution QA: rendered clip has no video stream: {path}")
    stream = streams[0]
    raw_duration = stream.get("duration") or (payload.get("format") or {}).get("duration")
    return {"duration_seconds": float(raw_duration or 0),
            "width": int(stream.get("width") or 0), "height": int(stream.get("height") or 0),
            "frame_rate": str(stream.get("avg_frame_rate") or stream.get("r_frame_rate") or ""),
            "frame_count": int(stream.get("nb_frames") or 0)}


def validate_rendered_clip(path: Path, decision: dict[str, Any], *, fps: int = 30) -> dict[str, Any]:
    """Fail closed when an executed clip is missing or diverges from its EDL allocation."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size <= 1000:
        raise RuntimeError(f"EDL execution QA: rendered clip is missing or too small: {path}")
    actual = _probe_video(path)
    expected = float(decision["timeline"]["duration_seconds"])
    tolerance = max(1.0 / fps, 0.04)
    if actual["duration_seconds"] <= 0 or abs(actual["duration_seconds"] - expected) > tolerance:
        raise RuntimeError(
            f"EDL execution QA: duration mismatch for {decision['clip_id']}: expected {expected:.3f}s, "
            f"got {actual['duration_seconds']:.3f}s (tolerance {tolerance:.3f}s)"
        )
    if actual["width"] <= 0 or actual["height"] <= 0:
        raise RuntimeError(f"EDL rendered clip has invalid dimensions: {path}")
    return {"status": "pass", "expected_duration_seconds": expected,
            "actual_duration_seconds": round(actual["duration_seconds"], 6),
            "duration_delta_seconds": round(actual["duration_seconds"] - expected, 6),
            **actual}


def validate_final_output(path: Path, edl: dict[str, Any], timeline: dict[str, Any], *, fps: int | None = None) -> dict[str, Any]:
    """Validate assembled media, frame clock, audio coverage and visual continuity."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size <= 1000:
        raise RuntimeError(f"EDL delivery QA: final output is missing or too small: {path}")
    clips = list(edl.get("clips") or [])
    tracks = {str(track.get("kind")): track for track in timeline.get("tracks") or []}
    picture = list((tracks.get("video") or {}).get("clips") or [])
    if not clips or len(clips) != len(picture):
        raise RuntimeError("EDL delivery QA: EDL and timeline clip counts differ")
    expected_fps = int(fps or (edl.get("timebase") or {}).get("fps_num") or 30)
    cursor = 0
    for index, (decision, clip) in enumerate(zip(clips, picture)):
        timing = decision.get("timeline") or {}
        start, end = int(timing.get("start_frame", -1)), int(timing.get("end_frame", -1))
        if start != cursor or end <= start:
            raise RuntimeError(f"EDL delivery QA: non-contiguous EDL allocation at clip {index}")
        if int(clip.get("start_frame", -1)) != start or int(clip.get("end_frame", -1)) != end:
            raise RuntimeError(f"EDL delivery QA: timeline frame allocation differs at clip {index}")
        if str(clip.get("edl_clip_id") or "") != str(decision.get("clip_id") or ""):
            raise RuntimeError(f"EDL delivery QA: timeline clip identity differs at clip {index}")
        if (decision.get("execution_qa") or {}).get("status") != "pass":
            raise RuntimeError(f"EDL delivery QA: clip {index} has no passing execution QA")
        cursor = end
    expected_frames = int(edl.get("duration_frames") or 0)
    if cursor != expected_frames or int(timeline.get("duration_frames") or 0) != expected_frames:
        raise RuntimeError("EDL delivery QA: EDL and timeline total frame counts differ")
    completed = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,avg_frame_rate,r_frame_rate,nb_frames,duration,duration_ts,time_base:format=duration,size", "-of", "json", str(path)], capture_output=True, text=True, timeout=30, check=True)
    payload = json.loads(completed.stdout or "{}")
    streams = payload.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video or not audio:
        raise RuntimeError("EDL delivery QA: final output must contain both video and audio streams")
    actual_duration = float(video.get("duration") or (payload.get("format") or {}).get("duration") or 0)
    audio_duration = float(audio.get("duration") or 0)
    if not audio_duration and audio.get("duration_ts") and audio.get("time_base"):
        audio_duration = float(audio["duration_ts"]) * float(Fraction(str(audio["time_base"])))
    expected_duration = expected_frames / expected_fps
    tolerance = max(1.0 / expected_fps, 0.05)
    if abs(actual_duration - expected_duration) > tolerance:
        raise RuntimeError(f"EDL delivery QA: final duration mismatch; expected {expected_duration:.3f}s, got {actual_duration:.3f}s")
    if audio_duration <= 0 or abs(audio_duration - expected_duration) > tolerance:
        raise RuntimeError(f"EDL delivery QA: audio duration mismatch; expected {expected_duration:.3f}s, got {audio_duration:.3f}s")
    canvas = edl.get("canvas") or {}
    width, height = int(video.get("width") or 0), int(video.get("height") or 0)
    if width != int(canvas.get("width") or width) or height != int(canvas.get("height") or height):
        raise RuntimeError("EDL delivery QA: final dimensions differ from EDL canvas")
    raw_rate = str(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/0")
    try:
        actual_fps = float(Fraction(raw_rate))
    except (ValueError, ZeroDivisionError):
        actual_fps = 0.0
    if abs(actual_fps - expected_fps) > 0.01:
        raise RuntimeError(f"EDL delivery QA: frame-rate mismatch; expected {expected_fps}fps, got {raw_rate}")
    frame_count = int(video.get("nb_frames") or 0)
    if frame_count and abs(frame_count - expected_frames) > 1:
        raise RuntimeError(f"EDL delivery QA: encoded frame count mismatch; expected {expected_frames}, got {frame_count}")

    # Ignore intentional opening/closing fade-to-black intervals. Interior black
    # intervals are a hard defect; freeze intervals are evidence-only because
    # static cards/stills may be intentional and must not be falsely rejected.
    black_hits = _black_intervals(path, min_duration=0.25, pix_th=0.04)
    first_fade = int((clips[0].get("transition_in") or {}).get("duration_frames") or 0) / expected_fps
    last_fade = int((clips[-1].get("transition_out") or {}).get("duration_frames") or 0) / expected_fps
    interior_black = []
    intentional_fade_black = []
    for start, end in black_hits:
        if (first_fade and start <= first_fade + tolerance) or (last_fade and end >= expected_duration - last_fade - tolerance):
            intentional_fade_black.append((round(start, 3), round(end, 3)))
        else:
            interior_black.append((round(start, 3), round(end, 3)))
    if interior_black:
        raise RuntimeError(f"EDL delivery QA: interior black intervals detected: {interior_black}")

    # Freeze analysis is restricted to timeline ranges sourced from video.
    # Still-image and generated-card intervals are intentionally excluded.
    video_ranges = []
    for decision in clips:
        if (decision.get("source") or {}).get("kind") == "video":
            timing = decision.get("timeline") or {}
            video_ranges.append((int(timing.get("start_frame", 0)) / expected_fps,
                                 int(timing.get("end_frame", 0)) / expected_fps))
    freeze_hits = []
    if video_ranges:
        for start, end in _detect_frozen_intervals(path, min_duration=1.0):
            if any(start < right and end > left for left, right in video_ranges):
                freeze_hits.append((round(start, 3), round(end, 3)))
    visual_qa = {
        "status": "warning" if freeze_hits else "pass",
        "interior_black_intervals": interior_black,
        "intentional_fade_black_intervals": intentional_fade_black,
        "frozen_video_intervals": freeze_hits,
        "still_and_generated_intervals_excluded_from_freeze_gate": True,
    }
    return {"status": "pass", "expected_frames": expected_frames,
            "expected_duration_seconds": round(expected_duration, 6),
            "actual_duration_seconds": round(actual_duration, 6),
            "audio_duration_seconds": round(audio_duration, 6),
            "width": width, "height": height, "frame_rate": raw_rate,
            "frame_count": frame_count, "clip_count": len(clips),
            "audio_stream_present": True, "video_stream_present": True,
            "visual_qa": visual_qa}


def _select_source_segment(shot: dict, detail: dict, duration: float, media_duration: float | None, prior_ranges: list[tuple[float, float]]) -> dict[str, Any]:
    """Choose a deterministic source window; never invent semantic relevance."""
    explicit_in, explicit_out = shot.get("source_in"), shot.get("source_out")
    if explicit_in is not None or explicit_out is not None:
        start = float(explicit_in if explicit_in is not None else 0.0)
        end = float(explicit_out if explicit_out is not None else start + duration)
        return {"in_seconds": start, "out_seconds": end, "selection": "explicit_shot_override",
                "score": None, "candidate_count": 1, "rationale": "Shot-level source range explicitly supplied"}
    usable = max(0.0, float(media_duration or 0.0))
    length = min(duration, usable) if usable else duration
    max_start = max(0.0, usable - length)
    supplied = shot.get("source_segment_candidates") or detail.get("source_segment_candidates") or []
    candidates = []
    if isinstance(supplied, list):
        for item in supplied:
            if not isinstance(item, dict):
                continue
            try:
                start = float(item.get("in_seconds", item.get("start", 0)))
                end = float(item.get("out_seconds", item.get("end", start + length)))
                score = float(item.get("score", item.get("relevance_score", 0)) or 0)
            except (TypeError, ValueError):
                continue
            if start >= 0 and end > start and end-start >= min(length, 0.25) and (not usable or end <= usable + 1e-6):
                candidates.append({"in": start, "out": min(end, start+length), "score": score})
    if not candidates:
        starts = sorted(set([0.0, round(max_start/2, 6), round(max_start, 6)]))
        candidates = [{"in": x, "out": x+length, "score": 0.0} for x in starts]
    def overlaps(c):
        return any(c["in"] < end and c["out"] > start for start, end in prior_ranges)
    nonoverlap = [c for c in candidates if not overlaps(c)]
    pool = nonoverlap or candidates
    chosen = sorted(pool, key=lambda c: (-c["score"], c["in"], c["out"]))[0]
    rationale = "Highest-scoring supplied candidate" if supplied and candidates else "Deterministic earliest usable window"
    if nonoverlap and len(nonoverlap) < len(candidates):
        rationale += "; avoided adjacent source-range reuse"
    return {"in_seconds": round(chosen["in"], 6), "out_seconds": round(chosen["out"], 6),
            "selection": "metadata_candidate" if supplied and candidates else "deterministic_window",
            "score": chosen["score"] if supplied and candidates else None,
            "candidate_count": len(candidates), "rationale": rationale}


def _detect_frozen_intervals(path: Path, *, min_duration: float = 0.5) -> list[tuple[float, float]]:
    """Parse FFmpeg freezedetect events, including its freeze_duration field."""
    try:
        completed = subprocess.run([
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
            "-vf", f"freezedetect=n=0.003:d={min_duration}", "-an", "-f", "null", "-",
        ], capture_output=True, text=True, timeout=300)
    except Exception:
        return []
    log = (completed.stderr or "") + (completed.stdout or "")
    events = list(re.finditer(
        r"freeze_start:\s*(-?\d+(?:\.\d+)?)(.*?)(?=freeze_start:|$)", log, re.DOTALL
    ))
    intervals = []
    for event in events:
        start = float(event.group(1))
        detail = event.group(2)
        end_match = re.search(r"freeze_end:\s*(-?\d+(?:\.\d+)?)", detail)
        duration_match = re.search(r"freeze_duration:\s*(\d+(?:\.\d+)?)", detail)
        end = float(end_match.group(1)) if end_match else (
            start + float(duration_match.group(1)) if duration_match else _probe_duration(path)
        )
        intervals.append((start, end))
    return intervals


def _inspect_source_segment(path: str | Path | None, source_in: float, source_out: float,
                            media_duration: float | None, fps: int) -> dict[str, Any]:
    """Attach deterministic FFmpeg black/freeze evidence for a selected source window."""
    if not path or not media_duration or media_duration <= 0:
        return {"status": "not_checked", "reason": "source media could not be probed"}
    source = Path(path)
    if not source.is_file():
        return {"status": "not_checked", "reason": "source file is unavailable"}
    try:
        black = _black_intervals(source, min_duration=0.25, pix_th=0.04)
        frozen = _detect_frozen_intervals(source, min_duration=0.5)
        segment_duration = max(0.0, source_out-source_in)
        last_frame = max(0, int(round(segment_duration*fps))-1)
        middle_frame = max(0, last_frame//2)
        sampled = subprocess.run([
            "ffmpeg", "-v", "error", "-ss", str(source_in), "-i", str(source),
            "-t", str(segment_duration), "-vf",
            f"select='eq(n,0)+eq(n,{middle_frame})+eq(n,{last_frame})'",
            "-vsync", "0", "-f", "framemd5", "-",
        ], capture_output=True, text=True, timeout=90, check=True)
        sample_hashes = [line.rsplit(",", 1)[-1].strip() for line in sampled.stdout.splitlines()
                         if line.strip() and not line.lstrip().startswith("#") and "," in line]
    except Exception as exc:
        return {"status": "not_checked", "reason": f"analysis_error:{type(exc).__name__}"}

    def intersect(intervals: list[tuple[float, float]]) -> list[dict[str, float]]:
        result = []
        for start, end in intervals:
            left, right = max(float(start), source_in), min(float(end), source_out)
            if right > left:
                result.append({"start_seconds": round(left, 3), "end_seconds": round(right, 3),
                               "duration_seconds": round(right-left, 3)})
        return result

    black_hits, frozen_hits = intersect(black), intersect(frozen)
    duration = max(0.0, source_out-source_in)
    black_total = sum(x["duration_seconds"] for x in black_hits)
    frozen_total = sum(x["duration_seconds"] for x in frozen_hits)
    unusable = duration > 0 and (black_total >= duration - 1.0/fps or frozen_total >= duration - 1.0/fps)
    warnings = []
    if black_hits:
        warnings.append("black_frames_detected")
    if frozen_hits:
        warnings.append("frozen_frames_detected")
    if len(sample_hashes) < 3:
        warnings.append("incomplete_frame_sampling")
    return {
        "status": "unusable" if unusable else "warning" if warnings else "pass",
        "scan": "ffmpeg_blackdetect_freezedetect",
        "sample_points_seconds": [round(source_in, 3), round(source_in+middle_frame/fps, 3),
                                  round(source_in+last_frame/fps, 3)],
        "sampled_frame_count": len(sample_hashes),
        "sampled_frame_hashes": sample_hashes,
        "black_intervals": black_hits,
        "frozen_intervals": frozen_hits,
        "warnings": warnings,
        "fail_closed": bool(unusable),
    }


def build_edit_decisions(resolved_scenes: list[dict], motion_plan: list[dict] | None = None,
                         *, fps: int = 30, width: int = 1080,
                         height: int = 1920) -> dict[str, Any]:
    """Create and validate a pre-render EDL from resolved scene assets."""
    if fps <= 0 or width <= 0 or height <= 0:
        raise ValueError("EDL frame rate and canvas dimensions must be positive")
    if not resolved_scenes:
        raise ValueError("EDL requires at least one resolved scene")
    motion_by_index = {int(x.get("index", -1)): x for x in (motion_plan or [])
                       if isinstance(x, dict)}
    clips, cursor = [], 0
    prior_source_ranges: dict[str, list[tuple[float, float]]] = {}
    for position, item in enumerate(resolved_scenes):
        shot, asset = item.get("shot") or {}, item.get("asset_path")
        detail = item.get("detail") or {}
        start, end = _frame(shot.get("start", 0), fps), _frame(shot.get("end", 0), fps)
        if start != cursor or end <= start:
            raise ValueError(f"EDL discontinuity or invalid range at shot {position}: expected {cursor}, got {start}..{end}")
        duration, index = (end - start) / fps, int(shot.get("index", position))
        suffix = Path(asset).suffix.lower() if asset else ""
        kind = "video" if suffix in {".mp4", ".mov", ".mkv", ".webm", ".avi"} else "image" if asset else "generated"
        media_duration = _probe_duration(Path(asset)) if kind == "video" and asset and Path(asset).is_file() else None
        asset_key = str(Path(asset).resolve()) if asset else ""
        selected = _select_source_segment(shot, detail, duration, media_duration,
            prior_source_ranges.setdefault(asset_key, []) if asset_key else [])
        source_in, source_out = selected["in_seconds"], selected["out_seconds"]
        if source_in < 0 or source_out <= source_in:
            raise ValueError(f"shot {index} has an invalid source range")
        if media_duration and source_out > media_duration + (1.0 / fps):
            raise ValueError(f"shot {index} source_out {source_out:.3f}s exceeds media duration {media_duration:.3f}s")
        if asset_key:
            prior_source_ranges[asset_key].append((source_in, source_out))
        transition = str(shot.get("transition") or "cut").lower()
        edge_fade_in = transition == "fade" and position == 0
        edge_fade_out = transition == "fade" and position == len(resolved_scenes) - 1
        if transition not in {"cut", "fade"} or (transition == "fade" and not (edge_fade_in or edge_fade_out)):
            raise ValueError(f"unsupported transition for M1 executor at shot {index}: {transition}")
        clips.append({
            "clip_id": str(shot.get("shot_id") or f"shot-{index:03d}"),
            "shot_index": index,
            "fps": fps,
            "timeline": {"start_frame": start, "end_frame": end, "duration_frames": end-start,
                         "start_seconds": round(start/fps, 6), "duration_seconds": round(duration, 6)},
            "source": {"path": str(Path(asset).resolve()) if asset else None, "kind": kind,
                       "in_seconds": source_in, "out_seconds": source_out,
                       "selection": selected["selection"], "selection_score": selected["score"],
                       "candidate_count": selected["candidate_count"],
                       "selection_rationale": selected["rationale"],
                       "media_duration_seconds": media_duration,
                       "qa": _inspect_source_segment(asset, source_in, source_out, media_duration, fps)},
            "framing": dict(shot.get("framing") or {"mode": "fill", "width": width, "height": height}),
            "creative_direction": {
                key: shot.get(key) for key in (
                    "story_format", "visual_style", "visual_family", "shot_size",
                    "camera_angle", "camera_movement", "camera_instruction",
                    "lighting_direction", "composition_direction", "editing_rhythm",
                    "transition_intent", "continuity_group", "editorial_reason",
                ) if shot.get(key) is not None
            },
            "motion": dict(motion_by_index.get(index) or shot.get("motion") or {}),
            "transition_in": {"type": "fade" if edge_fade_in else "cut",
                               "duration_frames": min(12, max(1, (end-start)//3)) if edge_fade_in else 0},
            "transition_out": {"type": "fade" if edge_fade_out else "cut",
                                "duration_frames": min(12, max(1, (end-start)//3)) if edge_fade_out else 0},
            "narration": {"text": str(shot.get("claim") or shot.get("caption") or ""),
                          "start_frame": start, "end_frame": end},
            "editorial_reason": str(shot.get("editorial_reason") or shot.get("visual_intent") or ""),
        })
        cursor = end
    return {"schema": "nextdecode.edl.v1", "timebase": {"fps_num": fps, "fps_den": 1},
            "canvas": {"width": width, "height": height}, "duration_frames": cursor,
            "duration_seconds": round(cursor/fps, 6),
            "execution": {"renderer": "ffmpeg", "transition_support": ["cut", "edge_fade"]}, "clips": clips}


def write_edl(path: Path, edl: dict[str, Any]) -> Path:
    """Atomically persist the pre-render EDL."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(edl, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try: os.unlink(temp_name)
        except OSError: pass
        raise
    return path


def execute_clip(decision: dict[str, Any], render_fn: Callable[..., Path], shot: dict,
                 asset_path: Path | None, work_dir: Path, **render_kwargs: Any) -> Path:
    """Execute EDL source trims, then pass the selected segment to the visual renderer."""
    source, render_asset = decision["source"], Path(asset_path) if asset_path else None
    qa = source.get("qa") or {}
    # DRY_RUN fixtures deliberately use generated placeholder footage; retain QA
    # evidence but do not let synthetic fixture artifacts block mechanics tests.
    if qa.get("fail_closed") and os.getenv("DRY_RUN", "").strip().lower() not in {"1", "true", "yes", "on"}:
        raise RuntimeError(f"EDL source segment {decision['clip_id']} failed visual QA: {qa.get('warnings', [])}")
    execution_shot = dict(shot)
    timing = decision["timeline"]
    execution_shot.update({
        "start": timing["start_seconds"],
        "end": timing["start_seconds"] + timing["duration_seconds"],
        "duration": timing["duration_seconds"],
        "motion": dict(decision.get("motion") or {}),
        "framing": dict(decision.get("framing") or {}),
        "creative_direction": dict(decision.get("creative_direction") or {}),
        "edl_transition": {
            "in": decision.get("transition_in", {}).get("type") == "fade",
            "out": decision.get("transition_out", {}).get("type") == "fade",
            "duration_frames": max(
                int(decision.get("transition_in", {}).get("duration_frames", 0)),
                int(decision.get("transition_out", {}).get("duration_frames", 0)),
            ),
        },
    })
    if render_asset and source["kind"] == "video":
        source_in, source_out = float(source["in_seconds"]), float(source["out_seconds"])
        duration = source_out - source_in
        if duration <= 0:
            raise ValueError(f"EDL clip {decision['clip_id']} has invalid source duration")
        trimmed = Path(work_dir) / f"edl_source_{int(decision['shot_index']):03d}.mp4"
        _run(["ffmpeg", "-y", "-ss", str(source_in), "-i", str(render_asset), "-t", str(duration),
              "-map", "0:v:0", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
              "-pix_fmt", "yuv420p", str(trimmed)])
        if not trimmed.is_file() or trimmed.stat().st_size <= 1000:
            raise RuntimeError(f"EDL source trim failed for {decision['clip_id']}")
        render_asset = trimmed
    rendered = Path(render_fn(execution_shot, render_asset, work_dir, **render_kwargs))
    decision["execution_qa"] = validate_rendered_clip(rendered, decision, fps=int(decision.get("fps", 30)))
    return rendered
