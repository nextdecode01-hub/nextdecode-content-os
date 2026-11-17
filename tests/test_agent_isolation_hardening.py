from dataclasses import replace
from datetime import timedelta
import json

from app.autonomy.agent_isolation import AgentIsolationPreflight
from test_agent_isolation import NOW, _inputs


def test_workspace_snapshot_file_tampering_is_detected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    (tmp_path / request.plan["workspace_id"] / "workspace" / "baseline.md").write_text("tampered")
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert "workspace_file_digest_mismatch" in result["issue_codes"]


def test_workspace_manifest_tampering_is_detected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    path = tmp_path / request.plan["workspace_id"] / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["network_access"] = True
    path.write_text(json.dumps(manifest, sort_keys=True))
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert "workspace_manifest_digest_mismatch" in result["issue_codes"]
    assert "workspace_security_baseline_invalid" in result["issue_codes"]


def test_unlisted_workspace_file_is_detected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    workspace = tmp_path / request.plan["workspace_id"] / "workspace"
    (workspace / "unlisted.txt").write_text("not in signed snapshot")
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert "workspace_file_inventory_mismatch" in result["issue_codes"]


def test_workspace_path_binding_cannot_be_redirected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    plan = dict(request.plan, workspace_path="/tmp/other-workspace")
    result = AgentIsolationPreflight().validate(replace(request, plan=plan), now=NOW)
    assert "workspace_path_binding_mismatch" in result["issue_codes"]


def test_extra_staged_file_is_detected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    files = tmp_path / "staging" / request.staged_package_id / "files"
    (files / "unexpected.txt").write_text("extra")
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert "staged_file_inventory_mismatch" in result["issue_codes"]


def test_staged_manifest_duplicate_paths_are_detected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    path = tmp_path / "staging" / request.staged_package_id / "staging-manifest.json"
    package = json.loads(path.read_text())
    package["files"].append(dict(package["files"][0]))
    path.write_text(json.dumps(package))
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert "staged_duplicate_path" in result["issue_codes"]


def test_staged_path_traversal_is_detected(tmp_path, monkeypatch):
    request = _inputs(tmp_path, monkeypatch)
    path = tmp_path / "staging" / request.staged_package_id / "staging-manifest.json"
    package = json.loads(path.read_text())
    package["files"][0]["path"] = "../outside.txt"
    path.write_text(json.dumps(package))
    result = AgentIsolationPreflight().validate(request, now=NOW)
    assert "staged_path_invalid" in result["issue_codes"]
