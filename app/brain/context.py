from __future__ import annotations
import json
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTEXT_PATH = ROOT / "config" / "brain" / "project_context.v1.json"
def load_project_context(path: Path | str | None = None) -> dict[str, Any]:
    target = Path(path) if path is not None else DEFAULT_CONTEXT_PATH
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "nextdecode.brain.project-context.v1":
        raise ValueError("unsupported_project_context_schema")
    required = ("project", "identity", "production", "guardrails", "authority")
    if any(not isinstance(payload.get(key), dict) for key in required):
        raise ValueError("invalid_project_context_sections")
    return payload
