from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.autonomy.agent_runner import (
    BoundedAgentRunner, RunState, RunnerPolicy, inspect_output_tree,
)


def test_runner_policy_is_fail_closed():
    assert RunnerPolicy().enabled is False
    with pytest.raises(ValueError):
        RunnerPolicy(enabled=True)


def test_prepare_creates_blocked_record_without_execution(tmp_path):
    class FakeSandbox:
        def build_command(self, **kwargs):
            return ["/usr/bin/true"]

    executable = tmp_path / "agent"
    executable.write_bytes(b"agent-runtime")
    runner = BoundedAgentRunner(sandbox=FakeSandbox())
    command, record = runner.prepare(
        run_id="a" * 32, plan={"task_id": "task-1"},
        approval_id="approval-1", workspace_id="workspace-1",
        staging_id="staging-1", executable=str(executable),
        arguments=(), workspace=tmp_path, staged_input=tmp_path,
        output=tmp_path / "output",
    )
    assert command == ["/usr/bin/true"]
    assert record.state is RunState.BLOCKED
    assert record.started_at is None
    assert record.finished_at is None
    assert record.executable_sha256 == hashlib.sha256(b"agent-runtime").hexdigest()
    assert "agent_execution_disabled" in record.issue_codes


def test_prepare_rejects_invalid_run_id():
    with pytest.raises(ValueError):
        BoundedAgentRunner().prepare(
            run_id="../bad", plan={}, approval_id="a", workspace_id="w",
            staging_id="s", executable="/missing", arguments=(),
            workspace="/missing", staged_input="/missing", output="/missing",
        )


def test_output_manifest_hashes_files(tmp_path):
    (tmp_path / "nested").mkdir()
    data = b"safe-result"
    (tmp_path / "nested" / "result.txt").write_bytes(data)
    manifest = inspect_output_tree(tmp_path, max_bytes=100, max_files=10)
    assert manifest.complete
    assert manifest.total_bytes == len(data)
    assert manifest.files[0].sha256 == hashlib.sha256(data).hexdigest()
    assert manifest.files[0].path == "nested/result.txt"


def test_output_manifest_enforces_aggregate_byte_cap(tmp_path):
    (tmp_path / "a").write_bytes(b"1234")
    (tmp_path / "b").write_bytes(b"5678")
    manifest = inspect_output_tree(tmp_path, max_bytes=5, max_files=10)
    assert not manifest.complete
    assert "output_byte_quota_exceeded" in manifest.issue_codes


def test_output_manifest_enforces_file_count(tmp_path):
    (tmp_path / "a").write_text("a")
    (tmp_path / "b").write_text("b")
    manifest = inspect_output_tree(tmp_path, max_bytes=100, max_files=1)
    assert not manifest.complete
    assert "output_file_quota_exceeded" in manifest.issue_codes


def test_output_manifest_rejects_symlink(tmp_path):
    target = tmp_path / "target"
    target.write_text("secret")
    (tmp_path / "link").symlink_to(target)
    manifest = inspect_output_tree(tmp_path, max_bytes=100, max_files=10)
    assert not manifest.complete
    assert "output_non_regular_file_rejected" in manifest.issue_codes


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"exit_code": 0}, RunState.COMPLETED),
        ({"exit_code": 3}, RunState.FAILED),
        ({"exit_code": None}, RunState.FAILED),
        ({"exit_code": -9, "timed_out": True}, RunState.TIMED_OUT),
        ({"exit_code": -15, "cancelled": True}, RunState.CANCELLED),
    ],
)
def test_exit_classification(kwargs, expected):
    assert BoundedAgentRunner.classify_exit(**kwargs) is expected


def test_bounded_text_truncates_utf8_safely():
    result = BoundedAgentRunner.bounded_text("hello world", max_bytes=8)
    assert len(result.encode()) <= 8
    assert result == "hello wo"


def test_secure_output_export_copies_and_hashes_files(tmp_path):
    from app.autonomy.agent_runner import export_sandbox_output

    source = tmp_path / "sandbox-output"
    source.mkdir()
    (source / "nested").mkdir()
    payload = b"approved-result"
    (source / "nested" / "result.txt").write_bytes(payload)
    results = tmp_path / "results"
    exported = export_sandbox_output(
        source, export_id="d" * 32, max_bytes=100, max_files=10,
        results_root=results,
    )
    assert exported.manifest.complete
    assert exported.manifest.total_bytes == len(payload)
    target = Path(exported.destination) / "nested" / "result.txt"
    assert target.read_bytes() == payload
    assert exported.manifest.files[0].sha256 == hashlib.sha256(payload).hexdigest()


