"""Strong editorial pipeline for short-form video.

The legacy path in :mod:`create_short` produces one LLM call, one background
clip, and flat captions.  This module wires the stronger chain together:

``topic_selector`` -> ``research_desk`` -> ``script_studio`` -> ``voice_provider``
-> ``motion_director`` -> ``motion_render``

Every stage fails closed.  If research cannot be verified the script is not
written, and if the rendered video fails QA it is not published.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import motion_director
import motion_render
from app.script import studio as script_studio
import voice_provider
from app.research import desk as research_desk
from app.research import selector as topic_selector
from app.research.topics import discover_topics

ROOT = Path(__file__).resolve().parent
DEFAULT_CANDIDATE_LIMIT = 12
DEFAULT_MIN_TOPIC_SCORE = 55
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base").strip() or "base"


def _log(message: str) -> None:
    print(f"[*] {message}", flush=True)


def _candidate_urls(candidate: dict, research_candidates: list[dict]) -> list[str]:
    urls: list[str] = []
    primary = candidate.get("source_url") or candidate.get("url")
    if primary:
        urls.append(str(primary))
    for item in research_candidates:
        url = item.get("url") or item.get("source_url")
        if url and url not in urls:
            urls.append(str(url))
    return urls[:6]


def select_topic(
    topic: str | None,
    *,
    used_topics_file: Path | None = None,
    limit: int = DEFAULT_CANDIDATE_LIMIT,
    min_score: int = DEFAULT_MIN_TOPIC_SCORE,
) -> dict:
    """Pick the topic for this run.

    An explicit topic wins and is still scored, so the report records why it was
    chosen.  Otherwise the trending candidates are scored on the seven
    editorial dimensions and only a topic above the bar is accepted.
    """
    if topic:
        _log(f"Using explicit topic: {topic}")
        scored = topic_selector.rank_topics([{"title": topic}])
        entry = scored[0] if scored else {"topic": topic, "total_score": 0}
        return {
            "selected": entry,
            "ranked": scored,
            "rejected": [],
            "method": "explicit topic requested by the caller",
            "min_score": min_score,
        }

    candidates = discover_topics(used_topics_file, limit=limit)
    if not candidates:
        raise RuntimeError("No research candidates were discovered; cannot pick a topic.")
    _log(f"Scoring {len(candidates)} candidate topic(s) on the editorial scorecard...")
    result = topic_selector.select_best(candidates, limit=1, min_score=min_score)
    selected = result.get("selected")
    if not selected:
        detail = "; ".join(
            f"{item.get('topic', '')} ({item.get('reason', '')})" for item in result.get("rejected", [])[:4]
        )
        raise RuntimeError(f"No topic met the quality bar (min_score={min_score}). {detail}")
    _log(f"Selected topic: {selected.get('topic')} (score {selected.get('total_score')})")
    return result


def build_research(topic: str, *, source_urls: list[str] | None = None) -> dict:
    """Fetch and read the sources behind a topic."""
    _log(f"Researching '{topic}' (reading primary sources)...")
    bundle = research_desk.research_topic(topic, source_urls=source_urls or None)
    verdict = bundle.get("verdict")
    claims = bundle.get("claims") or []
    _log(f"Research verdict: {verdict} ({len(claims)} verifiable claim(s))")
    if bundle.get("unsupported_numbers"):
        _log(f"Unsupported numbers flagged: {bundle['unsupported_numbers']}")
    if bundle.get("contradictions"):
        _log(f"Contradictions found: {len(bundle['contradictions'])}")
    return bundle


def transcribe_words(audio_path: Path) -> list[dict]:
    """Word-level timings for kinetic captions. Returns [] when unavailable."""
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        _log(f"faster-whisper unavailable ({type(exc).__name__}); captions will use estimated timings.")
        return []
    try:
        _log(f"Transcribing audio with faster-whisper ({WHISPER_MODEL}) for kinetic captions...")
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio_path), word_timestamps=True)
        words: list[dict] = []
        for segment in segments:
            for word in segment.words or []:
                text = (word.word or "").strip()
                if text:
                    words.append({"word": text, "start": float(word.start), "end": float(word.end)})
        return words
    except Exception as exc:
        _log(f"Transcription failed ({type(exc).__name__}); captions will use estimated timings.")
        return []


def estimated_words(text: str, duration: float) -> list[dict]:
    """Proportional word timings used when transcription is unavailable."""
    tokens = re.findall(r"\S+", text or "")
    if not tokens or duration <= 0:
        return []
    step = duration / len(tokens)
    return [
        {"word": token, "start": index * step, "end": (index + 1) * step}
        for index, token in enumerate(tokens)
    ]


def build_captions(script: dict, audio_path: Path, ass_path: Path, duration: float) -> dict:
    """Produce the kinetic caption file."""
    words = transcribe_words(audio_path)
    source = "transcribed"
    if not words:
        words = estimated_words(script.get("voice_text", ""), duration)
        source = "estimated"
    motion_render.make_kinetic_ass(words, ass_path)
    _log(f"Captions built from {source} timings ({len(words)} words) -> {ass_path.name}")
    return {"word_count": len(words), "timing_source": source, "path": str(ass_path)}


def generate_voice(text: str, audio_path: Path) -> dict:
    """Synthesize the voiceover through the provider chain."""
    voice = os.getenv("TTS_VOICE", "").strip() or None
    result = voice_provider.synthesize_with_fallback(text, audio_path, preferred="edge_tts")
    if not result.get("path"):
        raise RuntimeError(f"Voice generation failed: {result.get('error')}")
    _log(f"Voice ready via {result.get('provider')} ({result.get('duration_hint', 0):.1f}s estimated)")
    return result


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


STOCK_PROVIDERS = {"pexels", "pixabay", "wikimedia"}
AI_PROVIDERS = {"ai_image", "gemini", "fal", "replicate", "openai"}
PROCEDURAL_PROVIDERS = {"procedural", "local"}


def _describe_visuals(assets: list[dict], shots: list[dict]) -> dict:
    """Describe the visuals honestly so the publish gate sees the truth."""
    providers = [str(asset.get("provider", "")) for asset in assets if isinstance(asset, dict)]
    counts: dict[str, int] = {}
    for provider in providers:
        counts[provider] = counts.get(provider, 0) + 1

    procedural_shot_count = max(0, len(shots) - len(assets))
    if not providers:
        mode = "multi_shot_procedural"
    elif procedural_shot_count:
        mode = "multi_shot_mixed"
    elif all(provider in STOCK_PROVIDERS for provider in providers):
        mode = "multi_shot_stock"
    elif all(provider in AI_PROVIDERS for provider in providers):
        mode = "multi_shot_ai"
    elif all(provider in PROCEDURAL_PROVIDERS for provider in providers):
        mode = "multi_shot_procedural"
    elif all(provider == "demo" for provider in providers):
        mode = "owner_recorded"
    else:
        mode = "multi_shot_mixed"

    first_path = next((str(asset.get("path", "")) for asset in assets if asset.get("path")), "")
    return {
        "mode": mode,
        "asset_count": len(assets),
        "asset_path": first_path,
        "shot_count": len(shots),
        "procedural_shot_count": procedural_shot_count,
        "providers": counts,
        "assets": assets,
        "credits": [asset.get("credit_line", "") for asset in assets if asset.get("credit_line")],
    }


def run(
    topic: str | None = None,
    *,
    seconds: int = 35,
    work_dir: Path | None = None,
    min_topic_score: int = DEFAULT_MIN_TOPIC_SCORE,
    used_topics_file: Path | None = None,
) -> dict:
    """Run the full strong pipeline and return the metadata payload."""
    started = time.perf_counter()
    work = Path(work_dir or ROOT)
    work.mkdir(parents=True, exist_ok=True)
    shots_dir = work / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    steps: list[dict] = []

    def step(name: str, payload: dict) -> None:
        steps.append({"step": name, **payload})

    selection = select_topic(topic, used_topics_file=used_topics_file, min_score=min_topic_score)
    chosen = selection.get("selected") or {}
    selected_topic = chosen.get("topic") or topic or ""
    step("topic", {"topic": selected_topic, "score": chosen.get("total_score"),
                   "angle": chosen.get("angle", ""), "pillar": chosen.get("pillar", "")})

    research = build_research(
        selected_topic,
        source_urls=_candidate_urls(chosen, [dict(r) for r in selection.get("ranked", [])]),
    )
    step("research", {"verdict": research.get("verdict"), "claims": len(research.get("claims") or []),
                      "sources": len(research.get("sources") or []),
                      "contradictions": len(research.get("contradictions") or []),
                      "limitations": len(research.get("limitations") or [])})

    script = script_studio.write_script(selected_topic, research, seconds=seconds, strict_research=True)
    step("script", {"title": script.get("title"), "words": script.get("word_count"),
                    "archetype": script.get("hook_archetype"), "slop": script.get("slop_score"),
                    "rewrites": script.get("rewrites")})
    _log(f"Script: {script.get('title')} ({script.get('word_count')} words, "
         f"hook '{script.get('hook', '')[:60]}')")

    audio_path = work / "voice.mp3"
    voice = generate_voice(script.get("voice_text", ""), audio_path)
    duration = probe_duration(audio_path)

    ass_path = work / "subtitles.ass"
    captions = build_captions(script, audio_path, ass_path, duration)

    shots = motion_director.plan_shots(script, audio_duration=duration)
    plan = motion_director.estimate_render_plan(shots)
    step("shots", {"count": len(shots), "avg_shot": round(plan.get("avg_shot", 0), 2),
                   "sources": plan.get("asset_counts", {})})
    _log(f"Shot plan: {len(shots)} shots, avg {plan.get('avg_shot', 0):.2f}s")
    for shot in shots:
        print(f"      shot {shot['index']:>2} {shot['duration']:>5.2f}s {shot['source']:<10} {shot['asset_query']!r}", flush=True)

    output_path = work / "output_short.mp4"
    render = motion_render.render_video(
        shots, audio_path, output_path, work_dir=shots_dir, ass_path=ass_path
    )
    qa = motion_render.qa_video(output_path, min_duration=max(12.0, duration * 0.75), max_duration=duration * 1.35)
    step("render", {"path": str(output_path), "duration": qa.get("duration"), "shots": render.get("shots"),
                    "music": render.get("music"), "sfx": render.get("sfx_count")})
    _log(f"Rendered {output_path.name}: {qa.get('duration', 0):.1f}s, {qa.get('width')}x{qa.get('height')}")

    source_urls = script.get("source_urls") or []
    visuals = _describe_visuals(render.get("assets") or [], shots)
    metadata: dict[str, Any] = {
        "quality": "strong",
        "topic": selected_topic,
        "title": script.get("title", ""),
        "hook": script.get("hook", ""),
        "voice_text": script.get("voice_text", ""),
        "content_pillar": script.get("content_pillar", ""),
        "hook_archetype": script.get("hook_archetype", ""),
        "word_count": script.get("word_count", 0),
        "duration_seconds": qa.get("duration", duration),
        "broll_query": script.get("broll_query", ""),
        "tags": script.get("youtube_tags", []),
        "youtube_tags": script.get("youtube_tags", []),
        "instagram_hashtags": script.get("instagram_hashtags", []),
        "platform_copy": script.get("platform_copy", {}),
        "source_urls": source_urls,
        "beat_sheet": script.get("beat_sheet", []),
        "shots": shots,
        "visuals": visuals,
        "captions": captions,
        "critic": script.get("critic", {}),
        "slop_score": script.get("slop_score", 0),
        "research": {
            "verdict": research.get("verdict"),
            "claims": research.get("claims", []),
            "contradictions": research.get("contradictions", []),
            "unsupported_numbers": research.get("unsupported_numbers", []),
            "limitations": research.get("limitations", []),
            "sources": [
                {k: v for k, v in source.items() if k in {"url", "title", "publisher", "published", "ok"}}
                for source in (research.get("sources") or [])
            ],
        },
        "topic_selection": {
            "score": chosen.get("total_score"),
            "angle": chosen.get("angle", ""),
            "method": selection.get("method", ""),
            "rejected": selection.get("rejected", [])[:5],
        },
        "voice": {"provider": voice.get("provider"), "duration": qa.get("duration", duration)},
        "steps": steps,
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "video_path": str(output_path),
    }
    return metadata


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the strong editorial pipeline")
    parser.add_argument("--topic", default="", help="Force a specific topic")
    parser.add_argument("--seconds", type=int, default=35)
    parser.add_argument("--work-dir", default=str(ROOT / "outputs"))
    parser.add_argument("--min-topic-score", type=int, default=DEFAULT_MIN_TOPIC_SCORE)
    parser.add_argument("--out", default="", help="Write the metadata JSON here")
    args = parser.parse_args(argv)

    metadata = run(
        args.topic or None,
        seconds=args.seconds,
        work_dir=Path(args.work_dir),
        min_topic_score=args.min_topic_score,
    )
    out_path = Path(args.out) if args.out else ROOT / "data" / "metadata_strong.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "success",
        "title": metadata["title"],
        "video_path": metadata["video_path"],
        "duration_seconds": metadata["duration_seconds"],
        "shots": len(metadata["shots"]),
        "claims": len(metadata["research"]["claims"]),
        "word_count": metadata["word_count"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
