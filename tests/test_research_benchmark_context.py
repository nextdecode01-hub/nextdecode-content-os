from pathlib import Path

from app.research.benchmark import clear_benchmark_cache, load_benchmark_context


def test_engine_can_read_the_competitor_benchmark():
    clear_benchmark_cache()
    context = load_benchmark_context()
    assert context["available"] is True
    assert context["video_count"] == 72
    assert context["channel_count"] == 9
    assert context["score_adjustment"] == 0.0
    assert context["usage"] == "advisory_only_no_score_adjustment"


def test_missing_benchmark_fails_open_without_score_adjustment(tmp_path: Path):
    missing = tmp_path / "not-created.csv"
    context = load_benchmark_context(str(missing))
    assert context["available"] is False
    assert context["video_count"] == 0
    assert context["score_adjustment"] == 0.0
