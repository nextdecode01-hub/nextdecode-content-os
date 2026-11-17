"""Pre-render storyboard and contact-sheet review gate.

This module does not replace the scene brief or the renderer.  It persists the
resolved scene plan, builds a contact sheet from the selected assets, and makes
the review state explicit before a full render starts.  It uses FFmpeg only,
so no new image/vision framework is required.

Environment:
    STORYBOARD_GATE=off      skip storyboard generation
    STORYBOARD_GATE=warn     generate and warn (explicit opt-out of the review gate)
    STORYBOARD_GATE=require  raise when review_status != auto_approved (default)
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WIDTH, HEIGHT = 1080, 1920
THUMB_WIDTH, THUMB_HEIGHT = 270, 480
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
APPROVED_STATUSES = {"auto_approved"}
PROVIDER_SHORT = {
    "motion_graphic": "CARD",
    "pixabay": "PIX",
    "coverr": "CVR",
    "openverse": "OV",
    "wikimedia": "WIKI",
    "pollinations": "AI",
    "gemini": "AI",
    "fal": "AI",
    "replicate": "AI",
    "openai": "AI",
    "cloudflare": "AI",
    "gradient": "GRAD",
    "procedural": "PROC",
}


def _safe_label(value: object, limit: int = 12) -> str:
    text = re.sub(r"[^A-Za-z0-9 _-]+", "", str(value or "").upper())
    return text.strip()[:limit] or "UNKNOWN"


def _sha256(path: Path) -> str:
    try:
        digest = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return ""


def _scene_digest(records: list[dict]) -> str:
    """Hash the reviewed scene plan so an approval cannot outlive an edit."""
    payload = [
        {
            "scene_id": record.get("scene_id"),
            "narration": record.get("narration"),
            "asset_path": record.get("asset_path"),
            "claim_ids": record.get("claim_ids"),
            "evidence_visual": record.get("evidence_visual"),
        }
        for record in records
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _file_time(path: Path) -> str:
    try:
        return datetime.fromtimestamp(Path(path).stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return ""


def _thumb_filter(scene_id: str, provider: str, confidence: str) -> str:
    label_one = _safe_label(scene_id, 6)
    short = PROVIDER_SHORT.get(str(provider or "").lower(), _safe_label(provider, 8))
    conf_short = {"high": "HIGH", "medium": "MED", "low": "LOW",
                  "none": "NONE", "unknown": "UNK"}.get(str(confidence).lower(), "UNK")
    label_two = _safe_label(f"{short} {conf_short}", 14)
    font = str(FONT_PATH)
    return (
        f"scale={THUMB_WIDTH}:{THUMB_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={THUMB_WIDTH}:{THUMB_HEIGHT},setsar=1,"
        f"drawtext=fontfile={font}:text='{label_one}':x=8:y=8:fontsize=22:"
        "fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=4,"
        f"drawtext=fontfile={font}:text='{label_two}':x=8:y=38:fontsize=15:"
        "fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=3"
    )


def _make_thumb(asset_path: Path | None, out_path: Path, scene_id: str,
                provider: str, confidence: str) -> bool:
    vf = _thumb_filter(scene_id, provider, confidence)
    if asset_path and Path(asset_path).is_file():
        suffix = Path(asset_path).suffix.lower()
        if suffix in VIDEO_SUFFIXES:
            commands = [
                ["ffmpeg", "-y", "-ss", "0.5", "-i", str(asset_path),
                 "-frames:v", "1", "-vf", vf, str(out_path)],
                ["ffmpeg", "-y", "-i", str(asset_path),
                 "-frames:v", "1", "-vf", vf, str(out_path)],
            ]
        else:
            commands = [
                ["ffmpeg", "-y", "-i", str(asset_path),
                 "-frames:v", "1", "-vf", vf, str(out_path)]
            ]
    else:
        commands = [
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", f"color=c=0x0b1220:s={THUMB_WIDTH}x{THUMB_HEIGHT}:r=1",
             "-frames:v", "1", "-vf", vf, str(out_path)]
        ]
    for command in commands:
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except Exception:
            continue
        if completed.returncode == 0 and out_path.is_file() and out_path.stat().st_size > 1000:
            return True
    return False


def _blank_thumb(path: Path) -> Path | None:
    command = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=0x0b1220:s={THUMB_WIDTH}x{THUMB_HEIGHT}:r=1",
        "-frames:v", "1", str(path),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    except Exception:
        return None
    return path if completed.returncode == 0 and path.is_file() else None


def _make_contact_sheet(thumbs: list[Path], out_path: Path) -> bool:
    """Compose thumbnails with xstack.

    ``tile`` can drop frames on partial image sequences in this FFmpeg build,
    so pad to a multiple of four and stack explicitly.
    """
    valid = [path for path in thumbs if path and Path(path).is_file()]
    if not valid:
        return False
    target = max(4, ((len(valid) + 3) // 4) * 4)
    blank = _blank_thumb(out_path.parent / "blank_tile.png")
    if not blank and target > len(valid):
        return False
    padded = valid + ([blank] * (target - len(valid)) if blank else [])
    if len(padded) != target or target % 4:
        return False
    columns = 4
    layout = "|".join(
        f"{(index % columns) * THUMB_WIDTH}_{(index // columns) * THUMB_HEIGHT}"
        for index in range(target)
    )
    inputs: list[str] = []
    for path in padded:
        inputs.extend(["-i", str(path)])
    outputs = "".join(f"[{index}:v]" for index in range(target))
    command = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", f"{outputs}xstack=inputs={target}:layout={layout}:fill=0x0b1220[out]",
        "-map", "[out]", "-frames:v", "1", "-q:v", "2", str(out_path),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except Exception:
        return False
    return completed.returncode == 0 and out_path.is_file() and out_path.stat().st_size > 1000


def _make_motion_thumb(shot_file: Path, out_path: Path, seconds: float,
                       label: str, detail: str = "") -> bool:
    font = str(FONT_PATH)
    vf = (
        f"scale={THUMB_WIDTH}:{THUMB_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={THUMB_WIDTH}:{THUMB_HEIGHT},setsar=1,"
        f"drawtext=fontfile={font}:text='{_safe_label(label, 14)}':x=8:y=8:fontsize=20:"
        "fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=4"
    )
    if detail:
        vf += (
            f",drawtext=fontfile={font}:text='{_safe_label(detail, 18)}':x=8:y=36:"
            "fontsize=14:fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=3"
        )
    command = [
        "ffmpeg", "-y", "-ss", f"{max(0.0, seconds):.2f}", "-i", str(shot_file),
        "-frames:v", "1", "-vf", vf, str(out_path),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    except Exception:
        return False
    return completed.returncode == 0 and out_path.is_file() and out_path.stat().st_size > 1000


def build_motion_contact_sheet(shot_files: list[Path], shots: list[dict],
                               work_dir: Path) -> str:
    """Start/mid/end frames for every rendered shot, as one review image.

    This is a post-render motion check, separate from the pre-render asset
    storyboard.  Two shots per row, three frames each.
    """
    work = Path(work_dir) / "storyboard"
    work.mkdir(parents=True, exist_ok=True)
    frames_dir = work / "motion_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    thumbs: list[Path] = []
    for position, shot_file in enumerate(shot_files):
        shot = shots[position] if position < len(shots) else {}
        index = int(shot.get("index", position) or 0)
        duration = max(0.4, float(shot.get("duration") or 1.0))
        times = (0.12, duration / 2.0, max(0.15, duration - 0.20))
        motion = shot.get("motion") or {}
        profile = str(motion.get("profile") or "")
        shot_id = str(shot.get("shot_id") or f"s{index:02d}")
        for phase, seconds in zip(("START", "MID", "END"), times):
            out = frames_dir / f"motion_{position:03d}_{phase.lower()}.png"
            detail = profile if phase == "START" else ""
            ok = _make_motion_thumb(
                Path(shot_file), out, seconds, f"{shot_id} {phase}", detail
            )
            if not ok:
                ok = bool(_blank_thumb(out))
            thumbs.append(out)

    columns = 6
    target = max(columns, ((len(thumbs) + columns - 1) // columns) * columns)
    blank = _blank_thumb(work / "blank_tile.png")
    if not blank and target > len(thumbs):
        return ""
    padded = thumbs + ([blank] * (target - len(thumbs)) if blank else [])
    layout = "|".join(
        f"{(index % columns) * THUMB_WIDTH}_{(index // columns) * THUMB_HEIGHT}"
        for index in range(target)
    )
    inputs: list[str] = []
    for path in padded:
        inputs.extend(["-i", str(path)])
    outputs = "".join(f"[{index}:v]" for index in range(target))
    out_path = work / "motion_sheet.jpg"
    command = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", f"{outputs}xstack=inputs={target}:layout={layout}:fill=0x0b1220[out]",
        "-map", "[out]", "-frames:v", "1", "-q:v", "2", str(out_path),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except Exception:
        return ""
    if completed.returncode != 0 or not out_path.is_file() or out_path.stat().st_size <= 1000:
        return ""
    return str(out_path)


def _review_reasons(scene: dict, detail: dict, path: Path | None) -> list[str]:
    reasons: list[str] = []
    provider = str(detail.get("provider") or "")
    if not path:
        reasons.append("no usable selected asset")
    if not provider:
        reasons.append("provider missing")
    if provider == "procedural":
        reasons.append("procedural source")
    if provider == "gradient":
        reasons.append("gradient caption fallback")
    if provider in {"pixabay", "coverr", "wikimedia", "openverse", "ai_image"} and not (detail.get("vision_review") or {}).get("checked"):
        reasons.append("external visual has not received a successful visual review")
    if detail.get("fallback_reason"):
        reasons.append(f"fallback: {detail['fallback_reason']}")
    if detail.get("visual_quality") == "low_light":
        reasons.append("low-light/flat asset")
    confidence = str(detail.get("relevance_confidence") or "unknown")
    if confidence in {"low", "none"}:
        reasons.append(f"{confidence} relevance confidence")
    if detail.get("semantic_review"):
        reasons.append(str(detail.get("review_reason") or "lexical match needs visual review"))
    if detail.get("vision_review", {}).get("checked"):
        verdict = str(detail["vision_review"].get("relevance") or "")
        quality = str(detail["vision_review"].get("quality") or "unknown")
        if verdict and verdict != "high":
            reasons.append(f"vision review: {verdict} relevance")
        if quality == "low":
            reasons.append("vision review: low visual quality")
    return reasons


def build_storyboard(shots: list[dict], details: list[dict], work_dir: Path, *,
                     planner: dict | None = None, title: str = "",
                     evidence: dict | None = None) -> dict:
    """Write storyboard.json and a contact sheet from resolved scene assets.

    ``evidence`` links scenes to claim-ledger records:
    ``{"scene_claims": {index: [claim, ...]}, "cutouts": {index: cutout},
    "script_sha256": ..., "ledger_sha256": ...}``.  Without it the storyboard is
    still produced, but every scene is reported as having no evidence link.
    """
    if planner is None:
        from app.visuals.chain import plan_scenes
        planner = plan_scenes(shots)
    evidence = evidence or {}
    scene_claims = evidence.get("scene_claims") or {}
    cutouts = evidence.get("cutouts") or {}
    work = Path(work_dir) / "storyboard"
    thumbs_dir = work / "thumbs"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    contact_path = work / "contact_sheet.jpg"
    json_path = work / "storyboard.json"

    records: list[dict] = []
    summary = {
        "high": 0, "medium": 0, "low": 0, "none": 0, "unknown": 0,
        "semantic_review": 0, "fallbacks": 0, "low_light": 0, "missing": 0,
    }
    all_reasons: list[str] = []
    for position, shot in enumerate(shots):
        index = int(shot.get("index", position) or position)
        scene = (planner.get("scenes") or {}).get(index) or {}
        detail = details[position] if position < len(details) else {}
        raw_path = detail.get("path")
        asset_path = Path(raw_path) if raw_path and Path(raw_path).is_file() else None
        provider = str(detail.get("provider") or "")
        confidence = str(detail.get("relevance_confidence") or "unknown")
        if confidence not in summary:
            confidence = "unknown"
        summary[confidence] += 1
        if detail.get("semantic_review"):
            summary["semantic_review"] += 1
        if detail.get("fallback_reason"):
            summary["fallbacks"] += 1
        if detail.get("visual_quality") == "low_light":
            summary["low_light"] += 1
        if asset_path is None:
            summary["missing"] += 1

        # The traceability id travels with the shot from the plan; the sNN
        # fallback keeps storyboards built without a plan byte-compatible.
        shot_id = str(shot.get("shot_id") or f"s{index:02d}")
        scene_id = shot_id
        thumb_path = thumbs_dir / f"thumb_{position:03d}.png"
        thumb_ok = _make_thumb(asset_path, thumb_path, shot_id,
                               provider or "missing", confidence)
        if not thumb_ok:
            thumb_ok = bool(_blank_thumb(thumb_path))
        reasons = _review_reasons(scene, detail, asset_path)
        plan_flags = [str(flag) for flag in shot.get("evidence_flags") or []]
        for flag in plan_flags:
            if flag not in {"no_action"}:
                reasons.append(f"shot-plan integrity: {flag}")
        scene_claim_list = [claim for claim in (scene_claims.get(index) or []) if claim]
        cutout = cutouts.get(index) or {}
        claim_ids = [str(claim.get("claim_id") or "") for claim in scene_claim_list]
        evidence_rows = [
            {
                "claim_id": str(claim.get("claim_id") or ""),
                "claim_type": str(claim.get("claim_type") or ""),
                "status": str((claim.get("verification") or {}).get("status") or "unverified"),
                "publisher": str(claim.get("publisher") or ""),
                "published": str(claim.get("published") or ""),
                "source_url": str(claim.get("source_url") or ""),
                "decision": str(claim.get("decision") or ""),
            }
            for claim in scene_claim_list
        ]
        weak = [row for row in evidence_rows if row["status"] in {"unverified", "conflicting", "outdated"}]
        if weak:
            reasons.append(
                "weak evidence for "
                + ", ".join(f"{row['claim_id']} ({row['status']})" for row in weak[:3])
            )
        if cutout and not cutout.get("publish_ready"):
            rights = (cutout.get("reuse_rights") or {})
            reasons.append(
                f"reuse rights {rights.get('status', 'unknown')} for cutout {cutout.get('claim_id', '')}"
            )
        if cutout and not cutout.get("rendered"):
            reasons.append(f"cutout {cutout.get('claim_id', '')} failed to render")
        for reason in reasons:
            all_reasons.append(f"{scene_id}: {reason}")
        record = {
            "scene_id": scene_id,
            "shot_id": shot_id,
            "shot_plan_ref": str(shot.get("shot_plan_ref") or ""),
            "subject": str(shot.get("subject") or ""),
            "narration_ref": dict(shot.get("narration_ref") or {}),
            "plan_claim_ids": [str(cid) for cid in shot.get("evidence_claim_ids") or []],
            "plan_evidence_flags": [str(flag) for flag in shot.get("evidence_flags") or []],
            "index": index,
            "start": round(float(shot.get("start", 0.0) or 0.0), 3),
            "end": round(float(shot.get("end", 0.0) or 0.0), 3),
            "duration": round(float(shot.get("duration", 0.0) or 0.0), 3),
            "narration": str(scene.get("narration") or shot.get("claim") or shot.get("caption") or ""),
            "visual_purpose": str(scene.get("visual_purpose") or ""),
            "visual_intent": str(scene.get("visual_intent") or scene.get("visual_purpose") or ""),
            "visual_type": str(detail.get("visual_type") or scene.get("visual_type") or ""),
            "scene_type": str(detail.get("scene_type") or scene.get("scene_type") or ""),
            "provider": provider,
            "asset_id": str(detail.get("asset_id") or ""),
            "card_variant": str(detail.get("card_variant") or scene.get("card_variant") or ""),
            "query": str(detail.get("query") or detail.get("keyword") or ""),
            "asset_path": str(asset_path) if asset_path else "",
            "title": str(detail.get("title") or ""),
            "description": str(detail.get("description") or ""),
            "tags": str(detail.get("tags") or ""),
            "author": str(detail.get("author") or ""),
            "source_url": str(detail.get("source_url") or detail.get("page_url") or ""),
            "object_name": str(detail.get("object_name") or ""),
            "relevance": str(detail.get("relevance") or ""),
            "relevance_confidence": confidence,
            "semantic_review": bool(detail.get("semantic_review")),
            "review_reason": str(detail.get("review_reason") or ""),
            "fallback_reason": str(detail.get("fallback_reason") or ""),
            "visual_quality": str(detail.get("visual_quality") or ""),
            "license": str(detail.get("license") or ""),
            "credit_line": str(detail.get("credit_line") or ""),
            "claim_ids": claim_ids,
            "evidence": evidence_rows,
            "evidence_visual": str(cutout.get("path") or "") if cutout else "",
            "reuse_rights": (cutout.get("reuse_rights") or {}) if cutout else {},
            "attribution": list(cutout.get("attribution_lines") or []) if cutout else [],
            "thumb": str(thumb_path) if thumb_ok else "",
            "review_reasons": reasons,
            "provenance": {
                "provider": provider,
                "asset_id": str(detail.get("asset_id") or ""),
                "title": str(detail.get("title") or ""),
                "license": str(detail.get("license") or ""),
                "tags": str(detail.get("tags") or ""),
                "query": str(detail.get("query") or ""),
                "content_sha256": _sha256(asset_path) if asset_path else "",
                "retrieved_at": _file_time(asset_path) if asset_path else "",
                "generated_video": dict(detail.get("generated_provenance") or {}),
            },
        }
        records.append(record)

    contact_ok = _make_contact_sheet(
        [Path(record["thumb"]) for record in records if record["thumb"]],
        contact_path,
    )
    if not contact_ok:
        all_reasons.append("contact sheet generation failed")

    # The same excerpt may not carry two scenes: repeating a quote is not emphasis,
    # it is padding, and it usually means the second scene lost its own evidence.
    # Reusing a research claim as supporting evidence across scenes is valid.
    # The restriction applies to repeated source-card excerpts, not evidence links.
    seen_cutout_claims: dict[str, str] = {}
    for record in records:
        if not record.get("evidence_visual"):
            continue
        for claim_id in record.get("claim_ids") or []:
            if claim_id in seen_cutout_claims:
                all_reasons.append(
                    f"{record['scene_id']}: source cutout claim {claim_id} already used by "
                    f"{seen_cutout_claims[claim_id]}"
                )
            else:
                seen_cutout_claims[claim_id] = record["scene_id"]

    linked_scenes = sum(1 for record in records if record.get("claim_ids"))
    cutout_scenes = sum(1 for record in records if record.get("evidence_visual"))
    blocked_cutouts = sum(
        1 for record in records
        if record.get("evidence_visual") and not (record.get("reuse_rights") or {}).get("status") == "permitted"
    )
    evidence_summary = {
        "linked": bool(evidence),
        "scenes_with_claims": linked_scenes,
        "scenes_with_cutout": cutout_scenes,
        "cutouts_blocked_by_rights": blocked_cutouts,
        "script_sha256": str(evidence.get("script_sha256") or ""),
        "ledger_sha256": str(evidence.get("ledger_sha256") or ""),
    }

    hard_block_flags = {"evidence_missing", "evidence_unsupported_status",
                        "evidence_reference_invalid", "uncovered_beat"}
    has_plan_integrity_block = any(
        hard_block_flags.intersection(record.get("plan_evidence_flags") or [])
        for record in records
    )
    if (any(not record["asset_path"] or not record["provider"] for record in records)
            or has_plan_integrity_block):
        review_status = "blocked"
    elif all_reasons:
        review_status = "needs_review"
    else:
        review_status = "auto_approved"
    if not contact_ok and review_status == "auto_approved":
        review_status = "needs_review"

    payload = {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "scene_count": len(records),
        "contact_sheet": str(contact_path) if contact_ok else "",
        "contact_sheet_ok": contact_ok,
        "review_status": review_status,
        "approved": review_status in APPROVED_STATUSES,
        "review_required": review_status != "auto_approved",
        "review_reasons": all_reasons,
        "summary": summary,
        "evidence": evidence_summary,
        "script_sha256": evidence_summary["script_sha256"],
        "ledger_sha256": evidence_summary["ledger_sha256"],
        "scene_digest": _scene_digest(records),
        "scenes": records,
        "approval_path": str(work / "storyboard.approval.json"),
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["json_path"] = str(json_path)
    return payload


def approve_storyboard(storyboard_path: Path, reviewer: str, note: str = "") -> dict:
    """Record an explicit human review after inspecting the contact sheet."""
    storyboard_path = Path(storyboard_path)
    payload = json.loads(storyboard_path.read_text(encoding="utf-8"))
    if payload.get("review_status") == "blocked":
        raise RuntimeError("cannot approve a blocked storyboard; resolve missing assets first")
    contact = Path(str(payload.get("contact_sheet") or ""))
    if not contact.is_file():
        raise RuntimeError("cannot approve a storyboard without a contact sheet")
    reviewer = str(reviewer or "").strip()
    if not reviewer:
        raise ValueError("reviewer name is required")
    approval = {
        "approved": True,
        "reviewer": reviewer,
        "note": str(note or "")[:500],
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "review_status": payload.get("review_status"),
        "scene_count": payload.get("scene_count"),
        "contact_sheet_sha256": _sha256(contact),
        "script_sha256": str(payload.get("script_sha256") or ""),
        "ledger_sha256": str(payload.get("ledger_sha256") or ""),
        "scene_digest": str(payload.get("scene_digest") or ""),
    }
    approval_path = Path(str(payload.get("approval_path") or storyboard_path.with_name("storyboard.approval.json")))
    approval_path.write_text(json.dumps(approval, indent=2) + "\n", encoding="utf-8")
    return approval


def _approval_valid(payload: dict) -> bool:
    approval_path = Path(str(payload.get("approval_path") or ""))
    contact = Path(str(payload.get("contact_sheet") or ""))
    if not approval_path.is_file() or not contact.is_file():
        return False
    try:
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        bool(approval.get("approved"))
        and str(approval.get("review_status") or "") == str(payload.get("review_status") or "")
        and str(approval.get("contact_sheet_sha256") or "") == _sha256(contact)
        and str(approval.get("reviewer") or "").strip() != ""
        # An approval is only valid for the exact scene plan, script and ledger it
        # was given.  Editing either one must force a fresh review.
        and str(approval.get("scene_digest") or "") == str(payload.get("scene_digest") or "")
        and str(approval.get("script_sha256") or "") == str(payload.get("script_sha256") or "")
        and str(approval.get("ledger_sha256") or "") == str(payload.get("ledger_sha256") or "")
    )


class StoryboardReviewRequired(RuntimeError):
    """The pre-render gate needs a human review that does not exist yet.

    Raised instead of a bare RuntimeError so the producer can persist the
    storyboard as an artifact, park the run as ``awaiting_review`` and resume
    after the operator approves the contact sheet.  It remains a RuntimeError
    subclass so existing callers and tests keep their behaviour.
    """

    def __init__(
        self,
        message: str,
        *,
        storyboard_path: str = "",
        review_status: str = "",
        reasons: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.storyboard_path = str(storyboard_path or "")
        self.review_status = str(review_status or "")
        self.reasons = list(reasons or [])


def enforce_review_gate(storyboard: dict, mode: str | None = None) -> None:
    """Apply the configured pre-render gate.  Default is require, and unknown values fail closed."""
    import os
    mode = (mode or os.getenv("STORYBOARD_GATE", "require")).strip().lower()
    if mode not in {"off", "skip", "warn", "require"}:
        raise RuntimeError(
            f"STORYBOARD_GATE={mode!r} is not a recognised mode (off, skip, warn or require); "
            "refusing to fall back to an unreviewed render")
    if mode in {"off", "skip"}:
        return
    status = str(storyboard.get("review_status") or "blocked")
    if status in APPROVED_STATUSES:
        return
    if _approval_valid(storyboard):
        storyboard["human_approved"] = True
        print("[storyboard] explicit human approval found")
        return
    reasons = "; ".join(storyboard.get("review_reasons") or [])[:600]
    if mode == "require":
        raise StoryboardReviewRequired(
            f"storyboard review required before render ({status}): {reasons}",
            storyboard_path=str(storyboard.get("json_path") or ""),
            review_status=status,
            reasons=list(storyboard.get("review_reasons") or []),
        )
    print(f"[storyboard] review {status}: {reasons}")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Approve a generated storyboard after review")
    parser.add_argument("storyboard", help="path to storyboard.json")
    parser.add_argument("--reviewer", required=True, help="name of the human reviewer")
    parser.add_argument("--note", default="", help="optional review note")
    args = parser.parse_args()
    approval = approve_storyboard(Path(args.storyboard), args.reviewer, args.note)
    print(json.dumps(approval, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
