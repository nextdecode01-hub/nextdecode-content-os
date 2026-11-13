"""Fail-closed bwrap sandbox for fixed, allow-listed project modules."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from .egress_proxy import EgressProxy, SANDBOX_SITECUSTOMIZE


ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_MODULES = {"pipelines.short", "pipelines.longform", "app.research.desk", "app.autonomy.specialist_cli"}
_SECRET_FILES = (".env", "youtube_token.json", "client_secret.json", "credentials.json")


class SandboxUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxOutcome:
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float
    profile: str


def _validate_module_args(module: str, args: list[str]) -> None:
    if module not in _ALLOWED_MODULES:
        raise ValueError("module is not allow-listed")
    if not isinstance(args, list) or any(not isinstance(item, str) for item in args):
        raise ValueError("sandbox arguments must be a list of strings")
    if len(args) > 12 or sum(len(item) for item in args) > 4096:
        raise ValueError("sandbox arguments exceed bounds")
    if any(item in {"-c", "-m", "--command", "--shell"} for item in args):
        raise ValueError("arbitrary code and command arguments are forbidden")
    if any(item.startswith(("http://", "https://", "file://")) for item in args):
        raise ValueError("raw URLs are not accepted as sandbox arguments")


def build_bwrap_command(module: str, args: list[str], *, network_access: bool,
                        egress_dir: str | Path | None = None,
                        local_model_access: bool = False) -> list[str]:
    """Build an isolated namespace; public network is brokered over one UDS."""
    _validate_module_args(module, args)
    if network_access and egress_dir is None:
        raise SandboxUnavailable("network specialists require the restricted egress broker")
    if local_model_access and not network_access:
        raise SandboxUnavailable("local model access requires the scoped egress broker")
    bwrap = shutil.which("bwrap")
    if not bwrap:
        raise SandboxUnavailable("bubblewrap is not installed")
    if not (ROOT / "venv" / "bin" / "python").exists():
        raise SandboxUnavailable("project virtualenv is unavailable")
    outputs_dir = ROOT / "outputs"
    artifacts_dir = outputs_dir / "autonomy" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    artifacts_dir.chmod(0o700)

    command = [
        bwrap, "--die-with-parent", "--new-session",
        "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--unshare-net",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64",
        "--ro-bind", "/etc", "/etc",
        # WSL's /etc/resolv.conf is a symlink into /mnt/wsl; bind the exact
        # resolver file without exposing the wider host runtime tree.
        "--dir", "/mnt", "--dir", "/mnt/wsl",
        "--ro-bind", "/mnt/wsl/resolv.conf", "/mnt/wsl/resolv.conf",
        "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
        "--ro-bind", str(ROOT), "/workspace",
        # Hide all pre-existing data/output files from child specialists.
        # Only the dedicated autonomy artifact directory persists writes.
        "--tmpfs", "/workspace/data",
        "--tmpfs", "/workspace/outputs",
        "--dir", "/workspace/outputs/autonomy",
        "--bind", str(artifacts_dir), "/workspace/outputs/autonomy/artifacts",
    ]
    if network_access:
        command.extend(["--ro-bind", str(egress_dir), "/run/nextdecode-egress"])

    # Mask the credentials that are known to exist in the repository root.
    for filename in _SECRET_FILES:
        host_path = ROOT / filename
        if host_path.exists() and host_path.is_file():
            command.extend(["--ro-bind", "/dev/null", f"/workspace/{filename}"])

    command.extend([
        "--chdir", "/workspace",
        "--clearenv",
        "--setenv", "HOME", "/tmp",
        "--setenv", "TMPDIR", "/tmp",
        "--setenv", "PATH", "/workspace/venv/bin:/usr/bin:/bin",
        "--setenv", "PYTHONPATH",
        "/run/nextdecode-egress:/workspace" if network_access else "/workspace",
        "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
        "--setenv", "TZ", "Asia/Kolkata",
        "--setenv", "DRY_RUN", "1",
        "--setenv", "PUBLISH_MODE", "review",
        "--setenv", "AUTO_PUBLISH_APPROVED", "false",
        "--setenv", "NEXTDECODE_AUTONOMY_MODE", "1",
        "--setenv", "AI_GENERATION_PROVIDER", "ollama",
        "--setenv", "AI_PROVIDER_CHAIN", "ollama",
    ])
    if network_access:
        command.extend(["--setenv", "NEXTDECODE_EGRESS_SOCKET", "/run/nextdecode-egress/broker.sock"])
    if local_model_access:
        command.extend(["--setenv", "NEXTDECODE_LOCAL_MODEL_ACCESS", "1"])
    for key in (
        "OMNIROUTE_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", "NVIDIA_API_KEY", "CF_API_TOKEN", "OPENROUTER_API_KEY",
        "MISTRAL_API_KEY", "CEREBRAS_API_KEY",
    ):
        command.extend(["--setenv", key, ""])
    command.extend(["/workspace/venv/bin/python", "-m", module, *args])
    return command


def run_sandboxed(module: str, args: list[str], *, network_access: bool = False,
                  local_model_access: bool = False,
                  timeout_seconds: int = 14_400) -> SandboxOutcome:
    started = time.monotonic()
    context = EgressProxy(allow_local_model=local_model_access) if network_access else nullcontext(None)
    try:
        with context as egress:
            if egress is not None:
                sitecustomize = egress.directory / "sitecustomize.py"
                sitecustomize.write_text(SANDBOX_SITECUSTOMIZE, encoding="utf-8")
                sitecustomize.chmod(0o444)
            command = build_bwrap_command(
                module, args, network_access=network_access,
                egress_dir=egress.directory if egress is not None else None,
                local_model_access=local_model_access,
            )
            result = subprocess.run(
                command, cwd=ROOT, stdin=subprocess.DEVNULL,
                capture_output=True, text=True,
                timeout=max(1, min(int(timeout_seconds), 14_400)), check=False,
            )
    except subprocess.TimeoutExpired:
        raise SandboxUnavailable("sandbox execution timed out") from None
    except OSError as exc:
        raise SandboxUnavailable(f"sandbox could not start: {type(exc).__name__}") from None
    return SandboxOutcome(
        returncode=result.returncode, stdout=result.stdout[-300_000:],
        stderr=result.stderr[-12_000:],
        elapsed_seconds=round(time.monotonic() - started, 3),
        profile="bwrap-isolated-egress-broker-" + ("on" if network_access else "off"),
    )