def test_secure_output_export_never_overwrites_existing_result(tmp_path):
    from app.autonomy.agent_runner import export_sandbox_output

    source = tmp_path / "source"
    source.mkdir()
    results = tmp_path / "results"
    results.mkdir()
    existing = results / ("e" * 32)
    existing.mkdir()
    (existing / "keep").write_text("original")
    with pytest.raises(FileExistsError):
        export_sandbox_output(
            source, export_id="e" * 32, max_bytes=100, max_files=10,
            results_root=results,
        )
    assert (existing / "keep").read_text() == "original"


def test_secure_output_export_rejects_symlink_files(tmp_path):
    from app.autonomy.agent_runner import export_sandbox_output

    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("not an artifact")
    (source / "link").symlink_to(outside)
    with pytest.raises(ValueError, match="non-regular"):
        export_sandbox_output(
            source, export_id="f" * 32, max_bytes=100, max_files=10,
            results_root=tmp_path / "results",
        )


def test_secure_output_export_enforces_aggregate_quota(tmp_path):
    from app.autonomy.agent_runner import export_sandbox_output

    source = tmp_path / "source"
    source.mkdir()
    (source / "a").write_bytes(b"1234")
    (source / "b").write_bytes(b"5678")
    with pytest.raises(ValueError, match="aggregate byte quota"):
        export_sandbox_output(
            source, export_id="1" * 32, max_bytes=5, max_files=10,
            results_root=tmp_path / "results",
        )
    assert not (tmp_path / "results" / ("1" * 32)).exists()


def test_secure_output_export_rejects_invalid_id_and_symlink_root(tmp_path):
    from app.autonomy.agent_runner import export_sandbox_output

    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(ValueError, match="export_id"):
        export_sandbox_output(
            source, export_id="../bad", max_bytes=100, max_files=10,
            results_root=tmp_path / "results",
        )
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="real directory"):
        export_sandbox_output(
            source, export_id="2" * 32, max_bytes=100, max_files=10,
            results_root=link,
        )


def test_lifecycle_records_start_and_cancel_without_signalling_real_process():
    from app.autonomy.agent_runner import ProcessLifecycleController

    controller = ProcessLifecycleController()
    controller.mark_started(pid=123, process_group_id=120, started_at="start")
    signalled = []
    controller.request_termination(
        "cancelled", terminate_group=lambda pgid: signalled.append(pgid)
    )
    assert signalled == [120]
    assert controller.observe_exit(-15, finished_at="finish") is RunState.CANCELLED
    snapshot = controller.snapshot()
    assert snapshot.pid == 123
    assert snapshot.started_at == "start"
    assert snapshot.finished_at == "finish"
    assert snapshot.termination_reason == "cancelled"


def test_lifecycle_timeout_takes_precedence_over_exit_code():
    from app.autonomy.agent_runner import ProcessLifecycleController

    controller = ProcessLifecycleController()
    controller.mark_started(pid=22, process_group_id=22)
    controller.request_termination("timed_out", terminate_group=lambda _pgid: None)
    assert controller.observe_exit(-9) is RunState.TIMED_OUT


def test_lifecycle_rejects_duplicate_start_and_exit_before_start():
    from app.autonomy.agent_runner import ProcessLifecycleController

    controller = ProcessLifecycleController()
    with pytest.raises(RuntimeError, match="before process start"):
        controller.observe_exit(0)
    controller.mark_started(pid=2, process_group_id=2)
    with pytest.raises(RuntimeError, match="only start"):
        controller.mark_started(pid=3, process_group_id=3)


def test_lifecycle_rejects_invalid_or_duplicate_termination():
    from app.autonomy.agent_runner import ProcessLifecycleController

    controller = ProcessLifecycleController()
    with pytest.raises(RuntimeError, match="not recorded as started"):
        controller.request_termination("cancelled", terminate_group=lambda _pgid: None)
    controller.mark_started(pid=5, process_group_id=5)
    calls = []
    controller.request_termination("cancelled", terminate_group=lambda pgid: calls.append(pgid))
    controller.request_termination("timed_out", terminate_group=lambda pgid: calls.append(pgid))
    assert calls == [5]
    controller.observe_exit(-15)
    with pytest.raises(RuntimeError, match="already finished"):
        controller.request_termination("cancelled", terminate_group=lambda _pgid: None)


def test_bounded_output_capture_enforces_separate_stream_caps():
    from app.autonomy.agent_runner import BoundedOutputCapture

    capture = BoundedOutputCapture(stdout_limit=5, stderr_limit=3)
    assert capture.feed("stdout", b"hello!!") == 5
    assert capture.feed("stderr", b"error") == 3
    assert capture.text("stdout") == "hello"
    assert capture.text("stderr") == "err"
    assert capture.was_truncated("stdout")
    assert capture.was_truncated("stderr")
