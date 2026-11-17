import json
from pathlib import Path

from fastapi import APIRouter

from .model_health import provider_inventory
from .model_router import routing_inventory

router = APIRouter(prefix="/providers", tags=["model-providers"])


@router.get("/inventory")
def get_provider_inventory():
    """Return configured models and last-known health without making provider calls."""
    return provider_inventory()


@router.get("/routing")
def get_model_routing():
    """Return task-specific model assignments and configuration readiness."""
    return routing_inventory()


@router.get("/video-capabilities")
def get_video_provider_capabilities():
    """Return local credential readiness only; never contacts a video provider."""
    from .video_generation import KlingVideoProvider, RunwayVideoProvider, GoogleVeoProvider
    return {
        "schema": "nextdecode.video-provider-capabilities.v1",
        "providers": [
            {"id": "kling", "configured": KlingVideoProvider().configured(), "route": "direct_provider_apis"},
            {"id": "google_veo", "configured": GoogleVeoProvider().configured(), "route": "direct_provider_apis"},
            {"id": "runway", "configured": RunwayVideoProvider().configured(), "route": "unified_gateway"},
        ],
        "generation_enabled": False,
        "live_probe_performed": False,
    }


@router.get("/portfolio")
def get_model_portfolio():
    """Return curated model candidates, qualification results and observed usage/quota."""
    root = Path(__file__).resolve().parents[2]
    def read_json(path: Path, default):
        try:
            return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
        except (OSError, ValueError):
            return default
    portfolio = read_json(root / "config" / "brain" / "model_portfolio.v1.json", {"candidates": []})
    qualification = read_json(root / "data" / "model_qualification.json", {})
    usage = read_json(root / "data" / "model_usage.v1.json", {"models": {}})
    quota = read_json(root / "data" / "provider_quota.v1.json", {"providers": {}})
    results = {item.get("id"): item for item in qualification.get("results", []) if isinstance(item, dict)}
    usage_models = usage.get("models", {})
    for candidate in portfolio.get("candidates", []):
        result = results.get(candidate.get("id"), {})
        candidate["qualification"] = result
        candidate["usage"] = usage_models.get(candidate.get("id"), usage_models.get(f"{candidate.get('provider')}:{candidate.get('model')}", {}))
        provider_quota = quota.get("providers", {}).get(candidate.get("provider"), {})
        model_quota = provider_quota.get("models", {}).get(candidate.get("model"), {}) if isinstance(provider_quota.get("models"), dict) else {}
        quota_view = dict(model_quota or provider_quota or {"status": "not_exposed_or_not_checked"})
        headers = quota_view.get("headers", {}) if isinstance(quota_view.get("headers"), dict) else {}
        dimensions = (("tokens", "x-ratelimit-remaining-tokens", "x-ratelimit-limit-tokens"), ("requests", "x-ratelimit-remaining-requests", "x-ratelimit-limit-requests"), ("generic", "x-ratelimit-remaining", "x-ratelimit-limit"))
        for dimension, remaining_key, limit_key in dimensions:
            try:
                remaining, limit = float(headers[remaining_key]), float(headers[limit_key])
                if limit > 0:
                    quota_view["dimension"] = dimension
                    quota_view["remaining"] = remaining
                    quota_view["limit"] = limit
                    quota_view["utilization_percent"] = round((1 - remaining / limit) * 100, 1)
                    quota_view["threshold_state"] = "switch_at_90_percent" if remaining / limit <= 0.10 else "normal"
                    break
            except (KeyError, TypeError, ValueError):
                continue
        if "threshold_state" not in quota_view:
            free = provider_quota.get("free_model_daily_requests")
            if isinstance(free, dict):
                try:
                    quota_view.update({"dimension": "daily_requests", "remaining": free["remaining"], "limit": free["limit"], "utilization_percent": round((1 - float(free["remaining"]) / float(free["limit"])) * 100, 1), "threshold_state": "switch_at_90_percent" if float(free["remaining"]) / float(free["limit"]) <= 0.10 else "normal"})
                except (KeyError, TypeError, ValueError, ZeroDivisionError):
                    pass
        quota_view.setdefault("threshold_state", "unknown")
        candidate["quota"] = quota_view
    return {
        "schema": "nextdecode.model-portfolio-view.v1",
        "target_count": portfolio.get("selection_policy", {}).get("target_count", 10),
        "candidate_pool_count": len(portfolio.get("candidates", [])),
        "checked_at": qualification.get("checked_at"),
        "successful": qualification.get("successful", 0),
        "candidates": portfolio.get("candidates", []),
        "quota_checked_at": quota.get("checked_at"),
        "quota_source_note": "Provider-reported counters only; unavailable quota is not estimated.",
    }
