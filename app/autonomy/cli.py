"""CLI for enqueueing, inspecting and running autonomous tasks."""
from __future__ import annotations
import argparse
import json
import signal
import threading
from pathlib import Path
from dotenv import load_dotenv
from .models import TaskRequest
from .planner import TaskPlanner
from .tool_catalog import list_capabilities as list_tool_capabilities, rank_candidates
from .registry import build_default_registry
from .store import create_task_store
from .worker import TaskWorker
from .worker_lifecycle import reconcile_workers
from .agent_runtime import agent_runtime_registry, execution_readiness_report, AgentReadinessEvidence
from .agent_assignment import AgentAssignmentPlanner, AssignmentRequest, QualificationRecord
from .agent_workspace import (
    prepare_workspace, list_workspaces, collect_workspace_changes,
    AgentExecutionAdapter,
)
from .agent_change_review import review_workspace_changes
from .agent_change_approval import approve_added_file, prepare_approved_staging

ROOT = Path(__file__).resolve().parents[2]

def _store(path: str | None):
    if path is not None:
        return create_task_store(path)
    return create_task_store()

def main(argv=None) -> int:
    load_dotenv(Path.home() / ".config" / "nextdecode" / "autonomy-db.env", override=False)
    parser = argparse.ArgumentParser(prog="nextdecode-task")
    parser.add_argument("--db", help="Explicit SQLite task database path (overrides DATABASE_URL)")
    sub = parser.add_subparsers(dest="command", required=True)
    enqueue = sub.add_parser("enqueue")
    enqueue.add_argument("task_type")
    enqueue.add_argument("--payload", default="{}")
    enqueue.add_argument("--idempotency-key")
    enqueue.add_argument("--max-attempts", type=int, default=3)
    sub.add_parser("list")
    inspect = sub.add_parser("show")
    inspect.add_argument("task_id")
    run = sub.add_parser("run-once")
    run.add_argument("--worker-id")
    serve = sub.add_parser("worker")
    serve.add_argument("--poll-seconds", type=float, default=2.0)
    sub.add_parser("capabilities")
    agents = sub.add_parser("agents", help="Read-only discovery of local specialist agent CLIs")
    agents.add_argument("--role")
    sub.add_parser("agent-readiness", help="Read-only agent readiness and qualification report; never invokes agents")
    assignment_plan = sub.add_parser("agent-assignment-plan", help="Evaluate a plan-only agent assignment from explicit JSON evidence; never invokes agents")
    assignment_plan.add_argument("--request", required=True, help="JSON assignment request")
    assignment_plan.add_argument("--readiness-evidence", default="{}", help="JSON readiness evidence keyed by agent ID")
    assignment_plan.add_argument("--qualification", help="JSON qualification record")
    agent_workspace = sub.add_parser("agent-workspace", help="Prepare and inspect coding-agent workspaces")
    workspace_sub = agent_workspace.add_subparsers(dest="workspace_command", required=True)
    workspace_sub.add_parser("prepare")
    workspace_sub.add_parser("list")
    workspace_collect = workspace_sub.add_parser("collect", help="Report workspace changes without importing them")
    workspace_collect.add_argument("workspace_id")
    workspace_review = workspace_sub.add_parser("review", help="Review workspace changes for safety; never imports them")
    workspace_review.add_argument("workspace_id")
    workspace_approve = workspace_sub.add_parser("approve", help="Explicitly approve one added file for staging only")
    workspace_approve.add_argument("workspace_id")
    workspace_approve.add_argument("--path", required=True)
    workspace_approve.add_argument("--sha256", required=True)
    workspace_approve.add_argument("--reason", required=True)
    workspace_stage = workspace_sub.add_parser("stage-approved", help="Prepare approved files in isolated staging; never imports")
    workspace_stage.add_argument("workspace_id")
    workspace_sub.add_parser("readiness", help="Inspect agent execution prerequisites without launching anything")
    workspace_plan = workspace_sub.add_parser("plan", help="Create a fail-closed agent invocation plan")
    workspace_plan.add_argument("workspace_id")
    workspace_plan.add_argument("--agent", required=True)
    workspace_plan.add_argument("--task", required=True)
    workspace_plan.add_argument("--timeout-seconds", type=int, default=900)
    plan = sub.add_parser("plan")
    plan.add_argument("goal")
    plan.add_argument("--topic")
    show_plan = sub.add_parser("show-plan")
    show_plan.add_argument("plan_id")
    catalog = sub.add_parser("tool-catalog")
    catalog.add_argument("--capability")
    event_feed = sub.add_parser("events")
    event_feed.add_argument("--after-event-id", type=int, default=0)
    event_feed.add_argument("--limit", type=int, default=100)
    recover = sub.add_parser("recover-expired")
    recover.add_argument("--limit", type=int, default=100)
    stuck = sub.add_parser("stuck-tasks")
    stuck.add_argument("--stale-after-seconds", type=int, default=120)
    stuck.add_argument("--limit", type=int, default=100)
    worker_reconcile = sub.add_parser("reconcile-workers")
    worker_reconcile.add_argument("--stale-after-seconds", type=int, default=45)
    worker_reconcile.add_argument("--apply", action="store_true")
    sub.add_parser("health")
    dead = sub.add_parser("dead-letters")
    dead.add_argument("--limit", type=int, default=100)
    args = parser.parse_args(argv)

    if args.command == "agent-workspace":
        if args.workspace_command == "prepare":
            print(json.dumps({"workspace": prepare_workspace().__dict__,
                              "agent_invocation": "disabled"}, indent=2))
        elif args.workspace_command == "list":
            print(json.dumps({"workspaces": list_workspaces(),
                              "agent_invocation": "disabled"}, indent=2))
        elif args.workspace_command == "collect":
            print(json.dumps(collect_workspace_changes(args.workspace_id), indent=2))
        elif args.workspace_command == "review":
            print(json.dumps(review_workspace_changes(args.workspace_id), indent=2))
        elif args.workspace_command == "approve":
            print(json.dumps(approve_added_file(
                args.workspace_id, args.path, args.sha256, args.reason
            ), indent=2))
        elif args.workspace_command == "stage-approved":
            print(json.dumps(prepare_approved_staging(args.workspace_id), indent=2))
        elif args.workspace_command == "readiness":
            print(json.dumps(execution_readiness_report(), indent=2))
        elif args.workspace_command == "plan":
            # Invocation remains disabled. This adapter is intentionally fail-closed.
            adapter = AgentExecutionAdapter()
            print(json.dumps(adapter.plan(
                agent_id=args.agent, workspace_id=args.workspace_id,
                task=args.task, timeout_seconds=args.timeout_seconds,
            ), indent=2))
        return 0

    if args.command == "agent-readiness":
        print(json.dumps(agent_runtime_registry.readiness(), indent=2))
        return 0

    if args.command == "agent-assignment-plan":
        try:
            request_data = json.loads(args.request)
            if not isinstance(request_data, dict):
                raise ValueError("assignment request must be a JSON object")
            allowed_request_fields = {
                "assignment_id", "task_id", "agent_id", "capability", "objective",
                "input_references", "acceptance_criteria", "permission_scope", "correlation_id",
                "timeout_seconds",
            }
            unknown_fields = sorted(set(request_data) - allowed_request_fields)
            if unknown_fields:
                raise ValueError("unsupported assignment fields: " + ", ".join(unknown_fields))
            request_data["input_references"] = tuple(request_data.get("input_references", ()))
            request_data["acceptance_criteria"] = tuple(request_data.get("acceptance_criteria", ()))
            request_data["permission_scope"] = tuple(request_data.get("permission_scope", ()))
            request = AssignmentRequest(**request_data)
            raw_evidence = json.loads(args.readiness_evidence)
            if not isinstance(raw_evidence, dict):
                raise ValueError("readiness evidence must be a JSON object")
            evidence = {agent_id: AgentReadinessEvidence(**record)
                        for agent_id, record in raw_evidence.items()}
            qualification = QualificationRecord(**json.loads(args.qualification)) if args.qualification else None
            decision = AgentAssignmentPlanner().plan(
                request, readiness_evidence=evidence, qualification=qualification,
            )
            print(json.dumps(decision, indent=2))
            return 0 if decision["accepted"] else 2
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "denied", "accepted": False,
                              "denial_reason_codes": ["invalid_assignment_input"],
                              "detail": str(exc), "process_started": False}, indent=2))
            return 2

    store = _store(args.db)
    if args.command == "enqueue":
        payload = json.loads(args.payload)
        capability = build_default_registry().get(args.task_type)
        if capability.payload_validator:
            payload = capability.payload_validator(payload)
        task = TaskRequest(task_type=args.task_type, payload=payload,
                           idempotency_key=args.idempotency_key, max_attempts=args.max_attempts)
        print(json.dumps(store.enqueue(task), indent=2))
    elif args.command == "list":
        print(json.dumps(store.list(), indent=2))
    elif args.command == "show":
        row = store.get(args.task_id)
        if row is None:
            print(json.dumps({"error": "not_found"}))
            return 1
        print(json.dumps({"task": row, "events": store.events(args.task_id)}, indent=2))
    elif args.command == "run-once":
        print(json.dumps({"worked": TaskWorker(store, worker_id=args.worker_id).run_once()}))
    elif args.command == "worker":
        shutdown = threading.Event()
        def request_shutdown(signum, _frame):
            shutdown.set()
        signal.signal(signal.SIGINT, request_shutdown)
        signal.signal(signal.SIGTERM, request_shutdown)
        TaskWorker(store).serve(args.poll_seconds, stop_event=shutdown)
    elif args.command == "capabilities":
        print(json.dumps(build_default_registry().describe(), indent=2))
    elif args.command == "agents":
        result = agent_runtime_registry.rank(args.role) if args.role else agent_runtime_registry.discover()
        print(json.dumps({"mode": "read_only_discovery", "invocation_enabled": False,
                          "agents": result}, indent=2))
    elif args.command == "plan":
        decision = TaskPlanner(store).propose(args.goal, topic=args.topic, dry_run=True)
        print(json.dumps({"accepted": decision.accepted, "reason": decision.reason,
                          "plan_id": decision.plan_id, "plan": decision.plan}, indent=2))
        return 0 if decision.accepted else 2
    elif args.command == "show-plan":
        plan_data = store.get_plan(args.plan_id)
        if plan_data is None:
            print(json.dumps({"error": "not_found"}))
            return 1
        print(json.dumps(plan_data, indent=2))
    elif args.command == "tool-catalog":
        result = rank_candidates(args.capability) if args.capability else list_tool_capabilities()
        print(json.dumps(result, indent=2))
    elif args.command == "events":
        print(json.dumps(store.event_feed(args.after_event_id, args.limit), indent=2))
    elif args.command == "recover-expired":
        print(json.dumps({"recovered": store.recover_expired_leases(args.limit)}, indent=2))
    elif args.command == "stuck-tasks":
        print(json.dumps({"stale_after_seconds": args.stale_after_seconds,
                          "tasks": store.stuck_tasks(args.stale_after_seconds, args.limit)}, indent=2))
    elif args.command == "reconcile-workers":
        print(json.dumps(reconcile_workers(store, stale_after_seconds=args.stale_after_seconds,
                                           apply=args.apply), indent=2))
    elif args.command == "health":
        print(json.dumps(store.health(), indent=2))
    elif args.command == "dead-letters":
        print(json.dumps(store.dead_letters(args.limit), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
