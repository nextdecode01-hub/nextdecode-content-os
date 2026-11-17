from __future__ import annotations

import hashlib
import json

import pytest

import app.autonomy.tasks as tasks
from app.autonomy.evaluator import evaluate_result
from app.autonomy.models import TaskRequest, TaskResult
from app.autonomy.sandbox import SandboxOutcome, run_sandboxed


def test_script_draft_requires_verified_research_dependency():
    result = tasks.short_script_draft(TaskRequest(
        "content.short.script.draft", {"topic": "AI"}
    ))
    assert result.status == "blocked"
    assert result.error_code == "research_dependency_required"


def test_document_text_specialist_returns_bounded_structure_only():
    result = tasks.document_text_analyze(TaskRequest(
        "documents.text.analyze",
        {"title": "Test", "text": "# Heading\nA small document with useful terms and https://example.com"},
    ))
    assert result.status == "succeeded"
    assert result.output["word_count"] > 0
    assert result.output["headings"] == ["Heading"]
    assert result.output["link_count"] == 1
    assert "text" not in result.output


def test_document_specialist_rejects_arbitrary_file_paths():
    with pytest.raises(ValueError, match="unsupported fields"):
        tasks.validate_document_payload({"path": "/etc/passwd"})


def test_dataset_profile_is_deterministic_and_does_not_return_rows():
    result = tasks.dataset_profile(TaskRequest(
        "data.dataset.profile",
        {"rows": [{"views": 10, "likes": 2}, {"views": 20, "likes": 4}, {"views": None, "likes": 6}]},
    ))
    assert result.status == "succeeded"
    assert result.output["row_count"] == 3
    views = next(item for item in result.output["columns"] if item["column"] == "views")
    assert views["missing"] == 1
    assert views["mean"] == 15.0
    assert "rows" not in result.output


def test_dataset_profile_rejects_oversized_input():
    with pytest.raises(ValueError, match="1..500"):
        tasks.validate_dataset_payload({"rows": [{}] * 501})


def test_sandboxed_specialist_verifies_artifact_before_success(tmp_path, monkeypatch):
    root = tmp_path
    artifact_dir = root / "outputs" / "autonomy" / "artifacts"
    artifact_dir.mkdir(parents=True)
    artifact = {
        "schema_version": "nextdecode.autonomy-artifact.v1",
        "artifact_id": "a" * 32,
        "run_id": "b" * 32,
        "artifact_type": "short-script-draft",
        "human_review_status": "pending",
        "external_actions_allowed": False,
        "payload": {"script": "hello"},
    }
    raw = (json.dumps(artifact, sort_keys=True) + "\n").encode()
    path = artifact_dir / "draft.json"
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(tasks, "ROOT", root)

    response = {"status": "success", "artifact_path": "outputs/autonomy/artifacts/draft.json",
                "artifact_sha256": digest, "artifact_type": "short-script-draft",
                "artifact_id": "a" * 32, "run_id": "b" * 32}
    monkeypatch.setattr(tasks, "run_sandboxed", lambda *a, **k: SandboxOutcome(
        0, json.dumps(response), "", 0.2, "bwrap-test"
    ))
    result = tasks._run_module("app.autonomy.specialist_cli", ["short-script", "--topic", "AI"],
                               network_access=True)
    assert result.status == "succeeded"
    assert result.evidence["artifact_verified"] is True


def test_sandboxed_specialist_rejects_artifact_hash_mismatch(tmp_path, monkeypatch):
    root = tmp_path
    artifact_dir = root / "outputs" / "autonomy" / "artifacts"
    artifact_dir.mkdir(parents=True)
    path = artifact_dir / "draft.json"
    path.write_text(json.dumps({
        "schema_version": "nextdecode.autonomy-artifact.v1",
        "artifact_type": "short-script-draft",
        "human_review_status": "pending",
        "external_actions_allowed": False,
    }))
    monkeypatch.setattr(tasks, "ROOT", root)
    response = {"status": "success", "artifact_path": "outputs/autonomy/artifacts/draft.json",
                "artifact_sha256": "0" * 64}
    monkeypatch.setattr(tasks, "run_sandboxed", lambda *a, **k: SandboxOutcome(
        0, json.dumps(response), "", 0.1, "bwrap-test"
    ))
    result = tasks._run_module("app.autonomy.specialist_cli", ["short-script", "--topic", "AI"],
                               network_access=True)
    assert result.status == "failed"
    assert result.error_code == "artifact_integrity_mismatch"


def test_evaluator_rejects_external_action_and_unverified_artifact(tmp_path, monkeypatch):
    import app.autonomy.evaluator as evaluator
    monkeypatch.setattr(evaluator, "ROOT", tmp_path)
    monkeypatch.setattr(evaluator, "ARTIFACT_ROOT", (tmp_path / "outputs" / "autonomy" / "artifacts").resolve())
    accepted, error, _ = evaluate_result(TaskResult(
        "succeeded", {"external_actions_allowed": True}
    ))
    assert not accepted and error == "external_action_policy_violation"
    accepted, error, _ = evaluate_result(TaskResult(
        "succeeded", {"artifact_path": "outputs/autonomy/artifacts/missing.json"}
    ))
    assert not accepted and error == "artifact_path_outside_allowed_store"


