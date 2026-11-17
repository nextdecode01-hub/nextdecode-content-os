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
from dataclasses import replace
from pathlib import Path

from app.visuals import beats as beat_module
from app.visuals import chain, creative_director, motion_director

SHOTPLAN_VERSION = 1
EVIDENCE_REQUIRED_STATUSES = frozenset({"supported", "partially_supported"})
_UNSUPPORTED_STATUSES = frozenset({"unverified", "conflicting", "outdated"})


def _text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalise(value: object) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", _text(value).lower()))


def _beat_indices_for_shot(shot: dict, shot_beats: list[beat_module.NarrationBeat],
                           position: int, shot_count: int) -> list[int]:
    """Bind a shot to every narration beat it actually contains.

    The script planner intentionally merges adjacent short beats to respect its
    shot-count ceiling. Treating the merged shot as belonging only to its first
    sentence created false uncovered-beat flags and lost traceability.
    """
    if not shot_beats:
        return []
    shot_text = _normalise(shot.get("claim") or shot.get("caption") or shot.get("visual"))
    if shot_text:
        exact = [beat.index for beat in shot_beats if _normalise(beat.text) == shot_text]
        if exact:
            return exact
        contained = [
            beat.index for beat in shot_beats
            if (beat_text := _normalise(beat.text)) and beat_text in shot_text
        ]
        if contained:
            return contained
        partial = [
            beat.index for beat in shot_beats
            if (beat_text := _normalise(beat.text))
            and (shot_text in beat_text or beat_text in shot_text)
        ]
        if partial:
            return partial
    return [min(len(shot_beats) - 1, int(position * len(shot_beats) / max(1, shot_count)))]


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
        claim = known_claim_ids.get(claim_id) or {}
        status = str((claim.get("verification") or {}).get("status") or "unverified")
        decision = str(claim.get("decision") or "")
        # Stale/contradictory explicit references are not allowed to override
        # a valid scene match. They remain visible only when no eligible claim
        # can support the beat.
        if (
            claim_id
            and claim_id in known_claim_ids
            and status in EVIDENCE_REQUIRED_STATUSES
            and decision in {"include", "qualify"}
            and claim_id not in explicit
        ):
            explicit.append(claim_id)

    flags: list[str] = []
    invalid_references = [
        str(claim_id) for claim_id in list(explicit_claim_ids or [])
        if str(claim_id) and str(claim_id) not in known_claim_ids
    ]
    if explicit:
        claim_ids = list(dict.fromkeys(explicit + claim_ids))
        statuses = {
            claim_id: str(
                (known_claim_ids.get(claim_id, {}).get("verification") or {}).get("status")
                or "unverified"
            )
            for claim_id in claim_ids if claim_id in known_claim_ids
        }
        if invalid_references:
            flags.append("evidence_reference_invalid")
    elif invalid_references:
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


