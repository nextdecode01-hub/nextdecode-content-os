from pathlib import Path
import shutil
import subprocess

import pytest

from app.render import edit_director


def _scenes(tmp_path):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    return [
        {"shot": {"index": 0, "shot_id": "a", "start": 0, "end": 1.5,
                  "claim": "Opening", "transition": "cut",
                  "story_format": "mini_documentary", "visual_style": "cinematic",
                  "shot_size": "close_up", "camera_angle": "low_angle",
                  "camera_movement": "slow_push_in", "editing_rhythm": "breathing_room",
                  "transition_intent": "match_cut", "continuity_group": "doc:opening"},
         "asset_path": source},
        {"shot": {"index": 1, "shot_id": "b", "start": 1.5, "end": 3.0,
                  "claim": "Payoff", "transition": "cut"},
         "asset_path": None},
    ]


def test_edl_is_frame_accurate_and_carries_editorial_decisions(tmp_path):
    scenes = _scenes(tmp_path)
    edl = edit_director.build_edit_decisions(
        scenes, [{"index": 1, "profile": "native"}], fps=30
    )
    assert edl["schema"] == "nextdecode.edl.v1"
    assert edl["duration_frames"] == 90
    first, second = edl["clips"]
    assert (first["timeline"]["start_frame"], first["timeline"]["end_frame"]) == (0, 45)
    assert first["source"]["in_seconds"] == 0
    assert first["source"]["out_seconds"] == 1.5
    assert first["source"]["kind"] == "video"
    assert first["creative_direction"]["story_format"] == "mini_documentary"
    assert first["creative_direction"]["shot_size"] == "close_up"
    assert first["creative_direction"]["camera_angle"] == "low_angle"
    assert first["creative_direction"]["transition_intent"] == "match_cut"
    assert first["creative_direction"]["continuity_group"] == "doc:opening"
    assert second["motion"]["profile"] == "native"
    assert second["narration"]["text"] == "Payoff"


def test_edl_rejects_timeline_gap_or_overlap(tmp_path):
    scenes = _scenes(tmp_path)
    scenes[1]["shot"]["start"] = 1.6
    with pytest.raises(ValueError, match="discontinuity"):
        edit_director.build_edit_decisions(scenes)


def test_edl_rejects_invalid_source_range(tmp_path):
    scenes = _scenes(tmp_path)
    scenes[0]["shot"]["source_in"] = 2
    scenes[0]["shot"]["source_out"] = 1
    with pytest.raises(ValueError, match="source range"):
        edit_director.build_edit_decisions(scenes)


def test_edl_rejects_source_out_beyond_probed_media_duration(monkeypatch, tmp_path):
    scenes = _scenes(tmp_path)
    scenes[0]["shot"]["source_in"] = 0.2
    scenes[0]["shot"]["source_out"] = 1.2
    monkeypatch.setattr(edit_director, "_probe_duration", lambda path: 1.0)
    with pytest.raises(ValueError, match="exceeds media duration"):
        edit_director.build_edit_decisions(scenes)


def test_existing_opening_and_closing_fades_are_preserved(tmp_path):
    scenes = _scenes(tmp_path)
    scenes[0]["shot"]["transition"] = "fade"
    scenes[1]["shot"]["transition"] = "fade"
    edl = edit_director.build_edit_decisions(scenes)
    assert edl["clips"][0]["transition_in"] == {"type": "fade", "duration_frames": 12}
    assert edl["clips"][1]["transition_out"] == {"type": "fade", "duration_frames": 12}
    assert edl["execution"]["transition_support"] == ["cut", "edge_fade"]


def test_m1_rejects_unsupported_transition_until_executor_supports_it(tmp_path):
    scenes = _scenes(tmp_path)
    scenes[1]["shot"]["transition"] = "dissolve"
    with pytest.raises(ValueError, match="unsupported transition"):
        edit_director.build_edit_decisions(scenes)


