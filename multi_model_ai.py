# multi_model_ai.py
"""Shared LLM provider layer for project generators and the CLI.

Features
--------
* Route script JSON requests through OmniRoute, Gemini, Groq, then local Ollama.
* Keep optional direct-provider CLI calls for Groq, OpenAI, Anthropic, Gemini, and Ollama.
* Optionally track/enforce estimated daily API-token budgets with ENABLE_TOKEN_BUDGET=true.
* CLI for quick ad‑hoc prompts.

Add the desired API keys to `shorts_studio/.env`:
```dotenv
GROQ_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
```
Paid providers are never used by the automatic video-generation fallback.
"""

import os
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from dotenv import load_dotenv
import requests

import omniroute_client

load_dotenv(Path(__file__).with_name(".env"))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_PROVIDER = "groq"  # change for the standalone CLI; generators use their own fallback order
ENABLE_TOKEN_BUDGET = os.getenv("ENABLE_TOKEN_BUDGET", "false").strip().lower() == "true"
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
DEFAULT_GROQ_FALLBACK_MODELS = "openai/gpt-oss-20b,openai/gpt-oss-120b"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_GEMINI_FALLBACK_MODELS = "gemini-flash-latest,gemini-3.5-flash-lite"
DAILY_TOKEN_LIMITS = {
    "groq": 5_000_000,
    "openai": 1_000_000,
    "anthropic": 1_000_000,
    "gemini": 10_000_000,
    "ollama": float("inf"),
}
TOKEN_USAGE_PATH = Path(__file__).with_name("token_usage.json")
PROVIDER_ORDER = ("omniroute", "gemini", "groq", "pollinations_text", "nvidia", "cloudflare", "openrouter", "mistral", "cerebras", "ollama")

# Free fallback providers (OpenAI-compatible endpoints)
POLLINATIONS_TEXT_URL = os.getenv("POLLINATIONS_TEXT_URL", "https://text.pollinations.ai/openai").strip().rstrip("/")
POLLINATIONS_TEXT_MODEL = os.getenv("POLLINATIONS_TEXT_MODEL", "openai").strip() or "openai"
NVIDIA_NIM_URL = os.getenv("NVIDIA_NIM_URL", "https://integrate.api.nvidia.com/v1").strip().rstrip("/")
NVIDIA_NIM_MODEL = os.getenv("NVIDIA_NIM_MODEL", "google/gemma-4-31b-it").strip()
CLOUDFLARE_AI_MODEL = os.getenv("CLOUDFLARE_AI_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast").strip()
OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1").strip().rstrip("/")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "recursive/flint-v1.0:free").strip()
MISTRAL_URL = os.getenv("MISTRAL_URL", "https://api.mistral.ai/v1").strip().rstrip("/")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-4").strip()
CEREBRAS_URL = os.getenv("CEREBRAS_URL", "https://api.cerebras.ai/v1").strip().rstrip("/")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "gpt-oss-120b").strip()

_exhausted_providers: set[str] = set()


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).lower()
    if any(marker in text for marker in ("429", "quota", "rate limit", "rate_limit", "exhausted")):
        return True
    code = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
    return code == 429


def _cf_ai_base_url() -> str:
    account = os.getenv("CF_ACCOUNT_ID", "").strip()
    token = os.getenv("CF_API_TOKEN", "").strip()
    if not account or not token:
        return ""
    return f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1"


def _model_chain(primary_env: str, fallback_env: str, default_primary: str, default_fallback: str) -> list[str]:
    """Ordered model list for one provider: the selected model first, then fallbacks."""
    primary = os.getenv(primary_env, default_primary).strip() or default_primary
    raw = os.getenv(fallback_env, default_fallback).strip()
    chain = [primary]
    for item in raw.split(","):
        candidate = item.strip()
        if candidate and candidate not in chain:
            chain.append(candidate)
    return chain


def groq_model_chain() -> list[str]:
    return _model_chain("GROQ_MODEL", "GROQ_FALLBACK_MODELS", DEFAULT_GROQ_MODEL, DEFAULT_GROQ_FALLBACK_MODELS)


def gemini_model_chain() -> list[str]:
    return _model_chain("GEMINI_MODEL", "GEMINI_FALLBACK_MODELS", DEFAULT_GEMINI_MODEL, DEFAULT_GEMINI_FALLBACK_MODELS)


def _health_gate_enabled() -> bool:
    return os.getenv("AI_HEALTH_GATE", "false").strip().lower() == "true"


def _unhealthy(provider: str) -> bool:
    if not _health_gate_enabled():
        return False
    try:
        import model_health

        return model_health.should_skip(provider)
    except Exception:
        return False


