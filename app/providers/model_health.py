"""Provider health probing and chain pruning for the LLM layer.

The pipeline uses hosted LLM providers configured in the active provider portfolio.  Providers rot: a key expires, a gateway dies, a model is
deprecated, a rate limit starts rejecting requests.  When that happens the
generation chain silently falls through to a slower or worse model, and the
video quality drops without anybody noticing.

This module probes each configured provider against the real workload shape
(JSON generation for a short-form script), records the outcome, and exposes a
ranked chain that :mod:`multi_model_ai` consumes so unhealthy providers are
skipped instead of tried first and failed.

Telemetry lives in ``model_health.json`` next to the project root.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
HEALTH_PATH = ROOT / "data" / "model_health.json"

DEFAULT_PROBE_TIMEOUT = 90
FAILURE_COOLDOWN_HOURS = 6
STALE_AFTER_HOURS = 24

PROBE_PROMPT = (
    "You are the short-form editorial producer for NEXTDECODE. "
    "Return only valid JSON with exactly these fields: "
    '{"hook": str, "title": str, "voice_text": str, "youtube_tags": [str]}. '
    "Topic: a research lab published a new open-weight speech model. "
    "The hook must be a vivid, truthful first sentence of voice_text. "
    "The title must be at most 60 characters. "
    "voice_text must be 92 to 118 words, matching NEXTDECODE's 45-60 second Shorts target. "
    "hook must exactly match the first sentence of voice_text. youtube_tags must be a non-empty array of strings. "
    "Do not invent numbers, quotes, prices, or availability."
)

REQUIRED_FIELDS = ("hook", "title", "voice_text", "youtube_tags")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp() -> str:
    return _now().isoformat()


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _looks_valid_json(raw: str) -> bool:
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return False
    return isinstance(parsed, dict)


def _schema_ok(parsed: Any) -> bool:
    if not isinstance(parsed, dict):
        return False
    missing = [field for field in REQUIRED_FIELDS if field not in parsed]
    if missing:
        return False
    title = str(parsed.get("title", ""))
    voice_text = str(parsed.get("voice_text", ""))
    if not title or len(title) > 60:
        return False
    words = len(voice_text.split())
    tags = parsed.get("youtube_tags")
    if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        return False
    hook = str(parsed.get("hook", "")).strip()
    first_sentence = voice_text.strip().split(".", 1)[0].strip()
    if not hook or hook.rstrip(".!?") != first_sentence.rstrip(".!?"):
        return False
    return 92 <= words <= 118


SUPPORTED_PROVIDERS = (
    "gemini", "groq", "pollinations_text", "nvidia",
    "cloudflare", "zai", "openrouter", "mistral", "cerebras",
)


def _provider_model(name: str) -> str:
    from . import multi_model_ai as ai
    models = {
        "gemini": ai.gemini_model_chain()[0],
        "groq": ai.groq_model_chain()[0],
        "pollinations_text": ai.POLLINATIONS_TEXT_MODEL,
        "nvidia": ai.NVIDIA_NIM_MODEL,
        "cloudflare": ai.CLOUDFLARE_AI_MODEL,
        "zai": os.getenv("ZAI_TEXT_MODEL", "glm-4.5-flash"),
        "openrouter": ai.OPENROUTER_MODEL,
        "mistral": ai.MISTRAL_MODEL,
        "cerebras": ai.CEREBRAS_MODEL,
    }
    return models.get(name, "unknown")


def _is_configured(name: str) -> bool:
    from . import multi_model_ai as ai
    checks = {
        "gemini": lambda: bool(_env("GEMINI_API_KEY")),
        "groq": lambda: bool(_env("GROQ_API_KEY")),
        # Public keyless endpoint: configured means addressable, not healthy.
        "pollinations_text": lambda: bool(ai.POLLINATIONS_TEXT_URL and ai.POLLINATIONS_TEXT_MODEL),
        "nvidia": lambda: bool(_env("NVIDIA_API_KEY") or _env("NVIDIA_API_KEY_2")),  # primary + existing secondary key
        "cloudflare": lambda: bool(_env("CF_ACCOUNT_ID") and _env("CF_API_TOKEN")),
        "zai": lambda: bool(_env("Z_API_KEY")),
        "openrouter": lambda: bool(_env("OPENROUTER_API_KEY")),
        "mistral": lambda: bool(_env("MISTRAL_API_KEY")),
        "cerebras": lambda: bool(_env("CEREBRAS_API_KEY")),
    }
    check = checks.get(name)
    return bool(check()) if check else False


def _call(name: str, prompt: str, timeout: int) -> str:
    from . import multi_model_ai as ai
    calls = {
        "gemini": lambda: ai.call_gemini(prompt, None, 0.4, timeout, json_mode=True),
        "groq": lambda: ai.call_groq(prompt, None, 0.4, timeout, json_mode=True),
        "pollinations_text": lambda: ai.call_pollinations_text(prompt, 0.4, timeout, json_mode=True),
        "nvidia": lambda: ai.call_nvidia_nim(prompt, 0.4, timeout, json_mode=True),
        "cloudflare": lambda: ai.call_cloudflare_ai(prompt, 0.4, timeout, json_mode=True),
        "zai": lambda: ai.call_zai(prompt, 0.4, timeout, json_mode=True),
        "openrouter": lambda: ai.call_openrouter(prompt, 0.4, timeout, json_mode=True),
        "mistral": lambda: ai.call_mistral(prompt, 0.4, timeout, json_mode=True),
        "cerebras": lambda: ai.call_cerebras(prompt, 0.4, timeout, json_mode=True),
    }
    call = calls.get(name)
    if call is None:
        raise RuntimeError(f"Unknown provider '{name}'.")
    return call()


def _call_model(provider: str, model: str, prompt: str, timeout: int) -> str:
    """Call exactly one candidate model; never silently walk another model chain."""
    from . import multi_model_ai as ai
    if provider == "groq":
        return ai.call_groq(prompt, model=model, temperature=0.4, timeout=timeout, json_mode=True)
    if provider == "gemini":
        return ai.call_gemini(prompt, model=model, temperature=0.4, timeout=timeout, json_mode=True)
    if provider == "nvidia":
        keys = [_env("NVIDIA_API_KEY"), _env("NVIDIA_API_KEY_2")]
        errors = []
        for key in dict.fromkeys(item for item in keys if item):
            try:
                return ai.call_openai_compatible(prompt, base_url=ai.NVIDIA_NIM_URL, api_key=key, model=model, temperature=0.4, timeout=timeout, json_mode=True, provider=provider)
            except Exception as exc:
                errors.append(type(exc).__name__)
        raise RuntimeError("NVIDIA NIM failed: " + ",".join(errors))
    if provider == "cloudflare":
        return ai.call_openai_compatible(prompt, base_url=ai._cf_ai_base_url(), api_key=_env("CF_API_TOKEN"), model=model, temperature=0.4, timeout=timeout, json_mode=True, provider=provider)
    if provider == "openrouter":
        return ai.call_openai_compatible(prompt, base_url=ai.OPENROUTER_URL, api_key=_env("OPENROUTER_API_KEY"), model=model, temperature=0.4, timeout=timeout, json_mode=True, provider=provider)
    if provider == "pollinations_text":
        return ai.call_openai_compatible(prompt, base_url=ai.POLLINATIONS_TEXT_URL, model=model, temperature=0.4, timeout=timeout, json_mode=True, provider=provider)
    if provider == "mistral":
        return ai.call_openai_compatible(prompt, base_url=ai.MISTRAL_URL, api_key=_env("MISTRAL_API_KEY"), model=model, temperature=0.4, timeout=timeout, json_mode=True, provider=provider)
    if provider == "cerebras":
        return ai.call_openai_compatible(prompt, base_url=ai.CEREBRAS_URL, api_key=_env("CEREBRAS_API_KEY"), model=model, temperature=0.4, timeout=timeout, json_mode=True, provider=provider)
    raise RuntimeError("Model-specific qualification is not supported for this provider.")


def probe_model(provider: str, model: str, *, timeout: int = 25) -> dict:
    """Qualify one exact model on a bounded structured-output task."""
    record = {"provider": provider, "model": model, "checked_at": _stamp(), "configured": _is_configured(provider),
              "ok": False, "valid_json": False, "schema_ok": False, "latency_ms": 0, "tokens_per_second": None, "error": ""}
    if not record["configured"]:
        record["error"] = "not_configured"
        return record
    started = time.perf_counter()
    try:
        raw = _call_model(provider, model, PROBE_PROMPT, timeout)
        elapsed = max(time.perf_counter() - started, 0.001)
        record["latency_ms"] = int(elapsed * 1000)
        record["valid_json"] = _looks_valid_json(raw)
        if record["valid_json"]:
            parsed = json.loads(raw)
            record["schema_ok"] = _schema_ok(parsed)
            output_words = len(str(parsed.get("voice_text", "")).split())
            record["output_words"] = output_words
            record["estimated_output_words_per_second"] = round(output_words / elapsed, 2)
        record["ok"] = bool(record["valid_json"] and record["schema_ok"])
        if not record["ok"]:
            record["error"] = "invalid_json" if not record["valid_json"] else "schema_mismatch"
    except Exception as exc:
        record["latency_ms"] = int((time.perf_counter() - started) * 1000)
        code = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
        record["http_status"] = int(code) if code else None
        record["error"] = type(exc).__name__
    return record


def _model_chain_for(name: str) -> list[str]:
    from . import multi_model_ai as ai
    chains = {
        "gemini": ai.gemini_model_chain,
        "groq": ai.groq_model_chain,
    }
    return chains[name]() if name in chains else [_provider_model(name)]


def probe_provider(name: str, *, timeout: int = DEFAULT_PROBE_TIMEOUT) -> dict:
    """Probe one provider with the real JSON workload and return a health record."""
    record: dict[str, Any] = {
        "provider": name,
        "model": _provider_model(name),
        "model_chain": _model_chain_for(name),
        "checked_at": _stamp(),
        "configured": _is_configured(name),
        "ok": False,
        "valid_json": False,
        "schema_ok": False,
        "latency_ms": 0,
        "error": "",
    }
    if not record["configured"]:
        record["error"] = "not_configured"
        return record

    started = time.perf_counter()
    try:
        raw = _call(name, PROBE_PROMPT, timeout)
        record["latency_ms"] = int((time.perf_counter() - started) * 1000)
        record["valid_json"] = _looks_valid_json(raw)
        if record["valid_json"]:
            record["schema_ok"] = _schema_ok(json.loads(raw))
        record["ok"] = record["valid_json"] and record["schema_ok"]
        if not record["ok"]:
            record["error"] = "invalid_json" if not record["valid_json"] else "schema_mismatch"
    except Exception as exc:
        record["latency_ms"] = int((time.perf_counter() - started) * 1000)
        # Exception messages may embed request URLs, headers or provider credentials.
        record["error"] = type(exc).__name__
    return record


def load_health(path: Path | None = None) -> dict:
    target = path or HEALTH_PATH
    if not target.is_file():
        return {"updated_at": "", "providers": {}}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"updated_at": "", "providers": {}}
    if not isinstance(data, dict):
        return {"updated_at": "", "providers": {}}
    data.setdefault("providers", {})
    data.setdefault("updated_at", "")
    return data


def save_health(data: dict, path: Path | None = None) -> Path:
    target = path or HEALTH_PATH
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return target


def probe_all(
    providers: list[str] | None = None,
    *,
    timeout: int = DEFAULT_PROBE_TIMEOUT,
    path: Path | None = None,
) -> dict:
    """Probe every provider (or the given subset) and persist the results."""
    _load_dotenv()
    names = providers if providers is not None else list(SUPPORTED_PROVIDERS)
    data = load_health(path)
    records = data.get("providers", {})
    for name in names:
        records[name] = probe_provider(name, timeout=timeout)
    data["providers"] = records
    data["updated_at"] = _stamp()
    save_health(data, path)
    return data


def provider_inventory(*, path: Path | None = None) -> dict:
    """Secret-free provider configuration and last-known health; performs no network calls."""
    from . import multi_model_ai as ai
    records = load_health(path).get("providers", {})
    providers = []
    for name in SUPPORTED_PROVIDERS:
        record = records.get(name) if isinstance(records, dict) else None
        record = record if isinstance(record, dict) else {}
        checked_at = str(record.get("checked_at") or "")
        fresh = _is_fresh(record, STALE_AFTER_HOURS) if checked_at else False
        configured = _is_configured(name)
        providers.append({
            "id": name,
            "model": _provider_model(name),
            "configured": configured,
            "configuration_status": "configured" if configured else "missing_credentials_or_settings",
            "health": "unknown" if not fresh else ("healthy" if record.get("ok") else "unhealthy"),
            "last_checked_at": checked_at or None,
            "latency_ms": int(record.get("latency_ms") or 0) if fresh else None,
            "last_error": str(record.get("error") or "")[:80] if fresh and not record.get("ok") else None,
            "eligible_for_routing": configured and not should_skip(name, path=path),
        })
    return {
        "schema": "nextdecode.providers.inventory.v1",
        "default_provider": os.getenv("AI_GENERATION_PROVIDER", "auto").strip().lower() or "auto",
        "provider_order": ai._provider_order(),
        "health_gate_enabled": os.getenv("AI_HEALTH_GATE", "true").strip().lower() == "true",
        "providers": providers,
        "live_probe_performed": False,
    }


def probe_account_quotas(*, timeout: int = 10, result_path: Path | None = None) -> dict:
    """Fetch only provider-published account quota endpoints; never infer unavailable quotas."""
    import requests
    _load_dotenv()
    snapshot = {"schema": "nextdecode.provider-quota.v1", "checked_at": _stamp(), "providers": {}}
    key = _env("OPENROUTER_API_KEY")
    if key:
        try:
            response = requests.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}, timeout=timeout)
            response.raise_for_status()
            body = response.json().get("data", {})
            snapshot["providers"]["openrouter"] = {
                "status": "available", "source": "account_api", "limit_remaining": body.get("limit_remaining"),
                "usage_daily": body.get("usage_daily"), "usage_weekly": body.get("usage_weekly"),
                "usage_monthly": body.get("usage_monthly"), "free_model_daily_requests": body.get("free_model_daily_requests"),
            }
        except Exception as exc:
            code = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
            snapshot["providers"]["openrouter"] = {"status": "unavailable", "error": type(exc).__name__, "http_status": int(code) if code else None}
    else:
        snapshot["providers"]["openrouter"] = {"status": "not_configured"}
    target = result_path or (ROOT / "data" / "provider_quota.v1.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if target.is_file():
        try:
            existing = json.loads(target.read_text(encoding="utf-8")).get("providers", {})
        except (OSError, ValueError):
            existing = {}
    existing.update(snapshot["providers"])
    snapshot["providers"] = existing
    target.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    return snapshot


def qualify_portfolio(*, timeout: int = 20, portfolio_path: Path | None = None, result_path: Path | None = None) -> dict:
    """Run the bounded one-request qualification for every configured portfolio candidate."""
    _load_dotenv()
    source = portfolio_path or (ROOT / "config" / "brain" / "model_portfolio.v1.json")
    portfolio = json.loads(source.read_text(encoding="utf-8"))
    results = []
    for candidate in portfolio.get("candidates", []):
        result = probe_model(candidate["provider"], candidate["model"], timeout=timeout)
        result["id"] = candidate["id"]
        result["role"] = candidate.get("role", "")
        result["use_cases"] = candidate.get("use_cases", [])
        results.append(result)
    payload = {"schema": "nextdecode.model-qualification.v1", "checked_at": _stamp(), "timeout_seconds": timeout,
               "candidates_tested": len(results), "successful": sum(1 for item in results if item["ok"]), "results": results}
    quota = probe_account_quotas(timeout=min(timeout, 10))
    payload["quota_snapshot"] = quota
    target = result_path or (ROOT / "data" / "model_qualification.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _is_fresh(record: dict, hours: int) -> bool:
    checked = record.get("checked_at", "")
    try:
        moment = datetime.fromisoformat(checked)
    except (TypeError, ValueError):
        return False
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return _now() - moment <= timedelta(hours=hours)


def healthy_providers(*, path: Path | None = None, max_age_hours: int = STALE_AFTER_HOURS) -> list[str]:
    """Providers that passed the probe recently, fastest healthy provider first."""
    data = load_health(path)
    records = data.get("providers", {})
    healthy = []
    for name, record in records.items():
        if not isinstance(record, dict) or not record.get("ok"):
            continue
        if not _is_fresh(record, max_age_hours):
            continue
        healthy.append((int(record.get("latency_ms") or 0), name))
    healthy.sort()
    return [name for _, name in healthy]


def unhealthy_providers(*, path: Path | None = None, max_age_hours: int = STALE_AFTER_HOURS) -> list[str]:
    """Providers that were configured but failed the probe inside the cooldown."""
    data = load_health(path)
    records = data.get("providers", {})
    failed = []
    for name, record in records.items():
        if not isinstance(record, dict):
            continue
        if not record.get("configured") or record.get("ok"):
            continue
        if not _is_fresh(record, max_age_hours):
            continue
        failed.append(name)
    return sorted(failed)


def quota_status(name: str, *, model: str | None = None, max_age_hours: float = 2.0,
                 path: Path | None = None) -> str:
    """Return available, low, exhausted or unknown from fresh provider-reported quota only.

    Stale, missing or malformed counters are unknown, never interpreted as
    available. Callers that require cost-safe routing must fail closed on unknown.
    """
    target = path or (ROOT / "data" / "provider_quota.v1.json")
    try:
        data = json.loads(target.read_text(encoding="utf-8")) if target.is_file() else {}
    except (OSError, ValueError):
        return "unknown"
    provider_record = (data.get("providers") or {}).get(name, {})
    if not isinstance(provider_record, dict) or not provider_record:
        return "unknown"
    model_record = provider_record.get("models", {}).get(model, {}) if model and isinstance(provider_record.get("models"), dict) else {}
    if not isinstance(model_record, dict):
        model_record = {}
    checked_at = model_record.get("checked_at") or provider_record.get("checked_at") or data.get("checked_at")
    try:
        stamp = datetime.fromisoformat(str(checked_at).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds() / 3600
        if age < -1 or age > max_age_hours:
            return "unknown"
    except (TypeError, ValueError, OverflowError):
        return "unknown"
    headers = model_record.get("headers", {}) if isinstance(model_record.get("headers"), dict) else {}
    if not headers and isinstance(provider_record.get("headers"), dict):
        headers = provider_record["headers"]
    for remaining_key, limit_key in (
        ("x-ratelimit-remaining-tokens", "x-ratelimit-limit-tokens"),
        ("x-ratelimit-remaining-requests", "x-ratelimit-limit-requests"),
        ("x-ratelimit-remaining", "x-ratelimit-limit"),
    ):
        try:
            remaining, limit = float(headers[remaining_key]), float(headers[limit_key])
            if limit > 0:
                ratio = remaining / limit
                return "exhausted" if remaining <= 0 else ("low" if ratio <= 0.10 else "available")
        except (KeyError, TypeError, ValueError):
            continue
    free = provider_record.get("free_model_daily_requests")
    if isinstance(free, dict):
        try:
            limit, remaining = float(free["limit"]), float(free["remaining"])
            if limit > 0:
                ratio = remaining / limit
                return "exhausted" if remaining <= 0 else ("low" if ratio <= 0.10 else "available")
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            pass
    try:
        limit, remaining = float(provider_record["limit"]), float(provider_record["limit_remaining"])
        if limit > 0:
            ratio = remaining / limit
            return "exhausted" if remaining <= 0 else ("low" if ratio <= 0.10 else "available")
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        pass
    return "unknown"


def quota_threshold_reached(name: str, *, model: str | None = None, threshold: float = 0.90, path: Path | None = None, max_age_minutes: float = 5.0) -> bool:
    """Return true only when provider-reported quota proves >= threshold consumption.

    Per-minute rate-limit headers (x-ratelimit-*) are only meaningful when
    fresh — they refill constantly, so a stale snapshot proves nothing about
    the current minute.  Account/day-level caps are treated as valid for the
    whole day.  Stale or missing evidence means "not proven exhausted" and
    allows the call; the call then records fresh headers via
    ``_record_provider_quota`` so a subsequent decision rests on truth.
    """
    target = path or (ROOT / "data" / "provider_quota.v1.json")
    try:
        data = json.loads(target.read_text(encoding="utf-8")) if target.is_file() else {}
    except (OSError, ValueError):
        return False
    record = data.get("providers", {}).get(name, {})
    if not isinstance(record, dict):
        return False
    model_record = record.get("models", {}).get(model, {}) if model and isinstance(record.get("models"), dict) else {}
    headers = model_record.get("headers", {}) if isinstance(model_record, dict) and isinstance(model_record.get("headers"), dict) else record.get("headers", {}) if isinstance(record.get("headers"), dict) else {}
    stamp = None
    if isinstance(model_record, dict):
        stamp = model_record.get("checked_at")
    if not stamp:
        stamp = record.get("checked_at") or data.get("checked_at")
    fresh = True
    if stamp:
        try:
            parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 60.0
            fresh = -1.0 < age <= max_age_minutes
        except (TypeError, ValueError, OverflowError):
            fresh = True
    # Missing timestamp: fail closed on the recorded remaining/limit ratio (the
    # provider-reported numbers are all the evidence we have).  A stale
    # timestamp proves nothing about the current minute for per-minute limits.
    pairs = (("x-ratelimit-remaining-tokens", "x-ratelimit-limit-tokens"),
             ("x-ratelimit-remaining-requests", "x-ratelimit-limit-requests"),
             ("x-ratelimit-remaining", "x-ratelimit-limit"))
    if fresh:
        for remaining_key, limit_key in pairs:
            try:
                remaining, limit = float(headers[remaining_key]), float(headers[limit_key])
                if limit > 0 and remaining / limit <= (1.0 - threshold):
                    return True
            except (KeyError, TypeError, ValueError):
                continue
    free = record.get("free_model_daily_requests")
    if isinstance(free, dict):
        try:
            limit, remaining = float(free["limit"]), float(free["remaining"])
            if limit > 0 and remaining / limit <= (1.0 - threshold):
                return True
        except (KeyError, TypeError, ValueError):
            pass
    try:
        limit, remaining = float(record["limit"]), float(record["limit_remaining"])
        if limit > 0 and remaining / limit <= (1.0 - threshold):
            return True
    except (KeyError, TypeError, ValueError):
        pass
    return False


def should_skip(name: str, *, path: Path | None = None, cooldown_hours: int = FAILURE_COOLDOWN_HOURS) -> bool:
    """True when the provider failed recently and should be skipped for now."""
    if _env("AI_IGNORE_HEALTH") == "1":
        return False
    data = load_health(path)
    record = data.get("providers", {}).get(name)
    if not isinstance(record, dict):
        return False
    if record.get("ok"):
        return False
    if not record.get("configured"):
        return False
    return _is_fresh(record, cooldown_hours)


def prune_env(path: Path | None = None) -> dict:
    """Rewrite the provider order in ``.env`` so healthy providers come first.

    ``AI_GENERATION_PROVIDER`` is set to ``auto`` so the chain stays dynamic; the
    ordered list is recorded in ``AI_PROVIDER_CHAIN`` and consumed by
    :mod:`multi_model_ai`.
    """
    env_path = path or (ROOT / ".env")
    chain = healthy_providers()
    if not chain:
        from . import multi_model_ai as ai
        chain = ai._provider_order()
    if not env_path.is_file():
        return {"updated": False, "chain": chain}
    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("AI_PROVIDER_CHAIN=") or stripped.startswith("AI_GENERATION_PROVIDER="):
            continue
        kept.append(line)
    kept.append(f"AI_GENERATION_PROVIDER=auto")
    kept.append(f"AI_PROVIDER_CHAIN={','.join(chain)}")
    env_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return {"updated": True, "chain": chain}


def render_report(data: dict | None = None) -> str:
    payload = data or load_health()
    records = payload.get("providers", {})
    lines = [
        "Provider health",
        f"  updated_at: {payload.get('updated_at', 'never')}",
        "",
        f"  {'provider':<12} {'model':<32} {'ok':<5} {'json':<5} {'schema':<7} {'ms':>7}  note",
    ]
    for name in sorted(records):
        record = records[name]
        lines.append(
            f"  {name:<12} {str(record.get('model', ''))[:32]:<32} "
            f"{str(record.get('ok')):<5} {str(record.get('valid_json')):<5} "
            f"{str(record.get('schema_ok')):<7} {str(record.get('latency_ms', 0)):>7}  "
            f"{record.get('error', '')[:60]}"
        )
    chain = healthy_providers()
    lines.append("")
    lines.append(f"  healthy chain: {', '.join(chain) if chain else 'none'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Probe LLM providers and prune the chain")
    parser.add_argument("--probe", action="store_true", help="run a live probe against every provider")
    parser.add_argument("--providers", default="", help="comma separated provider subset")
    parser.add_argument("--timeout", type=int, default=DEFAULT_PROBE_TIMEOUT)
    parser.add_argument("--prune", action="store_true", help="rewrite the provider chain in .env")
    parser.add_argument("--json", action="store_true", help="print raw JSON")
    args = parser.parse_args(argv)

    _load_dotenv()
    if args.probe:
        subset = [item.strip() for item in args.providers.split(",") if item.strip()] or None
        data = probe_all(subset, timeout=args.timeout)
    else:
        data = load_health()

    if args.prune:
        result = prune_env()
        print(f"chain rewritten: {', '.join(result['chain'])}")

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(render_report(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
