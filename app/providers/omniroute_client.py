"""Small OpenAI-compatible client for the local OmniRoute gateway."""
from __future__ import annotations

import json
import os
import re

import requests


DEFAULT_MODEL = "groq/openai/gpt-oss-120b"
DEFAULT_FALLBACK_MODELS = ""


def is_configured() -> bool:
    return bool(
        os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1").strip()
        and os.getenv("OMNIROUTE_API_KEY", "").strip()
    )


def model_chain() -> list[str]:
    """Ordered model list for the gateway, primary first."""
    primary = os.getenv("OMNIROUTE_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    raw = os.getenv("OMNIROUTE_FALLBACK_MODELS", DEFAULT_FALLBACK_MODELS).strip()
    chain = [primary]
    for item in raw.split(","):
        candidate = item.strip()
        if candidate and candidate not in chain:
            chain.append(candidate)
    return chain


def generate_json(prompt: str, temperature: float, timeout: int) -> dict:
    base_url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1").strip().rstrip("/")
    api_key = os.getenv("OMNIROUTE_API_KEY", "").strip()
    if not base_url or not api_key:
        raise RuntimeError("Set OMNIROUTE_BASE_URL and OMNIROUTE_API_KEY in .env.")

    errors: list[str] = []
    for model in model_chain():
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                },
                timeout=timeout,
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"].strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("OmniRoute returned JSON that is not an object.")
            return parsed
        except Exception as exc:
            errors.append(f"{model} {type(exc).__name__}")
    raise RuntimeError("OmniRoute request failed: " + ", ".join(errors))
