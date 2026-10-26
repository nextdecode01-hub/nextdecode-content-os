"""Shared pytest configuration.

The project loads `.env` at import time, so runtime switches such as the
provider health gate and the explicit provider chain would otherwise leak into
tests and change which provider the chain picks.  Both are cleared here so the
suite always exercises the default fallback order.
"""
from __future__ import annotations

import os

import pytest

RUNTIME_ONLY_ENV = (
    "AI_HEALTH_GATE",
    "AI_PROVIDER_CHAIN",
    "AI_GENERATION_PROVIDER",
    "AI_IGNORE_HEALTH",
)


@pytest.fixture(autouse=True)
def _neutralize_runtime_provider_switches(monkeypatch):
    for key in RUNTIME_ONLY_ENV:
        monkeypatch.delenv(key, raising=False)
    yield