def _moe_visual_queries(topic: str, narration: str) -> list[str]:
    """Return intent-specific searches for MoE beats, never topic-wide repeats."""
    topic_text = str(topic or "").lower()
    text = str(narration or "").lower()
    domain_text = f"{topic_text} {text}"
    if not re.search(r"\b(?:mixture of experts|moe|mixtral|few experts)\b", domain_text):
        return []

    if any(term in text for term in ("memory", "stored", "store all", "inactive parameter", "weights occupy")):
        return [
            "GPU memory modules close up",
            "graphics card VRAM memory chips",
            "AI server memory modules",
        ]
    if any(term in text for term in ("dormant", "inactive experts", "stay idle", "not selected")):
        return [
            "GPU server cluster idle accelerator cards",
            "GPU accelerator cards close up",
            "data center server rack close up",
        ]
    if any(term in text for term in ("communication", "interconnect", "overhead", "between gpus")):
        return [
            "GPU cluster interconnect cables",
            "data center high speed network switches",
            "GPU server rack networking",
        ]
    if any(term in text for term in ("company", "specialist team", "library of specialists", "office", "analogy")):
        return [
            "office team collaboration meeting",
            "warehouse order sorting conveyor workers",
            "dispatch team assigning incoming tasks",
        ]
    if "sparse" in text or "selected subset" in text:
        return [
            "sparse expert network router flowchart",
            "GPU accelerator cards close up",
            "graphics card VRAM memory chips",
            "AI server rack close up",
        ]
    if any(term in text for term in ("router", "gating", "routes", "routing", "token-by-token")):
        return [
            "mixture of experts token routing diagram",
            "GPU server racks data center",
            "AI server room cinematic footage",
            "GPU cluster network switches",
            "multiple processor cores on circuit board",
        ]
    if any(term in text for term in ("expert", "experts", "selected", "subset", "pool", "specialist networks")):
        return [
            "parallel computer processing nodes server cluster",
            "multiple processor cores on circuit board",
            "data center computing racks wide shot",
        ]
    if any(term in text for term in ("mixtral", "parameter", "compute", "model", "open weights")):
        return [
            "GPU server racks data center",
            "AI compute server cluster",
            "computer processor chips close up",
        ]
    return [
        "AI data center server racks",
        "GPU compute cluster",
        "artificial intelligence hardware",
    ]

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
    topic = _text(script.get("topic") or script.get("title"))
    for shot in shots:
        shot.setdefault("topic", topic)
    narration = _text(script.get("voice_text") or script.get("text"))
    if not narration:
        narration = " ".join(
            _text(shot.get("claim") or shot.get("caption") or shot.get("visual"))
            for shot in shots
        )
    shot_beats = beat_module.analyse_narration(narration)
    # Carry the creator's editorial direction into the evidence/shot planner.
    # Previously this second parser discarded the director's chosen subject,
    # action, visual family and asset query, producing empty actions and repeated
    # generic searches even though the script already contained that direction.
    directed_beats = creative_director.direct_shots(
        list(script.get("beat_sheet") or []),
        topic=topic,
        story_format=str(script.get("story_format") or "auto"),
        visual_style=str(script.get("visual_style") or "auto"),
    )
    creative_beats = {
        int(item.get("index", position)): item
        for position, item in enumerate(directed_beats)
        if isinstance(item, dict)
    }
    enriched_beats = []
    for beat in shot_beats:
        creative = creative_beats.get(beat.index) or {}
        visual_action = _text(creative.get("visual_action") or creative.get("action"))
        visual_subject = _text(creative.get("visual_subject") or creative.get("subject"))
        action = beat.action or visual_action
        subject = visual_subject or beat.subject
        flags = tuple(
            flag for flag in beat.flags
            if not (flag == "no_action" and action)
            and not (flag == "no_subject" and subject)
        )
        enriched_beats.append(replace(
            beat, subject=subject, action=action,
            context=_text(creative.get("visual_context") or creative.get("context")) or beat.context,
            emotion=_text(creative.get("emotion")) or beat.emotion,
            flags=flags,
        ))
    shot_beats = enriched_beats
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
        indices = _beat_indices_for_shot(shot, shot_beats, position, len(shots))
        for index in indices:
            assigned.setdefault(index, []).append(shot)

    entries: list[dict] = []
    evidence_missing: list[str] = []
    evidence_invalid: list[str] = []
    uncovered: list[int] = []
    for beat in shot_beats:
        beat_shots = assigned.get(beat.index, [])
        primary = beat_shots[0] if beat_shots else None
        if primary:
            # Classify from the actual narration sentence, not the planner's
            # shortened search caption. The latter can be generic ("Mixtral",
            # "sparse expert network") and was incorrectly turning mechanism
            # beats into b-roll even when the narration explicitly described
            # routing, token selection, or specialist networks.
            classification_shot = dict(primary)
            classification_shot["claim"] = beat.text
            classification_shot["caption"] = beat.text
            classification_shot["narration"] = beat.text
            classification_shot["beat_subject"] = beat.subject
            classification_shot["beat_subject_type"] = beat.subject_type
            classification_shot["beat_action"] = beat.action
            classification_shot["beat_context"] = beat.context
            classification_shot["beat_emotion"] = beat.emotion
            brief = chain.build_scene_brief(classification_shot, index=beat.index)
        else:
            brief = {}
        creative = creative_beats.get(beat.index) or {}
        # The creative director's beat-specific semantic search is authoritative;
        # narration-derived classifier queries remain fallbacks, not replacements.
        creative_query = _text(creative.get("asset_query"))
        creative_variants = [
            _text(value) for value in creative.get("asset_query_variants") or []
            if _text(value)
        ]
        if creative_query:
            brief["search_query"] = creative_query
            brief["queries"] = list(dict.fromkeys([creative_query, *creative_variants]))
        visual_family = str(creative.get("visual_family") or "").lower()
        family_types = {
            "real_footage": ("broll", "footage"),
            "diagram": ("motion_graphic", "diagram"),
            "chart": ("motion_graphic", "chart"),
            "typography": ("motion_graphic", "typography"),
            "screen_recording": ("screen_recording", "interface"),
            "product_demo": ("screen_recording", "interface"),
        }
        if visual_family in family_types:
            brief["visual_type"], brief["scene_type"] = family_types[visual_family]
        if creative.get("editorial_reason"):
            brief["visual_purpose"] = _text(creative["editorial_reason"])
        visual_queries = _moe_visual_queries(topic, beat.text)
        if visual_queries and not creative_query:
            brief["search_query"] = visual_queries[0]
            brief["queries"] = list(visual_queries)
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
            "visual_subject": beat.subject,
            "visual_action": beat.action,
            "visual_context": beat.context,
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
        search = entry.get("search") or {}
        search_variants = [str(value) for value in search.get("variants") or [] if str(value).strip()]
        if search.get("primary"):
            planned_primary = str(search["primary"]).strip()
            creator_primary = str(item.get("asset_query") or "").strip()
            refs = list(entry.get("shots") or [])
            ref_position = next(
                (i for i, ref in enumerate(refs)
                 if int(ref.get("shot_index", -1)) == index),
                0,
            )
            concise_variants = [
                value for value in search_variants
                if value and len(value.split()) <= 7
            ]
            query_pool = list(dict.fromkeys([planned_primary, *concise_variants]))
            selected_query = query_pool[ref_position % len(query_pool)] if query_pool else planned_primary
            # Preserve beat-level creative intent while varying repeated coverage
            # shots so the same visual search is not downloaded for every cut.
            if not creator_primary or len(creator_primary.split()) > 7:
                creator_primary = planned_primary
            item["asset_query"] = selected_query or creator_primary
            item["asset_query_variants"] = query_pool or [creator_primary]
        item["visual_subject"] = str(entry.get("visual_subject") or "")
        item["visual_action"] = str(entry.get("visual_action") or "")
        item["visual_context"] = str(entry.get("visual_context") or "")
        item["narration_ref"] = dict(entry.get("narration_ref") or {})
        narration_text = str(item["narration_ref"].get("text") or "").strip()
        if narration_text:
            item["narration"] = narration_text
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
