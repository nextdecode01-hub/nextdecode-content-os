"""Allow-listed specialist handlers with bounded payloads and fail-closed sandboxing."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import statistics
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .models import TaskRequest, TaskResult
from .sandbox import ROOT, SandboxUnavailable, run_sandboxed


TIMEOUT_SECONDS = 4 * 60 * 60
_SECRET_PATTERNS = (
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*"), r"\1[REDACTED]"),
    (re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"\b(?:sk|pk|ghp|xoxb|ya29)[_-][A-Za-z0-9_-]{8,}\b"), "[REDACTED_TOKEN]"),
    (re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"), "[REDACTED_TOKEN]"),
)


def _redact_output(value: str) -> str:
    for pattern, replacement in _SECRET_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def _topic(request: TaskRequest) -> str:
    topic = request.payload.get("topic", "")
    if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 200:
        raise ValueError("topic must be 1..200 characters")
    return topic.strip()


def validate_topic_payload(payload: dict) -> dict:
    if set(payload) - {"topic", "max_sources"}:
        raise ValueError("research payload contains unsupported fields")
    topic = payload.get("topic")
    if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 200:
        raise ValueError("topic must be 1..200 characters")
    max_sources = payload.get("max_sources", 4)
    if not isinstance(max_sources, int) or isinstance(max_sources, bool) or not 1 <= max_sources <= 5:
        raise ValueError("max_sources must be between 1 and 5")
    return {"topic": topic.strip(), "max_sources": max_sources}


def validate_script_payload(payload: dict) -> dict:
    if set(payload) - {"topic"}:
        raise ValueError("script payload contains unsupported fields")
    topic = payload.get("topic")
    if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 200:
        raise ValueError("topic must be 1..200 characters")
    return {"topic": topic.strip()}


def validate_generation_payload(payload: dict) -> dict:
    if set(payload) - {"topic", "dry_run", "approval_required"}:
        raise ValueError("generation payload contains unsupported fields")
    topic = payload.get("topic", "")
    if not isinstance(topic, str) or len(topic.strip()) > 200:
        raise ValueError("topic must be a string of at most 200 characters")
    if payload.get("dry_run", True) is not True:
        raise ValueError("autonomous generation is review-only")
    if payload.get("approval_required", True) is not True:
        raise ValueError("human approval cannot be disabled")
    return {"topic": topic.strip(), "dry_run": True, "approval_required": True}


def _last_json_object(stdout: str) -> dict | None:
    for line in reversed((stdout or "").splitlines()):
        try:
            value = json.loads(line.strip())
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    return None


def _verified_artifact(output: dict) -> tuple[bool, str | None]:
    artifact_path = output.get("artifact_path")
    digest = output.get("artifact_sha256")
    if not artifact_path:
        return True, None
    path = (ROOT / str(artifact_path)).resolve()
    allowed = (ROOT / "outputs" / "autonomy" / "artifacts").resolve()
    if allowed not in path.parents or not path.is_file():
        return False, "artifact_path_outside_allowed_store"
    raw = path.read_bytes()
    if len(raw) > 1_000_000:
        return False, "artifact_exceeds_size_limit"
    if not isinstance(digest, str) or hashlib.sha256(raw).hexdigest() != digest:
        return False, "artifact_integrity_mismatch"
    try:
        envelope = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return False, "artifact_is_not_valid_json"
    if envelope.get("external_actions_allowed") is not False:
        return False, "artifact_external_action_policy_missing"
    if output.get("artifact_type") != envelope.get("artifact_type"):
        return False, "artifact_type_mismatch"
    if not isinstance(envelope.get("artifact_id"), str) or len(envelope["artifact_id"]) != 32:
        return False, "artifact_id_invalid"
    if not isinstance(envelope.get("run_id"), str) or len(envelope["run_id"]) != 32:
        return False, "artifact_run_id_invalid"
    if output.get("artifact_id") != envelope.get("artifact_id"):
        return False, "artifact_id_mismatch"
    if output.get("run_id") != envelope.get("run_id"):
        return False, "artifact_run_id_mismatch"
    if envelope.get("human_review_status") != "pending":
        return False, "artifact_review_state_invalid"
    return True, None


def _run_module(module: str, args: list[str], *, network_access: bool,
                local_model_access: bool = False,
                timeout_seconds: int = TIMEOUT_SECONDS) -> TaskResult:
    started = datetime.now(timezone.utc).isoformat()
    run_id = uuid.uuid4().hex
    try:
        outcome = run_sandboxed(
            module, args, network_access=network_access,
            local_model_access=local_model_access, timeout_seconds=timeout_seconds
        )
    except SandboxUnavailable as exc:
        # Do not retry timed-out work automatically: partial artifacts may exist.
        message = str(exc)
        timed_out = "timed out" in message.lower() or "timeout" in message.lower()
        return TaskResult("failed", error_code="sandbox_timeout" if timed_out else "sandbox_unavailable",
                          retryable=False,
                          evidence={"run_id": run_id,
                                    "failure_kind": "timeout" if timed_out else "sandbox_start",
                                    "message": message[:300]})
    evidence = {
        "run_id": run_id,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "sandbox_profile": outcome.profile,
        "elapsed_seconds": outcome.elapsed_seconds,
        "exit_code": outcome.returncode,
        "stdout_sha256": hashlib.sha256(outcome.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(outcome.stderr.encode("utf-8")).hexdigest(),
        "stdout_tail": _redact_output(outcome.stdout[-4000:]),
        "stderr_tail": _redact_output(outcome.stderr[-2000:]),
    }
    response = _last_json_object(outcome.stdout)
    if outcome.returncode != 0:
        error_code = response.get("error_code") if response else None
        return TaskResult("failed", error_code=error_code or f"process_exit_{outcome.returncode}",
                          retryable=outcome.returncode in {75}, evidence=evidence)
    if response is None or response.get("status") != "success":
        return TaskResult("failed", error_code="invalid_specialist_response",
                          evidence=evidence)
    valid, error = _verified_artifact(response)
    if not valid:
        return TaskResult("failed", error_code=error or "artifact_evaluation_failed",
                          evidence=evidence)
    output = {key: value for key, value in response.items() if key != "status"}
    evidence["artifact_verified"] = bool(output.get("artifact_path"))
    evidence["execution_mode"] = "sandboxed"
    return TaskResult("succeeded", output, evidence=evidence)


def _run_pipeline_short(topic: str) -> TaskResult:
    args = ["--quality", "strong"]
    if topic:
        args.extend(["--topic", topic])
    result = _run_module("pipelines.short", args, network_access=False)
    if result.status != "succeeded":
        return result
    # A successful dry run must identify the procedural artifact and remain
    # explicitly non-publishable. A zero exit code alone is not acceptance.
    output = result.output
    if output.get("dry_run") is not True:
        return TaskResult("failed", error_code="pipeline_dry_run_contract_missing",
                          evidence=result.evidence)
    return result


def research_topic_collect(request: TaskRequest) -> TaskResult:
    payload = validate_topic_payload(request.payload)
    return _run_module(
        "app.autonomy.specialist_cli",
        ["research", "--topic", payload["topic"], "--max-sources", str(payload["max_sources"])],
        network_access=True,
        timeout_seconds=600,
    )


def _script_draft(request: TaskRequest, specialist: str) -> TaskResult:
    payload = validate_script_payload(request.payload)
    args = [specialist, "--topic", payload["topic"]]
    dependencies = request.context.get("dependencies", [])
    research_dependencies = [
        item for item in dependencies
        if item.get("task_type") == "research.topic.collect" and item.get("status") == "succeeded"
    ]
    if len(research_dependencies) > 1:
        return TaskResult("blocked", error_code="ambiguous_research_dependencies")
    if not research_dependencies:
        return TaskResult("blocked", error_code="research_dependency_required")
    if research_dependencies:
        output = research_dependencies[0].get("output", {})
        artifact_path = output.get("artifact_path")
        artifact_sha256 = output.get("artifact_sha256")
        if not artifact_path or not artifact_sha256:
            return TaskResult("blocked", error_code="research_dependency_missing_artifact")
        args.extend(["--research-artifact", str(artifact_path),
                     "--research-sha256", str(artifact_sha256)])
    return _run_module("app.autonomy.specialist_cli", args, network_access=True,
                       local_model_access=True, timeout_seconds=1800)


def short_script_draft(request: TaskRequest) -> TaskResult:
    return _script_draft(request, "short-script")


def longform_script_draft(request: TaskRequest) -> TaskResult:
    return _script_draft(request, "longform-script")


def generate_short(request: TaskRequest) -> TaskResult:
    if request.payload.get("dry_run", True) is not True:
        return TaskResult("blocked", error_code="non_dry_run_requires_separate_authorization")
    payload = validate_generation_payload(request.payload)
    return _run_pipeline_short(payload["topic"])


def generate_longform(request: TaskRequest) -> TaskResult:
    # The existing long-form entrypoint does not implement a safe dry-run mode.
    # Do not run it through the autonomy worker until that contract is complete.
    return TaskResult("blocked", error_code="longform_video_dry_run_not_implemented")


def publish_check(request: TaskRequest) -> TaskResult:
    return TaskResult(
        "blocked",
        {"reason": "external publishing is disabled in autonomous core",
         "requested": request.payload.get("target", "all")},
        error_code="external_action_guard",
    )


def validate_document_payload(payload: dict) -> dict:
    if set(payload) - {"title", "text"}:
        raise ValueError("document payload contains unsupported fields")
    title = str(payload.get("title", "Untitled"))[:200]
    content = payload.get("text")
    if not isinstance(content, str) or not 1 <= len(content) <= 32_000:
        raise ValueError("document text must contain 1..32000 characters")
    return {"title": title, "text": content}


def document_text_analyze(request: TaskRequest) -> TaskResult:
    payload = validate_document_payload(request.payload)
    content = payload["text"]
    words = re.findall(r"\b[\w'-]+\b", content.casefold())
    stop = {"the", "and", "for", "that", "with", "this", "from", "are", "was", "were",
            "have", "has", "had", "you", "your", "into", "its", "not", "but", "about",
            "what", "when", "where", "which", "will", "can", "their", "they", "them"}
    terms = Counter(word for word in words if len(word) > 3 and word not in stop)
    headings = [line.lstrip("#").strip()[:160] for line in content.splitlines()
                if line.lstrip().startswith("#")][:30]
    links = re.findall(r"https?://[^\s)\]>]+", content)
    output = {
        "title": payload["title"],
        "character_count": len(content),
        "word_count": len(words),
        "line_count": len(content.splitlines()),
        "heading_count": len(headings),
        "headings": headings,
        "link_count": len(links),
        "top_terms": [{"term": term, "count": count} for term, count in terms.most_common(15)],
    }
    return TaskResult("succeeded", output, evidence={"execution_mode": "in_process_deterministic"})


def validate_dataset_payload(payload: dict) -> dict:
    if set(payload) - {"rows"}:
        raise ValueError("dataset payload contains unsupported fields")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise ValueError("dataset must contain 1..500 rows")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("dataset rows must be objects")
    columns = set().union(*(row.keys() for row in rows))
    if not columns or len(columns) > 50:
        raise ValueError("dataset must contain 1..50 columns")
    if any(not isinstance(key, str) or len(key) > 80 for key in columns):
        raise ValueError("dataset column names must be strings up to 80 characters")
    return {"rows": rows}


def dataset_profile(request: TaskRequest) -> TaskResult:
    rows = validate_dataset_payload(request.payload)["rows"]
    columns = sorted(set().union(*(row.keys() for row in rows)))
    summary = []
    for column in columns:
        values = [row.get(column) for row in rows]
        present = [value for value in values if value is not None and value != ""]
        numeric = [float(value) for value in present
                   if isinstance(value, (int, float)) and not isinstance(value, bool)
                   and math.isfinite(float(value))]
        record = {
            "column": column,
            "non_missing": len(present),
            "missing": len(rows) - len(present),
            "distinct": len({json.dumps(value, sort_keys=True, default=str) for value in present}),
            "numeric": bool(present) and len(numeric) == len(present),
        }
        if record["numeric"]:
            record.update({
                "min": min(numeric),
                "max": max(numeric),
                "mean": round(statistics.fmean(numeric), 6),
                "median": statistics.median(numeric),
            })
        summary.append(record)
    return TaskResult("succeeded", {
        "row_count": len(rows),
        "column_count": len(columns),
        "columns": summary,
    }, evidence={"execution_mode": "in_process_deterministic"})



def _parse_csv_payload(payload: dict) -> dict:
    if set(payload) - {"csv_text", "delimiter"}:
        raise ValueError("CSV payload contains unsupported fields")
    text = payload.get("csv_text")
    if not isinstance(text, str) or not 1 <= len(text.encode("utf-8")) <= 48_000:
        raise ValueError("CSV text must contain 1..48000 UTF-8 bytes")
    delimiter = payload.get("delimiter", ",")
    if not isinstance(delimiter, str) or delimiter not in {",", ";", "\t", "|"}:
        raise ValueError("CSV delimiter must be comma, semicolon, tab or pipe")
    if "\x00" in text:
        raise ValueError("CSV text contains a null byte")
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
        headers = reader.fieldnames
        if not headers or not 1 <= len(headers) <= 50:
            raise ValueError("CSV must contain 1..50 columns")
        normalized = [str(item or "").strip() for item in headers]
        if any(not item or len(item) > 80 for item in normalized):
            raise ValueError("CSV headers must be 1..80 characters")
        if len(set(normalized)) != len(normalized):
            raise ValueError("CSV headers must be unique")
        reader.fieldnames = normalized
        rows = []
        for row in reader:
            if None in row:
                raise ValueError("CSV row contains more values than its header")
            if len(rows) >= 500:
                raise ValueError("CSV may contain at most 500 data rows")
            converted = {}
            for key, value in row.items():
                if value is None or value == "":
                    converted[key] = None
                    continue
                if len(value) > 2_000:
                    raise ValueError("CSV cell exceeds 2000 characters")
                candidate = value.strip()
                if re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", candidate):
                    number = float(candidate)
                    if math.isfinite(number):
                        converted[key] = int(number) if number.is_integer() and "." not in candidate else number
                        continue
                converted[key] = value
            rows.append(converted)
        if not rows:
            raise ValueError("CSV must contain at least one data row")
    except csv.Error:
        raise ValueError("CSV structure is malformed") from None
    return {"rows": rows, "delimiter": delimiter}


def validate_csv_payload(payload: dict) -> dict:
    parsed = _parse_csv_payload(payload)
    return {"csv_text": payload["csv_text"], "delimiter": parsed["delimiter"]}


def csv_dataset_profile(request: TaskRequest) -> TaskResult:
    payload = _parse_csv_payload(request.payload)
    result = dataset_profile(TaskRequest(
        task_type="data.dataset.profile",
        payload={"rows": payload["rows"]},
    ))
    return TaskResult(
        "succeeded",
        {**result.output, "source_format": "csv", "delimiter": payload["delimiter"]},
        evidence={"execution_mode": "in_process_deterministic", "input_format": "csv"},
    )
