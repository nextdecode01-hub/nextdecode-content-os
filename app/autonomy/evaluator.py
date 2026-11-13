"""Post-execution acceptance checks for task results and local artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .models import TaskResult


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = (ROOT / "outputs" / "autonomy" / "artifacts").resolve()


def evaluate_result(result: TaskResult) -> tuple[bool, str | None, dict]:
    if not isinstance(result, TaskResult):
        return False, "result_contract_invalid", {"accepted": False}
    if not isinstance(result.output, dict) or not isinstance(result.evidence, dict):
        return False, "result_shape_invalid", {"accepted": False}
    if result.status != "succeeded":
        return True, None, {"accepted": True, "not_applicable": True}
    exit_code = result.evidence.get("exit_code")
    if exit_code is not None and exit_code != 0:
        return False, "nonzero_exit_cannot_succeed", {"accepted": False}
    if result.output.get("external_actions_allowed") is True:
        return False, "external_action_policy_violation", {"accepted": False}
    if "dry_run" in result.output and result.output["dry_run"] is not True:
        return False, "non_dry_run_result_rejected", {"accepted": False}

    artifact_path = result.output.get("artifact_path")
    if not artifact_path:
        return True, None, {"accepted": True, "artifact_verified": False}
    path = (ROOT / str(artifact_path)).resolve()
    if ARTIFACT_ROOT not in path.parents or not path.is_file():
        return False, "artifact_path_outside_allowed_store", {"accepted": False}
    raw = path.read_bytes()
    if len(raw) > 1_000_000:
        return False, "artifact_exceeds_size_limit", {"accepted": False}
    expected = result.output.get("artifact_sha256")
    actual = hashlib.sha256(raw).hexdigest()
    if not isinstance(expected, str) or actual != expected:
        return False, "artifact_integrity_mismatch", {"accepted": False}
    try:
        envelope = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return False, "artifact_is_not_valid_json", {"accepted": False}
    if envelope.get("schema_version") != "nextdecode.autonomy-artifact.v1":
        return False, "artifact_schema_invalid", {"accepted": False}
    if result.output.get("artifact_type") != envelope.get("artifact_type"):
        return False, "artifact_type_mismatch", {"accepted": False}
    if not isinstance(envelope.get("artifact_id"), str) or len(envelope["artifact_id"]) != 32:
        return False, "artifact_id_invalid", {"accepted": False}
    if not isinstance(envelope.get("run_id"), str) or len(envelope["run_id"]) != 32:
        return False, "artifact_run_id_invalid", {"accepted": False}
    if result.output.get("artifact_id") != envelope.get("artifact_id"):
        return False, "artifact_id_mismatch", {"accepted": False}
    if result.output.get("run_id") != envelope.get("run_id"):
        return False, "artifact_run_id_mismatch", {"accepted": False}
    if envelope.get("external_actions_allowed") is not False:
        return False, "artifact_external_action_policy_missing", {"accepted": False}
    if envelope.get("human_review_status") != "pending":
        return False, "artifact_review_state_invalid", {"accepted": False}
    return True, None, {
        "accepted": True,
        "artifact_verified": True,
        "artifact_sha256": actual,
        "artifact_bytes": len(raw),
        "artifact_type": envelope.get("artifact_type"),
    }
