from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .autonomy_observer import collect_local_autonomy_state
from .context import ROOT, load_project_context

BRAIN_VERSION = "nextdecode.brain.deterministic.v1"
MAX_RUNS = 30
MAX_MANIFEST_BYTES = 1024 * 1024


def _read_manifest(path: Path) -> dict[str, Any] | None:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_MANIFEST_BYTES:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not isinstance(value.get("run_id"), str):
            return None
        stages = value.get("stages") if isinstance(value.get("stages"), list) else []
        safe_stages = [
            {key: stage.get(key) for key in ("name", "status", "started_at", "finished_at")}
            for stage in stages[-40:] if isinstance(stage, dict)
        ]
        failure = value.get("failure") if isinstance(value.get("failure"), dict) else None
        safe_failure = {
            key: failure.get(key) for key in ("stage", "error_type", "error_category")
        } if failure else None
        artifacts = value.get("artifacts") if isinstance(value.get("artifacts"), dict) else {}
        return {
            "run_id": value["run_id"][:120],
            "topic": str(value.get("topic") or "")[:200],
            "status": str(value.get("status") or "unknown")[:40],
            "started_at": value.get("started_at"),
            "finished_at": value.get("finished_at"),
            "last_stage": safe_stages[-1] if safe_stages else None,
            "stages": safe_stages,
            "failure": safe_failure,
            "artifact_names": sorted(str(name)[:80] for name in artifacts.keys())[:40],
            "source": "run_manifest",
        }
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def collect_recent_runs(runs_root: Path | str | None = None, limit: int = MAX_RUNS) -> list[dict]:
    root = Path(runs_root) if runs_root is not None else ROOT / "outputs" / "runs"
    if not root.exists() or root.is_symlink() or not root.is_dir():
        return []
    bounded = max(1, min(int(limit), MAX_RUNS))
    candidates = []
    try:
        for run_dir in root.iterdir():
            if run_dir.is_symlink() or not run_dir.is_dir():
                continue
            manifest = run_dir / "manifest.json"
            try:
                stamp = manifest.stat().st_mtime
            except OSError:
                continue
            candidates.append((stamp, manifest))
    except OSError:
        return []
    result = []
    for _, manifest in sorted(candidates, reverse=True)[:bounded]:
        item = _read_manifest(manifest)
        if item:
            result.append(item)
    return result


def decide_next_action(runs: list[dict], operations: dict | None = None) -> dict:
    operations = operations or {}
    if runs and runs[0].get("status") == "failed":
        latest = runs[0]
        failure = latest.get("failure") or {}
        return {
            "action": "diagnose_failed_run",
            "reason": "latest_run_failed",
            "evidence": [{
                "run_id": latest["run_id"],
                "stage": failure.get("stage") or (latest.get("last_stage") or {}).get("name"),
                "error_type": failure.get("error_type"),
                "error_category": failure.get("error_category"),
            }],
            "authority": "recommendation_only",
        }

    if operations.get("available"):
        if operations.get("expired_running_leases", 0):
            return {
                "action": "inspect_expired_task_leases",
                "reason": "local_queue_contains_expired_running_leases",
                "evidence": [{"count": operations["expired_running_leases"]}],
                "authority": "recommendation_only",
            }
        if operations.get("stale_workers", 0):
            return {
                "action": "inspect_stale_worker_heartbeats",
                "reason": "local_workers_have_stale_heartbeats",
                "evidence": [{"count": operations["stale_workers"]}],
                "authority": "recommendation_only",
            }
        if operations.get("recent_failures"):
            first = operations["recent_failures"][0]
            return {
                "action": "review_failed_autonomy_tasks",
                "reason": "local_autonomy_queue_has_failed_tasks",
                "evidence": [{
                    "task_id": first.get("task_id"),
                    "task_type": first.get("task_type"),
                    "error_code": first.get("error_code"),
                }],
                "authority": "recommendation_only",
            }
        queued = int(operations.get("queue_counts", {}).get("queued", 0))
        running = int(operations.get("queue_counts", {}).get("running", 0))
        if queued and not operations.get("active_workers"):
            return {
                "action": "inspect_worker_availability",
                "reason": "queued_work_without_recent_active_worker_heartbeat",
                "evidence": [{"queued_tasks": queued, "active_workers": 0}],
                "authority": "recommendation_only",
            }
        if queued:
            return {
                "action": "monitor_queued_autonomy_work",
                "reason": "local_autonomy_queue_has_queued_tasks",
                "evidence": [{"queued_tasks": queued, "active_workers": operations.get("active_workers", 0)}],
                "authority": "recommendation_only",
            }
        if running:
            return {
                "action": "verify_autonomy_task_progress",
                "reason": "local_autonomy_tasks_are_running",
                "evidence": [{"running_tasks": running}],
                "authority": "recommendation_only",
            }

    if runs:
        latest = runs[0]
        run_id = latest["run_id"]
        status = latest.get("status")
        if status == "in_progress":
            return {
                "action": "verify_run_liveness",
                "reason": "latest_run_not_terminal",
                "evidence": [{"run_id": run_id, "last_stage": latest.get("last_stage")}],
                "authority": "recommendation_only",
            }
        if status == "ok":
            return {
                "action": "review_completed_video",
                "reason": "latest_run_completed_requires_quality_review",
                "evidence": [{"run_id": run_id, "artifact_names": latest.get("artifact_names", [])}],
                "authority": "recommendation_only",
            }
        return {
            "action": "inspect_run_state",
            "reason": "latest_run_state_unrecognized",
            "evidence": [{"run_id": run_id, "status": status}],
            "authority": "recommendation_only",
        }

    return {
        "action": "inspect_or_start_first_run",
        "reason": "no_run_manifest_found",
        "evidence": [],
        "authority": "recommendation_only",
    }


def build_brain_overview(
    *,
    runs_root: Path | str | None = None,
    context_path: Path | str | None = None,
    autonomy_db_path: Path | str | None = None,
    limit: int = MAX_RUNS,
) -> dict:
    context = load_project_context(context_path)
    runs = collect_recent_runs(runs_root, limit)
    operations = collect_local_autonomy_state(database_path=autonomy_db_path)
    counts = {}
    for run in runs:
        state = run.get("status", "unknown")
        counts[state] = counts.get(state, 0) + 1
    return {
        "schema": "nextdecode.brain.overview.v1",
        "brain_version": BRAIN_VERSION,
        "mode": "deterministic_read_only",
        "project": context["project"],
        "identity": context["identity"],
        "production": context["production"],
        "guardrails": context["guardrails"],
        "authority": context["authority"],
        "observed_state": {
            "runs_inspected": len(runs),
            "run_status_counts": counts,
            "latest_run": runs[0] if runs else None,
        },
        "operations": operations,
        "recent_runs": runs,
        "next_action": decide_next_action(runs, operations),
        "limitations": [
            "No AI/LLM reasoning is enabled in this version.",
            "The autonomy queue and worker heartbeats are local runtime telemetry, not canonical P0 control-plane entities.",
            "The PostgreSQL autonomy adapter is not observed until a non-mutating read-only adapter is qualified.",
            "WP1-WP5 detailed contracts remain candidates/open; no canonical P0 schema is inferred by Brain.",
            "Recommendations are not persisted and never execute actions.",
        ],
    }
