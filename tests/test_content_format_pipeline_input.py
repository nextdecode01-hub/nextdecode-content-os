"""content_format is a first-class pipeline input, validated and fail-closed."""
from __future__ import annotations

import inspect

import pytest

from app.content.formats import (
    list_format_capabilities,
    producer_for_format,
    resolve_content_format,
)
from app.research.channel_profile import enabled_content_formats
from app.script import pipeline


def test_default_format_is_a_youtube_short_produced_by_the_short_pipeline():
    contract = resolve_content_format(producer="short_video")
    assert contract["format_id"] == "youtube_shorts"
    assert contract["producer"] == "short_video"
    assert contract["platforms"] == ["youtube"]
    assert contract["channel_id"] == "nextdecode"
    assert "youtube_longform" in contract["declared_formats"]


def test_reels_are_produced_by_the_short_video_producer():
    for format_id, platform in (
        ("instagram_reels", "instagram"),
        ("facebook_reels", "facebook"),
    ):
        contract = resolve_content_format(format_id, producer="short_video")
        assert contract["format_id"] == format_id
        assert contract["platforms"] == [platform]


def test_longform_is_never_produced_by_the_short_pipeline():
    with pytest.raises(RuntimeError) as caught:
        resolve_content_format("youtube_longform", producer="short_video")
    assert "long_video" in str(caught.value)

    # And the long-form producer refuses a Short.
    with pytest.raises(RuntimeError) as caught:
        resolve_content_format("youtube_shorts", producer="long_video")
    assert "short_video" in str(caught.value)


def test_declared_but_unimplemented_formats_fail_closed():
    with pytest.raises(RuntimeError) as caught:
        resolve_content_format("instagram_carousels", producer="short_video")
    message = str(caught.value)
    assert "no producer yet" in message
    assert "not_implemented" in message


def test_unknown_format_raises_value_error():
    with pytest.raises(ValueError):
        resolve_content_format("made_up_format", producer="short_video")


def test_every_enabled_format_has_a_capability_entry():
    capability_ids = {item["format_id"] for item in list_format_capabilities()}
    assert set(enabled_content_formats()) <= capability_ids


def test_producer_lookup_is_honest_about_missing_producers():
    assert producer_for_format("youtube_shorts") == "short_video"
    assert producer_for_format("youtube_longform") == "long_video"
    assert producer_for_format("instagram_carousels") is None


def test_pipeline_rejects_a_bad_format_before_any_production_work(monkeypatch):
    def _must_not_run(*args, **kwargs):
        raise AssertionError("production must not start for an unimplemented format")

    monkeypatch.setattr(pipeline, "select_topic", _must_not_run)
    with pytest.raises(RuntimeError) as caught:
        pipeline.run("Any topic", content_format="instagram_carousels")
    assert "no producer yet" in str(caught.value)


def test_pipeline_run_accepts_content_format_as_a_keyword():
    signature = inspect.signature(pipeline.run)
    assert "content_format" in signature.parameters
    assert signature.parameters["content_format"].default == "youtube_shorts"
