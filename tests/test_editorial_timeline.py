from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.render.timeline import TIMELINE_SCHEMA, build_timeline, write_timeline


def _media(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.write_bytes((name + "-fixture").encode())
    return path


def _fixture(tmp_path: Path):
    shot_a = _media(tmp_path, "shot-a.mp4")
    shot_b = _media(tmp_path, "shot-b.mp4")
    voice = _media(tmp_path, "voice.wav")
    mixed = _media(tmp_path, "mix.wav")
    music = _media(tmp_path, "music.wav")
    sfx = _media(tmp_path, "impact.wav")
    ass = _media(tmp_path, "captions.ass")
    shots = [
        {"index": 0, "shot_id": "s00", "start": 0, "end": 1.5,
         "duration": 1.5, "claim": "The opening.", "transition": "cut"},
        {"index": 1, "shot_id": "s01", "start": 1.5, "end": 3.0,
         "duration": 1.5, "claim": "The payoff.", "transition": "cut"},
    ]
    return shots, [shot_a, shot_b], voice, mixed, music, sfx, ass


def test_builds_frame_accurate_multitrack_timeline(tmp_path):
    shots, files, voice, mixed, music, sfx, ass = _fixture(tmp_path)
    timeline = build_timeline(
        shots, files, voice_path=voice, mixed_audio_path=mixed,
        music_path=music, sfx_timed=[(1.5, sfx)], ass_path=ass,
        motion_plan=[{"index": 1, "profile": "native"}],
        storyboard={"review_status": "auto_approved"},
        edit_decisions={
            "schema": "nextdecode.edl.v1", "duration_frames": 90,
            "clips": [
                {"shot_index": 0, "clip_id": "edl-0", "source": {"in_seconds": 2.0, "out_seconds": 3.5},
                 "framing": {"mode": "contain"}, "transition_in": {"type": "fade", "duration_frames": 12},
                 "transition_out": {"type": "cut", "duration_frames": 0}, "motion": {"mode": "native"}},
                {"shot_index": 1, "clip_id": "edl-1", "source": {"in_seconds": 0.0, "out_seconds": 1.5},
                 "framing": {"mode": "fill"}, "transition_in": {"type": "cut", "duration_frames": 0},
                 "transition_out": {"type": "fade", "duration_frames": 12}, "motion": {}},
            ],
        },
    )
    assert timeline["schema"] == TIMELINE_SCHEMA
    assert timeline["timebase"] == {"fps_num": 30, "fps_den": 1, "drop_frame": False}
    assert timeline["duration_frames"] == 90
    tracks = {track["kind"]: track for track in timeline["tracks"]}
    assert [clip["start_frame"] for clip in tracks["video"]["clips"]] == [0, 45]
    assert tracks["sfx"]["clips"][0]["start_frame"] == 45
    assert tracks["music"]["clips"][0]["end_frame"] == 90
    assert tracks["captions"]["clips"][0]["format"] == "ass"
    assert tracks["video"]["clips"][1]["director_motion"]["profile"] == "native"
    assert tracks["video"]["clips"][0]["edl_clip_id"] == "edl-0"
    assert tracks["video"]["clips"][0]["source_range"] == {"in_seconds": 2.0, "out_seconds": 3.5}
    assert tracks["video"]["clips"][0]["framing"]["mode"] == "contain"
    assert tracks["video"]["clips"][0]["transition_in"] == "fade"
    assert tracks["video"]["clips"][0]["transition_in_detail"]["type"] == "fade"
    assert timeline["edit_decisions"]["schema"] == "nextdecode.edl.v1"


def test_rejects_gap_or_overlap_between_picture_clips(tmp_path):
    shots, files, voice, mixed, music, sfx, ass = _fixture(tmp_path)
    shots[1]["start"] = 1.6
    shots[1]["end"] = 3.1
    with pytest.raises(ValueError, match="discontinuity"):
        build_timeline(shots, files, voice_path=voice, mixed_audio_path=mixed)


def test_rejects_duration_that_disagrees_with_frame_range(tmp_path):
    shots, files, voice, mixed, music, sfx, ass = _fixture(tmp_path)
    shots[0]["duration"] = 1.4
    with pytest.raises(ValueError, match="duration"):
        build_timeline(shots, files, voice_path=voice, mixed_audio_path=mixed)


def test_rejects_missing_rendered_shot_media(tmp_path):
    shots, files, voice, mixed, music, sfx, ass = _fixture(tmp_path)
    files[1] = tmp_path / "missing.mp4"
    with pytest.raises(ValueError, match="missing"):
        build_timeline(shots, files, voice_path=voice, mixed_audio_path=mixed)


def test_caption_word_cues_share_the_video_frame_clock(tmp_path):
    shots, files, voice, mixed, music, sfx, ass = _fixture(tmp_path)
    words = tmp_path / "captions.words.json"
    words.write_text(json.dumps({
        "schema": "nextdecode.word-cues.v1",
        "words": [
            {"word": "Director", "start": 0.10, "end": 0.45},
            {"word": "cut.", "start": 0.46, "end": 0.80},
        ],
    }))
    timeline = build_timeline(
        shots, files, voice_path=voice, mixed_audio_path=mixed,
        ass_path=ass, caption_words_path=words,
    )
    captions = next(track for track in timeline["tracks"] if track["kind"] == "captions")
    cues = captions["clips"][0]["word_cues"]
    assert [(cue["start_frame"], cue["end_frame"]) for cue in cues] == [(3, 14), (14, 24)]


def test_write_timeline_is_valid_json_and_atomic_output(tmp_path):
    shots, files, voice, mixed, music, sfx, ass = _fixture(tmp_path)
    timeline = build_timeline(shots, files, voice_path=voice, mixed_audio_path=mixed)
    target = write_timeline(tmp_path / "edit" / "timeline.json", timeline)
    assert json.loads(target.read_text())["duration_frames"] == 90
    assert not list(target.parent.glob("*.tmp"))
