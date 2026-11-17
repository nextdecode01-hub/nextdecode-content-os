"""Runs are attributed to a channel, and rotation never crosses channels."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.research import selector
from app.research.channel_profile import load_channel_profile
from app.tracking import run_tracker as rt

LARGE_VIDEO = b"0" * 200_000
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


def _write_index(tmp_path: Path, rows: list[dict]) -> Path:
    index = tmp_path / "index.jsonl"
    index.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    return index


def test_start_run_records_the_channel_and_format_in_manifest_and_index(tmp_path: Path):
    index = tmp_path / "index.jsonl"
    tracker = rt.start_run(
        "AI agents reshape software teams",
        runs_root=tmp_path / "runs",
        index_path=index,
        now=NOW,
        channel_id="nextdecode",
        content_format="instagram_reels",
    )
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["channel_id"] == "nextdecode"
    assert manifest["content_format"] == "instagram_reels"

    tracker.mark_ok()
    row = json.loads(index.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert row["channel_id"] == "nextdecode"
    assert row["content_format"] == "instagram_reels"
    assert row["topic"] == "AI agents reshape software teams"


def test_unattributed_runs_are_recorded_honestly_as_empty(tmp_path: Path):
    tracker = rt.start_run(
        "t", runs_root=tmp_path / "runs", index_path=tmp_path / "i.jsonl", now=NOW
    )
    manifest = json.loads((tracker.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["channel_id"] == ""
    assert manifest["content_format"] == ""


def test_legacy_rows_count_for_nextdecode_and_never_leak_to_another_channel(tmp_path: Path):
    index = _write_index(tmp_path, [
        # written before channel attribution existed
        {"run_id": "1", "status": "ok", "topic": "New AI model beats every benchmark"},
        # a second channel's delivered video
        {"run_id": "2", "status": "published", "topic": "Startup raises a funding round",
         "channel_id": "marketpulse"},
    ])

    nextdecode = selector.load_rotation_lanes(index, channel_id="nextdecode")
    assert nextdecode == ["artificial_intelligence"]

    marketpulse = selector.load_rotation_lanes(index, channel_id="marketpulse")
    assert marketpulse == ["startups_entrepreneurship"]

    assert selector.load_recent_run_topics(index, channel_id="marketpulse") == [
        "Startup raises a funding round"
    ]


def test_one_channels_delivery_does_not_rotate_another_channel(tmp_path: Path):
    index = _write_index(tmp_path, [
        {"run_id": "1", "status": "ok", "topic": "New AI model beats every benchmark",
         "channel_id": "nextdecode"},
        {"run_id": "2", "status": "ok", "topic": "Startup raises a funding round",
         "channel_id": "marketpulse"},
    ])
    entries = [
        {"topic": "Stock market rally lifts the semiconductor industry",
         "total_score": 80.0, "niche_lane": "markets_industry_shifts"},
        {"topic": "New AI model sets another benchmark",
         "total_score": 79.0, "niche_lane": "artificial_intelligence"},
    ]

    marketpulse_lanes = selector.load_rotation_lanes(index, channel_id="marketpulse")
    assert marketpulse_lanes == ["startups_entrepreneurship"]
    ordered, rotation = selector.apply_niche_rotation(
        entries, marketpulse_lanes, tolerance=10.0
    )
    # marketpulse's last pillar is startups: this story is already fresh, so the
    # nextdecode AI delivery must not force a rotation.
    assert ordered[0]["niche_lane"] == "markets_industry_shifts"
    assert rotation["repeat"] is False


def test_select_best_reads_history_for_the_active_channel():
    with patch.object(selector, "load_rotation_lanes", return_value=[]) as loader, \
            patch.multiple(
                selector,
                derive_past_performance=lambda: {},
                load_used_topics=lambda: [],
                _ensure_judgements=lambda candidates, used: None,
                _youtube_total_results=lambda query: (None, "probe disabled in test", []),
                _image_provider_available=lambda: False,
                _JUDGE_CACHE={},
            ):
        selector.select_best(
            [{"title": "AI agents automate developer workflows", "summary": ""}],
            min_score=0,
        )
    loader.assert_called_once_with(channel_id=selector.active_channel_id())


def test_active_channel_id_comes_from_the_channel_profile():
    assert selector.active_channel_id() == load_channel_profile()["channel_id"] == "nextdecode"


def test_short_pipeline_attributes_the_run_to_the_channel(tmp_path: Path):
    import pipelines.short as ps

    def fake_strong(topic, work_dir, metadata_file, **_kwargs):
        (work_dir / "output_short.mp4").write_bytes(LARGE_VIDEO)
        return {"title": "Isolation", "topic": "isolation",
                "voice_text": "text", "video_path": "output_short.mp4"}

    with patch.object(ps, "SCRIPT_DIR", tmp_path), \
            patch.object(ps, "run_strong_pipeline", side_effect=fake_strong), \
            patch.object(ps, "archive_video", return_value=tmp_path / "archived.mp4"), \
            patch.object(ps, "record_topic"), \
            patch.object(ps, "_record_failure") as failure, \
            patch.dict(os.environ, {"DRY_RUN": ""}, clear=False), \
            patch("sys.argv", [str(tmp_path / "pipelines" / "short.py"),
                               "--topic", "isolation",
                               "--content-format", "instagram_reels"]):
        ps.main()

    failure.assert_not_called()
    runs = sorted((tmp_path / "outputs" / "runs").iterdir())
    assert len(runs) == 1
    manifest = json.loads((runs[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["channel_id"] == "nextdecode"
    assert manifest["content_format"] == "instagram_reels"

    index = tmp_path / "data" / "runs" / "index.jsonl"
    row = json.loads(index.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert row["channel_id"] == "nextdecode"
    assert row["content_format"] == "instagram_reels"