def test_execute_clip_trims_video_from_edl_before_render(monkeypatch, tmp_path):
    scenes = _scenes(tmp_path)
    edl = edit_director.build_edit_decisions(scenes)
    edl["clips"][0]["motion"] = {"mode": "native", "zoom_from": 1.0}
    edl["clips"][0]["transition_in"] = {"type": "fade", "duration_frames": 12}
    trimmed_path = tmp_path / "edl_source_000.mp4"
    commands = []

    def fake_run(command):
        commands.append(command)
        trimmed_path.write_bytes(b"x" * 1201)

    monkeypatch.setattr(edit_director, "_run", fake_run)
    captured = {}

    rendered_path = tmp_path / "rendered.mp4"
    def render_fn(shot, asset, work_dir, **kwargs):
        captured["asset"] = asset
        captured["shot"] = shot
        rendered_path.write_bytes(b"x" * 1201)
        return rendered_path

    monkeypatch.setattr(edit_director, "_probe_video", lambda path: {
        "duration_seconds": 1.5, "width": 1080, "height": 1920,
        "frame_rate": "30/1", "frame_count": 45,
    })

    result = edit_director.execute_clip(
        edl["clips"][0], render_fn, scenes[0]["shot"], scenes[0]["asset_path"], tmp_path
    )
    assert commands and commands[0][commands[0].index("-ss") + 1] == "0.0"
    assert captured["asset"] == trimmed_path
    assert captured["shot"]["motion"]["mode"] == "native"
    assert captured["shot"]["duration"] == 1.5
    assert captured["shot"]["edl_transition"]["in"] is True
    assert result.name == "rendered.mp4"
    assert edl["clips"][0]["execution_qa"]["status"] == "pass"


def test_edl_write_is_json_and_atomic(tmp_path):
    edl = edit_director.build_edit_decisions(_scenes(tmp_path))
    target = edit_director.write_edl(tmp_path / "edit" / "edit_decisions.json", edl)
    assert target.exists()
    assert '"nextdecode.edl.v1"' in target.read_text()
    assert not list(target.parent.glob("*.tmp"))

def test_source_segment_candidate_scoring_is_deterministic(tmp_path, monkeypatch):
    scenes = _scenes(tmp_path)
    monkeypatch.setattr(edit_director, "_probe_duration", lambda path: 12.0)
    scenes[0]["shot"]["source_segment_candidates"] = [
        {"in_seconds": 0, "out_seconds": 1.5, "score": 0.2},
        {"in_seconds": 6, "out_seconds": 7.5, "score": 0.9},
    ]
    first = edit_director.build_edit_decisions(scenes)["clips"][0]["source"]
    second = edit_director.build_edit_decisions(scenes)["clips"][0]["source"]
    assert first["in_seconds"] == 6
    assert first["selection"] == "metadata_candidate"
    assert first["selection_score"] == 0.9
    assert first == second


def test_source_segment_avoids_adjacent_reuse_of_same_asset(tmp_path, monkeypatch):
    scenes = _scenes(tmp_path)
    scenes[1]["asset_path"] = scenes[0]["asset_path"]
    monkeypatch.setattr(edit_director, "_probe_duration", lambda path: 6.0)
    edl = edit_director.build_edit_decisions(scenes)
    first, second = [clip["source"] for clip in edl["clips"]]
    assert first["in_seconds"] == 0
    assert second["in_seconds"] == 2.25
    assert "avoided adjacent source-range reuse" in second["selection_rationale"]


def test_explicit_source_range_overrides_candidates(tmp_path, monkeypatch):
    scenes = _scenes(tmp_path)
    monkeypatch.setattr(edit_director, "_probe_duration", lambda path: 10.0)
    scenes[0]["shot"].update({
        "source_in": 2.0, "source_out": 3.5,
        "source_segment_candidates": [{"in_seconds": 6, "out_seconds": 7.5, "score": 1.0}],
    })
    source = edit_director.build_edit_decisions(scenes)["clips"][0]["source"]
    assert (source["in_seconds"], source["out_seconds"]) == (2.0, 3.5)
    assert source["selection"] == "explicit_shot_override"



