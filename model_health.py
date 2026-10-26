"""Provider health probing and chain pruning for the LLM layer.

The pipeline leans on a small set of LLM providers (OmniRoute gateway, Gemini,
Groq, Ollama).  Providers rot: a key expires, a gateway dies, a model is
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

ROOT = Path(__file__).resolve().parent
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
    "voice_text must be 40 to 60 words. "
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
    return 20 <= words <= 120


def _provider_model(name: str) -> str:
    if name == "omniroute":
        return _env("OMNIROUTE_MODEL") or "groq/openai/gpt-oss-120b"
    if name == "gemini":
        return _env("GEMINI_MODEL") or "gemini-2.5-flash"
    if name == "groq":
        return _env("GROQ_MODEL") or "qwen/qwen3-8b"
    if name == "ollama":
        return _env("OLLAMA_MODEL") or "gemma3:4b"
    return "unknown"


def _is_configured(name: str) -> bool:
    if name == "omniroute":
        return bool(_env("OMNIROUTE_BASE_URL") and _env("OMNIROUTE_API_KEY"))
    if name == "gemini":
        return bool(_env("GEMINI_API_KEY"))
    if name == "groq":
        return bool(_env("GROQ_API_KEY"))
    if name == "ollama":
        return bool(_env("OLLAMA_BASE_URL") and _env("OLLAMA_MODEL"))
    if name == "openai":
        return bool(_env("OPENAI_API_KEY"))
    if name == "anthropic":
        return bool(_env("ANTHROPIC_API_KEY"))
    return False


def _call(name: str, prompt: str, timeout: int) -> str:
    import multi_model_ai

    if name == "omniroute":
        import omniroute_client

        parsed = omniroute_client.generate_json(prompt, 0.4, timeout)
        return json.dumps(parsed)
    if name == "gemini":
        return multi_model_ai.call_gemini(prompt, None, 0.4, timeout, json_mode=True)
    if name == "groq":
        return multi_model_ai.call_groq(prompt, None, 0.4, timeout, json_mode=True)
    if name == "ollama":
        return multi_model_ai.call_ollama(prompt, _provider_model(name), 0.4, timeout, json_mode=True)
    if name == "openai":
        return multi_model_ai.call_openai(prompt, _provider_model(name), 0.4, timeout)
    if name == "anthropic":
        return multi_model_ai.call_anthropic(prompt, _provider_model(name), 0.4, timeout)
    raise RuntimeError(f"Unknown provider '{name}'.")


def _model_chain_for(name: str) -> list[str]:
    if name == "omniroute":
        import omniroute_client

        return omniroute_client.model_chain()
    import multi_model_ai

    if name == "gemini":
        return multi_model_ai.gemini_model_chain()
    if name == "groq":
        return multi_model_ai.groq_model_chain()
    return [_provider_model(name)]


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
        record["error"] = f"{type(exc).__name__}: {exc}"[:400]
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
    names = providers or ["omniroute", "gemini", "groq", "ollama"]
    data = load_health(path)
    records = data.get("providers", {})
    for name in names:
        records[name] = probe_provider(name, timeout=timeout)
    data["providers"] = records
    data["updated_at"] = _stamp()
    save_health(data, path)
    return data


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
        chain = ["omniroute", "gemini", "groq", "ollama"]
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
