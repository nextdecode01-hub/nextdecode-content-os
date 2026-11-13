"""Conservative stale-worker reconciliation for the local autonomy runtime.

Only a stale process on this same host that is conclusively absent is marked
stopped. Remote-host and permission-ambiguous observations remain untouched.
"""
from __future__ import annotations

import errno
import os
import socket
from typing import Any


def _pid_status(pid: int) -> str:
    if int(pid) <= 0:
        return "unknown"
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return "dead"
    except PermissionError:
        return "unknown"
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return "dead"
        if exc.errno == errno.EPERM:
            return "unknown"
        return "unknown"
    return "alive"


def reconcile_workers(store: Any, *, stale_after_seconds: int = 45,
                      apply: bool = False) -> dict:
    """Classify stale heartbeats; optionally mark confirmed local dead PIDs stopped.

    The store update is conditional on the observed heartbeat, PID and hostname,
    so a worker that has heartbeated again since inspection is not overwritten.
    """
    health = store.health(stale_after_seconds=stale_after_seconds)
    local_hostname = socket.gethostname()
    decisions = []
    updated = []

    for worker in health["workers"]:
        if worker["state"] in {"stopping", "stopped"}:
            continue
        if not worker["stale"]:
            continue

        if worker["hostname"] != local_hostname:
            classification = "remote_stale_unverified"
            reason = "worker host differs; local PID inspection is not valid"
        else:
            pid_state = _pid_status(worker["pid"])
            if pid_state == "dead":
                classification = "confirmed_dead"
                reason = "same-host PID does not exist"
                if apply:
                    changed = store.mark_worker_stopped(
                        worker_id=worker["worker_id"],
                        hostname=worker["hostname"],
                        pid=worker["pid"],
                        expected_heartbeat_at=worker["heartbeat_at"],
                    )
                    if changed:
                        updated.append(worker["worker_id"])
                        classification = "marked_stopped"
                    else:
                        classification = "changed_during_reconcile"
                        reason = "heartbeat or worker identity changed; no update applied"
            elif pid_state == "alive":
                classification = "stale_but_pid_alive"
                reason = "heartbeat is old but process still exists"
            else:
                classification = "stale_pid_unknown"
                reason = "permission or OS error prevents a safe liveness conclusion"

        decisions.append({
            "worker_id": worker["worker_id"],
            "hostname": worker["hostname"],
            "pid": worker["pid"],
            "heartbeat_at": worker["heartbeat_at"],
            "classification": classification,
            "reason": reason,
        })

    return {
        "mode": "apply" if apply else "dry_run",
        "stale_after_seconds": health["heartbeat_stale_after_seconds"],
        "local_hostname": local_hostname,
        "inspected_stale_workers": len(decisions),
        "marked_stopped": updated,
        "decisions": decisions,
        "history_preserved": True,
    }
