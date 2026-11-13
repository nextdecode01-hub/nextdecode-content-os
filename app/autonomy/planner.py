"""Bounded multi-step planner with validated capability DAGs."""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass

from .plan_contract import PlanValidationError, validate_plan_nodes
from .registry import CapabilityRegistry, build_default_registry
from .store import create_task_store


@dataclass(frozen=True)
class PlanDecision:
    accepted: bool
    reason: str
    plan_id: str | None = None
    plan: dict | None = None


class TaskPlanner:
    """Convert editorial requests into a bounded, dependency-aware DAG.

    Research is an explicit first-class task. Script drafting consumes the
    verified research artifact through worker-supplied dependency context.
    Video rendering and all external actions remain outside this planner.
    """

    def __init__(self, store, registry: CapabilityRegistry | None = None):
        self.store = store
        self.registry = registry or build_default_registry()

    @staticmethod
    def _topic(goal: str, supplied: str | None) -> str:
        if supplied is not None:
            if not isinstance(supplied, str):
                raise ValueError("topic_must_be_a_string")
            value = supplied.strip()
        else:
            match = re.search(r"(?:about|on|regarding|topic[:=])\s+(.+)$", goal, re.I)
            if match:
                value = match.group(1).strip(" .!?")
            else:
                value = re.sub(r"^(?:please\s+)?(?:research|investigate|create|make|write|draft)\s+", "", goal, flags=re.I).strip(" .!?")
                if not value:
                    value = goal.strip(" .!?")
        if not value:
            raise ValueError("topic_required")
        if len(value) > 200:
            raise ValueError("topic_too_long")
        return value

    def _proposal(self, goal: str, topic: str) -> tuple[dict, str]:
        text = goal.casefold()
        if any(marker in text for marker in (
            "workflow", "multi-step", "multi step", "step-by-step",
            "content package", "campaign plan", "series plan",
        )):
            from .local_planner import LocalPlannerUnavailable, propose_plan
            try:
                proposal, _model = propose_plan(goal, self.registry.describe())
                return proposal, "local_model_validated_dag"
            except LocalPlannerUnavailable:
                # The deterministic rules below remain the no-cost offline fallback.
                pass
        long_form = any(word in text for word in (
            "long-form", "longform", "long form", "long video", "documentary",
            "10 minute", "10-minute", "8 minute", "8-minute",
        ))
        short_form = any(word in text for word in (
            "short", "shorts", "reel", "reels", "60 second", "60-second",
            "vertical video", "short video",
        ))
        research_requested = any(word in text for word in (
            "research", "investigate", "source-check", "fact-check", "evidence brief",
        ))
        script_requested = any(word in text for word in (
            "script", "draft", "write", "create", "make", "produce", "prepare",
        ))
        if any(word in text for word in (
            "publish", "upload", "post publicly", "send live", "schedule a post",
        )):
            raise ValueError("external_publishing_requires_separate_human_approval")
        if not short_form and not long_form and not research_requested:
            media_target = any(word in text for word in (
                "video", "youtube", "explainer", "promo", "film",
            ))
            if media_target:
                from .local_planner import classify_goal
                try:
                    selected, _model = classify_goal(goal)
                except Exception:
                    # The safe deterministic fallback is a reviewable Short script,
                    # never a full render or external action.
                    selected = "content.short.script.draft"
                if selected not in {"content.short.script.draft", "content.longform.script.draft"}:
                    raise ValueError("unsupported_goal_needs_specialist_or_clarification")
                long_form = selected == "content.longform.script.draft"
                short_form = selected == "content.short.script.draft"
            else:
                raise ValueError("unsupported_goal_needs_specialist_or_clarification")
        if not script_requested and (short_form or long_form):
            # A video request starts with the reviewable script deliverable.
            script_requested = True
        if not (research_requested or script_requested):
            raise ValueError("unsupported_goal_needs_specialist_or_clarification")

        nodes = []
        needs_research = research_requested or script_requested
        if needs_research:
            nodes.append({
                "step_id": "research",
                "task_type": "research.topic.collect",
                "payload": {"topic": topic, "max_sources": 4},
                "depends_on": [],
                "priority": 120,
                "max_attempts": 2,
            })
        if script_requested:
            if short_form:
                nodes.append({
                    "step_id": "short_script",
                    "task_type": "content.short.script.draft",
                    "payload": {"topic": topic},
                    "depends_on": ["research"],
                    "priority": 100,
                    "max_attempts": 2,
                })
            if long_form:
                nodes.append({
                    "step_id": "longform_script",
                    "task_type": "content.longform.script.draft",
                    "payload": {"topic": topic},
                    "depends_on": ["research"],
                    "priority": 100,
                    "max_attempts": 2,
                })
        if not nodes:
            raise ValueError("no_safe_plan_steps_available")
        summary = (
            "Research a topic and prepare reviewable script drafts; rendering, "
            "publishing and external actions are not part of this plan."
        )
        return {"summary": summary, "nodes": nodes}, "research_and_script_draft"

    def propose(self, goal: str, *, topic: str | None = None, dry_run: bool = True,
                idempotency_key: str | None = None) -> PlanDecision:
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 1000:
            return PlanDecision(False, "goal_must_be_1_to_1000_characters")
        if dry_run is not True:
            return PlanDecision(False, "non_dry_run_requires_separate_authorization")
        if idempotency_key is not None and (
            not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 200
        ):
            return PlanDecision(False, "invalid_idempotency_key")
        if any(word in goal.casefold() for word in (
            "publish", "upload", "post publicly", "send live", "schedule a post",
        )):
            return PlanDecision(False, "external_publishing_requires_separate_human_approval")
        try:
            topic_value = self._topic(goal, topic)
            proposal, intent = self._proposal(goal.strip(), topic_value)
            nodes = validate_plan_nodes(proposal, self.registry)
        except (ValueError, PlanValidationError) as exc:
            return PlanDecision(False, str(exc)[:240])
        except Exception as exc:
            return PlanDecision(False, f"planner_unavailable:{type(exc).__name__}")

        plan_id = uuid.uuid4().hex
        plan = {
            "schema_version": "nextdecode.autonomy.plan.v1",
            "plan_id": plan_id,
            "goal": goal.strip(),
            "summary": proposal.get("summary", ""),
            "intent": intent,
            "status": "queued",
            "human_approval_required": True,
            "external_actions_allowed": False,
            "nodes": nodes,
        }
        if idempotency_key:
            plan["idempotency_key"] = idempotency_key
        try:
            stored = self.store.enqueue_plan(
                plan_id, goal.strip(), nodes, plan, idempotency_key=idempotency_key
            )
        except ValueError as exc:
            return PlanDecision(False, str(exc)[:240])
        persisted_plan = json.loads(stored["plan"]["plan_json"])
        return PlanDecision(
            True,
            "plan_created" if stored["plan"]["plan_id"] == plan_id else "idempotent_replay",
            stored["plan"]["plan_id"],
            persisted_plan,
        )
