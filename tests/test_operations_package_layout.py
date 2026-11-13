"""Canonical operations package layout and CLI tests."""
from __future__ import annotations
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("analytics_collect", "meta_preflight", "monetization_tracker", "review_ledger", "video_archive", "workspace_sync")

@pytest.mark.parametrize("name", MODULES)
def test_operations_have_one_canonical_package_module(name: str) -> None:
    module = import_module(f"app.operations.{name}")
    assert Path(module.__file__).resolve() == ROOT / "app" / "operations" / f"{name}.py"
    assert not (ROOT / f"{name}.py").exists()

@pytest.mark.parametrize(("name", "attribute"), (
    ("analytics_collect", "ROOT"), ("meta_preflight", "ROOT"),
    ("monetization_tracker", "ROOT"), ("review_ledger", "ROOT"),
    ("workspace_sync", "ROOT"),
))
def test_operations_paths_remain_anchored_at_repository_root(name: str, attribute: str) -> None:
    module = import_module(f"app.operations.{name}")
    assert Path(getattr(module, attribute)).resolve() == ROOT

def test_setup_check_remains_a_standalone_root_script() -> None:
    source = (ROOT / "setup_check.py").read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in source
    assert "def format_report(" in source

@pytest.mark.parametrize("name", ("analytics_collect", "monetization_tracker", "review_ledger", "workspace_sync"))
def test_operations_module_cli_help(name: str) -> None:
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run([sys.executable, "-m", f"app.operations.{name}", "--help"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
