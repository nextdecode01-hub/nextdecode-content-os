"""Z.AI GLM adapters. Provisional until quality, quota and latency gates pass."""
from __future__ import annotations
import os, requests
from typing import Any

BASE_URL=os.getenv("ZAI_BASE_URL","https://api.z.ai/api/paas/v4").rstrip("/")
TEXT_MODEL=os.getenv("ZAI_TEXT_MODEL","glm-4.5-flash")
VISION_MODEL=os.getenv("ZAI_VISION_MODEL","glm-4.6v-flash")
TIMEOUT=(8,60)

def _key() -> str:
    return os.getenv("Z_API_KEY","").strip()

def chat(messages: list[dict[str,Any]], *, model: str|None=None, temperature: float=0.2, max_tokens: int=1800) -> dict:
    """OpenAI-compatible chat completion; raises on auth/quota errors, no hidden fallback."""
    key=_key()
    if not key: raise RuntimeError("Z_API_KEY is not configured")
    chosen=model or TEXT_MODEL
    r=requests.post(f"{BASE_URL}/chat/completions",
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
        json={"model":chosen,"messages":messages,"temperature":max(0,min(float(temperature),1)),
              "max_tokens":max(1,min(int(max_tokens),4096))},timeout=TIMEOUT)
    r.raise_for_status(); data=r.json(); choices=data.get("choices") or []
    if not choices: raise RuntimeError("Z.AI returned no completion choices")
    return {"provider":"zai","model":chosen,"content":(choices[0].get("message") or {}).get("content",""),
            "usage":data.get("usage") or {}}

def inspect_image(image_url: str, prompt: str, *, model: str|None=None, max_tokens: int=900) -> dict:
    """Inspect a reachable HTTP(S) image URL using GLM vision."""
    key=_key()
    if not key: raise RuntimeError("Z_API_KEY is not configured")
    if not str(image_url).startswith(("https://","http://")): raise ValueError("image_url must be HTTP(S)")
    chosen=model or VISION_MODEL
    r=requests.post(f"{BASE_URL}/chat/completions",
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
        json={"model":chosen,"messages":[{"role":"user","content":[{"type":"text","text":str(prompt)[:4000]},
              {"type":"image_url","image_url":{"url":image_url}}]}],
              "max_tokens":max(1,min(int(max_tokens),2048)),"temperature":0.1},timeout=TIMEOUT)
    r.raise_for_status(); data=r.json(); choices=data.get("choices") or []
    if not choices: raise RuntimeError("Z.AI returned no vision choices")
    return {"provider":"zai","model":chosen,"content":(choices[0].get("message") or {}).get("content",""),
            "usage":data.get("usage") or {}}
