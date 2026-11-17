from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from app.autonomy.agent_isolation import (
    AgentIsolationExecutor, AgentIsolationPreflight, ExecutionPreflight,
    OwnerApprovalAuthority, OwnerExecutionApproval,
)
from app.autonomy.agent_workspace import WORKSPACE_ROOT


NOW = datetime(2026, 11, 14, 1, 0, tzinfo=timezone.utc)


def _inputs(tmp_path, monkeypatch):
    workspace_id = "a" * 32
    staging_id = "b" * 32
    root = tmp_path / "staging" / staging_id
    (root / "files").mkdir(parents=True)
    content = b"reviewed proposal"
    (root / "files" / "proposal.md").write_bytes(content)
    import hashlib
    digest = hashlib.sha256(content).hexdigest()
    workspace = tmp_path / workspace_id / "workspace"
    workspace.mkdir(parents=True)
    baseline_content = b"baseline snapshot"
    (workspace / "baseline.md").write_bytes(baseline_content)
    manifest = {
        "schema_version": "nextdecode.agent-workspace.v1",
        "workspace_id": workspace_id,
        "agent_execution_enabled": False,
        "network_access": False,
        "credentials_included": False,
        "files": [{
            "path": "baseline.md",
            "sha256": hashlib.sha256(baseline_content).hexdigest(),
        }],
    }
    manifest_path = tmp_path / workspace_id / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    package = {
        "schema_version": "nextdecode.agent-staging-package.v1",
        "staging_id": staging_id, "workspace_id": workspace_id,
        "files": [{"path": "proposal.md", "sha256": digest}],
        "main_repository_modified": False, "repository_import_performed": False,
    }
    (root / "staging-manifest.json").write_text(json.dumps(package))
    monkeypatch.setattr("app.autonomy.agent_isolation.WORKSPACE_ROOT", tmp_path)
    plan = {
        "schema_version": "nextdecode.agent-invocation-plan.v1",
        "plan_id": "plan-1", "workspace_id": workspace_id,
        "workspace_path": str(workspace),
        "workspace_manifest_sha256": manifest_digest,
        "task_sha256": "c" * 64, "created_at": (NOW - timedelta(seconds=30)).isoformat(),
        "status": "plan_only", "process_started": False,
        "invocation_authorized": False, "network_access": False,
        "credential_forwarding": False, "direct_repository_write": False,
    }
    approval = OwnerApprovalAuthority().issue(
        plan, owner_identity="owner",
        approval_evidence_reference="owner-approval://record-1",
        now=NOW - timedelta(seconds=10),
    )
    request = ExecutionPreflight(
        plan=plan, approval=approval, readiness_observed_at=NOW.isoformat(),
        readiness_available=True, readiness_qualified=True,
        readiness_not_suspended=True, readiness_not_revoked=True,
        staged_package_id=staging_id,
    )
    return request


def test_complete_preflight_passes_but_does_not_execute(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert result["accepted"] is True
    assert result["status"] == "preflight_passed_not_executed"
    assert result["process_started"] is False
    assert result["execution_backend"] == "disabled_pending_os_sandbox_qualification"


@pytest.mark.parametrize("field,reason", [
    ("readiness_available", "agent_no_longer_available"),
    ("readiness_qualified", "agent_no_longer_qualified"),
    ("readiness_not_suspended", "agent_suspended"),
    ("readiness_not_revoked", "agent_revoked"),
])
def test_readiness_must_be_rechecked_at_launch(tmp_path, monkeypatch, field, reason):
    request = _inputs(tmp_path, monkeypatch)
    request = replace(request, **{field: False})
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert reason in result["issue_codes"]


def test_expired_approval_is_denied(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    approval = replace(request.approval, expires_at=(NOW - timedelta(seconds=1)).isoformat())
    result = AgentIsolationPreflight().validate(replace(request, approval=approval), now=NOW)
    assert "owner_approval_expired_or_invalid" in result["issue_codes"]


def test_approval_must_bind_exact_plan_workspace_and_task(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    approval = replace(request.approval, task_sha256="d" * 64)
    result = AgentIsolationPreflight().validate(replace(request, approval=approval), now=NOW)
    assert "owner_approval_task_binding_mismatch" in result["issue_codes"]


def test_staged_artifact_digest_is_rechecked(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    file = tmp_path / "staging" / request.staged_package_id / "files" / "proposal.md"
    file.write_text("tampered after approval")
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert "staged_file_digest_mismatch" in result["issue_codes"]


def test_plan_cannot_claim_invocation_authorized(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    plan = dict(request.plan, invocation_authorized=True)
    result = AgentIsolationPreflight().validate(replace(request, plan=plan), now=NOW)
    assert "planning_must_not_grant_invocation" in result["issue_codes"]


def test_executor_refuses_even_after_successful_preflight(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    with pytest.raises(PermissionError, match="backend is disabled"):
        AgentIsolationExecutor().execute(request, now=NOW)