def _provider_order() -> list[str]:
    raw = os.getenv("AI_PROVIDER_CHAIN", "").strip()
    if not raw:
        return list(PROVIDER_ORDER)
    order = [item.strip().lower() for item in raw.split(",") if item.strip()]
    for provider in PROVIDER_ORDER:
        if provider not in order:
            order.append(provider)
    return order

# ---------------------------------------------------------------------------
# Helper: token budgeting
# ---------------------------------------------------------------------------
def _load_token_usage() -> dict:
    if TOKEN_USAGE_PATH.exists():
        return json.loads(TOKEN_USAGE_PATH.read_text(encoding="utf-8"))
    return {}

def _save_token_usage(data: dict) -> None:
    TOKEN_USAGE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

def _reset_if_new_day(usage: dict) -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    if usage.get("date") != today:
        usage = {"date": today, "counts": {"groq": 0, "openai": 0, "anthropic": 0, "gemini": 0, "ollama": 0}}
    return usage

def _increment_usage(provider: str, tokens: int) -> None:
    if not ENABLE_TOKEN_BUDGET:
        return
    usage = _load_token_usage()
    usage = _reset_if_new_day(usage)
    usage["counts"][provider] = usage["counts"].get(provider, 0) + int(tokens or 0)
    _save_token_usage(usage)

def _check_budget(provider: str, est_tokens: int) -> bool:
    if not ENABLE_TOKEN_BUDGET:
        return True
    usage = _load_token_usage()
    usage = _reset_if_new_day(usage)
    used = usage["counts"].get(provider, 0)
    limit = DAILY_TOKEN_LIMITS.get(provider, float("inf"))
    return (used + est_tokens) <= limit


def _usage_value(usage, *names: str) -> int:
    if usage is None:
        return 0
    for name in names:
        if isinstance(usage, dict):
            value = usage.get(name)
        else:
            value = getattr(usage, name, None)
        if value is not None:
            return int(value)
    return 0


def _check_provider_budget(provider: str, prompt: str) -> None:
    estimate = max(1, len(prompt) // 4)
    if not _check_budget(provider, estimate):
        raise RuntimeError(f"Daily token limit exceeded for {provider}.")


def _response_text(response) -> str:
    text = response.choices[0].message.content
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("AI provider returned an empty response.")
    return text.strip()

# ---------------------------------------------------------------------------
# Provider‑specific call helpers (each returns the generated text)
# ---------------------------------------------------------------------------
def call_groq(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    timeout: int = 60,
    json_mode: bool = False,
) -> str:
    import groq
    _check_provider_budget("groq", prompt)
    client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    models = groq_model_chain() if model is None else [model]
    errors: list[str] = []
    for candidate in models:
        request = dict(
            model=candidate,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            timeout=timeout,
        )
        if json_mode:
            request["response_format"] = {"type": "json_object"}
        for attempt in range(2):
            try:
                response = client.chat.completions.create(**request)
            except Exception as exc:
                errors.append(f"{candidate} {type(exc).__name__}")
                break
            usage = getattr(response, "usage", None)
            if usage:
                _increment_usage("groq", _usage_value(usage, "total_tokens"))
            try:
                return _response_text(response)
            except Exception as exc:
                errors.append(f"{candidate} {type(exc).__name__}")
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                break
    raise RuntimeError("Groq request failed: " + ", ".join(errors))

def call_openai(
    prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    timeout: int = 60,
) -> str:
    import openai
    _check_provider_budget("openai", prompt)
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        timeout=timeout,
    )
    usage = getattr(response, "usage", None)
    if usage:
        _increment_usage("openai", _usage_value(usage, "total_tokens"))
    return _response_text(response)


def call_anthropic(
    prompt: str,
    model: str = "claude-3-5-sonnet-20240620",
    temperature: float = 0.7,
    timeout: int = 60,
) -> str:
    import anthropic
    _check_provider_budget("anthropic", prompt)
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        timeout=timeout,
    )
    usage = getattr(response, "usage", None)
    if usage:
        total = _usage_value(usage, "input_tokens") + _usage_value(usage, "output_tokens")
        _increment_usage("anthropic", total)
    return response.content[0].text


