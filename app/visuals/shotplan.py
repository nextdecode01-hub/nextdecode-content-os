"""Structured shot planning for the NEXTDECODE short pipeline.

`plan_shot_plan()` turns a script (plus the claim ledger when available) into a
plan whose entries describe *why* each narration beat gets a shot, who the shot
is about, which evidence back it, and what to search for.  It wraps the existing
timeline planner (`motion_director.plan_shots`) so shot start/end/duration stay
identical to today's behaviour; nothing in the renderer is changed.

The plan is deterministic: same script + same ledger -> same plan.  It is also
honest: when evidence cannot be linked, the entry carries an explicit flag
instead of inventing a claim reference.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.visuals import beats as beat_module
from app.visuals import chain, motion_director

SHOTPLAN_VERSION = 1
EVIDENCE_REQUIRED_STATUSES = frozenset({"supported", "partially_supported"})
_UNSUPPORTED_STATUSES = frozenset({"unverified", "conflicting", "outdated"})


def _text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalise(value: object) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", _text(value).lower()))


def _beat_index_for_shot(shot: dict, shot_beats: list[beat_module.NarrationBeat],
                         position: int, shot_count: int) -> int:
    """Bind a shot to its narration beat.

    An exact (or contained) text match wins because the script stage usually
    copies the beat text into the shot.  Otherwise the shot is placed
    proportionally, which keeps order and guarantees coverage.
    """
    if not shot_beats:
        return 0
    shot_text = _normalise(shot.get("claim") or shot.get("caption") or shot.get("visual"))
    if shot_text:
        for beat in shot_beats:
            if _normalise(beat.text) == shot_text:
                return beat.index
        for beat in shot_beats:
            beat_text = _normalise(beat.text)
            if beat_text and (shot_text in beat_text or beat_text in shot_text):
                return beat.index
    return min(len(shot_beats) - 1, int(position * len(shot_beats) / max(1, shot_count)))


def _ledger_claims(ledger: dict | None) -> dict[str, dict]:
    if not isinstance(ledger, dict):
        return {}
    return {
        str(claim.get("claim_id") or ""): claim
        for claim in ledger.get("claims") or []
        if claim.get("claim_id")
    }


def _claims_for(ledger: dict | None, narration: str) -> list[dict]:
    if not isinstance(ledger, dict) or not ledger.get("claims"):
        return []
    from app.research import claims as ledger_module

    return ledger_module.claims_for_scene(ledger, narration)


def _evidence_for(beat: beat_module.NarrationBeat, shots: list[dict],
                  ledger: dict | None, known_claim_ids: dict[str, dict],
                  explicit_claim_ids: list[str] | None = None) -> dict:
    derived = _claims_for(ledger, beat.text)
    claim_ids = [str(item.get("claim_id")) for item in derived if item.get("claim_id")]
    statuses = {
        str(item.get("claim_id")): str((item.get("verification") or {}).get("status") or "unverified")
        for item in derived if item.get("claim_id")
    }

    explicit: list[str] = []
    for claim_id in list(explicit_claim_ids or []) + [
            cid for shot in shots for cid in shot.get("claim_ids") or []]:
        claim_id = str(claim_id)
        if claim_id and claim_id not in explicit:
            explicit.append(claim_id)

    flags: list[str] = []
    invalid_references = [claim_id for claim_id in explicit if claim_id not in known_claim_ids]
    if explicit:
        claim_ids = explicit
        statuses = {
            claim_id: str(
                (known_claim_ids.get(claim_id, {}).get("verification") or {}).get("status")
                or "unverified"
            )
            for claim_id in explicit if claim_id in known_claim_ids
        }
        if invalid_references:
            flags.append("evidence_reference_invalid")

    if ledger is None or not isinstance(ledger, dict):
        flags.append("evidence_ledger_absent")
    if beat.evidence_required and not claim_ids:
        flags.append("evidence_missing")
    if any(status not in EVIDENCE_REQUIRED_STATUSES for status in statuses.values()):
        flags.append("evidence_needs_review")
    if any(status in _UNSUPPORTED_STATUSES for status in statuses.values()):
        flags.append("evidence_unsupported_status")

    return {
        "required": beat.evidence_required,
        "claim_ids": claim_ids,
        "statuses": statuses,
        "invalid_references": invalid_references,
        "flags": flags,
    }


def _duration_basis(total_duration: float, audio_duration: float | None) -> str:
    if not audio_duration:
        return f"planned:{round(total_duration, 3)}s"
    share = total_duration / audio_duration if audio_duration else 0.0
    return f"planned:{round(total_duration, 3)}s | audio_ratio:{share:.3f}"


def plan_shot_plan(script: dict, *, ledger: dict | None = None,
                   audio_duration: float | None = None) -> dict:
    """Build the structured plan for one short.

    ``audio_duration`` is passed straight through to ``plan_shots`` so callers
    that already know the voice track length keep today's timing exactly.
    """
    script = dict(script or {})
    shots = motion_director.plan_shots(script, audio_duration=audio_duration)
    narration = _text(script.get("voice_text") or script.get("text"))
    if not narration:
        narration = " ".join(
            _text(shot.get("claim") or shot.get("caption") or shot.get("visual"))
            for shot in shots
        )
    shot_beats = beat_module.analyse_narration(narration)
    known_claim_ids = _ledger_claims(ledger)
    # plan_shots() rebuilds shot dicts, so an explicit reference is read from the
    # script's own shots and matched to its beat by text.
    explicit_refs: dict[str, list[str]] = {}
    for source_shot in script.get("shots") or []:
        ids = [str(claim_id) for claim_id in source_shot.get("claim_ids") or [] if claim_id]
        if not ids:
            continue
        key = _normalise(source_shot.get("claim") or source_shot.get("caption")
                         or source_shot.get("text"))
        if key:
            explicit_refs.setdefault(key, []).extend(ids)

    assigned: dict[int, list[dict]] = {beat.index: [] for beat in shot_beats}
    for position, shot in enumerate(shots):
        if not shot_beats:
            break
        index = _beat_index_for_shot(shot, shot_beats, position, len(shots))
        assigned.setdefault(index, []).append(shot)

    entries: list[dict] = []
    evidence_missing: list[str] = []
    evidence_invalid: list[str] = []
    uncovered: list[int] = []
    for beat in shot_beats:
        beat_shots = assigned.get(beat.index, [])
        primary = beat_shots[0] if beat_shots else None
        brief = chain.build_scene_brief(primary, index=beat.index) if primary else {}
        evidence = _evidence_for(
            beat, beat_shots, ledger, known_claim_ids,
            explicit_refs.get(_normalise(beat.text), []),
        )
        total_duration = round(sum(float(shot.get("duration") or 0.0) for shot in beat_shots), 3)
        flags = list(beat.flags) + list(evidence["flags"])
        if not beat_shots:
            flags.append("uncovered_beat")
            uncovered.append(beat.index)
        if "evidence_missing" in evidence["flags"]:
            evidence_missing.append(f"s{beat.index:02d}")
        if evidence["invalid_references"]:
            evidence_invalid.append(f"s{beat.index:02d}")

        rationale_parts = [
            f"{brief.get('scene_type') or 'footage'} scene: {brief.get('visual_purpose') or 'support the narration'}",
        ]
        if evidence["claim_ids"]:
            rationale_parts.append(f"evidence: {len(evidence['claim_ids'])} claim link(s)")
        elif evidence["required"]:
            rationale_parts.append("evidence required but not linked (flagged)")
        else:
            rationale_parts.append("no factual claim in this beat")
        if not beat_shots:
            rationale_parts.append("no shot scheduled (flagged)")

        entries.append({
            "shot_id": f"s{beat.index:02d}",
            "index": beat.index,
            "narration_ref": {
                "sentence_index": beat.sentence_index,
                "text": beat.text,
                "claim_ids": evidence["claim_ids"],
            },
            "subject": {"name": beat.subject, "type": beat.subject_type},
            "action": beat.action,
            "context": beat.context,
            "emotion": beat.emotion,
            "visual_objective": brief.get("visual_purpose") or "",
            "visual_type": brief.get("visual_type") or "",
            "scene_type": brief.get("scene_type") or "",
            "expected_duration": total_duration,
            "duration_basis": _duration_basis(total_duration, audio_duration),
            "search": {
                "primary": brief.get("search_query") or "",
                "variants": list(brief.get("queries") or []),
            },
            "transition_intent": str((primary or {}).get("transition") or "cut"),
            "evidence": evidence,
            "shots": [
                {
                    "shot_index": int(shot.get("index", position) or 0),
                    "start": float(shot.get("start") or 0.0),
                    "end": float(shot.get("end") or 0.0),
                    "duration": float(shot.get("duration") or 0.0),
                }
                for position, shot in enumerate(beat_shots)
            ],
            "rationale": "; ".join(rationale_parts),
            "flags": flags,
        })

    covered = sum(1 for entry in entries if entry["shots"])
    ratio = (covered / len(entries)) if entries else 0.0
    return {
        "plan_version": SHOTPLAN_VERSION,
        "topic": _text(script.get("topic") or script.get("title")),
        "shot_count": len(shots),
        "beat_count": len(entries),
        "timing": {
            "total_duration": round(sum(float(shot.get("duration") or 0.0) for shot in shots), 3),
            "audio_duration": round(float(audio_duration), 3) if audio_duration else None,
        },
        "coverage": {
            "sentences": len(entries),
            "with_shots": covered,
            "ratio": round(ratio, 3),
            "uncovered": uncovered,
        },
        "evidence": {
            "ledger_present": isinstance(ledger, dict),
            "linked_beats": sum(1 for entry in entries if entry["evidence"]["claim_ids"]),
            "missing": evidence_missing,
            "invalid_references": evidence_invalid,
        },
        "query_reuse": {},
        "flags": sorted({
            flag for entry in entries for flag in entry["flags"]
        }),
        "beats": entries,
    }


def annotate_shots(shots: list[dict], plan: dict) -> list[dict]:
    """Attach plan traceability to rendered shots without touching the renderer.

    Every shot gets a unique, deterministic ``shot_id`` (its timeline index) and,
    when the plan covers it, the beat reference, narration text, subject and
    claim ids.  The input list is never mutated.
    """
    by_index: dict[int, dict] = {}
    for entry in plan.get("beats") or []:
        for ref in entry.get("shots") or []:
            try:
                by_index.setdefault(int(ref.get("shot_index", -1)), entry)
            except (TypeError, ValueError):
                continue
    annotated: list[dict] = []
    for position, shot in enumerate(shots or []):
        item = dict(shot or {})
        try:
            index = int(item.get("index", position) or 0)
        except (TypeError, ValueError):
            index = position
        entry = by_index.get(index) or {}
        evidence = entry.get("evidence") or {}
        item["shot_id"] = f"s{index:02d}"
        item["shot_plan_ref"] = str(entry.get("shot_id") or "")
        item["narration_ref"] = dict(entry.get("narration_ref") or {})
        item["subject"] = str((entry.get("subject") or {}).get("name") or "")
        item["evidence_claim_ids"] = [str(cid) for cid in evidence.get("claim_ids") or []]
        item["evidence_flags"] = [str(flag) for flag in evidence.get("flags") or []]
        annotated.append(item)
    return annotated


def plan_summary(plan: dict, *, path: str | Path = "") -> dict:
    """Small, deterministic view of the plan for run metadata."""
    return {
        "path": str(path),
        "version": plan.get("plan_version"),
        "shot_count": plan.get("shot_count"),
        "beat_count": plan.get("beat_count"),
        "coverage": dict(plan.get("coverage") or {}),
        "evidence": dict(plan.get("evidence") or {}),
        "flags": list(plan.get("flags") or []),
    }


def validate_coverage(plan: dict, narration: str) -> dict:
    """Compare a plan against the narration it claims to cover."""
    expected = beat_module.analyse_narration(narration)
    planned_indexes = {int(entry.get("index", -1)) for entry in plan.get("beats") or []}
    missing = [beat.index for beat in expected if beat.index not in planned_indexes]
    return {
        "expected_beats": len(expected),
        "planned_beats": len(planned_indexes),
        "missing": missing,
        "complete": not missing,
    }


def write_shot_plan(plan: dict, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return path
