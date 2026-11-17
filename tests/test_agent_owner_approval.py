from dataclasses import replace
import json
import os
import stat

import pytest

from app.autonomy.agent_isolation import (
    AgentIsolationPreflight, OwnerApprovalAuthority,
)
from test_agent_isolation import NOW, _inputs


def test_owner_approval_is_bound_to_exact_plan(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    changed = dict(request.plan, timeout_seconds=120)
    assert not OwnerApprovalAuthority().verify(request.approval, changed)
    result = AgentIsolationPreflight().validate(
        replace(request, plan=changed), now=NOW
    )
    assert "owner_approval_signature_invalid" in result["issue_codes"]


def test_tampered_approval_signature_is_rejected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    forged = replace(request.approval, owner_identity="attacker")
    result = AgentIsolationPreflight().validate(
        replace(request, approval=forged), now=NOW
    )
    assert "owner_approval_signature_invalid" in result["issue_codes"]


def test_approval_signature_cannot_be_replaced_with_arbitrary_text(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    forged = replace(request.approval, signature="f" * 64)
    assert not OwnerApprovalAuthority().verify(forged, request.plan)


def test_approval_issuer_refuses_self_authorized_plan(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="must not self-authorize"):
        OwnerApprovalAuthority().issue(
            dict(request.plan, invocation_authorized=True),
            owner_identity="owner",
            approval_evidence_reference="approval://test",
            now=NOW,
        )


def test_approval_key_must_be_private_regular_file(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    key = tmp_path / ".owner-approval-hmac.key"
    key.chmod(0o644)
    with pytest.raises(PermissionError, match="private regular file"):
        OwnerApprovalAuthority().verify(request.approval, request.plan)


def test_approval_payload_is_deterministically_serialized(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    reordered = dict(reversed(list(request.plan.items())))
    assert OwnerApprovalAuthority().verify(request.approval, reordered)



def test_signed_approval_artifact_round_trips(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    authority = OwnerApprovalAuthority()
    path = authority.save(request.approval, request.plan)
    loaded = authority.load(path, request.plan)
    assert loaded == request.approval
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_signed_approval_artifact_tampering_is_rejected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    authority = OwnerApprovalAuthority()
    path = authority.save(request.approval, request.plan)
    document = json.loads(path.read_text())
    document["owner_identity"] = "forged-owner"
    path.write_text(json.dumps(document))
    with pytest.raises(PermissionError, match="signature or identity"):
        authority.load(path, request.plan)


def test_approval_artifact_cannot_be_loaded_for_another_plan(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    authority = OwnerApprovalAuthority()
    path = authority.save(request.approval, request.plan)
    changed_plan = dict(request.plan, task_sha256="d" * 64)
    with pytest.raises(PermissionError, match="signature or identity"):
        authority.load(path, changed_plan)
