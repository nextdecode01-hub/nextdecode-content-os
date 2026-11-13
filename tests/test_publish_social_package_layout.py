"""Canonical social publishing package tests."""
from __future__ import annotations
from pathlib import Path
from app.publish import social_orchestrator

ROOT = Path(__file__).resolve().parents[1]

def test_social_publisher_has_one_canonical_location() -> None:
    assert Path(social_orchestrator.__file__).resolve() == ROOT / "app" / "publish" / "social_orchestrator.py"
    assert not (ROOT / "publish_social.py").exists()
    assert social_orchestrator.ROOT.resolve() == ROOT
