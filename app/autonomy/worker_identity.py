"""Process-local worker identity lifecycle for the autonomy runtime.

This registry identifies running local worker instances only. It is deliberately
not a durable WP3 enrollment, trust, credential, or eligibility authority.
A heartbeat is liveness evidence, never proof of trust.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import threading
import uuid


WORKER_STATES = frozenset({"starting", "idle", "working", "stopping", "stopped"})


@dataclass(frozen=True)
class WorkerIdentity:
    worker_id: str
    instance_id: str
    hostname: str
    pid: int
    started_at: str


class RuntimeWorkerRegistry:
    """Thread-safe, process-local index of worker instances and lifecycle state."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._instances: dict[str, dict] = {}

    def register(self, identity: WorkerIdentity) -> None:
        if not identity.worker_id or len(identity.worker_id) > 200:
            raise ValueError("worker_id must be 1..200 characters")
        if not identity.instance_id or len(identity.instance_id) != 32:
            raise ValueError("instance_id must be a 32-character UUID hex")
        with self._lock:
            if identity.instance_id in self._instances:
                existing = self._instances[identity.instance_id]["identity"]
                if existing != identity:
                    raise ValueError("worker_instance_identity_conflict")
                return
            self._instances[identity.instance_id] = {
                "identity": identity,
                "state": "starting",
            }

    def set_state(self, instance_id: str, state: str) -> None:
        if state not in WORKER_STATES:
            raise ValueError("invalid worker lifecycle state")
        with self._lock:
            entry = self._instances.get(instance_id)
            if entry is None:
                raise KeyError("worker_instance_not_registered")
            entry["state"] = state

    def get(self, instance_id: str) -> dict | None:
        with self._lock:
            entry = self._instances.get(instance_id)
            if entry is None:
                return None
            return {**asdict(entry["identity"]), "state": entry["state"]}

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [
                {**asdict(entry["identity"]), "state": entry["state"]}
                for entry in self._instances.values()
            ]


# One index per Python process. It is not shared across processes or machines.
runtime_worker_registry = RuntimeWorkerRegistry()


def new_worker_identity(worker_id: str, hostname: str, pid: int, started_at: str) -> WorkerIdentity:
    return WorkerIdentity(
        worker_id=worker_id,
        instance_id=uuid.uuid4().hex,
        hostname=hostname,
        pid=int(pid),
        started_at=started_at,
    )
