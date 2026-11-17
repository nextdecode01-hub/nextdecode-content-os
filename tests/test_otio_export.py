from pathlib import Path

import pytest
import opentimelineio as otio

from app.render.otio_export import export_edl_to_otio


def _edl(media: Path) -> dict:
    return {
        "schema": "nextdecode.edl.v1",
        "timebase": {"fps_num": 30, "fps_den": 1},
        "clips": [
            {
                "clip_id": "scene-01",
                "timeline": {"start_frame": 0, "end_frame": 45},
                "source": {"path": str(media), "kind": "video", "in_seconds": 1.0, "out_seconds": 2.5},
                "creative_direction": {"shot_size": "close_up", "camera_angle": "low_angle"},
                "editorial_reason": "hook: mini documentary",
            }
        ],
    }


def test_export_edl_to_otio_preserves_source_range_and_creator_metadata(tmp_path):
    media = tmp_path / "source.mp4"
    media.write_bytes(b"media")
    output = export_edl_to_otio(_edl(media), tmp_path / "edit.otio")
    timeline = otio.adapters.read_from_file(str(output))
    track = timeline.tracks[0]
    assert len(track) == 1
    clip = track[0]
    assert isinstance(clip, otio.schema.Clip)
    assert clip.source_range.start_time.value == 30
    assert clip.source_range.duration.value == 45
    assert clip.metadata["nextdecode"]["creative_direction"]["camera_angle"] == "low_angle"


def test_export_edl_blocks_missing_media_unless_gap_mode_is_explicit(tmp_path):
    edl = _edl(tmp_path / "missing.mp4")
    with pytest.raises(FileNotFoundError, match="media missing"):
        export_edl_to_otio(edl, tmp_path / "blocked.otio")
    output = export_edl_to_otio(edl, tmp_path / "review.otio", allow_missing_media=True)
    timeline = otio.adapters.read_from_file(str(output))
    gap = timeline.tracks[0][0]
    assert isinstance(gap, otio.schema.Gap)
    assert gap.metadata["nextdecode"]["missing_media"] is True
