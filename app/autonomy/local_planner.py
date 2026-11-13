"""Bounded local-model planner adapter; model output is never executable."""
from __future__ import annotations

import json
import os
import urllib.request


DEFAULT_MODEL = "gemma3:4b"
MAX_GOAL_CHARS = 1000


class LocalPlannerUnavailable(RuntimeError):
    pass


def _chat(messages: list[dict], schema: dict, timeout: float) -> tuple[dict, str]:
    model = os.environ.get("NEXTDECODE_LOCAL_PLANNER_MODEL", DEFAULT_MODEL).strip()
    if not model or len(model) > 100:
        raise LocalPlannerUnavailable("invalid local planner model setting")
    payload = {
        "model": model,
        "stream": False,
        "format": schema,
        "options": {"temperature": 0, "num_predict": 768},
        "messages": messages,
    }
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            envelope = json.loads(response.read().decode("utf-8"))
        content = envelope.get("message", {}).get("content", "")
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError("model response must be an object")
        return result, model
    except Exception as exc:
        raise LocalPlannerUnavailable(type(exc).__name__) from None


def propose_plan(goal: str, capabilities: list[dict], timeout: float = 25.0) -> tuple[dict, str]:
    """Ask the local model for a bounded capability DAG using a JSON schema."""
    if not isinstance(goal, str) or not 1 <= len(goal.strip()) <= MAX_GOAL_CHARS:
        raise ValueError("goal must be 1..1000 characters")
    allowed = sorted({
        item["name"] for item in capabilities
        if item.get("enabled") is True and item.get("planner_allowed") is True
    })
    if not allowed:
        raise LocalPlannerUnavailable("no planner-approved capabilities are registered")
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "maxLength": 200},
            "nodes": {
                "type": "array",
                "minItems": 1,
                "maxItems": 8,
                "items": {
                    "type": "object",
                    "properties": {
                        "step_id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,31}$"},
                        "task_type": {"type": "string", "enum": allowed},
                        "payload": {"type": "object"},
                        "depends_on": {
                            "type": "array", "maxItems": 8,
                            "items": {"type": "string"},
                        },
                        "priority": {"type": "integer", "minimum": -1000, "maximum": 1000},
                        "max_attempts": {"type": "integer", "minimum": 1, "maximum": 10},
                    },
                    "required": ["step_id", "task_type", "payload", "depends_on"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["summary", "nodes"],
        "additionalProperties": False,
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are a bounded workflow planner for NEXTDECODE. Return a DAG only. "
                "Use only the supplied registered capability IDs. The only permitted "
                "deliverables are research briefs and editorial script drafts. Do not "
                "plan full video rendering, publishing, uploading, shell execution, code "
                "execution, browser actions, arbitrary file access, credentials, URLs, "
                "or external paid services. A script draft always requires human review. "
                "Every script-draft node must have exactly one upstream research.topic.collect node. "
                "Use dependencies by step_id. Never duplicate a task merely to make a longer plan. "
                "Payloads may contain "
                "only topic and, for research, max_sources. Return concise JSON."
            ),
        },
        {"role": "user", "content": goal.strip()[:MAX_GOAL_CHARS]},
    ]
    return _chat(messages, schema, timeout)


def classify_goal(goal: str, timeout: float = 12.0) -> tuple[str, str]:
    """Compatibility classifier for ambiguous editorial-format requests."""
    allowed = {"content.short.script.draft", "content.longform.script.draft"}
    schema = {
        "type": "object",
        "properties": {"task_type": {"type": "string", "enum": sorted(allowed)}},
        "required": ["task_type"],
        "additionalProperties": False,
    }
    messages = [
        {
            "role": "system",
            "content": (
                "Choose the appropriate script-draft capability only. "
                "Use content.short.script.draft for Shorts/Reels up to 90 seconds. "
                "Use content.longform.script.draft for a long-form YouTube explainer. "
                "Do not choose full video rendering, publishing, uploading, code, or tools."
            ),
        },
        {"role": "user", "content": goal[:MAX_GOAL_CHARS]},
    ]
    result, model = _chat(messages, schema, timeout)
    task_type = result.get("task_type")
    if task_type not in allowed:
        raise LocalPlannerUnavailable("local model returned an unsupported capability")
    return task_type, model
