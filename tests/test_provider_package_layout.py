"""Canonical provider package layout tests."""
from __future__ import annotations
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("multi_model_ai", "model_health", "omniroute_client")

def test_provider_modules_live_only_in_canonical_package() -> None:
    for name in MODULES:
        module = import_module(f"app.providers.{name}")
        assert Path(module.__file__).resolve() == ROOT / "app" / "providers" / f"{name}.py"
        assert not (ROOT / f"{name}.py").exists()

def test_provider_state_paths_remain_under_repository_root() -> None:
    model_health = import_module("app.providers.model_health")
    multi_model_ai = import_module("app.providers.multi_model_ai")
    assert multi_model_ai.PROJECT_ROOT.resolve() == ROOT
    assert multi_model_ai.TOKEN_USAGE_PATH == ROOT / "data" / "token_usage.json"
    assert model_health.ROOT.resolve() == ROOT
    assert model_health.HEALTH_PATH == ROOT / "data" / "model_health.json"

def test_provider_modules_use_the_shared_package_client() -> None:
    multi_model_ai = import_module("app.providers.multi_model_ai")
    packaged = import_module("app.providers.omniroute_client")
    assert multi_model_ai.omniroute_client is packaged

def test_provider_module_cli_help() -> None:
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    for name in ("multi_model_ai", "model_health"):
        result = subprocess.run([sys.executable, "-m", f"app.providers.{name}", "--help"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout.lower()