def test_edl_records_black_and_frozen_source_evidence_and_fails_closed(monkeypatch, tmp_path):
    scenes = _scenes(tmp_path)
    monkeypatch.setattr(edit_director, "_probe_duration", lambda path: 4.0)
    monkeypatch.setattr(edit_director, "_black_intervals", lambda *a, **k: [(0.0, 1.5)])
    monkeypatch.setattr(edit_director, "_detect_frozen_intervals", lambda *a, **k: [])
    monkeypatch.setattr(edit_director.subprocess, "run", lambda *a, **k: type(
        "Result", (), {"stdout": "0,0,0,0,0,0,0,0,0,aaa\\n0,1,0,0,0,0,0,0,0,bbb\\n0,2,0,0,0,0,0,0,0,ccc\\n"}
    )())
    source = edit_director.build_edit_decisions(scenes)["clips"][0]["source"]
    assert source["qa"]["status"] == "unusable"
    assert source["qa"]["fail_closed"] is True
    assert source["qa"]["black_intervals"] == [{
        "start_seconds": 0.0, "end_seconds": 1.5, "duration_seconds": 1.5
    }]


def test_execute_clip_rejects_source_that_failed_visual_qa(tmp_path):
    decision = {
        "clip_id": "bad-source", "source": {"kind": "video", "qa": {"fail_closed": True,
        "warnings": ["black_frames_detected"]}}, "timeline": {"start_seconds": 0,
        "duration_seconds": 1,},
    }
    called = []
    with pytest.raises(RuntimeError, match="failed visual QA"):
        edit_director.execute_clip(decision, lambda *a, **k: called.append(True),
                                   {"index": 0}, None, tmp_path)
    assert called == []


def test_ffmpeg_fixture_detects_full_black_segment(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is not installed")
    clip = tmp_path / "black_fixture.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=160x90:r=10:d=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip),
    ], check=True, capture_output=True, timeout=30)
    duration = edit_director._probe_duration(clip)
    qa = edit_director._inspect_source_segment(clip, 0.0, duration, duration, 10)
    assert qa["status"] == "unusable"
    assert qa["fail_closed"] is True
    assert qa["black_intervals"]


def test_rendered_clip_duration_is_checked_against_edl_with_ffprobe(tmp_path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg/ffprobe is not installed")
    clip = tmp_path / "rendered_fixture.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=s=160x90:r=10:d=1.5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip),
    ], check=True, capture_output=True, timeout=30)
    decision = {"clip_id": "fixture", "timeline": {"duration_seconds": 1.5}}
    evidence = edit_director.validate_rendered_clip(clip, decision, fps=10)
    assert evidence["status"] == "pass"
    assert evidence["frame_count"] == 15
    assert evidence["width"] == 160
    assert abs(evidence["actual_duration_seconds"] - 1.5) <= 0.04


def test_rendered_clip_duration_mismatch_fails_closed(monkeypatch, tmp_path):
    clip = tmp_path / "wrong_duration.mp4"
    clip.write_bytes(b"x" * 1201)
    monkeypatch.setattr(edit_director, "_probe_video", lambda path: {
        "duration_seconds": 0.8, "width": 1080, "height": 1920,
        "frame_rate": "30/1", "frame_count": 24,
    })
    decision = {"clip_id": "wrong", "timeline": {"duration_seconds": 1.5}}
    with pytest.raises(RuntimeError, match="EDL execution QA: duration mismatch"):
        edit_director.validate_rendered_clip(clip, decision, fps=30)


def test_ffmpeg_fixture_detects_frozen_segment(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is not installed")
    clip = tmp_path / "frozen_fixture.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x336699:s=160x90:r=10:d=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip),
    ], check=True, capture_output=True, timeout=30)
    intervals = edit_director._detect_frozen_intervals(clip, min_duration=0.5)
    assert intervals
    assert intervals[0][1] - intervals[0][0] >= 1.0


