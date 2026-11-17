from __future__ import annotations

from typing import Any

from app.autonomy.planner import TaskPlanner


_ALLOWED_FIELDS = {
    "goal", "topic", "dry_run", "idempotency_key",
    "studio_version_id", "studio_content_sha256", "studio_snapshot",
}


def propose_studio_workflow(data: Any, planner: TaskPlanner) -> dict:
    """Validate and create a provenance-bound Studio research→script plan.

    This is an API-layer adapter kept separate from the production observability
    routes. The caller remains responsible for authentication and HTTP mapping.
    """
    if not isinstance(data, dict) or set(data) - _ALLOWED_FIELDS:
        raise ValueError("invalid Studio plan request fields")
    if not all(key in data for key in (
        "goal", "studio_version_id", "studio_content_sha256", "studio_snapshot"
    )):
        raise ValueError("Studio plan requires goal, version ID, digest and snapshot")
    decision = planner.propose(
        data.get("goal"),
        topic=data.get("topic"),
        dry_run=data.get("dry_run", True),
        idempotency_key=data.get("idempotency_key"),
        studio_version_id=data.get("studio_version_id"),
        studio_content_sha256=data.get("studio_content_sha256"),
        studio_snapshot=data.get("studio_snapshot"),
    )
    if not decision.accepted:
        raise ValueError(decision.reason)
    return {"plan_id": decision.plan_id, "plan": decision.plan}
