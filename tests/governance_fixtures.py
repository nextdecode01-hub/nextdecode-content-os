"""Fixture builders for publishing-governance tests.

Every fixture is a self-contained sandbox root so ``authorize_publish`` can bind real
digests without touching the repository's live ``data/`` or ``outputs/`` slots.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Synthetic run id used for the orchestrated stamp + run-manifest receipt that
# the fail-closed governance validation (ND-ENG-006) requires on the short path.
FIXTURE_RUN_ID = "20260101-000000-approval-fixture"

PUBLISHABLE_VISUALS = {
    "mode": "multi_shot_stock",
    "asset_count": 1,
    "shot_count": 1,
    "procedural_shot_count": 0,
    "providers": {"pixabay": 1},
    "assets": [{"provider": "pixabay", "title": "Grid control room",
                "license": "Pixabay Content License"}],
}


def approved_timestamp() -> str:
    return datetime.now(IST).isoformat()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publishable_metadata(*, ledger_relative_path="research/claim_ledger.json",
                         cutouts=None, rights_status="permitted") -> dict:
    return {
        "quality": "strong",
        "title": "NIST updates its AI risk framework",
        "hook": "NIST updated its framework",
        "voice_text": "NIST updated its framework.",
        "content_pillar": "What Changed",
        "created_at": approved_timestamp(),
        "storyboard": {"review_status": "auto_approved", "approved": True,
                       "review_required": False, "review_reasons": []},
        "captions_burned": True,
        "qa": {"status": "pass", "duration": 48.0, "width": 1080, "height": 1920,
               "fps": 30.0, "errors": [], "warnings": []},
        "visuals": dict(PUBLISHABLE_VISUALS),
        "evidence": {
            "flags": [],
            "summary": {"claims": 2, "by_status": {"supported": 2}},
            "ledger_path": ledger_relative_path,
            "ledger_sha256": "",
            "rights_gate": {"checked": 0, "blocked": 0, "publish_ready": True,
                            "blocked_claim_ids": []},
            "cutouts": list(cutouts or []),
            "unmapped_factual": [],
        },
        "shots": [{"index": 0, "shot_id": "s00", "evidence_flags": [],
                   "evidence_claim_ids": ["clm_0001"]}],
    }


def permitted_cutout(claim_id="clm_0001", status="permitted") -> dict:
    rights = None if status is None else {"status": status, "basis": "open licence",
                                          "attribution": "example.gov"}
    record = {"claim_id": claim_id, "scene_index": 0}
    if rights is not None:
        record["reuse_rights"] = rights
    return record


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _governance_stamp(purpose: str) -> tuple[dict, str | None]:
    """Governance stamp for the sandbox payload + its synthetic run id (short)."""
    if purpose == "longform":
        return {"entry": "longform", "publishable": True, "stamped_at": _utc_stamp()}, None
    return {"entry": "orchestrated", "publishable": True,
            "run_id": FIXTURE_RUN_ID, "stamped_at": _utc_stamp()}, FIXTURE_RUN_ID


def _write_run_receipt(root: Path, run_id: str, metadata_file: Path, video_file: Path) -> Path:
    """Synthetic completed run manifest so the receipt cross-check passes."""
    metadata_sha = _digest(metadata_file)
    video_sha = _digest(video_file)
    run_dir = root / "outputs" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "schema_version": 1,
        "status": "ok",
        "quality": "strong",
        "topic": "governance fixture",
        "artifacts": {
            "metadata": {"path": "metadata.json", "sha256": metadata_sha,
                         "bytes": metadata_file.stat().st_size, "stage": "fixture"},
            "video": {"path": "output_short.mp4", "sha256": video_sha,
                      "bytes": video_file.stat().st_size, "stage": "fixture"},
        },
        "stages": [],
        "failure": None,
        "promotion": {"status": "completed",
                      "targets": {"metadata": metadata_sha, "video": video_sha},
                      "journal_path": str(root / "data" / "runs" / "promotions" / f"{run_id}.json")},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (root / "data" / "runs").mkdir(parents=True, exist_ok=True)
    (root / "data" / "runs" / "index.jsonl").open("a", encoding="utf-8").write(
        json.dumps({"run_id": run_id, "status": "ok", "topic": "governance fixture"}) + "\n")
    return run_dir / "manifest.json"


def build_sandbox(root: Path, *, metadata=None, video_bytes=b"video-bytes",
                  purpose="short", approved_at=None, public_release=None,
                  mutate_metadata=None, mutate_approval=None,
                  stamp_governance=True) -> dict:
    """Create an approved, hash-consistent publishing sandbox and return its paths."""
    root = Path(root)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "outputs").mkdir(parents=True, exist_ok=True)
    (root / "research").mkdir(parents=True, exist_ok=True)

    ledger = root / "research" / "claim_ledger.json"
    ledger.write_text(json.dumps({"claims": [{"claim_id": "clm_0001", "status": "supported"}]}),
                      encoding="utf-8")

    payload = metadata if metadata is not None else publishable_metadata()
    payload = json.loads(json.dumps(payload))
    if isinstance(payload.get("evidence"), dict):
        payload["evidence"]["ledger_sha256"] = _digest(ledger)
    if mutate_metadata:
        mutate_metadata(payload)
    # ND-ENG-006 fail-closed governance: sandbox artifacts carry the publishable
    # stamp (plus its run receipt on the short path) — but any caller-supplied
    # governance key (even a malformed one, for negative tests) is preserved.
    if stamp_governance and "governance" not in payload:
        payload["governance"], run_id = _governance_stamp(purpose)
        if run_id:
            payload["run_id"] = run_id
    elif stamp_governance and isinstance(payload.get("governance"), dict) and \
            purpose == "short" and \
            payload["governance"].get("entry") == "orchestrated" and \
            payload["governance"].get("run_id"):
        payload.setdefault("run_id", payload["governance"]["run_id"])

    if purpose == "longform":
        metadata_file = root / "data" / "longform_metadata.json"
        video_file = root / "outputs" / "output_longform.mp4"
        approval_file = root / "data" / "longform_review_approved.json"
    else:
        metadata_file = root / "data" / "metadata.json"
        video_file = root / "outputs" / "output_short.mp4"
        approval_file = root / "data" / "review_approved.json"

    metadata_file.write_text(json.dumps(payload), encoding="utf-8")
    video_file.write_bytes(video_bytes)

    # Short-path orchestrated stamps require the run receipt the validator
    # reads (records the sha256 of the FINAL, stamped metadata bytes).
    if isinstance(payload.get("governance"), dict) and \
            payload["governance"].get("entry") == "orchestrated" and \
            payload["governance"].get("publishable") is True and \
            str(payload["governance"].get("run_id") or ""):
        _write_run_receipt(root, str(payload["governance"]["run_id"]),
                           metadata_file, video_file)

    package = {
        "status": "pending_human_review" if purpose == "short" else "approved",
        "title": payload.get("title"),
        "visuals": payload.get("visuals"),
        "metadata_sha256": _digest(metadata_file),
        "video_sha256": _digest(video_file),
    }
    if purpose != "short":
        package["approved_at"] = approved_at or approved_timestamp()
    package_file = root / "data" / "review_package.json"
    package_file.write_text(json.dumps(package), encoding="utf-8")

    if purpose == "short":
        decision = {
            "status": "approved",
            "approved_at": approved_at or approved_timestamp(),
            "reviewer": "owner",
            "rationale": "Hermetic publishing-governance fixture",
            "purpose": "short",
            "platform": "youtube",
            "destination": "private",
            "checklist": {name: True for name in (
                "two_sources_checked", "primary_source_checked",
                "real_demo_or_original_visual", "limitation_stated",
                "captions_audio_and_9x16_checked", "platform_copy_checked",
                "publish_approved")},
            "package": str(package_file),
            "review_package_sha256": _digest(package_file),
            "metadata_sha256": package["metadata_sha256"],
            "video_sha256": package["video_sha256"],
        }
        decisions_dir = root / "data" / "review_approvals"
        decisions_dir.mkdir(parents=True, exist_ok=True)
        decision_path = decisions_dir / "fixture-approval.json"
        decision_path.write_text(json.dumps(decision), encoding="utf-8")
        approval = {
            "status": "approved",
            "package": str(package_file),
            "decision_record": str(decision_path),
            "decision_record_sha256": _digest(decision_path),
        }
    else:
        approval = {
            "status": "approved",
            "approved_at": package["approved_at"],
            "reviewer": "owner",
            "package": str(package_file),
            "metadata_sha256": package["metadata_sha256"],
            "video_sha256": package["video_sha256"],
        }
    if mutate_approval:
        mutate_approval(approval)
    approval_file.write_text(json.dumps(approval), encoding="utf-8")

    release_file = root / "data" / "public_release_approved.json"
    if public_release:
        release_file.write_text(json.dumps({
            "status": "approved", "owner": "owner", "approved_at": approved_timestamp(),
            "metadata_sha256": approval["metadata_sha256"],
            "video_sha256": approval["video_sha256"],
        }), encoding="utf-8")

    return {"root": root, "metadata": metadata_file, "video": video_file,
            "approval": approval_file, "package": package_file, "ledger": ledger,
            "public_release": release_file}
