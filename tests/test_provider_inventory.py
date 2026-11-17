from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import main as api_main
from app.providers import model_health


def test_provider_inventory_covers_all_existing_routing_adapters(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-gemini")
    monkeypatch.setenv("GROQ_API_KEY", "secret-groq")
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-nvidia")
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-openrouter")
    monkeypatch.setenv("MISTRAL_API_KEY", "secret-mistral")
    monkeypatch.setenv("CEREBRAS_API_KEY", "secret-cerebras")
    monkeypatch.setenv("CF_ACCOUNT_ID", "account-id")
    monkeypatch.setenv("CF_API_TOKEN", "secret-cloudflare")
    inventory = model_health.provider_inventory(path=tmp_path / "no-health.json")
    ids = [item["id"] for item in inventory["providers"]]
    assert ids == list(model_health.SUPPORTED_PROVIDERS)
    assert all(item["health"] == "unknown" for item in inventory["providers"])
    assert all(item["eligible_for_routing"] for item in inventory["providers"] if item["configured"])
    assert "secret-" not in json.dumps(inventory)
    assert inventory["live_probe_performed"] is False


def test_provider_inventory_does_not_treat_stale_health_as_current(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")
    health = tmp_path / "health.json"
    health.write_text(json.dumps({
        "providers": {
            "groq": {
                "configured": True, "ok": True, "checked_at": "2020-01-01T00:00:00+00:00",
                "latency_ms": 12,
            }
        }
    }), encoding="utf-8")
    inventory = model_health.provider_inventory(path=health)
    groq = next(item for item in inventory["providers"] if item["id"] == "groq")
    assert groq["health"] == "unknown"
    assert groq["latency_ms"] is None


def test_probe_all_defaults_to_every_supported_provider(tmp_path):
    with patch.object(model_health, "probe_provider", side_effect=lambda name, timeout: {
        "provider": name, "configured": False, "ok": False, "checked_at": "x"
    }) as probe:
        result = model_health.probe_all(path=tmp_path / "health.json")
    assert [call.args[0] for call in probe.call_args_list] == list(model_health.SUPPORTED_PROVIDERS)
    assert set(result["providers"]) == set(model_health.SUPPORTED_PROVIDERS)


def test_provider_probe_error_does_not_persist_exception_message(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")
    with patch.object(model_health, "_call", side_effect=RuntimeError("authorization: secret-test-token")):
        result = model_health.probe_provider("groq", timeout=1)
    assert result["ok"] is False
    assert result["error"] == "RuntimeError"
    assert "secret-test-token" not in json.dumps(result)


def test_provider_inventory_api_is_authenticated_and_read_only(monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "provider-test-key")
    client = TestClient(api_main.app)
    assert client.get("/providers/inventory").status_code == 401
    headers = {"Authorization": "Bearer provider-test-key"}
    response = client.get("/providers/inventory", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "nextdecode.providers.inventory.v1"
    assert len(payload["providers"]) == len(model_health.SUPPORTED_PROVIDERS)
    assert client.post("/providers/inventory", headers=headers).status_code == 405


def test_quota_threshold_requires_real_provider_remaining_and_limit(tmp_path):
    quota = tmp_path / "quota.json"
    quota.write_text(json.dumps({"providers": {"groq": {"models": {
        "qwen/model": {"headers": {"x-ratelimit-limit-tokens": "10000", "x-ratelimit-remaining-tokens": "500"}},
        "other/model": {"headers": {"x-ratelimit-limit-tokens": "10000", "x-ratelimit-remaining-tokens": "9000"}}
    }}}}), encoding="utf-8")
    assert model_health.quota_threshold_reached("groq", model="qwen/model", path=quota)
    assert not model_health.quota_threshold_reached("groq", model="other/model", path=quota)
    assert not model_health.quota_threshold_reached("gemini", path=quota)


def test_openrouter_quota_threshold_uses_account_daily_counter(tmp_path):
    quota = tmp_path / "quota.json"
    quota.write_text(json.dumps({"providers": {"openrouter": {
        "free_model_daily_requests": {"used": 54, "limit": 50, "remaining": 0}
    }}}), encoding="utf-8")
    assert model_health.quota_threshold_reached("openrouter", path=quota)


def test_model_portfolio_api_is_authenticated(monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "provider-test-key")
    client = TestClient(api_main.app)
    assert client.get("/providers/portfolio").status_code == 401
    response = client.get("/providers/portfolio", headers={"Authorization": "Bearer provider-test-key"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "nextdecode.model-portfolio-view.v1"
    assert payload["target_count"] == 10
    assert payload["candidate_pool_count"] == len(payload["candidates"]) == 12
    super_vl = next(item for item in payload["candidates"] if item["model"] == "nvidia/nemotron-3.5-super-vl-120b-a12b")
    assert super_vl["role"] == "visual_qa"
    assert super_vl["selection_status"] == "provisional_candidate"


def test_model_qualification_schema_enforces_nextdecode_short_length_and_hook():
    valid = {"title": "MoE Explained", "hook": "Imagine a team of experts", "voice_text": "Imagine a team of experts. " + "Specialists route the right work to the right place. " * 11, "youtube_tags": ["AI", "MoE"]}
    assert model_health._schema_ok(valid)
    short = dict(valid, voice_text="Imagine a team of experts. " + "Too short. " * 12)
    assert not model_health._schema_ok(short)
    wrong_hook = dict(valid, hook="Different opening")
    assert not model_health._schema_ok(wrong_hook)
    no_tags = dict(valid, youtube_tags=[])
    assert not model_health._schema_ok(no_tags)


def test_provider_chain_filters_unknown_and_duplicate_entries(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_CHAIN", "groq,unknown,groq,gemini")
    from app.providers import multi_model_ai
    order = multi_model_ai._provider_order()
    assert order[:2] == ["groq", "gemini"]
    assert len(order) == len(set(order))
    assert set(order) == set(multi_model_ai.PROVIDER_ORDER)


def test_model_routing_api_is_authenticated_and_has_ten_selected_models(monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "provider-test-key")
    client = TestClient(api_main.app)
    assert client.get("/providers/routing").status_code == 401
    response = client.get("/providers/routing", headers={"Authorization": "Bearer provider-test-key"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "nextdecode.model-routing-inventory.v1"
    assert payload["candidate_count"] == 5
    assert payload["candidate_pool_count"] == 10
    assert payload["qualification_required"] is True
    assert "script_drafting" in payload["tasks"]
    assert payload["tasks"]["script_drafting"][0]["model"] == "openai/gpt-oss-120b"


def test_video_capabilities_api_is_authenticated_and_read_only(monkeypatch):
    monkeypatch.setenv(api_main.API_KEY_ENV, "provider-test-key")
    client = TestClient(api_main.app)
    assert client.get("/providers/video-capabilities").status_code == 401
    response = client.get("/providers/video-capabilities", headers={"Authorization": "Bearer provider-test-key"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "nextdecode.video-provider-capabilities.v1"
    assert payload["generation_enabled"] is False
    assert payload["live_probe_performed"] is False
    assert client.post("/providers/video-capabilities", headers={"Authorization": "Bearer provider-test-key"}).status_code == 405