def test_real_bwrap_sandbox_runs_only_the_allowlisted_specialist_cli():
    import shutil
    if not shutil.which("bwrap"):
        pytest.skip("bubblewrap is not installed")
    outcome = run_sandboxed(
        "app.autonomy.specialist_cli", ["--help"],
        network_access=False, timeout_seconds=20,
    )
    assert outcome.returncode == 0
    assert "nextdecode-specialist" in outcome.stdout



def test_csv_specialist_profiles_bounded_inline_numeric_dataset():
    from app.autonomy.tasks import csv_dataset_profile, validate_csv_payload

    raw_payload = {"csv_text": "views,likes\n10,2\n20,4\n30,6\n"}
    validated = validate_csv_payload(raw_payload)
    assert validated == {**raw_payload, "delimiter": ","}
    result = csv_dataset_profile(TaskRequest("data.csv.profile", validated))
    assert result.status == "succeeded"
    assert result.output["source_format"] == "csv"
    assert result.output["row_count"] == 3
    assert result.output["column_count"] == 2
    views = next(item for item in result.output["columns"] if item["column"] == "views")
    assert views["numeric"] is True
    assert views["mean"] == 20
    assert result.evidence["input_format"] == "csv"


def test_csv_specialist_supports_explicit_semicolon_delimiter():
    from app.autonomy.tasks import csv_dataset_profile

    result = csv_dataset_profile(TaskRequest(
        "data.csv.profile",
        {"csv_text": "name;score\nalpha;3\nbeta;5\n", "delimiter": ";"},
    ))
    assert result.status == "succeeded"
    assert result.output["delimiter"] == ";"
    assert result.output["row_count"] == 2


@pytest.mark.parametrize("payload", [
    {"csv_text": "value,value\n1,2\n"},
    {"csv_text": "value\n\"unterminated\n"},
    {"csv_text": "value\n1,extra\n"},
    {"csv_text": "value\n1\n", "delimiter": ["bad"]},
    {"csv_text": "value\n1\n", "path": "/etc/passwd"},
])
def test_csv_specialist_rejects_malformed_or_unsafe_payloads(payload):
    from app.autonomy.tasks import validate_csv_payload

    with pytest.raises(ValueError):
        validate_csv_payload(payload)


def test_csv_specialist_enforces_input_and_row_bounds():
    from app.autonomy.tasks import validate_csv_payload

    with pytest.raises(ValueError, match="48000"):
        validate_csv_payload({"csv_text": "x\n" + ("a" * 48_001)})
    rows = "value\n" + "\n".join(str(index) for index in range(501))
    with pytest.raises(ValueError, match="500 data rows"):
        validate_csv_payload({"csv_text": rows})


def test_csv_specialist_is_registered_but_not_automatically_planned():
    from app.autonomy.registry import build_default_registry

    capability = build_default_registry().get("data.csv.profile")
    assert capability.enabled is True
    assert capability.planner_allowed is False
    assert capability.network_access is False
    assert capability.sandbox_profile == "in-process-bounded"



def test_script_specialist_bounds_model_context_to_two_verified_sources(tmp_path, monkeypatch):
    import hashlib
    import json
    import app.autonomy.specialist_cli as specialist

    artifact_root = tmp_path / "outputs" / "autonomy" / "artifacts"
    artifact_root.mkdir(parents=True)
    monkeypatch.setattr(specialist, "ROOT", tmp_path)
    monkeypatch.setattr(specialist, "ARTIFACT_ROOT", artifact_root)
    envelope = {
        "schema_version": "nextdecode.autonomy-artifact.v1",
        "artifact_type": "research-brief",
        "payload": {"sources": [
            {"title": f"Source {index}", "url": f"https://example.com/{index}"}
            for index in range(4)
        ]},
    }
    path = artifact_root / "research.json"
    raw = json.dumps(envelope).encode()
    path.write_bytes(raw)
    sources = specialist._load_research_artifact(
        "outputs/autonomy/artifacts/research.json", hashlib.sha256(raw).hexdigest()
    )
    assert [item["title"] for item in sources] == ["Source 0", "Source 1"]


def test_specialist_artifact_verification_binds_studio_provenance(tmp_path, monkeypatch):
    artifact_dir = tmp_path / "outputs" / "autonomy" / "artifacts"
    artifact_dir.mkdir(parents=True)
    envelope = {
        "schema_version": "nextdecode.autonomy-artifact.v1",
        "artifact_id": "a" * 32,
        "run_id": "b" * 32,
        "artifact_type": "research-brief",
        "human_review_status": "pending",
        "external_actions_allowed": False,
        "studio_provenance": {
            "studio_version_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "studio_content_sha256": "c" * 64,
        },
        "payload": {"sources": [{"url": "https://example.com"}]},
    }
    raw = json.dumps(envelope, sort_keys=True).encode()
    path = artifact_dir / "research.json"
    path.write_bytes(raw)
    monkeypatch.setattr(tasks, "ROOT", tmp_path)
    output = {
        "artifact_path": "outputs/autonomy/artifacts/research.json",
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "artifact_type": "research-brief", "artifact_id": "a" * 32, "run_id": "b" * 32,
        **envelope["studio_provenance"],
    }
    assert tasks._verified_artifact(output) == (True, None)
    output["studio_content_sha256"] = "d" * 64
    assert tasks._verified_artifact(output) == (False, "artifact_studio_provenance_mismatch")
