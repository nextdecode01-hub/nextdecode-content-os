#!/usr/bin/env python3
"""One shared publishing authorization boundary for every Shorts Studio route.

``approval_integrity`` still owns the primitives (file digests, IST-day expiry, the
20:00 window).  This module is the only place that decides whether content may leave
the machine, so no publisher, orchestrator or CLI can define its own policy.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.security.approval_integrity import approved_today, sha256_file, upload_window_open
from app.visuals.visual_quality import has_publishable_visuals

ROOT = Path(__file__).resolve().parents[2]
POLICY_VERSION = "1"

__all__ = [
    "POLICY_VERSION",
    "PublishNotAuthorized",
    "authorize_publish",
    "verify_approval_binding",
    "verify_protected_action_decision",
    "authorization_error",
    "DEFAULT_DESTINATION",
    "ALLOWED_DESTINATIONS",
    "GOVERNED_ENTRY_PURPOSES",
    "backfill_line_sha256",
]


class PublishNotAuthorized(RuntimeError):
    """Raised instead of publishing.  ``code`` keeps the machine-readable reason."""

    def __init__(self, reason: str, *, code: str = "blocked_approval", violations=None):
        super().__init__(reason)
        self.reason = reason
        self.code = code
        self.violations = list(violations or [])


PACKAGES = {
    "short": {
        "approval": ("data", "review_approved.json"),
        "metadata": ("data", "metadata.json"),
        "video": ("outputs", "output_short.mp4"),
    },
    "longform": {
        "approval": ("data", "longform_review_approved.json"),
        "metadata": ("data", "longform_metadata.json"),
        "video": ("outputs", "output_longform.mp4"),
    },
}

# Instagram, Facebook and the social adapters have no private state: the publish
# call itself is the owner-approved act.  YouTube destinations are explicit.
PRIVATE_CAPABLE_PLATFORMS = frozenset({"youtube", "youtube_longform"})
ALLOWED_DESTINATIONS = ("private", "unlisted", "public")
DEFAULT_DESTINATION = "private"

APPROVED_STORYBOARD_STATUSES = frozenset({"auto_approved", "human_approved"})
# Allow-list: anything missing, null, empty, malformed or unrecognized fails closed.
PERMITTED_RIGHT_STATUSES = frozenset({"permitted"})
PRODUCTION_QUALITY = "strong"
BLOCKING_CLAIM_STATUSES = frozenset({"unsupported", "outdated", "unverified", "conflicting"})
BLOCKING_EVIDENCE_FLAGS = frozenset({
    "unsupported_factual",
    "evidence_missing",
    "evidence_ledger_absent",
    "evidence_reference_invalid",
    "evidence_unsupported_status",
    # A claim still marked for review has not been verified, so it blocks under the
    # approved missing/unverified-evidence policy rather than shipping as "flagged".
    "evidence_needs_review",
})
BLOCKING_SHOT_FLAGS = BLOCKING_EVIDENCE_FLAGS


def _load_json(path: Path, label: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PublishNotAuthorized(f"{label} is missing: {path}") from None
    except OSError:
        raise PublishNotAuthorized(f"{label} is unreadable: {path}") from None
    except (ValueError, json.JSONDecodeError):
        raise PublishNotAuthorized(f"{label} is malformed: {path}") from None
    if not isinstance(payload, dict):
        raise PublishNotAuthorized(f"{label} is malformed: {path}")
    return payload


def _digest(path: Path, label: str) -> str:
    if not path.is_file():
        raise PublishNotAuthorized(f"{label} is missing: {path}")
    try:
        return sha256_file(path)
    except OSError:
        raise PublishNotAuthorized(f"{label} is unreadable: {path}") from None


def _approval_records(*, data_root: Path, purpose: str) -> tuple[dict, dict]:
    pointer = _load_json(data_root / Path(*PACKAGES[purpose]["approval"]), "Approval record")
    package_path = str(pointer.get("package") or "").strip()
    if not package_path:
        raise PublishNotAuthorized("Approval record does not name its review package")
    package = _load_json(Path(package_path), "Review package")
    if purpose == "short":
        decision_path = str(pointer.get("decision_record") or "").strip()
        if not decision_path:
            raise PublishNotAuthorized("Approval pointer does not name an immutable decision record")
        decision_digest = _digest(Path(decision_path), "Approval decision record")
        if pointer.get("decision_record_sha256") != decision_digest:
            raise PublishNotAuthorized("Approval decision record digest mismatch")
        approval = _load_json(Path(decision_path), "Approval decision record")
        if approval.get("status") != "approved" or pointer.get("status") != "approved":
            raise PublishNotAuthorized("Review decision is not approved")
        if approval.get("package") != package_path:
            raise PublishNotAuthorized("Approval decision is bound to a different review package")
        if package.get("status") != "pending_human_review":
            raise PublishNotAuthorized("Original review package is not an immutable pending snapshot")
        if approval.get("review_package_sha256") != _digest(Path(package_path), "Review package"):
            raise PublishNotAuthorized("Review package changed after human approval")
        if not str(approval.get("reviewer") or "").strip():
            raise PublishNotAuthorized("Approval decision has no accountable reviewer identity")
        if not str(approval.get("rationale") or "").strip():
            raise PublishNotAuthorized("Approval decision has no rationale")
        checklist = approval.get("checklist")
        required_checks = (
            "two_sources_checked", "primary_source_checked",
            "real_demo_or_original_visual", "limitation_stated",
            "captions_audio_and_9x16_checked", "platform_copy_checked",
            "publish_approved",
        )
        if not isinstance(checklist, dict) or any(checklist.get(name) is not True for name in required_checks):
            raise PublishNotAuthorized("Approval decision checklist is incomplete")
        if approval.get("purpose") != "short" or approval.get("platform") != "youtube" or approval.get("destination") != "private":
            raise PublishNotAuthorized("Approval decision scope is not the authorized private YouTube short")
    else:
        approval = pointer
        if approval.get("status") != "approved" or package.get("status") != "approved":
            raise PublishNotAuthorized("Review package is not marked approved")
        if approval.get("approved_at") != package.get("approved_at"):
            raise PublishNotAuthorized("Approval record and review package disagree")
    if not approved_today(approval.get("approved_at")):
        raise PublishNotAuthorized(
            "Approval is missing or expired for today (Asia/Kolkata); approve the current package again")
    return approval, package


def _bind_artifacts(*, approval: dict, package: dict, metadata: dict,
                    metadata_file: Path, video_file: Path) -> dict:
    digests = {
        "metadata_sha256": _digest(metadata_file, "Generated metadata"),
        "video_sha256": _digest(video_file, "Rendered video"),
    }
    for name, value in digests.items():
        if approval.get(name) != value or package.get(name) != value:
            raise PublishNotAuthorized(
                f"Approval does not match the current {'metadata' if name.startswith('metadata') else 'video'}; "
                "create a fresh review package and approve it again")
    for field in ("title", "hook", "content_pillar"):
        if package.get(field) not in (None, metadata.get(field)) or approval.get(field) not in (None, metadata.get(field)):
            raise PublishNotAuthorized(
                f"The approved review package does not match the current generated {field.replace('_', ' ')}")
    if "visuals" in package and package.get("visuals") != metadata.get("visuals"):
        raise PublishNotAuthorized(
            "The approved review package describes different visuals than the current artifact")
    return digests


# Publishable governance stamps are produced only by governed producers:
# pipelines/short.py::main (receipt-backed orchestrated strong runs), the
# longform pipeline (anchored by the longform approval binding) and the
# owner-run backfill utility (external hash-chained receipt journal).
GOVERNED_ENTRY_PURPOSES = {
    "orchestrated": frozenset({"short"}),
    "longform": frozenset({"longform"}),
    "legacy-backfill": frozenset({"short", "longform"}),  # purpose-gated by the binding
}


def backfill_line_sha256(raw_line: str) -> str:
    """Digest of one raw journal line (without its trailing newline).

    Shared by the validator below and by the backfill utility, so both sides
    always use the identical hash-chain definition.
    """
    return hashlib.sha256(raw_line.encode("utf-8")).hexdigest()


def _run_manifest_receipt(*, root: Path, run_id: str, metadata_digest: str) -> None:
    """Cross-check an orchestrated stamp against the append-only run manifest.

    run_tracker guarantees this receipt: ``record_artifact`` refuses duplicate
    registrations, promotion refuses digest drift ("hash changed after
    recording"), and a failed run is never marked ``ok``.  Same-domain
    limitation: this hardens the self-attested stamp; the approval digest
    binding above remains the final anchor of artifact identity.
    """
    manifest_path = root / "outputs" / "runs" / run_id / "manifest.json"
    try:
        manifest = _load_json(manifest_path, "Run manifest")
    except PublishNotAuthorized:
        raise PublishNotAuthorized(
            f"Governance run receipt is missing or unreadable for run {run_id}",
            code="blocked_governance") from None
    if manifest.get("run_id") != run_id:
        raise PublishNotAuthorized(
            "Run manifest does not describe the stamped run", code="blocked_governance")
    if manifest.get("status") != "ok" or (
            (manifest.get("promotion") or {}).get("status") != "completed"):
        raise PublishNotAuthorized(
            f"Run {run_id} is not a completed governed run; its artifacts are draft-only",
            code="blocked_governance")
    recorded = (manifest.get("artifacts") or {}).get("metadata") or {}
    if str(recorded.get("sha256") or "") != metadata_digest:
        raise PublishNotAuthorized(
            "Run receipt does not match the current metadata digest; regenerate the artifact",
            code="blocked_governance")


def _backfill_journal_receipt(*, metadata: dict, root: Path, ref: str, digests: dict, purpose: str) -> None:
    """Legacy artifacts authorize only against an external hash-chained receipt.

    The in-file stamp carries a ``receipt_ref`` only — never digests — so no
    in-file field is self-validating.  Trust lives in the owner-run journal
    ``data/governance_backfill.jsonl`` and its two-record protocol:

      * ``stamp-commit`` line: digests of the metadata payload WITH the
        governance stamp but WITHOUT ``receipt_ref`` (canonical serialization),
        plus the video digest, purpose, timestamp, owner_note, prev_sha256.
      * ``stamped-artifact`` line: ``receipt_ref`` (the sha256 of the
        stamp-commit line), the digests of the final stamped bytes,
        ``prev_sha256`` = stamp-commit line digest.

    The chain is tamper-EVIDENT, not tamper-proof: any edit, splice or rebuild
    fails the end-to-end re-hash.  Same-domain limitation (documented trust
    boundary): an operator able to rewrite the journal in place *and*
    recompute the chain is outside the hash-chain model — that is guarded
    operationally (owner-only file permissions, append-only workflow, and the
    owner re-approval that must precede every backfill).

    The final digest is never taken on trust from the artifact line: the
    validator re-derives the expected stamped bytes from the commit binding and
    compares against the live artifact digests.
    """
    ref = str(ref or "").strip().lower()
    journal_path = root / "data" / "governance_backfill.jsonl"
    try:
        raw = journal_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        raise PublishNotAuthorized(
            "Legacy-backfill receipt journal is missing or unreadable, "
            "and metadata without a receipt journal is never trusted automatically",
            code="blocked_governance") from None
    lines = [line for line in raw.splitlines() if line.strip()]
    if not lines:
        raise PublishNotAuthorized(
            "Legacy-backfill receipt journal is empty", code="blocked_governance")
    if len(ref) != 64:
        raise PublishNotAuthorized(
            "Legacy-backfill stamp carries no valid receipt reference", code="blocked_governance")

    commit_line = None
    commit_line_digest = None
    artifact_line = None
    prev = ""
    for raw_line in lines:
        try:
            record = json.loads(raw_line)
        except (TypeError, ValueError, json.JSONDecodeError):
            raise PublishNotAuthorized(
                "Legacy-backfill receipt journal is malformed", code="blocked_governance") from None
        if not isinstance(record, dict) or record.get("prev_sha256") != prev or \
                record.get("kind") not in {"stamp-commit", "stamped-artifact"}:
            raise PublishNotAuthorized(
                "Legacy-backfill receipt chain fails the hash-chain check", code="blocked_governance")
        digest = backfill_line_sha256(raw_line)
        if digest == ref and record.get("kind") == "stamp-commit":
            commit_line = record
            commit_line_digest = digest
        elif record.get("kind") == "stamped-artifact" and record.get("receipt_ref") == ref:
            artifact_line = record
        prev = digest
    if commit_line is None or artifact_line is None or \
            artifact_line.get("prev_sha256") != commit_line_digest:
        raise PublishNotAuthorized(
            "Legacy-backfill receipt reference does not match the journal",
            code="blocked_governance")

    # Bind the stamp-commit line to this exact payload: recompute the canonical
    # serialization of the live metadata with receipt_ref removed (the same
    # rule the backfill utility used to produce the commit line) and require
    # identical digests — no in-file field can fake this binding.
    bind_payload = json.loads(json.dumps(metadata))
    bind_governance = bind_payload.get("governance")
    if not isinstance(bind_governance, dict) or "receipt_ref" not in bind_governance:
        raise PublishNotAuthorized(
            "Legacy-backfill stamp does not carry a receipt reference", code="blocked_governance")
    if str(commit_line.get("purpose") or "") != purpose:
        raise PublishNotAuthorized(
            "Legacy-backfill receipt journal was not authored for this publish purpose",
            code="blocked_governance")
    bind_governance.pop("receipt_ref")
    commit_digest = backfill_line_sha256(json.dumps(bind_payload, indent=2) + "\n")
    if str(commit_line.get("metadata_sha256") or "") != commit_digest:
        raise PublishNotAuthorized(
            "Legacy-backfill receipt does not match the current metadata payload",
            code="blocked_governance")
    # ND-ENG-006-R7 hardening: never trust the artifact line's claimed final
    # digest — re-derive the expected stamped bytes from the commit binding
    # itself (canonical serialization plus the receipt ref) and compare that
    # derived digest against the live artifact digests.
    bind_governance["receipt_ref"] = str(ref or "").strip().lower()
    expected_final_digest = backfill_line_sha256(json.dumps(bind_payload, indent=2) + "\n")
    if str(expected_final_digest) != str(digests["metadata_sha256"]):
        raise PublishNotAuthorized(
            "Legacy-backfill receipt does not match the stamped metadata bytes",
            code="blocked_governance")
    # Defense in depth: the journal artifact-line claims must also agree with
    # the live stamped artifact bytes.
    if str(commit_line.get("video_sha256") or "") != str(digests["video_sha256"]) or \
            str(artifact_line.get("video_sha256") or "") != str(digests["video_sha256"]) or \
            str(artifact_line.get("metadata_sha256") or "") != str(digests["metadata_sha256"]):
        raise PublishNotAuthorized(
            "Legacy-backfill receipt does not match the current artifact digests",
            code="blocked_governance")


def _validate_governance(metadata: dict, *, purpose: str, digests: dict, root: Path) -> None:
    """Fail-closed governance validation (replaces the old ``_check_direct_entry``).

    There is no silent-acceptance path: a missing ``governance`` record — the
    former fail-open — blocks exactly like every other artifact-level failure.
    """
    governance = metadata.get("governance")
    if not isinstance(governance, dict):
        raise PublishNotAuthorized(
            "Artifact governance record is missing or malformed; "
            "publish only through the configured pipeline",
            code="blocked_governance")
    entry = str(governance.get("entry") or "").strip()
    purposes = GOVERNED_ENTRY_PURPOSES.get(entry)
    if governance.get("publishable") is not True or purposes is None:
        name = entry or "unlabeled"
        raise PublishNotAuthorized(
            f"Artifacts from the {name} entry point are draft-only; publish through the approved pipeline",
            code="blocked_governance")
    if purpose not in purposes:
        raise PublishNotAuthorized(
            f"Governance entry {entry!r} does not authorize {purpose} publishing",
            code="blocked_governance")
    if entry == "orchestrated":
        run_id = str(governance.get("run_id") or "").strip()
        if not run_id or run_id != str(metadata.get("run_id") or "").strip():
            raise PublishNotAuthorized(
                "Governance stamp run_id does not match the artifact run_id",
                code="blocked_governance")
        _run_manifest_receipt(root=root, run_id=run_id,
                              metadata_digest=digests["metadata_sha256"])
    elif entry == "legacy-backfill":
        _backfill_journal_receipt(metadata=metadata, root=root,
                                  ref=governance.get("receipt_ref"), digests=digests,
                                  purpose=purpose)


def _check_storyboard(metadata: dict) -> str:
    storyboard = metadata.get("storyboard")
    if not isinstance(storyboard, dict):
        raise PublishNotAuthorized("Storyboard review record is missing; render with the storyboard gate enabled")
    status = str(storyboard.get("review_status") or "blocked")
    approved = status in APPROVED_STORYBOARD_STATUSES or storyboard.get("human_approved") is True
    if not approved:
        reasons = "; ".join(str(item)[:120] for item in (storyboard.get("review_reasons") or [])[:3])
        raise PublishNotAuthorized(
            f"Storyboard review is not approved (status={status}): {reasons or 'no reasons recorded'}",
            code="blocked_review")
    return status


def _check_visuals(metadata: dict) -> None:
    if not has_publishable_visuals(metadata.get("visuals")):
        raise PublishNotAuthorized(
            "Procedural or unverified visuals are draft-only; publishing is blocked", code="blocked_quality")


def _check_short_render_quality(metadata: dict) -> None:
    """Require the actual Shorts render to satisfy its production contract."""
    qa = metadata.get("qa")
    if not isinstance(qa, dict) or qa.get("status") != "pass":
        raise PublishNotAuthorized(
            "Short render has no passing technical/editorial QA record",
            code="blocked_quality",
        )
    if metadata.get("captions_burned") is not True:
        raise PublishNotAuthorized(
            "Short render does not confirm burned-in captions",
            code="blocked_quality",
        )
    try:
        duration = float(qa.get("duration"))
        width = int(qa.get("width"))
        height = int(qa.get("height"))
        fps = float(qa.get("fps"))
    except (TypeError, ValueError):
        raise PublishNotAuthorized(
            "Short render QA metadata is incomplete or malformed",
            code="blocked_quality",
        ) from None
    if not 45.0 <= duration <= 60.0:
        raise PublishNotAuthorized(
            f"Short duration {duration:.2f}s is outside the 45-60s production target",
            code="blocked_quality",
        )
    if (width, height) != (1080, 1920) or abs(fps - 30.0) > 0.05:
        raise PublishNotAuthorized(
            "Short render must be 1080x1920 at 30 FPS",
            code="blocked_quality",
        )


def _evidence_violations(metadata: dict) -> list[str]:
    evidence = metadata.get("evidence")
    if not isinstance(evidence, dict):
        return ["evidence metadata is missing; regenerate with the research-backed pipeline"]
    violations: list[str] = []
    for flag in evidence.get("flags") or []:
        if isinstance(flag, dict) and str(flag.get("flag")) in BLOCKING_EVIDENCE_FLAGS:
            violations.append(f"{flag.get('flag')} on claim {flag.get('claim_id') or flag.get('sentence', '')[:60]}")
    for shot in metadata.get("shots") or []:
        if not isinstance(shot, dict):
            continue
        for flag in shot.get("evidence_flags") or []:
            if str(flag) in BLOCKING_SHOT_FLAGS:
                violations.append(f"shot {shot.get('shot_id', shot.get('index', '?'))}: {flag}")
    summary = evidence.get("summary")
    by_status = summary.get("by_status") if isinstance(summary, dict) else None
    if not isinstance(by_status, dict) or not by_status:
        violations.append("claim status summary is missing")
    else:
        for status, count in by_status.items():
            if str(status) in BLOCKING_CLAIM_STATUSES and isinstance(count, int) and count > 0:
                violations.append(f"{count} claim(s) are {status}")
    if isinstance(evidence.get("unmapped_factual"), list) and evidence["unmapped_factual"]:
        violations.append(f"{len(evidence['unmapped_factual'])} factual sentence(s) have no claim record")
    return violations


def _check_ledger_binding(evidence: dict, data_root: Path) -> None:
    if not isinstance(evidence, dict):
        return
    digest = str(evidence.get("ledger_sha256") or "")
    ledger_path = str(evidence.get("ledger_path") or "")
    if not digest or not ledger_path:
        raise PublishNotAuthorized("Claim ledger is not bound to this artifact", code="blocked_evidence")
    path = Path(ledger_path)
    if not path.is_absolute():
        path = data_root / path
    if _digest(path, "Claim ledger") != digest:
        raise PublishNotAuthorized(
            "Claim ledger changed after the script was generated; regenerate and re-approve",
            code="blocked_evidence")


def _rights_violations(metadata: dict) -> list[str]:
    evidence = metadata.get("evidence") or {}
    violations: list[str] = []
    cutouts = evidence.get("cutouts") if isinstance(evidence, dict) else None
    for item in cutouts or []:
        if not isinstance(item, dict):
            violations.append("cutout record is malformed")
            continue
        claim = str(item.get("claim_id") or item.get("scene_index", "?"))
        rights = item.get("reuse_rights")
        if not isinstance(rights, dict) or not str(rights.get("status") or "").strip():
            violations.append(f"cutout {claim}: reuse_rights is missing or empty")
        elif str(rights.get("status")) not in PERMITTED_RIGHT_STATUSES:
            violations.append(f"cutout {claim}: reuse_rights={rights.get('status')} is not a permitted basis")
    return violations


def _check_destination(platform: str, requested: str | None) -> dict:
    """Enforce the current deny-by-default public-distribution policy.

    Only private YouTube staging is permitted. Non-private YouTube destinations
    and platforms without a private destination are blocked until a separate,
    owner-approved public-publishing policy is implemented.
    """
    wanted = str(requested or "").strip().lower()

    if platform not in PRIVATE_CAPABLE_PLATFORMS:
        raise PublishNotAuthorized(
            f"Public publishing is disabled by policy for {platform}; no private destination exists",
            code="blocked_public_policy",
        )

    destination = wanted or DEFAULT_DESTINATION
    if destination not in ALLOWED_DESTINATIONS:
        raise PublishNotAuthorized(
            f"Unknown destination {destination!r}; expected one of {ALLOWED_DESTINATIONS}"
        )
    if destination != "private":
        raise PublishNotAuthorized(
            f"Destination {destination!r} is disabled by the public-publishing policy",
            code="blocked_public_policy",
        )

    return {"destination": "private", "public_release": None}


def authorize_publish(*, platform: str, purpose: str = "short", data_root=None,
                      metadata_file=None, video_file=None, destination: str | None = None,
                      require_window: bool = False, public_release_file=None) -> dict:
    """Return an authorization decision, or raise :class:`PublishNotAuthorized`.

    Validation is unconditional: a dry run is checked exactly like a live publish and
    only the network call is skipped by the caller.
    """
    if purpose not in PACKAGES:
        raise PublishNotAuthorized(f"Unknown publishing purpose {purpose!r}")
    if not str(platform or "").strip():
        raise PublishNotAuthorized("A platform name is required")

    root = Path(data_root) if data_root else ROOT
    spec = PACKAGES[purpose]
    metadata_path = Path(metadata_file) if metadata_file else root / Path(*spec["metadata"])
    video_path = Path(video_file) if video_file else root / Path(*spec["video"])

    approval, package = _approval_records(data_root=root, purpose=purpose)
    metadata = _load_json(metadata_path, "Generated metadata")
    digests = _bind_artifacts(approval=approval, package=package, metadata=metadata,
                              metadata_file=metadata_path, video_file=video_path)

    if str(metadata.get("quality") or "").strip().lower() != PRODUCTION_QUALITY:
        raise PublishNotAuthorized(
            f"Only the {PRODUCTION_QUALITY} pipeline may publish (artifact quality="
            f"{metadata.get('quality') or 'missing'!r})", code="blocked_quality")
    _validate_governance(metadata, purpose=purpose, digests=digests, root=root)
    _check_storyboard(metadata)
    _check_visuals(metadata)
    if purpose == "short":
        _check_short_render_quality(metadata)

    violations = _evidence_violations(metadata)
    if violations:
        raise PublishNotAuthorized(
            f"Research evidence is not publish-ready: {violations[0]} ({len(violations)} finding(s))",
            code="blocked_evidence", violations=violations)
    _check_ledger_binding(metadata.get("evidence"), root)

    rights = _rights_violations(metadata)
    if rights:
        raise PublishNotAuthorized(
            f"Reuse rights are not cleared: {rights[0]} ({len(rights)} finding(s))",
            code="blocked_rights", violations=rights)

    # public_release_file remains accepted for call compatibility, but
    # cannot grant public distribution while the separate owner policy is absent.
    target = _check_destination(str(platform), destination)
    if require_window and not upload_window_open():
        raise PublishNotAuthorized("Scheduled publishing is restricted to the 20:00 IST hour",
                                   code="blocked_schedule")

    # WP5 protected-action binding: this receipt identifies the exact action
    # scope and immutable artifact digests that passed the shared governance gate.
    # It is an integrity binding, not a bearer token or a substitute for rechecking
    # authorization immediately before each external transfer.
    decision = {
        "policy_version": POLICY_VERSION,
        "status": "authorized",
        "action_type": "publish",
        "platform": str(platform),
        "purpose": purpose,
        "destination": target["destination"],
        "public_release": target["public_release"],
        "approved_at": approval.get("approved_at"),
        "reviewer": approval.get("reviewer") or package.get("reviewer"),
        "metadata_file": str(metadata_path),
        "video_file": str(video_path),
        **digests,
    }
    binding_fields = (
        "policy_version", "action_type", "platform", "purpose", "destination",
        "approved_at", "reviewer", "metadata_sha256", "video_sha256",
    )
    canonical_binding = {key: decision[key] for key in binding_fields}
    decision["authorization_id"] = hashlib.sha256(
        json.dumps(canonical_binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return decision


def verify_protected_action_decision(decision: dict, *, platform: str,
                                     purpose: str) -> dict:
    """Verify the integrity and scope of a WP5 protected-action receipt.

    This does not create authority: callers must obtain the receipt from
    authorize_publish in the same operation. The digest-pinned upload snapshot
    remains mandatory after this check.
    """
    if not isinstance(decision, dict) or decision.get("status") != "authorized":
        raise PublishNotAuthorized("Protected-action receipt is missing or invalid",
                                   code="blocked_authorization")
    expected_scope = {
        "action_type": "publish",
        "platform": str(platform),
        "purpose": str(purpose),
        "destination": "private",
    }
    if any(decision.get(key) != value for key, value in expected_scope.items()):
        raise PublishNotAuthorized("Protected-action receipt scope mismatch",
                                   code="blocked_authorization")
    binding_fields = (
        "policy_version", "action_type", "platform", "purpose", "destination",
        "approved_at", "reviewer", "metadata_sha256", "video_sha256",
    )
    try:
        canonical_binding = {key: decision[key] for key in binding_fields}
    except KeyError:
        raise PublishNotAuthorized("Protected-action receipt is incomplete",
                                   code="blocked_authorization") from None
    expected_id = hashlib.sha256(
        json.dumps(canonical_binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if decision.get("authorization_id") != expected_id:
        raise PublishNotAuthorized("Protected-action receipt integrity mismatch",
                                   code="blocked_authorization")
    if any(len(str(decision.get(key) or "")) != 64 for key in
           ("metadata_sha256", "video_sha256")):
        raise PublishNotAuthorized("Protected-action artifact binding is malformed",
                                   code="blocked_authorization")
    return decision


def verify_approval_binding(*, data_root=None, purpose: str = "short",
                            metadata_file=None, video_file=None) -> str:
    """Approval-binding probe only: identity, freshness and hashes.

    This is deliberately narrower than :func:`authorize_publish`.  Callers that need to
    answer "does this approval still describe the current artifact?" get "" or a reason,
    without the rights, evidence, storyboard or destination policy.  Full governance lives
    in exactly one place.
    """
    root = Path(data_root) if data_root else ROOT
    if purpose not in PACKAGES:
        return f"Unknown publishing purpose {purpose!r}"
    spec = PACKAGES[purpose]
    metadata_path = Path(metadata_file) if metadata_file else root / Path(*spec["metadata"])
    video_path = Path(video_file) if video_file else root / Path(*spec["video"])
    try:
        approval, package = _approval_records(data_root=root, purpose=purpose)
        metadata = _load_json(metadata_path, "Generated metadata")
        _bind_artifacts(approval=approval, package=package, metadata=metadata,
                        metadata_file=metadata_path, video_file=video_path)
        if not has_publishable_visuals(metadata.get("visuals")):
            return "Procedural or unverified visuals are draft-only; publishing is blocked"
    except PublishNotAuthorized as exc:
        return exc.reason
    except OSError as exc:
        return f"Approval state is unreadable: {type(exc).__name__}"
    return ""


def authorization_error(exc: Exception) -> tuple[str, str]:
    """Map any authorization failure to a ``(code, reason)`` pair for JSON output."""
    if isinstance(exc, PublishNotAuthorized):
        return exc.code, exc.reason
    return "blocked_authorization", f"{type(exc).__name__}: {exc}"
