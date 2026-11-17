"""Full-short assembly: concat, audio mix, mux, and the demo CLI.

Moved verbatim from motion_render.py in Phase 7B; logic unchanged.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.render.ffmpeg_tools import (
    AUDIO_RATE,
    DUCK_FILTER,
    FPS,
    HEIGHT,
    LOUDNORM_TARGET,
    WIDTH,
    _concat_videos,
    _mix_audio,
    _probe_duration,
    _run,
    audio_bitrate,
    music_bed_requested,
    music_bed_source,
    qa_video,
    synthesize_music_bed,
    synthesize_sfx,
)
from app.render.shots import render_shot
from app.render.edit_director import build_edit_decisions, execute_clip, validate_final_output, write_edl
from app.render.otio_export import export_edl_to_otio
from app.visuals import chain as visual_chain
from app.visuals import motion_director
from app.visuals import stock_fetcher

def _escape_filter_path(path: Path) -> str:
    text = str(Path(path).resolve()).replace("\\", "/")
    for char in (":", "'", ",", "[", "]"):
        text = text.replace(char, "\\" + char)
    return text


def _serialize_cutout_evidence(cutouts: dict) -> list[dict]:
    """Persist cutout evidence without weakening its structured rights decision."""
    return [
        {
            "scene_index": index,
            "claim_id": card.get("claim_id", ""),
            "path": card.get("path", ""),
            "publish_ready": card.get("publish_ready", False),
            "reuse_rights": card.get("reuse_rights") or {},
            "attribution": card.get("attribution_lines", []),
        }
        for index, card in sorted((cutouts or {}).items())
    ]


def _json_safe(value: object) -> object:
    """Round-trip a planning structure through JSON with explicit str fallback."""
    return json.loads(json.dumps(value, default=str))


def _write_render_plan(
    work_dir: Path, *, shots: list[dict], resolved_scenes: list[dict], planner: dict,
    assets: list[dict], motion_plan: list[dict], evidence: dict, storyboard: dict,
    width: int, height: int, fps: int,
    audio_path: str = "", ass_path: str = "", captions_path: str = "",
    ledger_path: str = "", script_sha256: str = "", ledger_sha256: str = "",
    duration: float = 0.0,
) -> Path:
    """Persist everything the render needs so an approved plan can be resumed.

    The gate runs after scene resolution, so a review stop would otherwise throw
    away downloaded assets and resolved briefs.  The plan records the exact
    inputs; a resume re-uses them instead of resolving again, which also keeps
    the approved contact sheet and scene digest byte-identical.
    """
    evidence_payload = dict(evidence)
    ledger = evidence_payload.pop("ledger", None)
    evidence_payload["ledger_present"] = bool(ledger)
    payload = {
        "version": 1,
        "written_at": datetime.now(timezone.utc).isoformat(),
        "shots": _json_safe(shots),
        "resolved_scenes": [
            {
                "shot": _json_safe(item.get("shot") or {}),
                "detail": _json_safe(item.get("detail") or {}),
                "asset_path": str(item.get("asset_path") or ""),
            }
            for item in resolved_scenes
        ],
        "planner": _json_safe(planner),
        "assets": _json_safe(assets),
        "motion_plan": _json_safe(motion_plan),
        "evidence": _json_safe(evidence_payload),
        "storyboard_path": str(storyboard.get("json_path") or ""),
        "audio_path": str(audio_path or ""),
        "ass_path": str(ass_path or ""),
        "captions_path": str(captions_path or ""),
        "ledger_path": str(ledger_path or ""),
        "script_sha256": str(script_sha256 or ""),
        "ledger_sha256": str(ledger_sha256 or ""),
        "duration": float(duration or 0.0),
        "width": width,
        "height": height,
        "fps": fps,
    }
    path = Path(work_dir) / "render_plan.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def render_video(shots: list[dict], audio_path: Path, out_path: Path, *, work_dir: Path,
                 ass_path: Path | None = None, caption_words_path: Path | None = None,
                 width: int = WIDTH, height: int = HEIGHT,
                 fps: int = FPS, evidence: dict | None = None,
                 resume_from: Path | str | None = None) -> dict:
    """Render a full multi-shot short. -> {'status','path','duration','shots','width',
    'height','music','sfx_count'} plus visual/audio diagnostics.

    ``evidence`` carries the claim ledger: ``{"ledger": {...}, "script_sha256": ...,
    "ledger_sha256": ...}``.  When present, scenes whose claims warrant it get a
    source cutout instead of b-roll, and every scene is linked to claim IDs in the
    storyboard.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path = Path(audio_path)

    if not audio_path.is_file():
        raise RuntimeError(f"render_video voice track is missing: {audio_path}")
    resume_path = Path(resume_from) if resume_from else None
    restored: dict = {}
    if resume_path is not None:
        if not resume_path.is_file():
            raise RuntimeError(f"render resume plan is missing: {resume_path}")
        restored = json.loads(resume_path.read_text(encoding="utf-8"))
        shots = [dict(item) for item in restored.get("shots") or []]
        print(f"[resume] continuing from {resume_path.name}: {len(shots)} planned shot(s)")
    if not shots:
        raise RuntimeError("render_video requires at least one shot")

    total_duration = float(shots[-1]["end"])
    adur = _probe_duration(audio_path)
    if adur > 0:
        total_duration = adur

    shot_files: list[Path] = []
    sfx_timed: list[tuple[float, Path]] = []
    music_gain_db = float(shots[0].get("music_gain_db", -15.0))
    music_bed: Path | None = None
    assets: list[dict] = []
    used_titles: set[str] = set()
    render_diagnostics: list[dict] = []
    dry_run = os.getenv("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}
    storyboard_gate = os.getenv("STORYBOARD_GATE", "require").strip().lower()
    if not dry_run and storyboard_gate != "require":
        raise RuntimeError(
            "production render requires STORYBOARD_GATE=require; "
            f"received {storyboard_gate!r}. Non-blocking modes are dry-run only."
        )
    if resume_path is not None:
        planner = restored.get("planner") or {}
        evidence = dict(restored.get("evidence") or {})
        if evidence.pop("ledger_present", False):
            evidence["ledger"] = {"resumed": True}
        resolved_scenes = []
        for item in restored.get("resolved_scenes") or []:
            entry = dict(item)
            entry["asset_path"] = Path(entry["asset_path"]) if entry.get("asset_path") else None
            resolved_scenes.append(entry)
        assets = list(restored.get("assets") or [])
        motion_plan = list(restored.get("motion_plan") or [])
        storyboard_path = Path(str(restored.get("storyboard_path") or ""))
        if not storyboard_path.is_file():
            raise RuntimeError(f"render resume storyboard is missing: {storyboard_path}")
        storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
        storyboard["json_path"] = str(storyboard_path)
        print(
            f"[resume] restored {len(resolved_scenes)} resolved scene(s); "
            f"storyboard {storyboard.get('review_status')}"
        )
    else:
        planner = visual_chain.plan_scenes(shots)
        print(f"[visual] plan: up to {planner['stock_cap']} stock b-roll scene(s) of {planner['total']}")

        evidence = dict(evidence or {})
        cutout_plan: dict[int, dict] = {}
        if evidence.get("ledger"):
            from app.research import claims as claim_ledger
            from app.visuals import cutouts as cutout_module

            scene_claims: dict[int, list[dict]] = {}
            for shot in shots:
                index = int(shot.get("index", 0) or 0)
                scene = (planner.get("scenes") or {}).get(index) or {}
                narration = str(scene.get("narration") or shot.get("claim") or shot.get("caption") or "")
                scene_claims[index] = claim_ledger.claims_for_scene(evidence["ledger"], narration)
            selection = cutout_module.select_cutout_scenes(evidence["ledger"], scene_claims)
            for entry in selection.get("selected") or []:
                index = entry["scene_index"]
                claim = next(
                    (item for item in scene_claims.get(index, [])
                     if item.get("claim_id") == entry["claim_id"]),
                    None,
                )
                if not claim:
                    continue
                card = cutout_module.build_source_card(claim, work_dir)
                if card.get("rendered"):
                    cutout_plan[index] = card
            evidence["scene_claims"] = scene_claims
            evidence["cutouts"] = cutout_plan
            evidence["cutout_selection"] = selection
            rights = cutout_module.rights_gate(list(cutout_plan.values()))
            evidence["rights_gate"] = rights
            print(
                f"[evidence] {len(cutout_plan)} source cutout(s) of {selection.get('budget', 0)} slot(s); "
                f"rights gate: {rights['blocked']} blocked"
            )

        resolved_scenes: list[dict] = []
        for shot in shots:
            index = int(shot.get("index", 0) or 0)
            cutout = cutout_plan.get(index)
            if cutout:
                # The excerpt replaces b-roll on this scene; the card carries its own
                # publisher, date and URL attribution.
                detail = {
                    "provider": "source_cutout",
                    "path": cutout.get("path", ""),
                    "title": f"{cutout.get('claim_id', '')} source excerpt",
                    "license": (cutout.get("reuse_rights") or {}).get("basis", ""),
                    "credit_line": cutout.get("attribution", ""),
                    "query": cutout.get("claim_id", ""),
                    "visual_type": "image",
                    "scene_type": "source_cutout",
                    "relevance": "evidence",
                    "relevance_confidence": "high",
                    "claim_id": cutout.get("claim_id", ""),
                }
            else:
                detail = visual_chain.resolve_scene(
                    shot, work_dir, planner, used_titles=used_titles, dry_run=dry_run
                )
            asset_path = detail.get("path")
            if asset_path and not Path(asset_path).exists():
                asset_path = None
            if detail.get("provider") and detail["provider"] != "procedural":
                if detail.get("title"):
                    used_titles.add(str(detail["title"]))
                entry = {k: v for k, v in detail.items() if k != "path"}
                entry["path"] = str(asset_path) if asset_path else ""
                entry["credit_line"] = (stock_fetcher.credit_lines([detail]) or [""])[0]
                assets.append(entry)
            resolved_scenes.append({"shot": shot, "detail": detail, "asset_path": asset_path})

        print(f"[visual] {visual_chain.stock_summary(planner)}")

    # Motion is planned after resolution because it depends on the scene type
    # and whether the chosen asset is video or a still.  A cut then starts at
    # the scale the previous shot ended on.  A resume reuses the approved plan.
    if resume_path is None:
        motion_plan = []
        try:
            motion_plan = motion_director.assign_motion(
                shots, [item["detail"] for item in resolved_scenes]
            )
            print(
                "[motion] " + ", ".join(
                    f"s{item['index']:02d}:{item['profile']} "
                    f"{item['zoom_from']}->{item['zoom_to']}"
                    for item in motion_plan[:6]
                )
            )
        except Exception as exc:
            print(f"[motion] scene-aware plan failed ({type(exc).__name__}); using planned values")

    storyboard_gate = os.getenv("STORYBOARD_GATE", "require").strip().lower()
    if resume_path is not None:
        if storyboard_gate not in {"off", "skip"}:
            from app.visuals.storyboard import enforce_review_gate
            enforce_review_gate(storyboard, storyboard_gate)
    else:
        storyboard = {"review_status": "disabled", "approved": False,
                      "review_required": False, "review_reasons": []}
        if storyboard_gate not in {"off", "skip"}:
            from app.visuals.storyboard import build_storyboard, enforce_review_gate
            storyboard = build_storyboard(
                shots,
                [item["detail"] for item in resolved_scenes],
                work_dir,
                planner=planner,
                title=str(shots[0].get("title") or ""),
                evidence=evidence or None,
            )
            print(
                f"[storyboard] {storyboard['review_status']} "
                f"({len(storyboard.get('scenes') or [])} scenes, "
                f"{len(storyboard.get('review_reasons') or [])} reason(s))"
            )
            # Persist the plan before the gate can stop the run, so an approved
            # storyboard can be resumed without re-resolving every asset.
            plan_path = _write_render_plan(
                work_dir, shots=shots, resolved_scenes=resolved_scenes,
                planner=planner, assets=assets, motion_plan=motion_plan,
                evidence=evidence, storyboard=storyboard,
                width=width, height=height, fps=fps,
            )
            print(f"[storyboard] review plan: {plan_path}")
            enforce_review_gate(storyboard, storyboard_gate)
    if storyboard.get("human_approved"):
        # Approval is bound to this exact contact sheet, script, ledger and
        # scene digest. Keep the original semantic-review signal for audit,
        # while telling final QA that a human explicitly accepted these assets.
        for asset in assets:
            asset["human_reviewed"] = True
            asset["human_review_reviewer"] = "storyboard approval"

    # The EDL is authored before picture rendering and becomes the execution input.
    edit_decisions = build_edit_decisions(
        resolved_scenes, motion_plan, fps=fps, width=width, height=height
    )
    edl_path = write_edl(work_dir / "edit_decisions.json", edit_decisions)
    print(f"[edit] pre-render EDL: {edl_path} ({len(edit_decisions['clips'])} clips)")

    for item, decision in zip(resolved_scenes, edit_decisions["clips"]):
        shot = item["shot"]
        asset_path = item["asset_path"]
        try:
            shot_file = execute_clip(
                decision, render_shot, shot, asset_path, work_dir,
                fps=fps, width=width, height=height, diagnostics=render_diagnostics,
            )
        except Exception as exc:
            if asset_path is None or "EDL source trim failed" in str(exc) or "failed visual QA" in str(exc) or "EDL execution QA" in str(exc):
                raise
            shot_file = execute_clip(
                decision, render_shot, shot, None, work_dir,
                fps=fps, width=width, height=height, diagnostics=render_diagnostics,
            )
        if not shot_file.is_file() or shot_file.stat().st_size <= 1000:
            raise RuntimeError(f"shot {shot.get('index', '?')} produced no usable video segment")
        shot_files.append(shot_file)
        kind = shot.get("sfx")
        if kind and kind != "none":
            sfx_path = synthesize_sfx(kind, work_dir)
            if sfx_path:
                sfx_timed.append((float(shot.get("start", 0.0)), sfx_path))

    # Export the actual rendered scene sequence as an NLE hand-off. The
    # authoritative JSON EDL retains original stock/source ranges; OTIO points
    # to the exact rendered scene files so procedural/graphic scenes are not gaps.
    try:
        handoff_edl = json.loads(json.dumps(edit_decisions))
        for clip, shot_file in zip(handoff_edl.get("clips") or [], shot_files):
            duration = float((clip.get("timeline") or {}).get("duration_seconds") or 0.0)
            clip["source"] = {
                **(clip.get("source") or {}),
                "path": str(Path(shot_file).resolve()),
                "kind": "video", "in_seconds": 0.0, "out_seconds": duration,
            }
        handoff_path = export_edl_to_otio(handoff_edl, work_dir / "editorial_handoff.otio")
        print(f"[edit] OpenTimelineIO hand-off: {handoff_path}")
    except Exception as exc:
        print(f"[edit] OpenTimelineIO export unavailable ({type(exc).__name__}); JSON EDL remains authoritative")

    # Persist post-render measurements into the same authoritative EDL artifact.
    write_edl(edl_path, edit_decisions)
    video_full = _concat_videos(shot_files, shots, work_dir)

    motion_sheet = ""
    try:
        from app.visuals.storyboard import build_motion_contact_sheet
        motion_sheet = build_motion_contact_sheet(shot_files, shots, work_dir) or ""
        if motion_sheet:
            print(f"[motion] start/mid/end sheet: {motion_sheet}")
    except Exception as exc:
        print(f"[motion] start/mid/end sheet failed ({type(exc).__name__})")

    sfx_count = len(sfx_timed)
    audio_mode = "mixed"
    audio_warning = ""
    if music_bed_requested() and total_duration > 0:
        try:
            music_bed = music_bed_source() or synthesize_music_bed(work_dir, total_duration)
        except Exception as exc:
            music_bed = None
            print(f"[audio] music bed failed ({type(exc).__name__}); mixing voice and SFX only")
    elif not music_bed_requested():
        music_bed = None
        print("[audio] music bed off (MUSIC_BED=on or MUSIC_BED_FILE=... to enable); voice-only mix")
    try:
        audio_mix = _mix_audio(shots, audio_path, work_dir, music_gain_db, music_bed, sfx_timed)
        if not audio_mix.is_file() or audio_mix.stat().st_size <= 1000:
            raise RuntimeError("audio mix produced an empty file")
        if not music_bed and not sfx_timed:
            # Nothing was summed with the narration: say so instead of claiming a
            # "mixed" stem that a listener would hear as bare voice.
            audio_mode = "voice_only"
    except Exception as exc:
        # Documented last resort: keep the voice track but make it visible.
        audio_mix = audio_path
        audio_mode = "voice_only"
        audio_warning = f"audio mix failed ({type(exc).__name__}); using the voice track only"
        print(f"[audio] {audio_warning}")

    captions_burned = False
    caption_filter = ""
    if ass_path is not None:
        ass_file = Path(ass_path)
        if not ass_file.is_file() or ass_file.stat().st_size == 0:
            raise RuntimeError(f"required caption file is missing or empty: {ass_file}")
        caption_filter = f"ass='{_escape_filter_path(ass_file)}'"

    base = ["ffmpeg", "-y", "-i", str(video_full), "-i", str(audio_mix)]
    tail = ["-c:a", "aac", "-b:a", audio_bitrate(), "-movflags", "+faststart",
            "-shortest", str(out_path)]
    if caption_filter:
        try:
            _run(base + ["-vf", caption_filter, "-c:v", "libx264", "-preset", "fast",
                         "-crf", "21", "-pix_fmt", "yuv420p"] + tail)
            captions_burned = True
        except Exception as exc:
            # Captions are part of the production deliverable, not an optional
            # decoration. A silent retry without them would create a false success.
            raise RuntimeError(
                f"required caption burn-in failed ({type(exc).__name__}); render rejected"
            ) from exc
    else:
        _run(base + ["-c:v", "copy"] + tail)

    status = "ok" if out_path.exists() and out_path.stat().st_size > 1000 else "failed"
    duration = _probe_duration(out_path) if out_path.exists() else 0.0

    # Persist the director's edit decision record on the same frame clock as
    # the rendered shots, voice, music, SFX and caption asset.
    from app.render.timeline import build_timeline, write_timeline
    timeline = build_timeline(
        shots,
        shot_files,
        voice_path=audio_path,
        mixed_audio_path=audio_mix,
        music_path=music_bed,
        sfx_timed=sfx_timed,
        ass_path=ass_path if captions_burned else None,
        caption_words_path=caption_words_path,
        motion_plan=motion_plan,
        storyboard=storyboard,
        edit_decisions=edit_decisions,
        width=width,
        height=height,
        fps=fps,
    )
    delivery_qa = validate_final_output(out_path, edit_decisions, timeline, fps=fps)
    timeline["delivery_qa"] = delivery_qa
    print(f"[edit] final delivery QA: {delivery_qa['status']} ({delivery_qa['actual_duration_seconds']:.3f}s, {delivery_qa['expected_frames']} frames)")
    timeline_path = write_timeline(work_dir / "timeline.json", timeline)
    print(f"[timeline] frame-accurate edit manifest: {timeline_path}")

    audio_boundaries: dict = {"checked": False}
    try:
        from app.render.audio_diagnostics import analyze_boundaries, summarize
        audio_boundaries = analyze_boundaries(
            out_path, [float(shot.get("start", 0.0) or 0.0) for shot in shots[1:]]
        )
        print(f"[audio] {summarize(audio_boundaries)}")
    except Exception as exc:
        audio_boundaries = {
            "checked": False,
            "reason": f"{type(exc).__name__}: {exc}"[:200],
        }
        print(f"[audio] boundary diagnostics unavailable ({type(exc).__name__})")
    provider_counts: dict[str, int] = {}
    for item in planner.get("resolved", []):
        provider = str(item.get("provider") or "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
    fallback_scenes = [
        item for item in planner.get("resolved", []) if item.get("fallback_reason")
    ]
    return {
        "status": status,
        "path": str(out_path),
        "duration": round(duration, 3),
        "shots": len(shots),
        "width": width,
        "height": height,
        "music": str(music_bed) if music_bed else None,
        "sfx_count": sfx_count,
        "audio_mix_mode": audio_mode,
        "audio_warning": audio_warning,
        "audio_settings": {
            "sample_rate": AUDIO_RATE,
            "channels": 1,
            "delivery_bitrate": audio_bitrate(),
            "music_bed": bool(music_bed),
            "music_gain_db": music_gain_db,
            "loudnorm_target": LOUDNORM_TARGET,
            "ducking": DUCK_FILTER if music_bed else None,
        },
        "captions_burned": captions_burned,
        "assets": assets,
        "credits": stock_fetcher.credit_lines(assets),
        "scene_briefs": [
            planner["scenes"][key] for key in sorted(planner.get("scenes", {}))
        ],
        "provider_counts": provider_counts,
        "fallback_scenes": fallback_scenes,
        "render_diagnostics": render_diagnostics,
        "storyboard": storyboard,
        "motion": motion_plan,
        "motion_contact_sheet": motion_sheet,
        "timeline_path": str(timeline_path),
        "edit_decisions_path": str(edl_path),
        "delivery_qa": delivery_qa,
        "audio_boundaries": audio_boundaries,
        "evidence": {
            "linked": bool(evidence.get("ledger")),
            "scene_claims": {
                str(index): [claim.get("claim_id", "") for claim in items]
                for index, items in (evidence.get("scene_claims") or {}).items()
            },
            "cutouts": _serialize_cutout_evidence(evidence.get("cutouts") or {}),
            "cutout_selection": evidence.get("cutout_selection") or {},
            "rights_gate": evidence.get("rights_gate") or {},
        },
        "visual_plan": {
            "stock_cap": planner.get("stock_cap", 0),
            "stock_used": planner.get("stock_used", 0),
            "scene_types": dict(planner.get("scene_types") or {}),
        },
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Motion renderer demo")
    ap.add_argument("--demo", action="store_true", help="run a quick synthetic render")
    args = ap.parse_args()
    if not args.demo:
        ap.print_help()
        return

    from app.visuals import motion_director

    work_dir = Path(__file__).resolve().parents[2] / "outputs" / "render_demo"
    work_dir.mkdir(parents=True, exist_ok=True)
    shots = motion_director.plan_shots(
        {"topic": "demo", "beat_sheet": [
            {"text": "shot one", "visual": "demo one"},
            {"text": "shot two", "visual": "demo two"},
            {"text": "shot three", "visual": "demo three"},
        ]}, audio_duration=9.0)
    for s in shots:
        s["source"] = "procedural"

    audio = work_dir / "silent.wav"
    _run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
          "-t", "9", "-c:a", "pcm_s16le", str(audio)])

    out = work_dir / "demo.mp4"
    result = render_video(shots, audio, out, work_dir=work_dir, ass_path=None)
    print(json.dumps(result, indent=2))
    try:
        print(json.dumps(qa_video(out, min_duration=1, max_duration=600), indent=2))
    except RuntimeError as exc:
        print("QA:", exc)

if __name__ == "__main__":
    main()
