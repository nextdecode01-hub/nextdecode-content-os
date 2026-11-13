"""Canonical run-tracker package layout tests."""
from __future__ import annotations
from pathlib import Path
from app.tracking import run_tracker
from pipelines import short

ROOT = Path(__file__).resolve().parents[1]

def test_run_tracker_has_one_canonical_package_location() -> None:
    assert Path(run_tracker.__file__).resolve() == ROOT / "app" / "tracking" / "run_tracker.py"
    assert not (ROOT / "run_tracker.py").exists()

def test_run_tracker_default_paths_remain_at_repository_root() -> None:
    assert run_tracker.ROOT.resolve() == ROOT
    assert run_tracker.DEFAULT_RUNS_ROOT == ROOT / "outputs" / "runs"
    assert run_tracker.DEFAULT_INDEX_PATH == ROOT / "data" / "runs" / "index.jsonl"

def test_pipeline_imports_canonical_tracker() -> None:
    assert short.start_run is run_tracker.start_run
