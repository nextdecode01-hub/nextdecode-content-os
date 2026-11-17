import json
from pathlib import Path

import pytest

from app.providers import model_router


def test_routing_config_has_task_specific_primary_and_fallbacks():
    data = model_router.load_routing()
    assert data["schema"] == "nextdecode.model-task-routing.v1"
    assert "script_drafting" in data["tasks"]
    assert data["tasks"]["script_drafting"]["primary"]["model"] == "openai/gpt-oss-120b"
    assert data["tasks"]["evidence_extraction"]["primary"]["provider"] == "nvidia"


def test_route_candidates_deduplicates_and_preserves_order(tmp_path):
    path = tmp_path / "routes.json"
    path.write_text(json.dumps({
        "schema": "nextdecode.model-task-routing.v1",
        "tasks": {"x": {"primary": {"provider": "groq", "model": "m1"},
                        "fallbacks": [{"provider": "groq", "model": "m1"},
                                      {"provider": "gemini", "model": "m2"}]}}
    }))
    assert model_router.route_candidates("x", path=path) == [
        {"provider": "groq", "model": "m1"}, {"provider": "gemini", "model": "m2"}
    ]


def test_exact_model_task_benchmark_can_override_provider_wide_health_failure(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    root = tmp_path
    bench = root / "data" / "model_benchmark_v1"
    bench.mkdir(parents=True)
    (bench / "latest.json").write_text(json.dumps({
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "aggregate": {
            "nvidia:nvidia/nemotron-3.5-bolt-e4b:evidence": {
                "trials": 3, "passes": 3, "mean_score": 100.0
            },
            "nvidia:nvidia/nemotron-3.5-bolt-e4b:script": {
                "trials": 3, "passes": 0, "mean_score": 75.0
            },
        },
    }))
    monkeypatch.setattr(model_router, "ROOT", root)
    assert model_router._qualified_for_task(
        "evidence_extraction", "nvidia", "nvidia/nemotron-3.5-bolt-e4b"
    ) is True
    assert model_router._qualified_for_task(
        "script_drafting", "nvidia", "nvidia/nemotron-3.5-bolt-e4b"
    ) is False


def test_exact_task_qualification_allows_only_the_tested_model_past_provider_health(monkeypatch):
    import app.providers.model_health as health
    monkeypatch.setattr(model_router, "_configured", lambda provider: True)
    monkeypatch.setattr(health, "should_skip", lambda provider: provider == "nvidia")
    monkeypatch.setattr(health, "quota_status", lambda *a, **k: "available")
    monkeypatch.setattr(model_router, "_qualified_for_task", lambda task, provider, model: (
        task == "evidence_extraction" and provider == "nvidia" and model.endswith("bolt-e4b")
    ))
    path = Path(__file__).resolve().parents[1] / "config" / "brain" / "model_task_routing.v1.json"
    calls = []
    monkeypatch.setattr(model_router, "_call_exact", lambda provider, model, prompt, timeout, json_mode, **kwargs: (
        calls.append((provider, model)) or "qualified"
    ))
    result = model_router.generate_for_task("evidence_extraction", "prompt", path=path)
    assert result["text"] == "qualified"
    assert calls == [("nvidia", "nvidia/nemotron-3.5-bolt-e4b")]


def test_quota_gate_is_not_overridden_by_exact_model_qualification(monkeypatch):
    import app.providers.model_health as health
    monkeypatch.setattr(model_router, "_configured", lambda provider: True)
    monkeypatch.setattr(health, "should_skip", lambda provider: True)
    monkeypatch.setattr(health, "quota_status", lambda *a, **k: "exhausted")
    monkeypatch.setattr(model_router, "_qualified_for_task", lambda *a, **k: True)
    calls = []
    monkeypatch.setattr(model_router, "_call_exact", lambda *a, **k: calls.append(a) or "should-not-run")
    with pytest.raises(model_router.ModelRouteError):
        model_router.generate_for_task("evidence_extraction", "prompt")
    assert calls == []


def test_disabled_task_returns_no_candidates_and_never_calls_provider(tmp_path, monkeypatch):
    path = tmp_path / "routes.json"
    path.write_text(json.dumps({
        "schema": "nextdecode.model-task-routing.v1",
        "tasks": {"visual_qa": {"enabled": False, "primary": None, "fallbacks": []}},
    }))
    assert model_router.route_candidates("visual_qa", path=path) == []
    calls = []
    monkeypatch.setattr(model_router, "_call_exact", lambda *a, **k: calls.append(a))
    with pytest.raises(model_router.ModelRouteError):
        model_router.generate_for_task("visual_qa", "analyze these frames", path=path)
    assert calls == []


def test_unknown_task_fails_closed():
    with pytest.raises(model_router.ModelRouteError):
        model_router.route_candidates("unknown_task")


def test_generate_for_task_uses_first_configured_exact_model(monkeypatch):
    monkeypatch.setattr(model_router, "_configured", lambda provider: True)
    monkeypatch.setattr(model_router.model_health if hasattr(model_router, "model_health") else __import__("app.providers.model_health", fromlist=["x"]), "should_skip", lambda provider: False)
    monkeypatch.setattr(__import__("app.providers.model_health", fromlist=["x"]), "quota_status", lambda *a, **k: "available")
    calls = []
    monkeypatch.setattr(model_router, "_call_exact", lambda provider, model, prompt, timeout, json_mode, **kwargs: calls.append((provider, model, json_mode, kwargs.get("temperature"))) or '{"ok":true}')
    result = model_router.generate_for_task("script_drafting", "prompt", json_mode=True, temperature=0.65)
    assert result["text"] == '{"ok":true}'
    assert result["route"]["provider"] == "groq"
    assert result["route"]["model"] == "openai/gpt-oss-120b"
    assert calls == [("groq", "openai/gpt-oss-120b", True, 0.65)]


def test_generate_for_task_falls_back_only_within_task_role(monkeypatch):
    import app.providers.model_health as health
    monkeypatch.setattr(model_router, "_configured", lambda provider: True)
    monkeypatch.setattr(health, "should_skip", lambda provider: False)
    monkeypatch.setattr(health, "quota_status", lambda *a, **k: "available")
    monkeypatch.setattr(model_router, "_qualified_for_task", lambda *a, **k: True)
    calls = []
    def call(provider, model, prompt, timeout, json_mode, **kwargs):
        calls.append((provider, model))
        if len(calls) == 1:
            raise TimeoutError()
        return "ok"
    monkeypatch.setattr(model_router, "_call_exact", call)
    result = model_router.generate_for_task("script_drafting", "prompt")
    assert result["text"] == "ok"
    assert result["route"]["fallback_used"] is True
    assert calls[0] == ("groq", "openai/gpt-oss-120b")
    assert calls[1] == ("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b")

def test_research_synthesis_uses_evidence_benchmark_qualification():
    from app.providers import model_router
    assert model_router._TASK_BENCHMARK_KIND["research_synthesis"] == "evidence"
