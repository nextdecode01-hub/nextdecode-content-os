"""OpenTimelineIO interchange export for approved NEXTDECODE edit decisions.

This is an editorial hand-off format, not a replacement renderer. FFmpeg remains
the execution engine; OTIO gives an NLE an inspectable frame-accurate timeline.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def export_edl_to_otio(edl: dict[str, Any], output_path: str | Path, *, allow_missing_media: bool = False) -> Path:
    try:
        import opentimelineio as otio
    except ImportError as exc:
        raise RuntimeError("OpenTimelineIO is not installed; install requirements.txt to export .otio") from exc

    if edl.get("schema") != "nextdecode.edl.v1":
        raise ValueError("unsupported edit-decision schema")
    fps = int((edl.get("timebase") or {}).get("fps_num") or 0)
    fps_den = int((edl.get("timebase") or {}).get("fps_den") or 1)
    if fps <= 0 or fps_den <= 0:
        raise ValueError("EDL timebase must be positive")
    rate = fps / fps_den
    timeline = otio.schema.Timeline(name="NEXTDECODE approved edit")
    video = otio.schema.Track(name="V1 - picture", kind=otio.schema.TrackKind.Video)
    for item in edl.get("clips") or []:
        timing = item.get("timeline") or {}
        source = item.get("source") or {}
        creative = item.get("creative_direction") or {}
        start = int(timing.get("start_frame") or 0)
        end = int(timing.get("end_frame") or 0)
        if start < 0 or end <= start:
            raise ValueError(f"invalid timeline range for {item.get('clip_id')}")
        duration = end - start
        path = str(source.get("path") or "")
        media_kind = str(source.get("kind") or "generated")
        if path and Path(path).is_file():
            source_in = max(0.0, float(source.get("in_seconds") or 0.0))
            source_duration = max(0.0, float(source.get("out_seconds") or source_in) - source_in)
            source_start_frames = round(source_in * rate)
            source_duration_frames = max(1, round(source_duration * rate)) if source_duration else duration
            ref = otio.schema.ExternalReference(target_url=Path(path).resolve().as_uri())
            clip = otio.schema.Clip(
                name=str(item.get("clip_id") or f"shot-{start}"),
                media_reference=ref,
                source_range=otio.opentime.TimeRange(
                    start_time=otio.opentime.RationalTime(source_start_frames, rate),
                    duration=otio.opentime.RationalTime(source_duration_frames, rate),
                ),
            )
            clip.metadata["nextdecode"] = {
                "source_kind": media_kind,
                "timeline_start_frame": start,
                "timeline_end_frame": end,
                "creative_direction": creative,
                "editorial_reason": str(item.get("editorial_reason") or ""),
            }
            video.append(clip)
        else:
            if not allow_missing_media:
                raise FileNotFoundError(f"EDL media missing for {item.get('clip_id')}: {path or 'no source path'}")
            gap = otio.schema.Gap(
                name=f"Missing media: {item.get('clip_id')}",
                source_range=otio.opentime.TimeRange(
                    start_time=otio.opentime.RationalTime(0, rate),
                    duration=otio.opentime.RationalTime(duration, rate),
                ),
            )
            gap.metadata["nextdecode"] = {
                "missing_media": True, "source_kind": media_kind,
                "timeline_start_frame": start, "timeline_end_frame": end,
                "creative_direction": creative,
            }
            video.append(gap)
    timeline.tracks.append(video)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    otio.adapters.write_to_file(timeline, str(output))
    return output
