"""Task-aware exact-model routing for NEXTDECODE production workloads.

The router never invents model names and never silently changes task roles.
It walks only the task's configured candidate list, checks configuration and
recent health, and records the selected model in a bounded run-local trace.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
DEFAULT_ROUTING_PATH = ROOT / "config" / "brain" / "model_task_routing.v1.json"


class ModelRouteError(RuntimeError):
    pass


def load_routing(path: str | Path | None = None) -> dict:
    data = json.loads(Path(path or DEFAULT_ROUTING_PATH).read_text(encoding="utf-8"))
    if data.get("schema") != "nextdecode.model-task-routing.v1":
        raise ValueError("unsupported model task-routing schema")
    return data


def _configured(provider: str) -> bool:
    from . import model_health
    return model_health._is_configured(provider)


def _call_exact(provider: str, model: str, prompt: str, timeout: int, json_mode: bool, temperature: float = 0.35) -> str:
    from . import multi_model_ai as ai
    if provider == "groq":
        return ai.call_groq(prompt, model=model, temperature=temperature, timeout=timeout, json_mode=json_mode)
    if provider == "gemini":
        return ai.call_gemini(prompt, model=model, temperature=temperature, timeout=timeout, json_mode=json_mode)
    if provider == "nvidia":
        keys = list(dict.fromkeys(x for x in (os.getenv("NVIDIA_API_KEY", "").strip(), os.getenv("NVIDIA_API_KEY_2", "").strip()) if x))
        if not keys:
            raise RuntimeError("provider_not_configured")
        errors = []
        for key in keys:
            try:
                return ai.call_openai_compatible(prompt, base_url=ai.NVIDIA_NIM_URL, api_key=key, model=model,
                    temperature=temperature, timeout=timeout, json_mode=json_mode, provider=provider)
            except Exception as exc:
                errors.append(type(exc).__name__)
        raise RuntimeError("NVIDIA request failed: " + ",".join(errors))
    if provider == "cloudflare":
        base = ai._cf_ai_base_url()
        if not base:
            raise RuntimeError("provider_not_configured")
        return ai.call_openai_compatible(prompt, base_url=base, api_key=os.getenv("CF_API_TOKEN", ""),
            model=model, temperature=temperature, timeout=timeout, json_mode=json_mode, provider=provider)
    if provider == "openrouter":
        return ai.call_openai_compatible(prompt, base_url=ai.OPENROUTER_URL,
            api_key=os.getenv("OPENROUTER_API_KEY", ""), model=model, temperature=temperature,
            timeout=timeout, json_mode=json_mode, provider=provider)
    if provider == "pollinations_text":
        return ai.call_openai_compatible(prompt, base_url=ai.POLLINATIONS_TEXT_URL, model=model,
            temperature=temperature, timeout=timeout, json_mode=json_mode, provider=provider)
    raise ModelRouteError(f"no exact-model adapter registered for provider: {provider}")


def route_candidates(task: str, *, path: str | Path | None = None) -> list[dict[str, str]]:
    data = load_routing(path)
    spec = data.get("tasks", {}).get(task)
    if not isinstance(spec, dict):
        raise ModelRouteError(f"unknown production task: {task}")
    if spec.get("enabled") is False:
        return []
    candidates = [spec.get("primary"), *(spec.get("fallbacks") or [])]
    clean = []
    seen = set()
    for item in candidates:
        if not isinstance(item, dict):
            continue
        provider, model = str(item.get("provider") or ""), str(item.get("model") or "")
        key = (provider, model)
        if provider and model and key not in seen:
            clean.append({"provider": provider, "model": model})
            seen.add(key)
    return clean


_TASK_BENCHMARK_KIND = {
    # Editorial topic judging and research synthesis use the evidence benchmark:
    # without this mapping, a healthy/qualified Groq model was incorrectly
    # skipped whenever the provider-level health circuit was open.
    "research_synthesis": "evidence",
    "script_drafting": "script",
    "script_review": "script",
    "evidence_extraction": "evidence",
    "visual_plan": "visual",
}


def _qualified_for_task(task: str, provider: str, model: str, *, min_trials: int = 3,
                        min_pass_rate: float = 0.80, max_age_hours: float = 168.0) -> bool:
    """Use recent exact-model/task benchmark evidence to refine provider-level health.

    A provider-wide probe can fail on its default model while a different exact
    model succeeds. Only a complete repeated benchmark for the same task role
    may override that coarse failure; quota gates are never overridden.
    """
    kind = _TASK_BENCHMARK_KIND.get(task)
    if not kind:
        return False
    target = ROOT / "data" / "model_benchmark_v1" / "latest.json"
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        completed = datetime.fromisoformat(str(data.get("completed_at") or "").replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - completed.astimezone(timezone.utc)).total_seconds() / 3600
        if age < -1 or age > max_age_hours:
            return False
        key = f"{provider}:{model}:{kind}"
        record = (data.get("aggregate") or {}).get(key) or {}
        trials = int(record.get("trials") or 0)
        passes = int(record.get("passes") or 0)
        score = record.get("mean_score")
        return trials >= min_trials and passes / max(trials, 1) >= min_pass_rate and score is not None and float(score) >= 80.0
    except (OSError, ValueError, TypeError, OverflowError):
        return False


def generate_for_task(task: str, prompt: str, *, timeout: int = 45, json_mode: bool = False,
                      temperature: float = 0.35, path: str | Path | None = None,
                      trace_path: str | Path | None = None) -> dict[str, Any]:
    """Generate with task-specific exact models; return text plus provenance."""
    from . import model_health
    routing = load_routing(path)
    qualification_required = bool((routing.get("selection_policy") or {}).get("qualification_required"))
    failures = []
    for candidate in route_candidates(task, path=path):
        provider, model = candidate["provider"], candidate["model"]
        benchmark_kind = _TASK_BENCHMARK_KIND.get(task)
        if qualification_required and benchmark_kind and not _qualified_for_task(task, provider, model):
            failures.append({"provider": provider, "model": model, "reason": "task_qualification_missing_or_failed"})
            continue
        if not _configured(provider):
            failures.append({"provider": provider, "model": model, "reason": "not_configured"})
            continue
        if model_health.should_skip(provider) and not _qualified_for_task(task, provider, model):
            failures.append({"provider": provider, "model": model, "reason": "provider_health_gate"})
            continue
        quota = model_health.quota_status(provider, model=model)
        # Fresh evidence is re-recorded on every successful provider call, so
        # blocking *everything* on a stale stamp deadlocks the pipeline — no
        # probe job is scheduled.  Only a proven "exhausted" frees the decision
        # to move to the next candidate; "low", "unknown" and "available" all
        # resolve to one real call attempt, which is the only reliable probe.
        if quota == "exhausted":
            failures.append({"provider": provider, "model": model, "reason": f"quota_{quota}"})
            continue
        started = datetime.now(timezone.utc)
        try:
            text = _call_exact(provider, model, prompt, timeout, json_mode, temperature=temperature)
            record = {
                "schema": "nextdecode.model-route-result.v1",
                "task": task, "provider": provider, "model": model,
                "started_at": started.isoformat(), "completed_at": datetime.now(timezone.utc).isoformat(),
                "status": "success", "fallback_used": bool(failures),
                "failures_before_selection": failures,
            }
            if trace_path:
                target = Path(trace_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            return {"text": text, "route": record}
        except Exception as exc:
            failures.append({"provider": provider, "model": model, "reason": type(exc).__name__})
    raise ModelRouteError(f"all configured candidates failed for task '{task}': {failures}")


def routing_inventory(path: str | Path | None = None) -> dict:
    data = load_routing(path)
    tasks = {}
    for task in data.get("tasks", {}):
        candidates = route_candidates(task, path=path)
        tasks[task] = [{
            **candidate,
            "configured": _configured(candidate["provider"]),
        } for candidate in candidates]
    return {
        "schema": "nextdecode.model-routing-inventory.v1",
        "status": data.get("status"),
        "candidate_count": len({(x["provider"], x["model"]) for rows in tasks.values() for x in rows}),
        "candidate_pool_count": data.get("selection_policy", {}).get("candidate_pool_count", 0),
        "qualification_required": bool(data.get("selection_policy", {}).get("qualification_required", False)),
        "tasks": tasks,
    }