def test_final_delivery_qa_validates_45_second_edl_timeline_audio_and_edge_fades(tmp_path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg/ffprobe is not installed")
    output = tmp_path / "final_45s.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=red:s=160x90:r=30:d=15",
        "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=30:d=15",
        "-f", "lavfi", "-i", "color=c=green:s=160x90:r=30:d=15",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=45",
        "-filter_complex",
        "[0:v]fade=t=in:st=0:d=1[v0];[1:v]null[v1];[2:v]fade=t=out:st=14:d=1[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[v]",
        "-map", "[v]", "-map", "3:a", "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest", str(output),
    ], check=True, capture_output=True, timeout=120)

    edl_clips = []
    timeline_clips = []
    for index in range(3):
        start, end = index * 450, (index + 1) * 450
        clip_id = f"fixture-{index}"
        edl_clips.append({
            "clip_id": clip_id,
            "timeline": {"start_frame": start, "end_frame": end},
            "execution_qa": {"status": "pass"},
        })
        timeline_clips.append({
            "edl_clip_id": clip_id, "start_frame": start, "end_frame": end,
        })
    edl = {
        "duration_frames": 1350,
        "timebase": {"fps_num": 30, "fps_den": 1},
        "canvas": {"width": 160, "height": 90},
        "clips": edl_clips,
    }
    timeline = {
        "duration_frames": 1350,
        "tracks": [{"kind": "video", "clips": timeline_clips}],
    }

    qa = edit_director.validate_final_output(output, edl, timeline)
    assert qa["status"] == "pass"
    assert qa["expected_frames"] == 1350
    assert qa["clip_count"] == 3
    assert qa["width"] == 160 and qa["height"] == 90
    assert qa["audio_stream_present"] is True
    assert qa["frame_rate"] == "30/1"
    assert qa["visual_qa"]["interior_black_intervals"] == []
    assert qa["visual_qa"]["still_and_generated_intervals_excluded_from_freeze_gate"] is True
    assert abs(qa["actual_duration_seconds"] - 45.0) <= 1 / 30

    # Confirm the actual encoded delivery contains black at both fade edges,
    # rather than only asserting that fade filter strings were constructed.
    black = edit_director._black_intervals(output, min_duration=0.05, pix_th=0.12)
    assert any(start <= 0.1 and end >= 0.2 for start, end in black)
    assert any(end >= 44.8 for start, end in black)


def test_final_delivery_qa_rejects_timeline_edl_clip_identity_mismatch(tmp_path):
    output = tmp_path / "not_needed.mp4"
    output.write_bytes(b"x" * 1201)
    edl = {
        "duration_frames": 30, "timebase": {"fps_num": 30},
        "clips": [{"clip_id": "edl-a", "timeline": {"start_frame": 0, "end_frame": 30},
                   "execution_qa": {"status": "pass"}}],
    }
    timeline = {
        "duration_frames": 30,
        "tracks": [{"kind": "video", "clips": [{"edl_clip_id": "wrong",
            "start_frame": 0, "end_frame": 30}]}],
    }
    with pytest.raises(RuntimeError, match="clip identity differs"):
        edit_director.validate_final_output(output, edl, timeline)


@pytest.mark.parametrize("fps,audio_seconds,expected_error", [
    (25, 6, "frame-rate mismatch"),
    (30, 5, "audio duration mismatch"),
])
def test_final_delivery_qa_rejects_frame_rate_or_audio_clock_mismatch(
    tmp_path, fps, audio_seconds, expected_error
):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg/ffprobe is not installed")
    output = tmp_path / f"bad_clock_{fps}_{audio_seconds}.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"testsrc2=s=160x90:r={fps}:d=6",
        "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=44100:duration={audio_seconds}",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", str(output),
    ], check=True, capture_output=True, timeout=60)
    edl = {
        "duration_frames": 180, "timebase": {"fps_num": 30, "fps_den": 1},
        "canvas": {"width": 160, "height": 90},
        "clips": [{"clip_id": "bad-clock", "timeline": {"start_frame": 0, "end_frame": 180},
                   "execution_qa": {"status": "pass"}, "transition_in": {"type": "cut", "duration_frames": 0},
                   "transition_out": {"type": "cut", "duration_frames": 0}, "source": {"kind": "image"}}],
    }
    timeline = {
        "duration_frames": 180,
        "tracks": [{"kind": "video", "clips": [{"edl_clip_id": "bad-clock",
            "start_frame": 0, "end_frame": 180}]}],
    }
    with pytest.raises(RuntimeError, match=expected_error):
        edit_director.validate_final_output(output, edl, timeline)
