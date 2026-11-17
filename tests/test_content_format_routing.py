import pytest
from fastapi import HTTPException

from app.content.formats import get_format_capability, list_format_capabilities
from api import main as api_main


def test_existing_video_formats_have_explicit_producers():
    assert get_format_capability("youtube_shorts").producer == "short_video"
    assert get_format_capability("instagram_reels").producer == "short_video"
    assert get_format_capability("facebook_reels").producer == "short_video"
    assert get_format_capability("youtube_longform").producer == "long_video"


def test_post_and_carousel_formats_fail_closed_at_api_boundary():
    for format_id in ("youtube_community_posts", "instagram_posts", "instagram_carousels",
                      "facebook_posts", "linkedin_posts", "x_posts"):
        with pytest.raises(HTTPException) as caught:
            api_main._validated_start_request({"content_format": format_id})
        assert caught.value.status_code == 422
        assert caught.value.detail["code"] == "content_format_not_implemented"


def test_longform_dry_run_is_accepted_at_request_boundary():
    request = api_main._validated_start_request({"content_format": "youtube_longform"})
    assert request["content_format"] == "youtube_longform"
    assert request["dry_run"] is True


def test_unknown_format_and_wrong_type_are_rejected():
    with pytest.raises(HTTPException) as unknown:
        api_main._validated_start_request({"content_format": "random_format"})
    assert unknown.value.status_code == 400
    with pytest.raises(HTTPException) as wrong_type:
        api_main._validated_start_request({"content_format": ["youtube_shorts"]})
    assert wrong_type.value.status_code == 400


def test_legacy_api_request_defaults_to_youtube_shorts():
    assert api_main._validated_start_request(None)["content_format"] == "youtube_shorts"
    assert api_main._validated_start_request({"topic": "AI agents"})["content_format"] == "youtube_shorts"


def test_longform_dry_run_invokes_the_longform_producer_in_dry_run_mode(tmp_path, monkeypatch):
    import json as _json
    import types

    job_id = "lfdry002"
    job = {"status": "queued", "dry_run": True, "topic": "AI", "quality": "strong",
           "content_format": "youtube_longform"}
    monkeypatch.setattr(api_main, "LOG_DIR", tmp_path)
    monkeypatch.setitem(api_main.jobs, job_id, job)
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["env"] = kwargs.get("env") or {}
        stdout = kwargs.get("stdout")
        stdout.write(_json.dumps({
            "status": "success",
            "format": "youtube_longform",
            "quality": "dry_run",
            "title": "DRY RUN",
            "video_path": str(tmp_path / "output_longform.mp4"),
        }) + "\n")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(api_main.subprocess, "run", fake_run)
    api_main.run_job(job_id, True, "AI", "strong", "youtube_longform")
    assert "-m" in captured["cmd"] and "pipelines.longform" in captured["cmd"]
    assert captured["env"].get("DRY_RUN") == "1"
    # The dry-run child gets an explicit gate opt-out; production keeps require.
    assert captured["env"].get("STORYBOARD_GATE") == "warn"
    assert job["status"] == "done"
    assert job["content_format"] == "youtube_longform"
    assert job["video_path"].endswith("output_longform.mp4")


def test_production_render_keeps_the_storyboard_gate_fail_closed(tmp_path, monkeypatch):
    import types

    job_id = "lfprod001"
    job = {"status": "queued", "dry_run": False, "topic": "AI", "quality": "strong",
           "content_format": "youtube_longform"}
    monkeypatch.setattr(api_main, "LOG_DIR", tmp_path)
    monkeypatch.setitem(api_main.jobs, job_id, job)
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["env"] = kwargs.get("env") or {}
        stdout = kwargs.get("stdout")
        stdout.write("")
        return types.SimpleNamespace(returncode=3)

    monkeypatch.setattr(api_main.subprocess, "run", fake_run)
    api_main.run_job(job_id, False, "AI", "strong", "youtube_longform")
    # Production child must not receive the dry-run gate relaxation.
    assert captured["env"].get("DRY_RUN") == "0"
    assert captured["env"].get("STORYBOARD_GATE") != "warn"


def test_format_registry_exposes_status_for_every_channel_format():
    rows = list_format_capabilities()
    assert len(rows) == 10
    assert {row["status"] for row in rows} == {"supported", "not_implemented"}
