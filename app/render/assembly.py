"""Full-short assembly: concat, audio mix, mux, and the demo CLI.

Moved verbatim from motion_render.py in Phase 7B; logic unchanged.
"""
from __future__ import annotations

import json
import os
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


def render_video(shots: list[dict], audio_path: Path, out_path: Path, *, work_dir: Path,
                 ass_path: Path | None = None, caption_words_path: Path | None = None,
                 width: int = WIDTH, height: int = HEIGHT,
                 fps: int = FPS, evidence: dict | None = None) -> dict:
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

    if not shots:
        raise RuntimeError("render_video requires at least one shot")
    if not audio_path.is_file():
        raise RuntimeError(f"render_video voice track is missing: {audio_path}")

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
    planner = visual_chain.plan_scenes(shots)
    dry_run = os.getenv("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}
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
    # the scale the previous shot ended on.
    motion_plan: list[dict] = []
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
    storyboard: dict = {"review_status": "disabled", "approved": False,
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
        enforce_review_gate(storyboard, storyboard_gate)

    for item in resolved_scenes:
        shot = item["shot"]
        asset_path = item["asset_path"]
        try:
            shot_file = render_shot(
                shot, asset_path, work_dir, fps=fps, width=width, height=height,
                diagnostics=render_diagnostics,
            )
        except Exception:
            if asset_path is None:
                raise
            shot_file = render_shot(
                shot, None, work_dir, fps=fps, width=width, height=height,
                diagnostics=render_diagnostics,
            )
        if not shot_file.is_file() or shot_file.stat().st_size <= 1000:
            raise RuntimeError(f"shot {shot.get('index', '?')} produced no usable video segment")
        shot_files.append(shot_file)
        kind = shot.get("sfx")
        if kind and kind != "none":
            sfx_path = synthesize_sfx(kind, work_dir)
            if sfx_path:
                sfx_timed.append((float(shot.get("start", 0.0)), sfx_path))
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
        width=width,
        height=height,
        fps=fps,
    )
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
