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


def test_longform_dry_run_is_rejected_at_request_boundary():
    with pytest.raises(HTTPException) as caught:
        api_main._validated_start_request({"content_format": "youtube_longform"})
    assert caught.value.status_code == 422
    assert caught.value.detail["code"] == "longform_dry_run_not_implemented"


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


def test_longform_dry_run_is_blocked_without_invoking_pipeline(tmp_path, monkeypatch):
    job_id = "lfdry001"
    job = {"status": "queued", "dry_run": True, "topic": "AI", "quality": "strong",
           "content_format": "youtube_longform"}
    monkeypatch.setattr(api_main, "LOG_DIR", tmp_path)
    monkeypatch.setitem(api_main.jobs, job_id, job)
    def unexpected_run(*args, **kwargs):
        raise AssertionError("long-form dry-run must not invoke a live producer")
    monkeypatch.setattr(api_main.subprocess, "run", unexpected_run)
    api_main.run_job(job_id, True, "AI", "strong", "youtube_longform")
    assert job["status"] == "failed"
    assert "longform_dry_run_not_implemented" in job["error"]


def test_format_registry_exposes_status_for_every_channel_format():
    rows = list_format_capabilities()
    assert len(rows) == 10
    assert {row["status"] for row in rows} == {"supported", "not_implemented"}
