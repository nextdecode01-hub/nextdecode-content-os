from pathlib import Path

import pytest

from app.autonomy.agent_sandbox import BubblewrapSandbox, SandboxLimits


def test_limits_reject_unbounded_values():
    with pytest.raises(ValueError):
        SandboxLimits(cpu_seconds=0)
    with pytest.raises(ValueError):
        SandboxLimits(processes=10000)


def test_bubblewrap_inert_probe_reports_actual_namespace_capability_fail_closed():
    result = BubblewrapSandbox().probe()
    if not result.available:
        assert not result.qualified
        assert "sandbox_tools_missing" in result.issue_codes
        return
    if result.qualified:
        assert all(result.checks.values())
        assert not result.issue_codes
        return
    # WSL/container hosts may expose bubblewrap but deny unprivileged
    # namespaces. The probe must report that limitation, never qualify it.
    failed_checks = {name for name, passed in result.checks.items() if not passed}
    assert failed_checks
    assert not result.qualified
    assert any(
        issue == "sandbox_probe_nonzero_exit"
        or issue.startswith("sandbox_probe_error:")
        or issue.startswith("sandbox_check_failed:")
        for issue in result.issue_codes
    )
    assert all(
        f"sandbox_check_failed:{name}" in result.issue_codes
        for name in failed_checks
    )


def test_command_uses_network_namespace_and_read_only_inputs(tmp_path, monkeypatch):
    import app.autonomy.agent_sandbox as sandbox_module

    root = tmp_path / "agent-workspaces"
    workspace = root / ("a" * 32) / "workspace"
    staged = root / "staging" / ("b" * 32) / "files"
    output = root / "results" / ("c" * 32)
    workspace.mkdir(parents=True)
    staged.mkdir(parents=True)
    monkeypatch.setattr(sandbox_module, "WORKSPACE_ROOT", root)
    sandbox = BubblewrapSandbox()
    command = sandbox.build_command(
        executable="/usr/bin/python3.14", arguments=("-c", "pass"),
        workspace=workspace, staged_input=staged, output=output,
    )
    assert "--unshare-net" in command
    assert "--unshare-pid" in command
    assert "--unshare-user" in command
    assert "--ro-bind" in command
    assert str(workspace) in command
    assert str(staged) in command
    assert str(output) in command
    assert "--fsize=67108864:67108864" in command
    assert "--nproc=256:256" in command


def test_command_rejects_workspace_outside_private_root(tmp_path, monkeypatch):
    import app.autonomy.agent_sandbox as sandbox_module

    root = tmp_path / "agent-workspaces"
    workspace = tmp_path / "outside"
    staged = root / "staging" / ("b" * 32) / "files"
    workspace.mkdir()
    staged.mkdir(parents=True)
    monkeypatch.setattr(sandbox_module, "WORKSPACE_ROOT", root)
    with pytest.raises(ValueError, match="private agent workspace root"):
        BubblewrapSandbox().build_command(
            executable="/usr/bin/python3.14", arguments=(),
            workspace=workspace, staged_input=staged,
            output=root / "results" / ("c" * 32),
        )


def test_command_rejects_symlink_workspace(tmp_path, monkeypatch):
    import app.autonomy.agent_sandbox as sandbox_module

    root = tmp_path / "agent-workspaces"
    real = root / "real"
    staged = root / "staging" / ("b" * 32) / "files"
    real.mkdir(parents=True)
    staged.mkdir(parents=True)
    link = root / ("a" * 32)
    link.symlink_to(real, target_is_directory=True)
    monkeypatch.setattr(sandbox_module, "WORKSPACE_ROOT", root)
    with pytest.raises(ValueError, match="symlinks"):
        BubblewrapSandbox().build_command(
            executable="/usr/bin/python3.14", arguments=(),
            workspace=link, staged_input=staged,
            output=root / "results" / ("c" * 32),
        )

def test_output_tmpfs_args_include_aggregate_size_cap():
    sandbox = BubblewrapSandbox(SandboxLimits(output_bytes=2 * 1024 * 1024))
    assert sandbox.output_tmpfs_args() == [
        "--size", str(2 * 1024 * 1024), "--tmpfs", "/output"
    ]


@pytest.mark.parametrize("destination", ["/", "relative", "/output/../host"])
def test_output_tmpfs_rejects_unsafe_destination(destination):
    with pytest.raises(ValueError):
        BubblewrapSandbox().output_tmpfs_args(destination=destination)


def test_bubblewrap_enforces_tmpfs_output_capacity():
    import os
    import subprocess

    sandbox = BubblewrapSandbox(SandboxLimits(output_bytes=2 * 1024 * 1024))
    if not sandbox.bwrap:
        pytest.skip("bubblewrap is unavailable")
    command = [
        sandbox.bwrap, "--unshare-user", "--unshare-pid", "--unshare-net",
        "--die-with-parent", "--new-session", *sandbox._runtime_binds(),
        "--proc", "/proc", "--dev", "/dev", *sandbox.output_tmpfs_args(),
        "--", "/usr/bin/python3", "-c",
        "import os; s=os.statvfs('/output'); print(s.f_blocks*s.f_frsize)",
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=10, check=False,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
    )
    assert completed.returncode == 0, completed.stderr
    reported_capacity = int(completed.stdout.strip())
    assert reported_capacity <= 2 * 1024 * 1024
