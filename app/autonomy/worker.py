"""Autonomous worker loop with bounded polling and graceful shutdown."""
from __future__ import annotations
import json
import logging
import os
import re
import socket
import sqlite3
import threading
import time
import uuid
from .models import TaskRequest, TaskResult, utc_now
from .registry import CapabilityRegistry, build_default_registry
from .store import TaskStore
from .worker_identity import new_worker_identity, runtime_worker_registry
from .execution_policy import LocalWorkerPolicy

logger = logging.getLogger(__name__)


def _safe_failure_message(exc: Exception, limit: int = 500) -> str:
    """Keep actionable exception context while removing common secret forms."""
    message = str(exc).replace("\\", "/")
    message = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", message)
    message = re.sub(
        r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|credential)\s*[=:]\s*)[^\s,;]+",
        r"\1[REDACTED]", message,
    )
    message = re.sub(r"(https?://[^\s?#]+)\?[^\s#]+", r"\1?[REDACTED]", message)
    return message[:limit]


class TaskWorker:
    def __init__(self, store: TaskStore, registry: CapabilityRegistry | None = None,
                 worker_id: str | None = None):
        self.store = store
        self.registry = registry or build_default_registry()
        self.worker_id = worker_id or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self.started_at = utc_now()
        self.identity = new_worker_identity(self.worker_id, self.hostname, self.pid, self.started_at)
        self.execution_policy = LocalWorkerPolicy()
        runtime_worker_registry.register(self.identity)
        self._heartbeat_state = "starting"
        self._heartbeat_lock = threading.Lock()

    def _set_heartbeat_state(self, state: str) -> None:
        with self._heartbeat_lock:
            self._heartbeat_state = state
        runtime_worker_registry.set_state(self.identity.instance_id, state)

    def _heartbeat_loop(self, stop: threading.Event, interval: float = 10.0) -> None:
        while not stop.is_set():
            with self._heartbeat_lock:
                state = self._heartbeat_state
            try:
                self.store.record_worker_heartbeat(
                    self.worker_id, self.hostname, self.pid, state, self.started_at
                )
            except Exception as exc:
                logger.warning("Autonomy worker heartbeat write failed (%s)", type(exc).__name__)
            if stop.wait(interval):
                break

    def _lease_renewal_loop(self, task_id: str, attempt: int,
                            stop: threading.Event, lost: threading.Event,
                            lease_seconds: int = 180, interval: float = 45.0) -> None:
        """Keep a running attempt alive; fail closed if its fencing lease is lost."""
        renew = getattr(self.store, "renew_lease", None)
        if not callable(renew):
            lost.set()
            logger.error("Task store does not support fenced lease renewal")
            return
        while not stop.wait(interval):
            try:
                if not renew(task_id, self.worker_id, attempt, lease_seconds):
                    lost.set()
                    logger.error("Task lease renewal rejected; attempt is fenced")
                    return
            except Exception as exc:
                lost.set()
                logger.error("Task lease renewal failed closed (%s)", type(exc).__name__)
                return

    def run_once(self) -> bool:
        lease_seconds = 180
        task = self.store.claim(self.worker_id, lease_seconds=lease_seconds)
        if task is None:
            self._set_heartbeat_state("idle")
            return False
        self._set_heartbeat_state("working")
        attempt = int(task["attempts"])
        lease_stop = threading.Event()
        lease_lost = threading.Event()
        lease_thread = threading.Thread(
            target=self._lease_renewal_loop,
            args=(task["task_id"], attempt, lease_stop, lease_lost, lease_seconds),
            name=f"autonomy-lease-{task['task_id'][:8]}", daemon=True,
        )
        lease_thread.start()
        execution_id = uuid.uuid4().hex
        execution_started = utc_now()
        capability = None
        policy_decision = None
        try:
            raw_payload = json.loads(task["payload_json"])
            selection = self.registry.select(task["task_type"], raw_payload, self.execution_policy)
            capability = selection.capability
            policy_decision = selection.policy_decision
            dependency_results = self.store.dependency_results(task["task_id"])
            request = TaskRequest(task_type=task["task_type"],
                payload=selection.normalized_payload, task_id=task["task_id"],
                max_attempts=task["max_attempts"], priority=task["priority"],
                idempotency_key=task["idempotency_key"], not_before=task["not_before"],
                context={"dependencies": dependency_results})
            if capability is None or not policy_decision.allowed:
                result = TaskResult("blocked", error_code=policy_decision.reason)
            else:
                result = capability.handler(request)
        except KeyError:
            result = TaskResult("blocked", error_code="capability_unavailable")
        except Exception as exc:
            result = TaskResult(
                "failed", error_code=type(exc).__name__.lower(), retryable=False,
                evidence={"failure": {
                    "exception_type": type(exc).__name__,
                    "message": _safe_failure_message(exc),
                }},
            )

        lease_stop.set()
        lease_thread.join()
        if lease_lost.is_set():
            self._set_heartbeat_state("idle")
            raise RuntimeError("task lease lost; result discarded to prevent stale completion")

        from .evaluator import evaluate_result
        accepted, evaluation_error, evaluation = evaluate_result(result)
        if not accepted:
            result = TaskResult(
                "failed", output=result.output,
                error_code=evaluation_error or "result_evaluation_failed",
                evidence={**result.evidence, "evaluation": evaluation},
            )
        handler_run_id = result.evidence.get("run_id")
        evidence = {
            **result.evidence,
            "handler_run_id": handler_run_id,
            "artifact_run_id": result.output.get("run_id"),
            "run_id": execution_id,
            "plan_id": task.get("plan_id"),
            "started_at": execution_started,
            "finished_at": utc_now(),
            "worker_id": self.worker_id,
            "worker_instance_id": self.identity.instance_id,
            "task_type": task["task_type"],
            "capability_version": getattr(capability, "version", "unknown"),
            "capability_route": getattr(selection, "route", "none") if "selection" in locals() else "none",
            "capability_selection_reason": getattr(selection, "reason", "selection_unavailable") if "selection" in locals() else "selection_unavailable",
            "permission_scopes": list(getattr(capability, "permission_scopes", ())),
            "execution_policy_version": getattr(policy_decision, "policy_version", None),
            "execution_policy_decision": getattr(policy_decision, "reason", "capability_unavailable"),
            "execution_policy_allowed": bool(getattr(policy_decision, "allowed", False)),
            "evaluation": evaluation,
        }
        result = TaskResult(
            result.status, output=result.output, error_code=result.error_code,
            retryable=result.retryable, evidence=evidence,
        )
        self.store.finish(task["task_id"], self.worker_id, result, attempt=attempt)
        self._set_heartbeat_state("idle")
        return True

    def serve(self, poll_seconds: float = 2.0, stop_event=None) -> None:
        storage_failures = 0
        shutdown = stop_event or threading.Event()
        heartbeat_stop = threading.Event()
        heartbeat = threading.Thread(
            target=self._heartbeat_loop, args=(heartbeat_stop,),
            name=f"autonomy-heartbeat-{self.worker_id}", daemon=True,
        )
        heartbeat.start()
        self._set_heartbeat_state("idle")
        try:
            while not shutdown.is_set():
                try:
                    worked = self.run_once()
                    storage_failures = 0
                except Exception as exc:
                    # Retry only connection/open failures identified by the selected
                    # storage adapter. SQL, schema, validation and policy errors fail fast.
                    transient_check = getattr(self.store, "is_transient_error", None)
                    if not callable(transient_check) or not transient_check(exc):
                        raise
                    storage_failures += 1
                    if storage_failures > 6:
                        logger.exception("Autonomy worker storage remained unavailable; exiting for supervisor recovery")
                        raise
                    delay = min(30.0, float(2 ** (storage_failures - 1)))
                    logger.warning(
                        "Autonomy %s database temporarily unavailable; retry %s/6 in %.0fs (%s)",
                        getattr(self.store, "backend", "unknown"),
                        storage_failures, delay, type(exc).__name__,
                    )
                    time.sleep(delay)
                    continue
                if not worked:
                    time.sleep(max(0.1, poll_seconds))
        finally:
            self._set_heartbeat_state("stopping")
            heartbeat_stop.set()
            heartbeat.join(timeout=2.0)
            try:
                self.store.record_worker_heartbeat(
                    self.worker_id, self.hostname, self.pid, "stopped", self.started_at
                )
            except Exception as exc:
                logger.warning("Could not persist stopped worker state (%s)", type(exc).__name__)
