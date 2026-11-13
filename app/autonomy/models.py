"""Versioned, validated contracts for autonomous task execution."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import re
import uuid

SCHEMA_VERSION = "nextdecode.autonomy.task.v1"
TASK_ID_RE = re.compile(r"^[a-f0-9]{32}$")
SENSITIVE_KEY_RE = re.compile(r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|credential)", re.I)

def _reject_secret_fields(value, path="payload"):
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                raise ValueError(f"sensitive field is not accepted: {path}.{key}")
            _reject_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_fields(child, f"{path}[{index}]")

@dataclass(frozen=True)
class TaskRequest:
    task_type: str
    payload: dict = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    max_attempts: int = 3
    priority: int = 100
    idempotency_key: str | None = None
    not_before: str | None = None
    schema_version: str = SCHEMA_VERSION
    context: dict = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self):
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported task schema version")
        if not TASK_ID_RE.fullmatch(self.task_id):
            raise ValueError("task_id must be a 32-character lowercase hex UUID")
        if not self.task_type or len(self.task_type) > 100:
            raise ValueError("task_type must be 1..100 characters")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be an object")
        _reject_secret_fields(self.payload)
        if not isinstance(self.context, dict):
            raise ValueError("execution context must be an object")
        _reject_secret_fields(self.context, "context")
        if len(str(self.context).encode("utf-8")) > 65_536:
            raise ValueError("execution context exceeds 65536 bytes")
        if not 1 <= self.max_attempts <= 10:
            raise ValueError("max_attempts must be between 1 and 10")
        if not -1000 <= self.priority <= 1000:
            raise ValueError("priority must be between -1000 and 1000")
        if self.idempotency_key is not None and (
            not isinstance(self.idempotency_key, str) or not 1 <= len(self.idempotency_key) <= 200
        ):
            raise ValueError("idempotency_key must be 1..200 characters")

    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("context", None)
        return data

@dataclass(frozen=True)
class TaskResult:
    status: str
    output: dict = field(default_factory=dict)
    error_code: str | None = None
    retryable: bool = False
    evidence: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.status not in {"succeeded", "failed", "blocked"}:
            raise ValueError("invalid task result status")
        if self.status == "failed" and not self.error_code:
            raise ValueError("failed result requires error_code")

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
