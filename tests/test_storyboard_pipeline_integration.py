import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pipelines import short


def test_dry_run_fails_closed_before_render_without_explicit_gate_opt_out(
    monkeypatch, tmp_path
):
    monkeypatch.delenv("STORYBOARD_GATE", raising=False)
    with patch("app.voice.provider.synthesize") as synthesize, patch.object(
        short, "_dry_run_background"
    ) as background, patch.object(short, "render_final_short") as render:
        with pytest.raises(RuntimeError, match="storyboard review required before render"):
            short.run_dry_run(tmp_path / "work", tmp_path / "metadata.json")

    synthesize.assert_not_called()
    background.assert_not_called()
    render.assert_not_called()
    assert not (tmp_path / "metadata.json").exists()


def test_dry_run_warn_mode_is_an_explicit_local_render_opt_out(monkeypatch, tmp_path):
    monkeypatch.setenv("STORYBOARD_GATE", "warn")
    work = tmp_path / "work"
    metadata = tmp_path / "metadata.json"
    audio = work / "voice.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"mock-audio")

    with patch("app.voice.provider.synthesize", return_value={"path": str(audio)}), patch(
        "app.voice.provider.probe_duration", return_value=30.0
    ), patch("app.render.subtitles.make_kinetic_ass") as captions, patch.object(
        short, "_dry_run_background"
    ) as background, patch.object(short.strong_pipeline, "estimated_words", return_value=[]), patch.object(
        short, "render_final_short"
    ) as render:
        result = short.run_dry_run(work, metadata)

    background.assert_called_once()
    captions.assert_called_once()
    render.assert_called_once()
    assert result["human_review_status"] == "not_for_publish"
    assert json.loads(metadata.read_text())["dry_run"] is True
