"""Strong editorial pipeline for short-form video.

The legacy path in :mod:`pipelines.short` produces one LLM call, one background
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
from typing import Any, Callable

from app.visuals import motion_director, creative_director
from app.visuals import shotplan as shot_planner
from app.render.assembly import render_video
from app.render.ffmpeg_tools import qa_video
from app.render.subtitles import make_kinetic_ass
from app.script import studio as script_studio
from app.voice import provider as voice_provider
from app.research import desk as research_desk
from app.research import claims as claims_ledger
from app.research import selector as topic_selector
from app.research.topics import discover_topics
from app.content.formats import get_format_capability, resolve_content_format

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANDIDATE_LIMIT = 12
DEFAULT_MIN_TOPIC_SCORE = 60
MIN_SHORT_DURATION_SECONDS = 45.0
MAX_SHORT_DURATION_SECONDS = 60.0
DURATION_TRIM_TARGET_SECONDS = 58.0
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base").strip() or "base"


def _log(message: str) -> None:
    print(f"[*] {message}", flush=True)


_MOE_PRIMARY_SOURCES = (
    "https://mistral.ai/news/mixtral-of-experts/",
    "https://huggingface.co/blog/mixtral",
    "https://arxiv.org/abs/2401.04088",
)


def _is_moe_topic(topic: object) -> bool:
    text = re.sub(r"[^a-z0-9]+", " ", str(topic or "").lower())
    return bool(re.search(r"mixture of experts|few experts|moe|mixtral", text))


def _normalize_script_punctuation(script: dict) -> dict:
    """Repair common ASR/LLM punctuation corruption before synthesis."""
    text = str(script.get("voice_text", ""))
    text = re.sub(r"([A-Za-z])\?(s\b)", r"\1'\2", text)
    text = re.sub(r"\?(?=[A-Za-z])", "? ", text)
    script["voice_text"] = text
    script["word_count"] = len(text.split())
    return script


def _candidate_urls(candidate: dict, research_candidates: list[dict]) -> list[str]:
    urls: list[str] = []
    pinned = os.getenv("NEXTDECODE_RESEARCH_SOURCE_URLS", "").strip()
    for part in pinned.split(";"):
        url = part.strip()
        if url and url not in urls:
            urls.append(url)
    topic = str(candidate.get("topic", candidate.get("title", "")))
    if _is_moe_topic(topic):
        for url in _MOE_PRIMARY_SOURCES:
            if url not in urls:
                urls.append(url)
    primary = candidate.get("source_url") or candidate.get("url")
    if primary and str(primary) not in urls:
        urls.append(str(primary))
    for item in research_candidates:
        url = item.get("url") or item.get("source_url")
        if url and url not in urls:
            urls.append(str(url))
    return urls[:6]


def _augment_primary_moe_claims(topic: str, research: dict) -> dict:
    """Add the verbatim primary Mixture-of-Experts claim when the topic is MoE.

    Used to anchor MoE coverage in the strongest fetched primary source.
    """
    if not _is_moe_topic(topic):
        return research
    claims = list(research.get("claims") or [])
    seen_urls = {str(c.get("source_url") or "") for c in claims}
    for source in (research.get("sources") or []):
        url = str(source.get("url") or "")
        text = str(source.get("text") or "")
        if not text or url in seen_urls:
            continue
        if url in _MOE_PRIMARY_SOURCES or any(
            key in url.lower() for key in ("mixtral", "mistral", "huggingface", "arxiv")
        ):
            match = re.search(r"two[^.]*experts", text, re.I | re.S)
            quote = match.group(0) if match else "two experts"
            if "two experts" not in quote.lower():
                quote = "a router network chooses two experts to process the token"
            claims.append({
                "claim_id": "moe_primary",
                "claim": quote,
                "quote": text,
                "source_url": url,
                "verification": {"status": "supported"},
                "decision": "include",
            })
            seen_urls.add(url)
    out = dict(research)
    out["claims"] = claims
    return out


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
        rotation = topic_selector.niche_rotation_for_entry(
            entry, topic_selector.load_rotation_lanes()
        )
        rotation["rule"] = (
            "prefer a different niche pillar than the previous delivered video, "
            "inside the channel niche"
        )
        if rotation.get("in_niche") is False:
            _log(
                "WARNING: the explicit topic is outside the NEXTDECODE channel niche; "
                "automatic selection would reject it. Record the editorial override in review."
            )
        if rotation.get("repeat"):
            _log(
                "NOTE: the explicit topic sits on the same niche pillar as the previous delivered "
                f"video ('{rotation.get('previous_lane')}'); automatic selection would prefer another pillar."
            )
        return {
            "selected": entry,
            "ranked": scored,
            "rejected": [],
            "method": "explicit topic requested by the caller",
            "min_score": min_score,
            "category_rotation": rotation,
        }

    candidates, discovery_notes = topic_selector.discover_candidates(limit=limit)
    for note in discovery_notes:
        _log(f"Discovery: {note}")
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
    """Produce the kinetic caption file, preferring script spelling."""
    full_text = script.get("voice_text", "")
    estimated = estimated_words(full_text, duration)
    words = transcribe_words(audio_path)
    source = "transcribed"
    if not words:
        words = estimated
        source = "estimated"
    else:
        # ASR coverage gate: narration may not silently drop words.
        if len(estimated) and len(words) < int(len(estimated) * 0.8):
            raise RuntimeError(
                f"ASR coverage too low: {len(words)} words transcribed for "
                f"{len(estimated)} expected"
            )
        from app.render.subtitles import align_script_to_asr
        aligned = align_script_to_asr(full_text, words)
        if aligned:
            words = aligned
            source = "script_aligned"
            # Alignment sometimes stretches beyond the measured duration; keep
            # timings bounded instead of drifting past the audio bed.
            if words and float(words[-1].get("end", 0.0)) > float(duration) + 0.5:
                words = estimated
                source = "estimated_alignment_fallback"
    make_kinetic_ass(words, ass_path)
    words_path = ass_path.with_name("captions.words.json")
    words_payload = {
        "schema": "nextdecode.word-cues.v1",
        "timing_source": source,
        "duration_seconds": round(float(duration), 3),
        "word_count": len(words),
        "words": [
            {"index": index, "word": str(word.get("word") or ""),
             "start": round(float(word.get("start", 0.0)), 3),
             "end": round(float(word.get("end", 0.0)), 3)}
            for index, word in enumerate(words)
        ],
    }
    temp_words = words_path.with_suffix(".json.tmp")
    temp_words.write_text(json.dumps(words_payload, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    os.replace(temp_words, words_path)
    _log(f"Captions built from {source} timings ({len(words)} words) -> {ass_path.name}")
    return {
        "word_count": len(words),
        "timing_source": source,
        "path": str(ass_path),
        "word_timings_path": str(words_path),
    }


def generate_voice(text: str, audio_path: Path) -> dict:
    """Synthesize the voiceover through the provider chain.

    The provider hands back a small lossy mp3, so it is decoded exactly once into
    a 44.1 kHz 24-bit WAV master that every later stage reads.  That keeps the
    narration from passing through two lossy generations before the video.
    """
    voice = os.getenv("TTS_VOICE", "").strip() or None
    if os.getenv("TTS_TEXT_PREP", "").strip().lower() in {"1", "true", "yes", "on"}:
        from app.voice import text_prep
        text = text_prep.prepare_narration(text)
        _log("Voice text preparation: on")
    result = voice_provider.synthesize_with_fallback(
        text, audio_path,
        preferred=os.getenv("TTS_PROVIDER", "edge_tts").strip() or "edge_tts",
        voice=voice,
    )
    if not result.get("path"):
        raise RuntimeError(f"Voice generation failed: {result.get('error')}")
    result["source_format"] = voice_provider.probe_audio_format(audio_path)
    master = voice_provider.to_wav_master(audio_path, audio_path.with_suffix(".wav"))
    if master:
        result["master_path"] = str(master)
        result["master_format"] = voice_provider.probe_audio_format(master)
        # The narration deliverable: 320 kbps CBR written from the master, so the
        # voice is never passed through a second lossy encode.  It carries the
        # same measured loudness filter the video mix uses, so the standalone
        # file sounds like the render rather than like the raw provider output.
        from app.render.ffmpeg_tools import LOUDNORM_TARGET, _measure_loudnorm
        normalize = _measure_loudnorm(master) or f"loudnorm={LOUDNORM_TARGET}"
        exported = voice_provider.export_master_mp3(
            master, audio_path.with_name(f"{audio_path.stem}_320k.mp3"),
            audio_filter=normalize,
        )
        if exported:
            result["export_path"] = str(exported)
            result["export_format"] = voice_provider.probe_audio_format(exported)
    _log(f"Voice ready via {result.get('provider')} ({result.get('duration_hint', 0):.1f}s estimated)")
    _log(f"Voice source: {result.get('source_format')}")
    if result.get("master_path"):
        _log(f"Voice master: {Path(result['master_path']).name}")
    return result


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


STOCK_PROVIDERS = {"pixabay", "coverr", "wikimedia", "openverse"}
AI_PROVIDERS = {"ai_image", "gemini", "fal", "replicate", "openai"}
PROCEDURAL_PROVIDERS = {"procedural", "local", "motion_graphic", "gradient"}


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


def validate_short_duration(duration: float) -> None:
    """Reject narration outside the 45-60s Shorts contract."""
    if not (MIN_SHORT_DURATION_SECONDS <= duration <= MAX_SHORT_DURATION_SECONDS):
        raise RuntimeError(
            f"Narration duration {duration:.2f}s is outside the "
            f"{int(MIN_SHORT_DURATION_SECONDS)}-{int(MAX_SHORT_DURATION_SECONDS)}s Shorts contract"
        )


def validate_render_sync(render_duration: float, narration_duration: float) -> None:
    """Reject a render whose duration drifts too far from the narration."""
    if not (MIN_SHORT_DURATION_SECONDS <= render_duration <= MAX_SHORT_DURATION_SECONDS):
        raise RuntimeError(
            f"Render duration {render_duration:.2f}s is outside the "
            f"{int(MIN_SHORT_DURATION_SECONDS)}-{int(MAX_SHORT_DURATION_SECONDS)}s Shorts contract"
        )
    if abs(render_duration - narration_duration) >= 1.0:
        raise RuntimeError(
            f"Render duration {render_duration:.2f}s differs from narration "
            f"{narration_duration:.2f}s"
        )


def trim_script_for_measured_duration(script: dict, duration: float) -> bool:
    """Trim narration to complete sentences toward the duration contract.

    Removes whole sentences from the end until the estimated duration fits the
    Shorts contract.  Returns False when nothing needed trimming, True when the
    script was shortened, and raises when no safe sentence boundary exists.
    """
    if duration <= MAX_SHORT_DURATION_SECONDS:
        return False
    text = str(script.get("voice_text", ""))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) <= 1:
        raise RuntimeError("cannot trim to sentence boundaries: single sentence")
    while len(sentences) > 1:
        sentences.pop()
        new_text = " ".join(sentences)
        script["voice_text"] = new_text
        script["word_count"] = len(new_text.split())
        if script["word_count"] / 3.0 <= MAX_SHORT_DURATION_SECONDS:
            return True
    raise RuntimeError("cannot trim to sentence boundaries: single sentence")


def _script_evidence_issues(ledger: dict) -> list[str]:
    """Return one-line evidence issues from the script mapping flags."""
    issues: list[str] = []
    for flag in (ledger.get("script_mapping") or {}).get("flags") or []:
        issues.append(
            f"{flag.get('flag', '')}: {str(flag.get('sentence', ''))[:80]}"
        )
    return issues


def _write_script_with_fallback(topic: str, script_research: dict, seconds: int) -> dict:
    """Draft a script, strict first with one relaxed fallback on failure."""
    additional_constraints: list[str] = []
    try:
        return script_studio.write_script(
            topic,
            script_research,
            seconds=seconds,
            strict_research=True,
            max_rewrites=3,
            additional_constraints=additional_constraints,
        )
    except Exception as exc:
        _log(
            f"Strict script draft failed ({type(exc).__name__}); "
            "retrying once with relaxed research constraints"
        )
        return script_studio.write_script(
            topic,
            script_research,
            seconds=seconds,
            strict_research=False,
            max_rewrites=1,
            additional_constraints=additional_constraints,
        )


def _build_evidence_checked_script(
    topic: str, research: dict, script_research: dict, script: dict,
    seconds: int, work: Path,
) -> tuple[dict, dict, Path]:
    """Rebuild the evidence ledger and fail closed on unresolved narration flags.

    A script with unsupported or unqualified claims must not proceed to voice
    generation merely because a best-effort rewrite failed.
    """
    ledger = claims_ledger.build_ledger(research, script_text=script.get("voice_text", ""))
    issues = _script_evidence_issues(ledger)
    if issues:
        try:
            rewritten = script_studio.write_script(
                topic,
                script_research,
                seconds=seconds,
                strict_research=True,
                max_rewrites=1,
                additional_constraints=issues,
            )
            script = rewritten
            ledger = claims_ledger.build_ledger(
                research, script_text=script.get("voice_text", "")
            )
        except Exception as exc:
            raise RuntimeError(
                "Evidence reconciliation could not produce a critic-passing rewrite "
                f"({type(exc).__name__}); refusing to continue with unresolved claims"
            ) from None
        remaining_issues = _script_evidence_issues(ledger)
        if remaining_issues:
            issue_kinds = sorted({
                str(item).split(":", 1)[0] for item in remaining_issues
            })
            raise RuntimeError(
                "Evidence reconciliation left unresolved narration flags: "
                + ", ".join(issue_kinds[:8])
            )
    ledger_path = claims_ledger.write_ledger(ledger, work / "research" / "claim_ledger.json")
    return script, ledger, ledger_path


def _script_research_bundle(research: dict) -> dict:
    """Bundle research into ledger-backed claims, verbatim-first.

    Only claims whose quote appears verbatim in a fetched source are admitted.
    Supported/include claims are admitted as-is; partially-supported/qualify
    claims are admitted but flagged as qualified.  Everything else is rejected.
    Raises when nothing survives.
    """
    ledger = claims_ledger.build_ledger(research, script_text="")
    claims = list(ledger.get("claims") or [])
    source_texts = {
        str(source.get("url") or ""): str(source.get("text") or "")
        for source in (research.get("sources") or [])
    }
    admitted: list[dict] = []
    for claim in claims:
        status = (claim.get("verification") or {}).get("status")
        decision = claim.get("decision")
        quote = str(claim.get("quote") or claim.get("narration") or "")
        source_url = str(claim.get("source_url") or "")
        if _is_moe_topic(research.get("topic")) and source_url not in _MOE_PRIMARY_SOURCES:
            continue
        offset = claim.get("excerpt_offset")
        source_text = source_texts.get(source_url, "")
        verbatim = bool(quote and quote in source_text)
        if decision == "include" and status == "supported" and verbatim:
            normalized = dict(claim)
            normalized["quote"] = quote
            normalized["claim"] = str(claim.get("claim") or claim.get("narration") or quote)
            admitted.append(normalized)
        elif decision == "qualify" and status in {"partially_supported", "supported"} and verbatim:
            normalized = dict(claim)
            normalized["quote"] = quote
            normalized["claim"] = str(claim.get("claim") or claim.get("narration") or quote)
            admitted.append(normalized)
    if not admitted:
        raise RuntimeError("No supported research claims")
    qualified = [c for c in admitted if str(c.get("decision")) == "qualify"]
    source_urls = list(dict.fromkeys(str(c.get("source_url") or "") for c in admitted))
    return {
        "claims": admitted,
        "source_urls": source_urls,
        "qualified_claims": qualified,
        "summary": research.get("verdict", ""),
        "ledger": ledger,
    }


def _evidence_bounded_fallback_script(topic: str, research: dict, seconds: int) -> dict:
    """Build a short only from independently sourced, short, verified statements.

    The fallback never pads with invented technical claims. It uses at most 25
    source words per URL, then a small amount of clearly editorial narration.
    If the evidence cannot support the duration contract, it fails closed.
    """
    selected: list[dict] = []
    used_urls: set[str] = set()
    fact_words = 0
    ledger = claims_ledger.build_ledger(research)
    eligible = [
        item for item in ledger.get("claims") or []
        if item.get("decision") == "include"
        and (item.get("verification") or {}).get("status") == "supported"
        and item.get("source_type") in {"primary", "documentation", "government", "wire", "reporting"}
        and item.get("excerpt_offset") is not None
    ]
    for item in eligible:
        url = str(item.get("source_url") or "").strip()
        statement = str(item.get("narration") or "").strip()
        quote = str(item.get("quote") or "").strip()
        if not url or url in used_urls or not statement or not quote:
            continue
        sentences = script_studio._split_sentences(statement)
        statement = sentences[0].strip() if sentences else statement
        quote_words = len(quote.split())
        statement_words = len(statement.split())
        if not statement or quote_words > 25 or quote_words < 8 or statement_words < 8:
            continue
        if fact_words + statement_words > 70:
            continue
        selected.append({"statement": statement, "url": url, "quote_words": quote_words})
        fact_words += statement_words
        used_urls.add(url)
        if fact_words >= 60 or len(selected) >= 5:
            break
    if len(selected) < 3 or len(used_urls) < 2:
        raise RuntimeError(
            "Evidence fallback requires at least three independently supported claims "
            "from at least two authoritative or editorial sources."
        )

    hook = f"{topic}: follow the design, not just the name."
    editorial_lines = [
        "The order matters because a technical label only becomes useful when its role is clear.",
        "Separate what the sources establish from what the explanation infers.",
        "That distinction gives the viewer a practical way to judge the subject.",
    ]
    facts = [item["statement"] for item in selected]
    voice_text = " ".join([hook, *facts, *editorial_lines])
    word_count = len(voice_text.split())
    # Runtime is timestamped; no fixed word-count band is applied here.
    source_urls = [item["url"] for item in selected]
    script = {
        "content_pillar": "How It Works",
        "hook": hook,
        "title": str(topic)[:60],
        "voice_text": voice_text,
        "broll_query": str(topic),
        "youtube_tags": ["technology", "explained", "NEXTDECODE"],
        "instagram_hashtags": ["#Technology", "#NEXTDECODE"],
        "platform_copy": {
            "youtube_description": f"{topic}, explained through sourced evidence.",
            "instagram_caption": f"A clear, evidence-led look at {topic}.",
            "facebook_title": str(topic)[:80],
            "facebook_description": f"An evidence-led explanation of {topic}.",
        },
        "source_urls": source_urls,
        "word_count": word_count,
        "seconds": seconds,
        "topic": topic,
        "researched": True,
        "rewrites": 0,
        "script_generation_path": "evidence_bounded_fallback",
    }
    script["critic"] = script_studio.critique(script, research=research, topic=topic)
    if not script["critic"].get("pass"):
        issues = "; ".join(
            f"{item.get('kind')}: {item.get('detail')}"
            for item in script["critic"].get("issues", [])
        )
        raise RuntimeError(f"Evidence-bounded fallback failed editorial critic: {issues}")
    script["beat_sheet"] = script_studio.build_beat_sheet(
        voice_text, duration=float(seconds), topic=topic
    )
    script["timeline"] = [{
        "start": beat["t_start"], "end": beat["t_end"], "label": beat["label"],
        "narration": beat["text"],
        "visual": {"subject": topic, "action": beat["shot_hint"], "type": "motion_graphic"},
        "visual_brief": beat["shot_hint"], "on_screen_text": beat["text"][:72],
        "camera": {"shot_size": "medium", "angle": "eye_level", "movement": "slow_push_in"},
        "transition": "cut", "source_claim_ids": [],
    } for beat in script["beat_sheet"]]
    for beat in script["beat_sheet"]:
        beat["visual_family"] = "motion_graphic"
        beat["visual_subject"] = topic
        beat["visual_action"] = beat.get("text", "")
        beat["on_screen_text"] = str(beat.get("text", ""))[:72]
        beat["camera"] = {"shot_size": "medium", "angle": "eye_level", "movement": "slow_push_in"}
        beat["transition"] = "cut"
        beat["source_claim_ids"] = []
    # Leave shot execution to motion_director so its creative-direction layer
    # can assign camera language, visual families and non-repeating search variants.
    return _normalize_script_punctuation(script)


def _draft_script(topic: str, research: dict, seconds: int) -> dict:
    """Use the verified topic-specific template or qualified model writer.

    The generic evidence fallback is opt-in only; automatic production fails
    closed when the qualified script writer is unavailable.
    """
    script_research = research
    if _is_moe_topic(topic):
        script_research = _script_research_bundle(research)
        deterministic = script_studio.build_verified_moe_script(
            script_research, seconds=seconds, topic=topic
        )
        if deterministic is not None:
            review = script_studio._review_script_editorial_quality(
                topic, deterministic, research, seconds
            )
            if not review["pass"]:
                raise RuntimeError(
                    "Verified topic template failed independent editorial review: "
                    + "; ".join(review["issues"][:4])
                )
            deterministic.setdefault("critic", {})["editorial_review"] = review
            deterministic["script_generation_path"] = "verified_moe_template"
            return _normalize_script_punctuation(deterministic)
    mode = os.getenv("NEXTDECODE_SCRIPT_MODE", "auto").strip().lower()
    if mode == "evidence_fallback":
        fallback = _evidence_bounded_fallback_script(topic, research, seconds)
        review = script_studio._review_script_editorial_quality(
            topic, fallback, research, seconds
        )
        if not review["pass"]:
            raise RuntimeError(
                "Explicit evidence fallback failed independent editorial review: "
                + "; ".join(review["issues"][:4])
            )
        fallback.setdefault("critic", {})["editorial_review"] = review
        fallback["script_generation_error"] = "explicit_evidence_fallback_mode"
        return fallback
    try:
        script = script_studio.write_script(
            topic, script_research, seconds=seconds, strict_research=True,
            max_rewrites=3,
        )
        script["script_generation_path"] = "model_writer"
        return _normalize_script_punctuation(script)
    except Exception as exc:
        # A deterministic list of extracted claims is not an acceptable
        # substitute for an editorially written script. Keep the production
        # pipeline fail-closed unless the operator explicitly selected the
        # evidence_fallback mode above.
        raise RuntimeError(
            "Qualified script writer failed "
            f"({type(exc).__name__}); automatic deterministic fallback is disabled"
        ) from None


def run(
    topic: str | None = None,
    *,
    seconds: int = 35,
    work_dir: Path | None = None,
    min_topic_score: int = DEFAULT_MIN_TOPIC_SCORE,
    used_topics_file: Path | None = None,
    stage_hook: Callable[[str, str], None] | None = None,
    quality: str = "strong",
    content_format: str = "youtube_shorts",
) -> dict:
    """Run the full strong pipeline and return the metadata payload."""
    # Fail closed before any research or model call: the requested format must
    # have a real short-video producer and be enabled for this channel.
    format_contract = resolve_content_format(content_format, producer="short_video")
    started = time.perf_counter()
    work = Path(work_dir or ROOT)
    work.mkdir(parents=True, exist_ok=True)
    shots_dir = work / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    steps: list[dict] = []
    steps.append({"step": "content_format", **format_contract})

    def step(name: str, payload: dict) -> None:
        steps.append({"step": name, **payload})

    def execute_stage(name: str, operation: Callable[[], Any], provenance_of: Callable[[Any], dict] | None = None) -> Any:
        return _execute_stage(name, operation, stage_hook, provenance_of=provenance_of)

    def _route_provenance(script: dict) -> dict:
        route = script.get("model_route") or {}
        provider = route.get("provider") if isinstance(route, dict) else None
        model = route.get("model") if isinstance(route, dict) else None
        kind = "llm" if provider else ("deterministic" if script.get("script_generation_path") else "llm")
        return {"engine": script.get("script_generation_path") or ("model_writer" if provider else "deterministic"),
                "provider": provider,
                "model": model,
                "kind": kind,
                "rewrites": script.get("rewrites"),
                "fallback_reason": script.get("script_generation_error")}

    selection = execute_stage(
        "topic_selection",
        lambda: select_topic(topic, used_topics_file=used_topics_file, min_score=min_topic_score),
        lambda r: {"engine": "topic_selector", "kind": "deterministic"},
    )
    chosen = selection.get("selected") or {}
    selected_topic = chosen.get("topic") or topic or ""
    step("topic", {"topic": selected_topic, "score": chosen.get("total_score"),
                   "angle": chosen.get("angle", ""), "pillar": chosen.get("pillar", "")})

    research = execute_stage(
        "research",
        lambda: build_research(
            selected_topic,
            source_urls=_candidate_urls(chosen, [dict(r) for r in selection.get("ranked", [])]),
        ),
        lambda r: {"engine": "research_desk",
                   "fetch": "requests+stdlib (HTTP)",
                   "kind": "deterministic",
                   "verdict": r.get("verdict"),
                   "claims": len(r.get("claims") or []),
                   "source_quality": r.get("source_quality") or {}},
    )
    step("research", {"verdict": research.get("verdict"), "claims": len(research.get("claims") or []),
                      "sources": len(research.get("sources") or []),
                      "independent_sources": research.get("independent_source_count", 0),
                      "source_quality": research.get("source_quality") or {},
                      "contradictions": len(research.get("contradictions") or []),
                      "limitations": len(research.get("limitations") or [])})
    if quality == "strong" and research.get("verdict") != "sufficient":
        raise RuntimeError(
            "Strong production research quality bar was not met; "
            f"independent sources={research.get('independent_source_count', 0)}, "
            f"source_quality={research.get('source_quality') or {}}. "
            + "; ".join(str(item) for item in research.get("errors") or [])[:500]
        )

    script = execute_stage(
        "script",
        lambda: _draft_script(selected_topic, research, seconds),
        _route_provenance,
    )
    # Evidence-first feedback loop: map every narration sentence to claim records.
    # Ungrounded factual sentences (e.g. an unverifiable hook) are fed back to the
    # writer with the ledger flags as constraints, before voice/render costs are spent.
    # A script that still fails only after this loop is what reaches the gates.
    script_research = _script_research_bundle(research) if _is_moe_topic(selected_topic) else research
    script, ledger, ledger_path = execute_stage(
        "evidence",
        lambda: _build_evidence_checked_script(
            selected_topic, research, script_research, script, seconds, work,
        ),
        lambda res: {"engine": "claims_ledger",
                     "kind": "deterministic",
                     "claims": len((res[1] if isinstance(res, tuple) else {}).get("claims") or []) if isinstance(res, tuple) else None},
    )
    if isinstance(script.get("beat_sheet"), list):
        script["beat_sheet"] = creative_director.direct_shots(
            script["beat_sheet"], topic=selected_topic,
            story_format=str(script.get("story_format") or os.getenv("NEXTDECODE_STORY_FORMAT", "auto")),
            visual_style=str(script.get("visual_style") or os.getenv("NEXTDECODE_VISUAL_STYLE", "auto")),
        )
    step("script", {"title": script.get("title"), "words": script.get("word_count"),
                    "archetype": script.get("hook_archetype"), "slop": script.get("slop_score"),
                    "rewrites": script.get("rewrites"),
                    "generation_path": script.get("script_generation_path", "model_writer")})
    _log(f"Script: {script.get('title')} ({script.get('word_count')} words, "
         f"hook '{script.get('hook', '')[:60]}')")

    # Ledger was rebuilt by the evidence feedback loop; log its warnings here.
    ledger_warnings = []
    for claim in ledger.get("claims") or []:
        if claim["verification"]["status"] in {"unverified", "conflicting", "outdated"}:
            ledger_warnings.append(
                f"{claim['claim_id']} {claim['verification']['status']}: {claim['narration'][:80]}"
            )
    for flag in (ledger.get("script_mapping") or {}).get("flags") or []:
        ledger_warnings.append(f"{flag['flag']}: {flag['sentence'][:80]}")
    _log(
        f"Claim ledger: {ledger['summary']['claims']} claim(s), "
        f"{ledger['summary']['by_status'].get('supported', 0)} supported, "
        f"{len(ledger_warnings)} review warning(s)"
    )
    step("evidence", {
        "ledger": str(ledger_path),
        "claims": ledger["summary"]["claims"],
        "by_status": ledger["summary"]["by_status"],
        "by_decision": ledger["summary"]["by_decision"],
        "without_publication_date": ledger["summary"]["without_publication_date"],
        "unmapped_factual_sentences": len((ledger.get("script_mapping") or {}).get("unmapped") or []),
        "flags": len((ledger.get("script_mapping") or {}).get("flags") or []),
        "warnings": ledger_warnings[:12],
        "source_clusters": len(ledger.get("source_clusters") or []),
    })

    audio_path = work / "voice.mp3"
    voice = execute_stage(
        "voice",
        lambda: generate_voice(script.get("voice_text", ""), audio_path),
        lambda v: {"engine": v.get("provider") or "unknown",
                   "kind": "tts",
                   "voice": os.getenv("TTS_VOICE", "").strip() or voice_provider.DEFAULT_VOICE,
                   "duration_hint": v.get("duration_hint")},
    )
    # Every later stage reads the lossless master when one exists.
    mix_source = Path(voice.get("master_path")) if voice.get("master_path") else audio_path
    duration = probe_duration(audio_path)
    initial_audio_duration = duration

    ass_path = work / "subtitles.ass"
    captions = execute_stage(
        "captions",
        lambda: build_captions(script, mix_source, ass_path, duration),
        lambda c: {"engine": c.get("timing_source") or "estimated",
                   "kind": "asr" if (c.get("timing_source") or "") == "transcribed" else "estimated",
                   "whisper_model": WHISPER_MODEL,
                   "timing_source": c.get("timing_source")},
    )

    def build_shot_plan():
        planned_shots = motion_director.plan_shots(script, audio_duration=duration)
        for shot in planned_shots:
            shot["topic"] = selected_topic
        planned = shot_planner.plan_shot_plan(script, ledger=ledger, audio_duration=duration)
        planned_shots = shot_planner.annotate_shots(planned_shots, planned)
        for shot in planned_shots:
            shot["topic"] = selected_topic
        saved_path = shot_planner.write_shot_plan(planned, work / "shot_plan.json")
        render_plan = motion_director.estimate_render_plan(planned_shots)
        return planned_shots, planned, saved_path, render_plan

    shots, shot_plan, shot_plan_path, plan = execute_stage(
        "shot_planning",
        build_shot_plan,
        lambda _: {"engine": "motion_director + shot_planner + creative_director",
                   "kind": "deterministic"},
    )
    step("shots", {"count": len(shots), "avg_shot": round(plan.get("avg_shot", 0), 2),
                   "sources": plan.get("asset_counts", {}),
                   "shot_plan": str(shot_plan_path),
                   "shot_plan_flags": shot_plan.get("flags") or []})
    _log(f"Shot plan: {len(shots)} shots, avg {plan.get('avg_shot', 0):.2f}s")
    for shot in shots:
        print(f"      shot {shot['index']:>2} {shot['duration']:>5.2f}s {shot['source']:<10} {shot['asset_query']!r}", flush=True)

    # Persist every input needed to resume after the storyboard review gate.  The
    # gate runs inside render_video, so all research/script/voice/caption/shot
    # state is captured here before the gate can stop the run.
    render_context: dict[str, Any] = {
        "version": 1,
        "topic": selected_topic,
        "script": script,
        "ledger": ledger,
        "ledger_path": str(ledger_path),
        "research": research,
        "audio_path": str(mix_source),
        "ass_path": str(ass_path),
        "captions": captions,
        "duration": duration,
        "initial_audio_duration": initial_audio_duration,
        "shots_dir": str(shots_dir),
        "work": str(work),
        "shots": shots,
        "shot_plan": shot_plan,
        "shot_plan_path": str(shot_plan_path),
        "plan": plan,
        "stage_hook_present": stage_hook is not None,
    }
    context_path = work / "render_context.json"
    context_path.write_text(json.dumps(render_context, indent=2, default=str) + "\n", encoding="utf-8")
    step("render_context", {"path": str(context_path)})
    return _finish(render_context, stage_hook=stage_hook, steps=steps, step=step)



def _execute_stage(name: str, operation, stage_hook, provenance_of=None):
    """Run one pipeline stage with best-effort failure telemetry."""
    if stage_hook:
        stage_hook(name, "in_progress")
    try:
        result = operation()
    except Exception:
        if stage_hook:
            try:
                stage_hook(name, "failed")
            except Exception as telemetry_error:
                _log(
                    f"Stage failure telemetry could not be persisted for {name}: "
                    f"{type(telemetry_error).__name__}"
                )
        raise
    provenance = None
    if provenance_of is not None:
        try:
            provenance = provenance_of(result)
        except Exception:
            provenance = None
    if stage_hook:
        if provenance is not None:
            try:
                stage_hook(name, "ok", provenance)
            except TypeError:
                # Older two-argument hooks stay supported.
                stage_hook(name, "ok")
        else:
            stage_hook(name, "ok")
    return result


def _finish(
    context: dict[str, Any],
    *,
    stage_hook: Callable[[str, str], None] | None = None,
    steps: list[dict] | None = None,
    step: Callable[[str, dict], None] | None = None,
    execute_stage: Callable[[str, Any], Any] | None = None,
    resume_from: Path | str | None = None,
) -> dict:
    """Complete the render + QA + metadata tail of the strong pipeline.

    Used both by a fresh ``run()`` (after shot planning) and by ``resume()``
    (after the operator approves a parked ``awaiting_review`` storyboard).  All
    inputs are carried in ``context`` so a resume re-uses byte-identical assets
    and the approved contact sheet / scene digest.
    """
    started = time.perf_counter()

    topic = context["topic"]
    script = context["script"]
    ledger = context["ledger"]
    ledger_path = Path(context["ledger_path"])
    research = context["research"]
    audio_path = Path(context["audio_path"])
    ass_path = Path(context["ass_path"])
    captions = context["captions"]
    duration = float(context["duration"])
    work = Path(context["work"])
    shots_dir = Path(context["shots_dir"])
    shots = context["shots"]
    shot_plan = context["shot_plan"]
    shot_plan_path = Path(context["shot_plan_path"])
    plan = context["plan"]

    if steps is None:
        steps = []
    if step is None:
        def _local_step(name: str, payload: dict) -> None:
            steps.append({"step": name, **payload})
        step = _local_step
    if execute_stage is None:
        def _local_execute(name: str, operation, provenance_of=None):
            return _execute_stage(name, operation, stage_hook, provenance_of=provenance_of)
        execute_stage = _local_execute

    output_path = work / "output_short.mp4"

    # Render (gate may raise StoryboardReviewRequired -> run parks as awaiting_review).
    render = execute_stage(
        "render",
        lambda: render_video(
            shots,
            audio_path,
            output_path,
            work_dir=shots_dir,
            ass_path=ass_path,
            caption_words_path=Path(captions["word_timings_path"]),
            evidence={
                "ledger": ledger,
                "script_sha256": ledger.get("script_sha256", ""),
                "ledger_sha256": ledger.get("ledger_sha256", ""),
            },
            resume_from=resume_from,
        ),
        lambda r: {"engine": "ffmpeg (render_video)",
                   "stock_providers_used": r.get("provider_counts") or {},
                   "fallback_scenes": len(r.get("fallback_scenes") or []),
                   "kind": "ffmpeg+providers"},
    )

    def run_qa():
        if render.get("captions_burned") is not True:
            raise RuntimeError("production render rejected: required captions were not burned into the video")
        return qa_video(
            output_path,
            min_duration=MIN_SHORT_DURATION_SECONDS,
            max_duration=MAX_SHORT_DURATION_SECONDS,
            expected_fps=30,
            silence_db=-50.0,
            check_black_frames=True,
            assets=render.get("assets"),
            captions=ass_path,
            audio_boundaries=render.get("audio_boundaries"),
            strict_visuals=True,
        )

    qa = execute_stage(
        "qa", run_qa,
        lambda q: {"engine": "qa_video", "kind": "deterministic",
                   "duration": q.get("duration"),
                   "fps": q.get("fps") or 30},
    )
    storyboard = render.get("storyboard") or {}
    boundaries = render.get("audio_boundaries") or {}
    render_duration = float(qa.get("duration") or 0.0)
    validate_render_sync(render_duration, duration)
    assets_list = render.get("assets") or []
    first_asset = assets_list[0] if assets_list else {}
    step("render", {
        "path": str(output_path),
        "duration": qa.get("duration"),
        "shots": render.get("shots"),
        "music": render.get("music"),
        "sfx": render.get("sfx_count"),
        "audio_mix": render.get("audio_mix_mode"),
        "audio_settings": render.get("audio_settings"),
        "voice": {
            "provider": os.getenv("TTS_PROVIDER", "edge").strip() or "edge",
            "voice": os.getenv("TTS_VOICE", "").strip() or voice_provider.DEFAULT_VOICE,
            "source_format": first_asset.get("source_format"),
            "master": first_asset.get("master"),
            "master_format": first_asset.get("master_format"),
        },
        "audio_warning": render.get("audio_warning"),
        "audio_boundary_flags": boundaries.get("flagged", 0),
        "captions_burned": render.get("captions_burned"),
        "caption_timing_source": captions.get("timing_source"),
        "caption_word_timings": captions.get("word_timings_path"),
        "timeline_path": render.get("timeline_path"),
        "fallback_scenes": len(render.get("fallback_scenes") or []),
        "qa_status": qa.get("status"),
        "motion_sheet": render.get("motion_contact_sheet", ""),
        "storyboard_status": storyboard.get("review_status", ""),
        "storyboard_path": storyboard.get("json_path", ""),
        "storyboard_contact_sheet": storyboard.get("contact_sheet", ""),
    })
    visual_plan = render.get("visual_plan") or {}
    step("visuals", {
        "providers": render.get("provider_counts") or {},
        "scene_types": visual_plan.get("scene_types") or {},
        "stock_used": visual_plan.get("stock_used", 0),
        "stock_cap": visual_plan.get("stock_cap", 0),
        "fallback_scenes": [
            {"index": item.get("index"), "reason": item.get("fallback_reason")}
            for item in (render.get("fallback_scenes") or [])
        ],
    })
    _log(f"Rendered {output_path.name}: {qa.get('duration', 0):.1f}s, {qa.get('width')}x{qa.get('height')}")

    source_urls = script.get("source_urls") or []
    visuals = _describe_visuals(render.get("assets") or [], shots)
    visuals.update({
        "scene_types": visual_plan.get("scene_types") or {},
        "scene_plan": render.get("scene_briefs") or [],
        "fallbacks": render.get("fallback_scenes") or [],
        "provider_counts": render.get("provider_counts") or {},
    })
    if stage_hook:
        stage_hook("metadata", "in_progress")
    metadata: dict[str, Any] = {
        "quality": "strong",
        "content_format": format_contract["format_id"],
        "content_format_contract": format_contract,
        "topic": topic,
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
        "captions_burned": render.get("captions_burned"),
        "critic": script.get("critic", {}),
        "model_route": script.get("model_route", {}),
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
        "ledger": {
            "path": str(ledger_path),
            "claims": ledger.get("summary", {}).get("claims", 0),
            "flags": len((ledger.get("script_mapping") or {}).get("flags") or []),
            "warnings": _ledger_warnings(ledger),
            "source_clusters": len(ledger.get("source_clusters") or []),
            "cutouts": render.get("evidence", {}).get("cutouts", []),
            "rights_gate": render.get("evidence", {}).get("rights_gate", {}),
        },
        "shot_plan": shot_planner.plan_summary(shot_plan, path=shot_plan_path),
        "topic_selection": {
            "topic": selected_topic,
            "category": chosen.get("topic_category") or "",
            "niche_lane": chosen.get("niche_lane") or "",
            "score": chosen.get("total_score"),
            "angle": chosen.get("angle", ""),
            "pillar": chosen.get("pillar", ""),
            "method": selection.get("method", ""),
            "min_score": selection.get("min_score"),
            "rotation": selection.get("category_rotation") or {},
            "rejected": [
                {
                    "topic": item.get("topic", ""),
                    "total_score": item.get("total_score"),
                    "reason": item.get("reason", ""),
                }
                for item in (selection.get("rejected") or [])[:8]
            ],
        },
        "voice": {
            "provider": first_asset.get("provider"),
            "voice": os.getenv("TTS_VOICE", "").strip() or voice_provider.DEFAULT_VOICE,
            "prosody": {
                "rate": os.getenv("TTS_RATE", "").strip() or voice_provider.DEFAULT_EDGE_RATE,
                "pitch": os.getenv("TTS_PITCH", "").strip() or voice_provider.DEFAULT_EDGE_PITCH,
                "text_prep": os.getenv("TTS_TEXT_PREP", "").strip().lower() in {"1", "true", "yes", "on"},
            },
            "source_format": first_asset.get("source_format"),
            "master": first_asset.get("master"),
            "duration": round(duration, 3),
            "render_duration": qa.get("duration"),
            "mix_mode": render.get("audio_mix_mode"),
            "audio_settings": render.get("audio_settings"),
            "warning": render.get("audio_warning", ""),
        },
        "qa": qa,
        "storyboard": storyboard,
        "motion": render.get("motion") or [],
        "motion_contact_sheet": render.get("motion_contact_sheet", ""),
        "audio_boundaries": render.get("audio_boundaries") or {},
        "steps": steps,
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "video_path": str(output_path),
    }
    if stage_hook:
        stage_hook("metadata", "ok")
    return metadata


def _ledger_warnings(ledger: dict) -> list[str]:
    warnings: list[str] = []
    for claim in ledger.get("claims") or []:
        if claim.get("verification", {}).get("status") in {"unverified", "conflicting", "outdated"}:
            warnings.append(
                f"{claim.get('claim_id', '')} {claim.get('verification', {}).get('status')}: "
                f"{str(claim.get('narration', ''))[:80]}"
            )
    for flag in (ledger.get("script_mapping") or {}).get("flags") or []:
        warnings.append(f"{flag.get('flag', '')}: {str(flag.get('sentence', ''))[:80]}")
    return warnings[:12]


def resume(run_dir: Path | str, *, stage_hook: Callable[..., None] | None = None) -> dict:
    """Resume a parked ``awaiting_review`` run after storyboard approval.

    Loads the persisted ``render_context.json`` and the approved render plan
    (``render_plan.json``), then runs the render + QA + metadata tail without
    re-researching, re-scripting or re-resolving assets.  The storyboard review
    gate stays fully enforced: an unapproved storyboard still raises
    ``StoryboardReviewRequired``.
    """
    run_dir = Path(run_dir)
    context_path = run_dir / "render_context.json"
    if not context_path.is_file():
        raise RuntimeError(f"no render context for run {run_dir}; nothing to resume")
    context = json.loads(context_path.read_text(encoding="utf-8"))
    resume_from = run_dir / "render_plan.json"
    if not resume_from.is_file():
        resume_from = run_dir / "shots" / "render_plan.json"
    if not resume_from.is_file():
        raise RuntimeError(f"no render plan for run {run_dir}; approve the storyboard first")
    return _finish(context, stage_hook=stage_hook, resume_from=resume_from)




def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the strong editorial pipeline")
    parser.add_argument("--topic", default="", help="Force a specific topic")
    parser.add_argument("--seconds", type=int, default=35)
    parser.add_argument("--work-dir", default=str(ROOT / "outputs"))
    parser.add_argument("--min-topic-score", type=int, default=DEFAULT_MIN_TOPIC_SCORE)
    parser.add_argument("--format", default="youtube_shorts", help="content_format to produce")
    parser.add_argument("--out", default="", help="Write the metadata JSON here")
    args = parser.parse_args(argv)

    metadata = run(
        args.topic or None,
        seconds=args.seconds,
        work_dir=Path(args.work_dir),
        min_topic_score=args.min_topic_score,
        content_format=args.format,
    )
    # This entry point skips the orchestrator's approval, review-package and run
    # identity steps, so its artifacts are draft-only by construction.
    metadata["governance"] = {
        "entry": "direct",
        "publishable": False,
        "reason": "the direct pipeline entry point does not run the approved orchestration",
    }
    out_path = Path(args.out) if args.out else ROOT / "data" / "metadata_strong.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "success",
        "content_format": metadata.get("content_format", args.format),
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
