"""Strict validation for model- or rule-proposed autonomy DAGs."""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from .models import TaskRequest

PLAN_SCHEMA_VERSION = "nextdecode.autonomy.plan.v1"
MAX_PLAN_NODES = 32
MAX_DEPENDENCIES = 8
MAX_NODE_PAYLOAD_BYTES = 65_536
MAX_PLAN_BYTES = 262_144
_STEP_ID = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_NODE_FIELDS = {"step_id", "task_type", "payload", "depends_on", "priority", "max_attempts"}


class PlanValidationError(ValueError):
    """A proposed plan violates the bounded execution contract."""


def canonical_plan_request(goal: str, nodes: list[dict]) -> dict:
    """Stable request identity independent of generated plan/task UUIDs."""
    step_for_task = {
        node["task_id"]: node.get("step_id", str(index))
        for index, node in enumerate(nodes)
    }
    normalized = []
    for index, node in enumerate(nodes):
        normalized.append({
            "step_id": node.get("step_id", str(index)),
            "task_type": node["task_type"],
            "payload": node.get("payload", {}),
            "priority": node.get("priority", 100),
            "max_attempts": node.get("max_attempts", 3),
            "depends_on": sorted(step_for_task[parent] for parent in node.get("depends_on", [])),
        })
    return {"goal": goal, "nodes": normalized}


def validate_plan_nodes(proposal: dict[str, Any], registry) -> list[dict]:
    """Validate a plan against registered capability contracts and return DAG nodes.

    The model controls neither executable commands nor permissions. It can only
    select an enabled, planner-approved capability and supply its bounded payload.
    """
    if not isinstance(proposal, dict) or set(proposal) - {"nodes", "summary"}:
        raise PlanValidationError("plan must be an object containing only nodes and summary")
    summary = proposal.get("summary", "")
    if not isinstance(summary, str) or len(summary) > 200:
        raise PlanValidationError("plan summary must be at most 200 characters")
    raw_nodes = proposal.get("nodes")
    if not isinstance(raw_nodes, list) or not 1 <= len(raw_nodes) <= MAX_PLAN_NODES:
        raise PlanValidationError(f"plan must contain 1..{MAX_PLAN_NODES} nodes")

    by_step: dict[str, dict] = {}
    for raw in raw_nodes:
        if not isinstance(raw, dict) or set(raw) - _NODE_FIELDS:
            raise PlanValidationError("plan node contains unknown fields")
        step_id = raw.get("step_id")
        if not isinstance(step_id, str) or not _STEP_ID.fullmatch(step_id):
            raise PlanValidationError("invalid plan step_id")
        if step_id in by_step:
            raise PlanValidationError("duplicate plan step_id")
        task_type = raw.get("task_type")
        if not isinstance(task_type, str):
            raise PlanValidationError("task_type must be a string")
        try:
            capability = registry.get(task_type)
        except KeyError:
            raise PlanValidationError("unsupported plan capability") from None
        if not getattr(capability, "planner_allowed", True):
            raise PlanValidationError("capability is not available to the planner")
        payload = raw.get("payload", {})
        if not isinstance(payload, dict):
            raise PlanValidationError("task payload must be an object")
        if len(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")) > MAX_NODE_PAYLOAD_BYTES:
            raise PlanValidationError("task payload exceeds 65536 bytes")
        priority = raw.get("priority", 100)
        max_attempts = raw.get("max_attempts", 3)
        try:
            # Reuse the task contract's secret, priority and retry validation.
            TaskRequest(task_type=task_type, payload=payload,
                        priority=priority, max_attempts=max_attempts)
        except (TypeError, ValueError) as exc:
            raise PlanValidationError(str(exc)) from None
        validator = getattr(capability, "payload_validator", None)
        if validator:
            try:
                payload = validator(dict(payload))
            except (TypeError, ValueError) as exc:
                raise PlanValidationError(str(exc)) from None
        dependencies = raw.get("depends_on", [])
        if not isinstance(dependencies, list) or len(dependencies) > MAX_DEPENDENCIES:
            raise PlanValidationError("each plan node supports at most 8 dependencies")
        if any(not isinstance(dep, str) for dep in dependencies):
            raise PlanValidationError("dependencies must reference step_id strings")
        if len(set(dependencies)) != len(dependencies):
            raise PlanValidationError("duplicate dependency")
        by_step[step_id] = {
            "step_id": step_id,
            "task_type": task_type,
            "payload": payload,
            "depends_on_steps": dependencies,
            "priority": priority,
            "max_attempts": max_attempts,
            "task_id": uuid.uuid4().hex,
        }

    for step_id, node in by_step.items():
        for parent in node["depends_on_steps"]:
            if parent not in by_step:
                raise PlanValidationError("dependency references an unknown step")
            if parent == step_id:
                raise PlanValidationError("task cannot depend on itself")

    visiting: set[str] = set()
    visited: set[str] = set()
    ordered: list[str] = []

    def visit(step_id: str) -> None:
        if step_id in visiting:
            raise PlanValidationError("plan dependency graph contains a cycle")
        if step_id in visited:
            return
        visiting.add(step_id)
        for parent in by_step[step_id]["depends_on_steps"]:
            visit(parent)
        visiting.remove(step_id)
        visited.add(step_id)
        ordered.append(step_id)

    for step_id in by_step:
        visit(step_id)

    # Script specialists may only execute with exactly one upstream research
    # task. Enforce this at plan time, not merely as a runtime handler check.
    script_capabilities = {
        "content.short.script.draft", "content.longform.script.draft",
    }
    for step_id, node in by_step.items():
        if node["task_type"] not in script_capabilities:
            continue
        ancestors: set[str] = set()
        stack = list(node["depends_on_steps"])
        while stack:
            parent = stack.pop()
            if parent in ancestors:
                continue
            ancestors.add(parent)
            stack.extend(by_step[parent]["depends_on_steps"])
        research_ancestors = [
            parent for parent in ancestors
            if by_step[parent]["task_type"] == "research.topic.collect"
        ]
        if len(research_ancestors) != 1:
            raise PlanValidationError(
                "script drafting requires exactly one upstream research step"
            )

    task_ids = {step_id: node["task_id"] for step_id, node in by_step.items()}
    nodes = []
    for step_id in ordered:
        node = by_step[step_id]
        nodes.append({
            "task_id": node["task_id"],
            "step_id": step_id,
            "task_type": node["task_type"],
            "payload": node["payload"],
            "priority": node["priority"],
            "max_attempts": node["max_attempts"],
            "depends_on": [task_ids[item] for item in node["depends_on_steps"]],
        })
    total_size = len(json.dumps(nodes, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    if total_size > MAX_PLAN_BYTES:
        raise PlanValidationError("plan exceeds 262144 bytes")
    return nodes
