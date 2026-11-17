"""Fail-closed bounded agent process runner.

AEC-02D introduces execution records, command planning, and output accounting.
It deliberately does not spawn a registered agent: execution remains disabled
until runtime, storage quotas, approval replay protection, and sandbox controls
are independently qualified.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import re

from .agent_sandbox import BubblewrapSandbox, SandboxLimits


class RunState(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    BLOCKED = "blocked"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass(frozen=True)
class OutputFile:
    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class OutputManifest:
    files: tuple[OutputFile, ...]
    total_bytes: int
    file_count: int
    complete: bool
    issue_codes: tuple[str, ...]


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    state: RunState
    created_at: str
    started_at: str | None
    finished_at: str | None
    plan_sha256: str
    approval_id: str
    workspace_id: str
    staging_id: str
    executable: str
    executable_sha256: str
    policy_sha256: str
    exit_code: int | None
    timed_out: bool
    termination_reason: str | None
    stdout: str
    stderr: str
    issue_codes: tuple[str, ...]


@dataclass(frozen=True)
class RunnerPolicy:
    enabled: bool = False
    max_stdout_bytes: int = 256 * 1024
    max_stderr_bytes: int = 256 * 1024
    max_output_bytes: int = 64 * 1024 * 1024
    max_output_files: int = 2_000

    def __post_init__(self) -> None:
        if self.enabled:
            raise ValueError("agent execution cannot be enabled before qualification")
        if not 1 <= self.max_stdout_bytes <= 4 * 1024 * 1024:
            raise ValueError("stdout cap must be 1 byte..4 MiB")
        if not 1 <= self.max_stderr_bytes <= 4 * 1024 * 1024:
            raise ValueError("stderr cap must be 1 byte..4 MiB")
        if not 1 <= self.max_output_bytes <= 1024**3:
            raise ValueError("output cap must be 1 byte..1 GiB")
        if not 1 <= self.max_output_files <= 100_000:
            raise ValueError("output file cap must be 1..100000")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_output_tree(root: str | Path, *, max_bytes: int,
                        max_files: int) -> OutputManifest:
    """Hash a result tree without following symlinks; reject unsafe entries."""
    base = Path(root)
    if not base.is_absolute() or base.is_symlink() or not base.is_dir():
        return OutputManifest((), 0, 0, False, ("invalid_output_root",))
    files: list[OutputFile] = []
    issues: list[str] = []
    total = 0
    try:
        for current, dirs, names in os.walk(base, followlinks=False):
            current_path = Path(current)
            for dirname in list(dirs):
                item = current_path / dirname
                if item.is_symlink():
                    issues.append("output_symlink_rejected")
                    dirs.remove(dirname)
            for name in names:
                item = current_path / name
                if item.is_symlink() or not item.is_file():
                    issues.append("output_non_regular_file_rejected")
                    continue
                size = item.stat(follow_symlinks=False).st_size
                relative = item.relative_to(base).as_posix()
                if size > max_bytes - total:
                    issues.append("output_byte_quota_exceeded")
                    return OutputManifest(tuple(files), total, len(files), False, tuple(issues))
                if len(files) >= max_files:
                    issues.append("output_file_quota_exceeded")
                    return OutputManifest(tuple(files), total, len(files), False, tuple(issues))
                files.append(OutputFile(relative, size, _sha256_file(item)))
                total += size
    except OSError:
        issues.append("output_scan_failed")
    return OutputManifest(tuple(files), total, len(files), not issues, tuple(issues))


class BoundedAgentRunner:
    """Prepare auditable run records while refusing all process execution."""

    def __init__(self, sandbox: BubblewrapSandbox | None = None,
                 policy: RunnerPolicy | None = None):
        self.policy = policy or RunnerPolicy()
        self.sandbox = sandbox or BubblewrapSandbox(
            SandboxLimits(output_bytes=self.policy.max_output_bytes)
        )

    def prepare(self, *, run_id: str, plan: dict, approval_id: str,
                workspace_id: str, staging_id: str, executable: str,
                arguments: tuple[str, ...], workspace: str | Path,
                staged_input: str | Path, output: str | Path,
                policy_document: dict | None = None) -> tuple[list[str] | None, RunRecord]:
        """Build an auditable plan; never starts a process."""
        if not re.fullmatch(r"[a-f0-9]{32}", run_id):
            raise ValueError("run_id must be 32 lowercase hexadecimal characters")
        plan_bytes = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
        policy_bytes = json.dumps(policy_document or asdict(self.policy),
                                  sort_keys=True, separators=(",", ":")).encode()
        plan_digest = hashlib.sha256(plan_bytes).hexdigest()
        policy_digest = hashlib.sha256(policy_bytes).hexdigest()
        executable_path = Path(executable)
        executable_digest = (_sha256_file(executable_path)
                             if executable_path.is_file() and not executable_path.is_symlink()
                             else "")
        try:
            command = self.sandbox.build_command(
                executable=executable, arguments=arguments, workspace=workspace,
                staged_input=staged_input, output=output,
            )
            state = RunState.BLOCKED
            issues = ("agent_execution_disabled", "runtime_qualification_pending")
        except (OSError, RuntimeError, ValueError) as exc:
            command = None
            state = RunState.BLOCKED
            issues = (f"sandbox_command_rejected:{type(exc).__name__}",
                      "agent_execution_disabled")
        record = RunRecord(
            run_id=run_id, state=state, created_at=_utc_now(), started_at=None,
            finished_at=None, plan_sha256=plan_digest, approval_id=approval_id,
            workspace_id=workspace_id, staging_id=staging_id,
            executable=str(executable_path), executable_sha256=executable_digest,
            policy_sha256=policy_digest, exit_code=None, timed_out=False,
            termination_reason=None, stdout="", stderr="", issue_codes=issues,
        )
        return command, record

    @staticmethod
    def classify_exit(*, exit_code: int | None, timed_out: bool = False,
                      cancelled: bool = False) -> RunState:
        if timed_out:
            return RunState.TIMED_OUT
        if cancelled:
            return RunState.CANCELLED
        if exit_code is None or exit_code != 0:
            return RunState.FAILED
        return RunState.COMPLETED

    @staticmethod
    def bounded_text(value: str, *, max_bytes: int) -> str:
        raw = value.encode("utf-8", errors="replace")
        if len(raw) <= max_bytes:
            return value
        suffix = b"\n[truncated by runner]"
        if max_bytes <= len(suffix):
            return raw[:max_bytes].decode("utf-8", errors="ignore")
        clipped = raw[:max_bytes - len(suffix)]
        return clipped.decode("utf-8", errors="ignore") + suffix.decode()


@dataclass(frozen=True)
class ExportedOutput:
    export_id: str
    destination: str
    manifest: OutputManifest


def export_sandbox_output(source: str | Path, *, export_id: str,
                          max_bytes: int, max_files: int,
                          results_root: str | Path) -> ExportedOutput:
    """Copy verified sandbox output into a private host result directory.

    Export is create-only: it never overwrites an existing result. Symlinks,
    traversal paths, non-regular files and quota violations fail closed.
    """
    import shutil
    import tempfile

    if not re.fullmatch(r"[a-f0-9]{32}", export_id):
        raise ValueError("export_id must be 32 lowercase hexadecimal characters")
    source_root = Path(source)
    if (not source_root.is_absolute() or source_root.is_symlink()
            or not source_root.is_dir()):
        raise ValueError("sandbox output root must be an existing real directory")
    source_root = source_root.resolve(strict=True)
    target_root = Path(results_root)
    if not target_root.is_absolute():
        raise ValueError("results root must be absolute")
    target_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if target_root.is_symlink() or not target_root.is_dir():
        raise ValueError("results root must be a real directory")
    target_root = target_root.resolve(strict=True)
    target_root.chmod(0o700)
    destination = target_root / export_id
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("result export already exists")
    staging = Path(tempfile.mkdtemp(prefix=f".{export_id}.", dir=target_root))
    staging.chmod(0o700)
    exported: list[OutputFile] = []
    total = 0
    try:
        for current, dirs, names in os.walk(source_root, followlinks=False):
            current_path = Path(current)
            relative_dir = current_path.relative_to(source_root)
            for dirname in list(dirs):
                entry = current_path / dirname
                if entry.is_symlink():
                    raise ValueError("sandbox output contains a symlink directory")
                (staging / relative_dir / dirname).mkdir(mode=0o700, exist_ok=True)
            for name in names:
                entry = current_path / name
                if entry.is_symlink() or not entry.is_file():
                    raise ValueError("sandbox output contains a non-regular file")
                relative = entry.relative_to(source_root)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("sandbox output path traversal rejected")
                size = entry.stat(follow_symlinks=False).st_size
                if size > max_bytes - total:
                    raise ValueError("sandbox output aggregate byte quota exceeded")
                if len(exported) >= max_files:
                    raise ValueError("sandbox output file-count quota exceeded")
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                digest = hashlib.sha256()
                copied = 0
                source_fd = os.open(entry, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                try:
                    target_fd = os.open(
                        target, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                        | getattr(os, "O_NOFOLLOW", 0), 0o600,
                    )
                    try:
                        with os.fdopen(source_fd, "rb", closefd=False) as reader, os.fdopen(
                            target_fd, "wb", closefd=False
                        ) as writer:
                            while True:
                                chunk = reader.read(1024 * 1024)
                                if not chunk:
                                    break
                                copied += len(chunk)
                                if copied > size or copied > max_bytes - total:
                                    raise ValueError("sandbox output changed or exceeded quota during export")
                                writer.write(chunk)
                                digest.update(chunk)
                            writer.flush()
                            os.fsync(writer.fileno())
                    finally:
                        os.close(target_fd)
                finally:
                    os.close(source_fd)
                if copied != size:
                    raise ValueError("sandbox output changed during export")
                exported.append(OutputFile(relative.as_posix(), copied, digest.hexdigest()))
                total += copied
        for current, dirs, _ in os.walk(staging, topdown=False):
            for dirname in dirs:
                (Path(current) / dirname).chmod(0o700)
        staging.rename(destination)
        manifest = OutputManifest(tuple(exported), total, len(exported), True, ())
        return ExportedOutput(export_id, str(destination), manifest)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


@dataclass(frozen=True)
class LifecycleSnapshot:
    state: RunState
    pid: int | None
    process_group_id: int | None
    started_at: str | None
    finished_at: str | None
    exit_code: int | None
    termination_reason: str | None
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool


class BoundedOutputCapture:
    """In-memory byte-capped stdout/stderr capture; never blocks on a pipe."""

    def __init__(self, *, stdout_limit: int, stderr_limit: int):
        if stdout_limit < 1 or stderr_limit < 1:
            raise ValueError("output capture limits must be positive")
        self._limits = {"stdout": stdout_limit, "stderr": stderr_limit}
        self._buffers = {"stdout": bytearray(), "stderr": bytearray()}
        self._truncated = {"stdout": False, "stderr": False}

    def feed(self, stream: str, chunk: bytes) -> int:
        if stream not in self._buffers:
            raise ValueError("stream must be stdout or stderr")
        if not isinstance(chunk, bytes):
            raise TypeError("output chunks must be bytes")
        buffer = self._buffers[stream]
        remaining = self._limits[stream] - len(buffer)
        accepted = min(max(remaining, 0), len(chunk))
        if accepted:
            buffer.extend(chunk[:accepted])
        if accepted < len(chunk):
            self._truncated[stream] = True
        return accepted

    def text(self, stream: str) -> str:
        if stream not in self._buffers:
            raise ValueError("stream must be stdout or stderr")
        return bytes(self._buffers[stream]).decode("utf-8", errors="replace")

    def was_truncated(self, stream: str) -> bool:
        if stream not in self._truncated:
            raise ValueError("stream must be stdout or stderr")
        return self._truncated[stream]


class ProcessLifecycleController:
    """Pure lifecycle state machine; it never creates or signals OS processes.

    The caller supplies a termination callback, making cancellation behavior
    testable without launching agents or sending real operating-system signals.
    """

    def __init__(self, *, output_capture: BoundedOutputCapture | None = None):
        self.state = RunState.PLANNED
        self.pid: int | None = None
        self.process_group_id: int | None = None
        self.started_at: str | None = None
        self.finished_at: str | None = None
        self.exit_code: int | None = None
        self.termination_reason: str | None = None
        self.output = output_capture or BoundedOutputCapture(
            stdout_limit=256 * 1024, stderr_limit=256 * 1024
        )

    def mark_started(self, *, pid: int, process_group_id: int,
                     started_at: str | None = None) -> None:
        if self.state is not RunState.PLANNED:
            raise RuntimeError("process can only start from planned state")
        if pid <= 0 or process_group_id <= 0:
            raise ValueError("pid and process group id must be positive")
        # This records a start reported by a future qualified adapter; it
        # does not create a process or make the runner executable.
        self.pid = pid
        self.process_group_id = process_group_id
        self.started_at = started_at or _utc_now()
        self.state = RunState.RUNNING

    def request_termination(self, reason: str, *,
                            terminate_group: object) -> None:
        if self.pid is None or self.process_group_id is None:
            raise RuntimeError("cannot terminate a process that was not recorded as started")
        if self.finished_at is not None:
            raise RuntimeError("process has already finished")
        if reason not in {"cancelled", "timed_out"}:
            raise ValueError("termination reason must be cancelled or timed_out")
        if self.termination_reason is not None:
            return
        if not callable(terminate_group):
            raise TypeError("terminate_group must be callable")
        terminate_group(self.process_group_id)
        self.termination_reason = reason

    def observe_exit(self, exit_code: int, *, finished_at: str | None = None) -> RunState:
        if self.pid is None:
            raise RuntimeError("cannot record exit before process start")
        if self.finished_at is not None:
            raise RuntimeError("process exit already recorded")
        self.exit_code = exit_code
        self.finished_at = finished_at or _utc_now()
        self.state = BoundedAgentRunner.classify_exit(
            exit_code=exit_code,
            timed_out=self.termination_reason == "timed_out",
            cancelled=self.termination_reason == "cancelled",
        )
        return self.state

    def snapshot(self) -> LifecycleSnapshot:
        return LifecycleSnapshot(
            state=self.state, pid=self.pid, process_group_id=self.process_group_id,
            started_at=self.started_at, finished_at=self.finished_at,
            exit_code=self.exit_code, termination_reason=self.termination_reason,
            stdout=self.output.text("stdout"), stderr=self.output.text("stderr"),
            stdout_truncated=self.output.was_truncated("stdout"),
            stderr_truncated=self.output.was_truncated("stderr"),
        )