def call_gemini(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    timeout: int = 60,
    json_mode: bool = False,
) -> str:
    import warnings
    import google.generativeai as genai
    _check_provider_budget("gemini", prompt)
    models = gemini_model_chain() if model is None else [model]
    errors: list[str] = []
    for candidate in models:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", FutureWarning)
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                gen_model = genai.GenerativeModel(candidate)
                generation_config = {"temperature": temperature}
                if json_mode:
                    generation_config["response_mime_type"] = "application/json"
                response = gen_model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    request_options={"timeout": timeout},
                )
            usage = getattr(response, "usage_metadata", None)
            if usage:
                _increment_usage("gemini", _usage_value(usage, "total_token_count"))
            text = getattr(response, "text", None)
            if not isinstance(text, str) or not text.strip():
                raise RuntimeError("Gemini returned an empty response.")
            return text.strip()
        except Exception as exc:
            errors.append(f"{candidate} {type(exc).__name__}")
    raise RuntimeError("Gemini request failed: " + ", ".join(errors))


def call_ollama(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    timeout: int = 120,
    json_mode: bool = False,
) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")
    model = model or os.getenv("OLLAMA_MODEL", "gemma3:4b").strip()
    if not base_url or not model:
        raise RuntimeError("Set OLLAMA_BASE_URL and OLLAMA_MODEL to use Ollama.")
    _check_provider_budget("ollama", prompt)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        payload["format"] = "json"
    response = requests.post(f"{base_url}/api/chat", json=payload, timeout=timeout)
    response.raise_for_status()
    result = response.json()
    text = result.get("message", {}).get("content")
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("Ollama returned an empty response.")
    _increment_usage("ollama", int(result.get("prompt_eval_count", 0)) + int(result.get("eval_count", 0)))
    return text.strip()


def call_openai_compatible(
    prompt: str,
    *,
    base_url: str,
    api_key: str = "",
    model: str,
    temperature: float = 0.7,
    timeout: int = 60,
    json_mode: bool = False,
) -> str:
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"].strip()
    if not raw:
        raise RuntimeError("AI provider returned an empty response.")
    return raw


def call_pollinations_text(prompt: str, temperature: float = 0.7, timeout: int = 60, json_mode: bool = False) -> str:
    return call_openai_compatible(
        prompt, base_url=POLLINATIONS_TEXT_URL, api_key="", model=POLLINATIONS_TEXT_MODEL,
        temperature=temperature, timeout=timeout, json_mode=json_mode,
    )


def call_nvidia_nim(prompt: str, temperature: float = 0.7, timeout: int = 60, json_mode: bool = False) -> str:
    api_key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is not configured.")
    return call_openai_compatible(
        prompt, base_url=NVIDIA_NIM_URL, api_key=api_key, model=NVIDIA_NIM_MODEL,
        temperature=temperature, timeout=timeout, json_mode=json_mode,
    )


def call_cloudflare_ai(prompt: str, temperature: float = 0.7, timeout: int = 60, json_mode: bool = False) -> str:
    base_url = _cf_ai_base_url()
    if not base_url:
        raise RuntimeError("Set CF_ACCOUNT_ID and CF_API_TOKEN to use Cloudflare Workers AI.")
    return call_openai_compatible(
        prompt, base_url=base_url, api_key=os.getenv("CF_API_TOKEN", "").strip(), model=CLOUDFLARE_AI_MODEL,
        temperature=temperature, timeout=timeout, json_mode=json_mode,
    )


def call_openrouter(prompt: str, temperature: float = 0.7, timeout: int = 60, json_mode: bool = False) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")
    return call_openai_compatible(
        prompt, base_url=OPENROUTER_URL, api_key=api_key, model=OPENROUTER_MODEL,
        temperature=temperature, timeout=timeout, json_mode=json_mode,
    )


def call_mistral(prompt: str, temperature: float = 0.7, timeout: int = 60, json_mode: bool = False) -> str:
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not configured.")
    return call_openai_compatible(
        prompt, base_url=MISTRAL_URL, api_key=api_key, model=MISTRAL_MODEL,
        temperature=temperature, timeout=timeout, json_mode=json_mode,
    )


