"""Bubblewrap sandbox qualification and fail-closed command construction.

Only the inert qualification probe is runnable here. This module does not
launch registered coding agents or enable the execution adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .agent_workspace import WORKSPACE_ROOT


@dataclass(frozen=True)
class SandboxLimits:
    cpu_seconds: int = 60
    address_space_bytes: int = 1024 * 1024 * 1024
    file_size_bytes: int = 64 * 1024 * 1024
    output_bytes: int = 64 * 1024 * 1024
    open_files: int = 64
    processes: int = 256
    wall_seconds: int = 120

    def __post_init__(self) -> None:
        if not 1 <= self.cpu_seconds <= 3600:
            raise ValueError("CPU limit must be 1..3600 seconds")
        if not 64 * 1024 * 1024 <= self.address_space_bytes <= 8 * 1024**3:
            raise ValueError("address-space limit must be 64 MiB..8 GiB")
        if not 1024 <= self.file_size_bytes <= 1024**3:
            raise ValueError("file-size limit must be 1 KiB..1 GiB")
        if not 1024 <= self.output_bytes <= 1024**3:
            raise ValueError("aggregate output tmpfs limit must be 1 KiB..1 GiB")
        if not 16 <= self.open_files <= 1024:
            raise ValueError("open-file limit must be 16..1024")
        if not 1 <= self.processes <= 256:
            raise ValueError("process limit must be 1..256")
        if not 1 <= self.wall_seconds <= 3600:
            raise ValueError("wall limit must be 1..3600 seconds")


@dataclass(frozen=True)
class SandboxProbeResult:
    available: bool
    qualified: bool
    backend: str
    checks: dict[str, bool]
    issue_codes: tuple[str, ...]


class BubblewrapSandbox:
    """Build a no-network, read-only-input sandbox using local bubblewrap."""

    def __init__(self, limits: SandboxLimits | None = None):
        self.limits = limits or SandboxLimits()
        self.bwrap = shutil.which("bwrap")
        self.prlimit = shutil.which("prlimit")

    def inspect(self) -> dict:
        return {
            "backend": "bubblewrap",
            "bwrap_path": self.bwrap,
            "prlimit_path": self.prlimit,
            "available": bool(self.bwrap and self.prlimit),
            "user_namespace": True,
            "pid_namespace": True,
            "network_namespace": True,
            "workspace_read_only": True,
            "staged_input_read_only": True,
            "output_isolated": True,
            "process_execution_enabled": False,
        }

    def _runtime_binds(self) -> list[str]:
        required = (Path("/usr"), Path("/usr/lib"), Path("/usr/lib64"))
        if any(not path.exists() for path in required):
            raise RuntimeError("required read-only runtime mount is missing")
        return [
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/usr/lib", "/lib",
            "--ro-bind", "/usr/lib64", "/lib64",
        ]

    def output_tmpfs_args(self, *, destination: str = "/output") -> list[str]:
        """Return a size-capped tmpfs mount for future sandbox output.

        This primitive is qualified separately; the current execution command
        still uses a private host result directory and remains disabled.
        """
        target = Path(destination)
        if not target.is_absolute() or target == Path("/") or ".." in target.parts:
            raise ValueError("tmpfs destination must be a safe absolute path")
        return ["--size", str(self.limits.output_bytes), "--tmpfs", str(target)]

    @staticmethod
    def _safe_directory(path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            raise ValueError("sandbox paths must be absolute")
        cursor = candidate
        while cursor != cursor.parent:
            if cursor.is_symlink():
                raise ValueError("sandbox path components must not be symlinks")
            cursor = cursor.parent
        resolved = candidate.resolve(strict=True)
        if not resolved.is_dir():
            raise ValueError("sandbox path must be an existing directory")
        return resolved

    def build_command(self, *, executable: str, arguments: tuple[str, ...],
                      workspace: str | Path, staged_input: str | Path,
                      output: str | Path) -> list[str]:
        """Build a bounded command; callers must not execute it in this phase."""
        if not self.bwrap or not self.prlimit:
            raise RuntimeError("bubblewrap and prlimit are required")
        workspace_path = self._safe_directory(workspace)
        staged_path = self._safe_directory(staged_input)
        output_path = Path(output)
        if not output_path.is_absolute():
            raise ValueError("output path must be absolute")
        workspace_root = self._safe_directory(WORKSPACE_ROOT)
        try:
            workspace_parts = workspace_path.relative_to(workspace_root).parts
            staged_parts = staged_path.relative_to(workspace_root).parts
        except ValueError:
            raise ValueError("workspace and staged input must remain under the private agent workspace root") from None
        if (len(workspace_parts) != 2 or workspace_path.name != "workspace"
                or not re.fullmatch(r"[a-f0-9]{32}", workspace_path.parent.name)):
            raise ValueError("workspace must be a prepared workspace snapshot")
        if (len(staged_parts) != 3 or staged_path.name != "files"
                or staged_path.parent.parent.name != "staging"
                or not re.fullmatch(r"[a-f0-9]{32}", staged_path.parent.name)):
            raise ValueError("staged input must be a prepared staging package")
        results_root = workspace_root / "results"
        results_root.mkdir(mode=0o700, exist_ok=True)
        results_root = self._safe_directory(results_root)
        if output_path.parent != results_root or not re.fullmatch(r"[a-f0-9]{32}", output_path.name):
            raise ValueError("output must be a unique private result directory")
        if output_path.exists() and (output_path.is_symlink() or not output_path.is_dir()):
            raise ValueError("output path must be a directory, not a symlink")
        output_path.mkdir(mode=0o700, exist_ok=True)
        output_path = self._safe_directory(output_path)
        if workspace_path == staged_path or workspace_path in staged_path.parents or staged_path in workspace_path.parents:
            raise ValueError("workspace and staged input must be separate trees")
        executable_path = Path(executable)
        if not executable_path.is_absolute() or not executable_path.is_file() or executable_path.is_symlink():
            raise ValueError("executable must be an existing absolute regular file")
        executable_path = executable_path.resolve(strict=True)
        if not any(root == executable_path or root in executable_path.parents
                   for root in (Path("/usr"), Path("/lib"), Path("/lib64"))):
            raise ValueError("agent executable is outside the allowlisted read-only runtime")
        if any(not isinstance(arg, str) or "\x00" in arg for arg in arguments):
            raise ValueError("invalid process argument")

        limits = self.limits
        command = [
            self.prlimit,
            f"--cpu={limits.cpu_seconds}:{limits.cpu_seconds}",
            f"--as={limits.address_space_bytes}:{limits.address_space_bytes}",
            f"--fsize={limits.file_size_bytes}:{limits.file_size_bytes}",
            f"--nofile={limits.open_files}:{limits.open_files}",
            f"--nproc={limits.processes}:{limits.processes}",
            "--",
            self.bwrap,
            "--unshare-user", "--unshare-pid", "--unshare-net",
            "--die-with-parent", "--new-session",
            *self._runtime_binds(),
            "--proc", "/proc", "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--dir", "/workspace",
            "--ro-bind", str(workspace_path), "/workspace",
            "--dir", "/input",
            "--ro-bind", str(staged_path), "/input",
            "--bind", str(output_path), "/output",
            "--chdir", "/workspace",
            "--clearenv",
            "--setenv", "HOME", "/tmp",
            "--setenv", "PATH", "/usr/bin:/usr/local/bin",
            "--setenv", "LANG", "C.UTF-8",
            "--",
            str(executable_path),
            *arguments,
        ]
        return command

    def probe(self) -> SandboxProbeResult:
        """Run only a tiny inert Python probe; never launches a registered agent."""
        checks = {
            "user_pid_network_namespaces": False,
            "workspace_read_only": False,
            "host_home_hidden": False,
            "isolated_output_writable": False,
            "outbound_network_blocked": False,
        }
        issues: list[str] = []
        if not self.bwrap or not self.prlimit:
            return SandboxProbeResult(False, False, "bubblewrap", checks,
                                      ("sandbox_tools_missing",))
        script = (
            "import pathlib,socket; "
            "assert pathlib.Path('/work/marker').read_text().strip() == 'probe'; "
            "print('workspace_read=pass'); "
            "print('host_home_hidden=' + str(not pathlib.Path('/home').exists())); "
            "exec(\"try:\\n pathlib.Path('/work/write-test').write_text('x')\\n raise AssertionError('workspace_write_allowed')\\nexcept OSError: print('workspace_read_only=pass')\"); "
            "pathlib.Path('/output/result').write_text('ok'); print('output_write=pass'); "
            "s=socket.socket(); s.settimeout(1); "
            "exec(\"try:\\n s.connect(('1.1.1.1',53))\\n print('network=reachable')\\nexcept OSError: print('network=blocked')\")"
        )
        try:
            with tempfile.TemporaryDirectory(prefix="nd-bwrap-probe-") as temp:
                root = Path(temp)
                workspace = root / "workspace"
                output = root / "output"
                workspace.mkdir()
                output.mkdir()
                (workspace / "marker").write_text("probe")
                script_path = root / "probe.py"
                script_path.write_text(script)
                command = [
                    self.prlimit,
                    f"--cpu={self.limits.cpu_seconds}:{self.limits.cpu_seconds}",
                    f"--as={self.limits.address_space_bytes}:{self.limits.address_space_bytes}",
                    f"--fsize={self.limits.file_size_bytes}:{self.limits.file_size_bytes}",
                    f"--nofile={self.limits.open_files}:{self.limits.open_files}",
                    f"--nproc={self.limits.processes}:{self.limits.processes}",
                    "--", self.bwrap,
                    "--unshare-user", "--unshare-pid", "--unshare-net",
                    "--die-with-parent", "--new-session",
                    *self._runtime_binds(),
                    "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                    "--dir", "/work", "--ro-bind", str(workspace), "/work",
                    "--bind", str(output), "/output",
                    "--ro-bind", str(script_path), "/probe.py",
                    "--chdir", "/work", "--", "/usr/bin/python3", "/probe.py",
                ]
                completed = subprocess.run(
                    command, capture_output=True, text=True,
                    timeout=min(self.limits.wall_seconds, 15), check=False,
                    env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                )
                output_text = completed.stdout
                checks["user_pid_network_namespaces"] = completed.returncode == 0
                checks["workspace_read_only"] = "workspace_read_only=pass" in output_text
                checks["host_home_hidden"] = "host_home_hidden=True" in output_text
                checks["isolated_output_writable"] = "output_write=pass" in output_text and (output / "result").is_file()
                checks["outbound_network_blocked"] = "network=blocked" in output_text
                if completed.returncode != 0:
                    issues.append("sandbox_probe_nonzero_exit")
                for name, passed in checks.items():
                    if not passed:
                        issues.append(f"sandbox_check_failed:{name}")
        except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
            issues.append(f"sandbox_probe_error:{type(exc).__name__}")
        return SandboxProbeResult(
            available=True, qualified=all(checks.values()), backend="bubblewrap",
            checks=checks, issue_codes=tuple(issues),
        )
