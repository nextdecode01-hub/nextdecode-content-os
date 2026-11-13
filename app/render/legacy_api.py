#!/usr/bin/env python3
"""Legacy render API adapters for pre-package callers; canonical render implementation lives in app.render.

Phase 7B split the FFmpeg work into app/render/:
    app/render/ffmpeg_tools.py  _run/_ffprobe/probes, Ken Burns filter, concat,
                                music bed, sfx, audio mix, qa_video
    app/render/shots.py         render_shot + procedural fallback
    app/render/subtitles.py     make_kinetic_ass / ASS timestamps
    app/render/assembly.py      render_video (full assembly) + demo CLI

Asset resolution lives in :mod:`app.visuals.chain`.  The legacy
``resolve_asset_detail``/``resolve_asset`` helpers below only translate the old
``source`` hint into that canonical chain, so ranking, dedupe and fallback
diagnostics have a single implementation.  Render API re-exports are kept so
existing imports (motion_render.X) continue to work unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.render.ffmpeg_tools import (
    AUDIO_RATE,
    FFMPEG_TIMEOUT,
    FPS,
    HEIGHT,
    WIDTH,
    _ZERO_AUDIO,
    _concat_videos,
    _ffprobe,
    _mix_audio,
    _probe_duration,
    _run,
    build_concat_filter,
    build_ken_burns_filter,
    qa_video,
    synthesize_music_bed,
    synthesize_sfx,
)
from app.render.shots import (
    _looks_like_image,
    _looks_like_video,
    _procedural_source,
    render_shot,
)
from app.render.subtitles import _ass_timestamp, make_kinetic_ass
from app.render.assembly import main, render_video
from app.visuals import chain as visual_chain


def resolve_asset_detail(shot: dict, work_dir: Path, used_titles: set[str] | None = None) -> dict:
    """Resolve a shot asset to a local file and report where it came from.

    Deprecated compatibility API: new code should call
    :func:`app.visuals.chain.resolve_scene`.  The legacy ``source`` hint is
    honoured while ranking/downloading goes through the canonical providers.

    Returns a dict with ``path`` (may be None), ``provider`` and, for real
    photographs, ``license``/``author``/``page_url`` for attribution.
    """
    source = str(shot.get("source") or "procedural")
    work_dir = Path(work_dir)
    index = int(shot.get("index", 0) or 0)
    keyword = visual_chain.extract_keyword(shot)
    queries = [str(item) for item in (shot.get("asset_query_variants") or [])]

    def wikimedia() -> dict | None:
        return visual_chain._wikimedia_asset(
            shot, keyword, work_dir, index, used_titles, extra_queries=queries,
        )

    def ai_image() -> dict | None:
        return visual_chain._ai_asset(shot, keyword, work_dir)

    if source == "demo":
        demo = os.getenv("DEMO_VIDEO_PATH", "").strip()
        if demo and Path(demo).is_file():
            return {"path": demo, "provider": "demo"}
        return {"path": None, "provider": "demo"}

    if source == "procedural":
        return {"path": None, "provider": "procedural"}

    detail: dict | None = None
    if source == "wikimedia":
        detail = wikimedia()
    elif source == "ai_image":
        detail = ai_image() or wikimedia()
    elif source in ("pexels", "pixabay"):
        fetch = visual_chain._pixabay_asset if source == "pixabay" else visual_chain._pexels_asset
        try:
            detail = fetch(keyword, work_dir, index)
        except Exception:
            detail = None
        detail = detail or wikimedia() or ai_image()
    else:
        return {"path": None, "provider": "procedural"}

    if not detail or not detail.get("path"):
        return {"path": None, "provider": source}
    detail = dict(detail)
    detail.setdefault("provider", "ai_image" if source == "ai_image" else source)
    return detail


def resolve_asset(shot: dict, work_dir: Path) -> Path | None:
    """Resolve a shot asset to a local file, degrading to None (procedural)."""
    detail = resolve_asset_detail(shot, work_dir)
    path = detail.get("path")
    if path and Path(path).exists():
        return Path(path)
    return None


if __name__ == "__main__":
    main()
