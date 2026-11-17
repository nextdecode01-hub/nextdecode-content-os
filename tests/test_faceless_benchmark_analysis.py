from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from research.analyze_faceless_benchmark import analyze


def test_current_benchmark_has_no_structural_errors():
    source = ROOT / "data/research/faceless_video_observations_pilot_2026-11-17.csv"
    result = analyze(source)
    assert result["rows_read"] == 72
    assert result["valid_rows"] == 72
    assert result["invalid_rows"] == 0
    assert result["channel_count"] == 9
    assert not result["validation_errors"]
