"""Canonical publishing orchestration package and CLI tests."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from app.publish import orchestration, scheduler

ROOT = Path(__file__).resolve().parents[1]

def test_publish_orchestration_has_one_canonical_location() -> None:
    assert Path(orchestration.__file__).resolve() == ROOT / "app" / "publish" / "orchestration.py"
    assert not (ROOT / "publish_all.py").exists()
    assert orchestration.ROOT.resolve() == ROOT

def test_scheduler_has_one_canonical_location() -> None:
    assert Path(scheduler.__file__).resolve() == ROOT / "app" / "publish" / "scheduler.py"
    assert not (ROOT / "scheduled_publish.py").exists()
    assert scheduler.ROOT.resolve() == ROOT

def test_publish_orchestration_module_cli_help() -> None:
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run([sys.executable, "-m", "app.publish.orchestration", "--help"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