def call_cerebras(prompt: str, temperature: float = 0.7, timeout: int = 60, json_mode: bool = False) -> str:
    api_key = os.getenv("CEREBRAS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("CEREBRAS_API_KEY is not configured.")
    return call_openai_compatible(
        prompt, base_url=CEREBRAS_URL, api_key=api_key, model=CEREBRAS_MODEL,
        temperature=temperature, timeout=timeout, json_mode=json_mode,
    )


def _parse_json_response(raw: str | dict) -> dict:
    if isinstance(raw, dict):
        parsed = raw
    else:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
        parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("AI provider returned JSON that is not an object.")
    return parsed


def is_configured() -> bool:
    return bool(
        omniroute_client.is_configured()
        or os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GROQ_API_KEY", "").strip()
        or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
        or True  # pollinations_text is keyless and always available
    )


def generate_json(prompt: str, temperature: float, timeout: int) -> dict:
    """Use a selected provider, or try the configured free/local providers in order."""
    attempts = []
    selected_provider = os.getenv("AI_GENERATION_PROVIDER", "auto").strip().lower()

    def add_provider(provider: str) -> None:
        if provider in _exhausted_providers or _unhealthy(provider):
            return
        if provider == "omniroute":
            if omniroute_client.is_configured():
                attempts.append(("omniroute", "OmniRoute", lambda: omniroute_client.generate_json(prompt, temperature, timeout)))
        elif provider == "gemini":
            if os.getenv("GEMINI_API_KEY", "").strip():
                attempts.append(("gemini", "Gemini", lambda: call_gemini(prompt, temperature=temperature, timeout=timeout, json_mode=True)))
        elif provider == "groq":
            if os.getenv("GROQ_API_KEY", "").strip():
                attempts.append((
                    "groq",
                    "Groq",
                    lambda: call_groq(
                        prompt,
                        temperature=temperature,
                        timeout=timeout,
                        json_mode=True,
                    ),
                ))
        elif provider == "ollama":
            attempts.append(("ollama", "Ollama", lambda: call_ollama(prompt, temperature=temperature, timeout=timeout, json_mode=True)))
        elif provider == "pollinations_text":
            attempts.append(("pollinations_text", "PollinationsText", lambda: call_pollinations_text(prompt, temperature=temperature, timeout=timeout, json_mode=True)))
        elif provider == "nvidia":
            if os.getenv("NVIDIA_API_KEY", "").strip():
                attempts.append(("nvidia", "NvidiaNim", lambda: call_nvidia_nim(prompt, temperature=temperature, timeout=timeout, json_mode=True)))
        elif provider == "cloudflare":
            if _cf_ai_base_url():
                attempts.append(("cloudflare", "CloudflareAI", lambda: call_cloudflare_ai(prompt, temperature=temperature, timeout=timeout, json_mode=True)))
        elif provider == "openrouter":
            if os.getenv("OPENROUTER_API_KEY", "").strip():
                attempts.append(("openrouter", "OpenRouter", lambda: call_openrouter(prompt, temperature=temperature, timeout=timeout, json_mode=True)))
        elif provider == "mistral":
            if os.getenv("MISTRAL_API_KEY", "").strip():
                attempts.append(("mistral", "Mistral", lambda: call_mistral(prompt, temperature=temperature, timeout=timeout, json_mode=True)))
        elif provider == "cerebras":
            if os.getenv("CEREBRAS_API_KEY", "").strip():
                attempts.append(("cerebras", "Cerebras", lambda: call_cerebras(prompt, temperature=temperature, timeout=timeout, json_mode=True)))
        elif provider != "omniroute":
            raise RuntimeError(f"AI_GENERATION_PROVIDER '{provider}' is not configured.")

    if selected_provider == "auto":
        for provider in _provider_order():
            add_provider(provider)
    elif selected_provider in set(PROVIDER_ORDER):
        add_provider(selected_provider)
    else:
        raise RuntimeError("AI_GENERATION_PROVIDER must be auto, omniroute, gemini, groq, or ollama.")

    errors = []
    for name, label, request in attempts:
        if name in _exhausted_providers:
            continue
        try:
            return _parse_json_response(request())
        except Exception as exc:
            if _is_quota_error(exc):
                _exhausted_providers.add(name)
            errors.append(f"{label} {type(exc).__name__}")
    detail = ", ".join(errors) if errors else "no providers are configured"
    raise RuntimeError("AI script generation failed: " + detail)

# ---------------------------------------------------------------------------
# Unified interface
# ---------------------------------------------------------------------------
def _auto_text_chain(prompt: str, timeout: int, **kwargs) -> str:
    """Walk the configured provider chain in order and return the first text."""
    attempts: list[tuple[str, Any]] = []

    def add(provider: str) -> None:
        if provider in _exhausted_providers or _unhealthy(provider):
            return
        if provider == "omniroute":
            if omniroute_client.is_configured():
                attempts.append(("omniroute", "OmniRoute", lambda: json.dumps(
                    omniroute_client.generate_json(prompt, 0.7, timeout), ensure_ascii=False)))
        elif provider == "groq":
            if os.getenv("GROQ_API_KEY", "").strip():
                attempts.append(("groq", "Groq", lambda: call_groq(prompt, temperature=0.7, timeout=timeout)))
        elif provider == "gemini":
            if os.getenv("GEMINI_API_KEY", "").strip():
                attempts.append(("gemini", "Gemini", lambda: call_gemini(prompt, temperature=0.7, timeout=timeout)))
        elif provider == "ollama":
            attempts.append(("ollama", "Ollama", lambda: call_ollama(prompt, temperature=0.7, timeout=timeout)))
        elif provider == "pollinations_text":
            attempts.append(("pollinations_text", "PollinationsText", lambda: call_pollinations_text(prompt, temperature=0.7, timeout=timeout)))
        elif provider == "nvidia":
            if os.getenv("NVIDIA_API_KEY", "").strip():
                attempts.append(("nvidia", "NvidiaNim", lambda: call_nvidia_nim(prompt, temperature=0.7, timeout=timeout)))
        elif provider == "cloudflare":
            if _cf_ai_base_url():
                attempts.append(("cloudflare", "CloudflareAI", lambda: call_cloudflare_ai(prompt, temperature=0.7, timeout=timeout)))
        elif provider == "openrouter":
            if os.getenv("OPENROUTER_API_KEY", "").strip():
                attempts.append(("openrouter", "OpenRouter", lambda: call_openrouter(prompt, temperature=0.7, timeout=timeout)))
        elif provider == "mistral":
            if os.getenv("MISTRAL_API_KEY", "").strip():
                attempts.append(("mistral", "Mistral", lambda: call_mistral(prompt, temperature=0.7, timeout=timeout)))
        elif provider == "cerebras":
            if os.getenv("CEREBRAS_API_KEY", "").strip():
                attempts.append(("cerebras", "Cerebras", lambda: call_cerebras(prompt, temperature=0.7, timeout=timeout)))

    for provider in _provider_order():
        add(provider)

    errors = []
    for name, label, request in attempts:
        if name in _exhausted_providers:
            continue
        try:
            return request()
        except Exception as exc:
            if _is_quota_error(exc):
                _exhausted_providers.add(name)
            errors.append(f"{label} {type(exc).__name__}")
    detail = ", ".join(errors) if errors else "no providers are configured"
    raise RuntimeError("LLM text generation failed: " + detail)


def generate(prompt: str, provider: str | None = None, **kwargs) -> str:
    """Generate text using the requested provider.

    Parameters
    ----------
    prompt: str – the user prompt.
    provider: str – one of ``groq``, ``openai``, ``anthropic``, ``gemini``, ``ollama``.
    When no provider is given the configured chain is walked in order, so a
    single slow or broken provider cannot stall a whole run.
    **kwargs: any provider‑specific arguments (e.g., ``model=``).
    """
    if provider is None:
        return _auto_text_chain(prompt, int(kwargs.get("timeout", 60)))
    provider = provider.lower()
    if provider not in {"groq", "openai", "anthropic", "gemini", "google", "ollama"}:
        raise ValueError(f"Unsupported provider: {provider}")
    try:
        if provider == "groq":
            return call_groq(prompt, **kwargs)
        if provider == "openai":
            return call_openai(prompt, **kwargs)
        if provider == "anthropic":
            return call_anthropic(prompt, **kwargs)
        if provider in {"gemini", "google"}:
            return call_gemini(prompt, **kwargs)
        if provider == "ollama":
            return call_ollama(prompt, **kwargs)
        raise ValueError(f"Unsupported provider: {provider}")
    except Exception as exc:
        if provider not in {"gemini", "google"} and os.getenv("GEMINI_API_KEY", "").strip():
            try:
                return call_gemini(prompt, timeout=20)
            except Exception as fallback_exc:
                raise RuntimeError(
                    f"LLM request failed for {provider} ({type(exc).__name__}); "
                    f"Gemini fallback failed ({type(fallback_exc).__name__})."
                ) from exc
        raise RuntimeError(f"LLM request failed for {provider}: {type(exc).__name__}.") from exc

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Unified LLM wrapper")
    parser.add_argument("prompt", help="Prompt string or @path-to-file")
    parser.add_argument("-p", "--provider", default=DEFAULT_PROVIDER, help="groq|openai|anthropic|gemini|ollama")
    parser.add_argument("-m", "--model", help="Override default model for the chosen provider")
    args = parser.parse_args()

    # Support @file syntax
    if args.prompt.startswith("@"):
        with open(args.prompt[1:], "r") as f:
            prompt_text = f.read()
    else:
        prompt_text = args.prompt

    try:
        result = generate(prompt_text, provider=args.provider, model=args.model) if args.model else generate(prompt_text, provider=args.provider)
        print(result)
    except Exception as exc:
        print(f"Error: {exc}", flush=True)
        exit(1)
