#!/usr/bin/env python3
"""
Autonomous Short Video Creator
Zero-cost automated video generation for YouTube Shorts & Instagram Reels.
Powered by: Gemini (Free), Edge-TTS (Free), Pexels (Free), Whisper (Free), FFmpeg (Free).
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from app.script import pipeline as strong_pipeline
from app.script.short import PROFILE, SCRIPT_PROFILE, generate_script, record_topic
from app.tracking.run_tracker import start_run
from app.operations.video_archive import archive_video
SCRIPT_DIR = ROOT
load_dotenv(SCRIPT_DIR / ".env", override=True)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
DEMO_VIDEO_PATH = os.getenv("DEMO_VIDEO_PATH", "").strip()
DEFAULT_VOICE = os.getenv("TTS_VOICE", "en-US-ChristopherNeural").strip()

_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(key|token|api_key|apikey|access_token|authorization|password|secret)=([^&\s'\"]+)")
_TOKEN_SHAPE_RE = re.compile(
    r"\b(?:sk|pk|ghp|xoxb|ya29)[_\-][A-Za-z0-9_\-]{6,}|\bAIza[A-Za-z0-9_\-]{6,}")
_SECRET_ENV_PREFIXES = ("CF_", "ELEVENLABS_", "CARTESIA_", "OPENAI_", "GEMINI_", "GROQ_",
                        "TELEGRAM_", "GOOGLE_", "PEXELS_", "PIXABAY_", "YOUTUBE_",
                        "META_", "INSTAGRAM_", "FACEBOOK_")


def _failure_log() -> Path:
    return SCRIPT_DIR / "data" / "last_failure.json"


def _draft_governance(entry: str) -> dict:
    """Stamp non-governed producer paths as permanently draft-only."""
    if entry not in {"dry_run", "standard-legacy"}:
        raise ValueError(f"Unsupported draft governance entry: {entry}")
    return {
        "entry": entry,
        "publishable": False,
        "reason": "this producer path does not run the approved orchestration and review gates",
    }


def _redact(value: object) -> str:
    """Remove credential-shaped content before a failure reaches a log or file.

    The exception text from a downstream stage can carry an API key or a signed
    URL, so the raw message is never printed or stored.
    """
    text = str(value or "")
    for name, secret in os.environ.items():
        if len(secret) >= 8 and (
                name.endswith(("_KEY", "_TOKEN", "_SECRET"))
                or name.upper().startswith(_SECRET_ENV_PREFIXES)):
            text = text.replace(secret, "***")
    text = _SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=***", text)
    text = _TOKEN_SHAPE_RE.sub("***", text)
    return text[:500]


def _record_failure(stage: str, detail: object, quality: str) -> dict:
    """Write sanitized failure diagnostics without touching any successful output."""
    if isinstance(detail, BaseException) and detail.args:
        message = detail.args[0]
    else:
        message = str(detail)
    payload = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "quality": quality,
        "error_type": type(detail).__name__ if isinstance(detail, BaseException) else "PolicyRefusal",
        "detail": _redact(message),
        "exit_code": 1 if stage == "strong_pipeline" else 2,
    }
    log = _failure_log()
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"[!] failure diagnostics could not be written ({type(exc).__name__})")
    return payload


def generate_voiceover(text: str, output_path: Path, voice: str = DEFAULT_VOICE):
    """Generates natural neural voiceover via edge-tts with gTTS fallback."""
    print(f"[*] Generating speech with Edge-TTS voice '{voice}'...")
    cleaned_text = text.replace('"', '\\"').replace("\n", " ").strip()
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", cleaned_text,
        "--write-media", str(output_path)
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as exc:
        print(f"[!] edge-tts failed ({type(exc).__name__}); falling back to gTTS")
    if not output_path.exists() or output_path.stat().st_size == 0:
        from gtts import gTTS
        gTTS(text=text, lang="en").save(str(output_path))
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Failed to generate voiceover audio file.")
    print(f"[+] Voiceover generated: {output_path.name}")

def get_background_video(query: str, output_path: Path, duration_sec: float = 45.0):
    """Generate dynamic multi-scene background using Pollinations/Kling AI."""
    print(f"[*] Generating AI scenes for query: '{query}'...")
    try:
        from app.visuals import visual_assets
        work_dir = output_path.parent / "temp_ai_broll"
        work_dir.mkdir(exist_ok=True)
        clip_paths = []
        scene_count = 5
        clip_dur = max(3.5, duration_sec / scene_count)
        
        # Sub-prompts based on query
        prompts = [
            f"cinematic high tech {query}, futuristic interface, 8k",
            f"dark modern server room data center, {query}, glowing lights",
            f"close up autonomous AI technology core, {query}, moody lighting",
            f"digital financial analytics screen, {query}, high contrast",
            f"futuristic corporate executive boardroom at night, {query}"
        ]
        
        for idx, p in enumerate(prompts):
            img_res = visual_assets.generate_image(p, work_dir)
            if img_res and img_res.get("path") and Path(img_res["path"]).exists():
                img_path = img_res["path"]
                clip_path = work_dir / f"ai_clip_{idx}.mp4"
                total_frames = int(clip_dur * 30)
                zoom_cmd = (
                    f"scale=-2:1280,"
                    f"zoompan=z='min(zoom+0.0016,1.18)':d={total_frames}:"
                    f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280"
                )
                cmd = [
                    "ffmpeg", "-y", "-loop", "1", "-i", str(img_path),
                    "-vf", zoom_cmd,
                    "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                    "-t", str(clip_dur), str(clip_path)
                ]
                res = subprocess.run(cmd, capture_output=True)
                if res.returncode == 0 and clip_path.exists():
                    clip_paths.append(clip_path)

        if clip_paths:
            concat_list = work_dir / "concat.txt"
            concat_list.write_text("\n".join(f"file '{c.resolve()}'" for c in clip_paths))
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-c", "copy", str(output_path)
            ], check=True)
            print(f"[+] AI multi-scene background assembled: {len(clip_paths)} clips.")
            return {"mode": "ai_video_scenes", "asset_count": len(clip_paths), "asset_path": str(output_path)}
    except Exception as exc:
        print(f"[!] AI scene assembly fallback: {exc}")

    # Fallback only if network completely down
    print("[*] Generating fallback dark tech background...")
    duration = int(duration_sec) + 5
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=0x070b14:s=720x1280:r=30:d={duration}",
        "-vf", "noise=alls=6:allf=t+u,drawgrid=width=90:height=90:thickness=1:color=0x22d3ee@0.10",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-t", str(duration), str(output_path)
    ]
    subprocess.run(cmd, check=True)
    return {"mode": "procedural_fallback", "asset_count": 0}


def to_ass_timestamp(seconds: float) -> str:
    """Converts seconds float to ASS timestamp format H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hrs}:{mins:02d}:{secs:05.2f}"

def generate_subtitles(audio_path: Path, output_ass: Path):
    """Transcribes audio using faster-whisper and generates karaoke style ASS subtitles."""
    print("[*] Transcribing audio with Faster-Whisper (word-level timestamps)...")
    from faster_whisper import WhisperModel
    
    # Use base model on CPU
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), word_timestamps=True)

    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,75,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,40,40,750,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogue_lines = []
    for segment in segments:
        if not segment.words:
            continue
        # Group words in chunks of 2-3 words for high readability
        chunk = []
        for word in segment.words:
            chunk.append(word)
            if len(chunk) >= 2 or word.word.endswith((".", "!", "?", ",")):
                start_t = to_ass_timestamp(chunk[0].start)
                end_t = to_ass_timestamp(chunk[-1].end)
                phrase = " ".join(w.word.strip().upper() for w in chunk)
                dialogue_lines.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{phrase}")
                chunk = []
        if chunk:
            start_t = to_ass_timestamp(chunk[0].start)
            end_t = to_ass_timestamp(chunk[-1].end)
            phrase = " ".join(w.word.strip().upper() for w in chunk)
            dialogue_lines.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{phrase}")

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(dialogue_lines))
    print(f"[+] Subtitles generated: {output_ass.name}")

def render_final_short(bg_video: Path, audio_path: Path, ass_path: Path, output_file: Path):
    """Render, normalize, and validate a vertical short before making it eligible for a separately authorized upload."""
    print("[*] Assembling final vertical video with FFmpeg...")
    ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")
    from app.render.ffmpeg_tools import LOUDNORM_TARGET, _measure_loudnorm, audio_bitrate
    normalize = _measure_loudnorm(Path(audio_path)) or f"loudnorm={LOUDNORM_TARGET}"
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(bg_video),
        "-i", str(audio_path),
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,subtitles='{ass_escaped}'[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "21",
        "-c:a", "aac", "-b:a", audio_bitrate(),
        "-af", normalize,
        "-movflags", "+faststart", "-shortest", str(output_file)
    ]
    subprocess.run(cmd, check=True)
    if not output_file.exists() or output_file.stat().st_size < 150_000:
        raise RuntimeError("Rendered video is missing or too small; skipping upload.")
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(output_file)
    ], capture_output=True, text=True, check=True)
    details = json.loads(probe.stdout)
    video = next((stream for stream in details.get("streams", []) if stream.get("codec_type") == "video"), None)
    audio = any(stream.get("codec_type") == "audio" for stream in details.get("streams", []))
    duration = float(details.get("format", {}).get("duration", 0))
    dimensions = (video.get("width"), video.get("height")) if video else None
    if not video or dimensions != (1080, 1920) or not audio or not 20 <= duration <= 60:
        raise RuntimeError(f"Rendered video failed QA (duration={duration:.1f}s, audio={audio}, dimensions={dimensions}); skipping upload.")
    print(f"[+] Video QA passed: {duration:.1f}s, 1080x1920, audio present.")
    print(f"\n[SUCCESS] Final Short Ready: {output_file.resolve()}\n")


def run_strong_pipeline(topic: str, work_dir: Path, metadata_file: Path) -> dict:
    """Run the strong editorial pipeline and persist its metadata."""
    print("[*] Running the strong pipeline (topic -> research -> script -> multi-shot motion)...")
    data = strong_pipeline.run(
        topic or None,
        seconds=PROFILE["seconds"],
        work_dir=work_dir,
    )
    data["script_profile"] = SCRIPT_PROFILE
    data["target_duration_seconds"] = PROFILE["seconds"]
    data["word_range"] = [PROFILE["min_words"], PROFILE["max_words"]]
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    metadata_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


DRY_RUN_TEXT = (
    "Local dry run proves the short pipeline can move from script to voice to background "
    "to captions to a checked vertical render without calling a paid model. Every stage "
    "uses local tools: ffmpeg creates a silent voice track and a procedural background, "
    "while the existing caption and quality checks run exactly as they do in production. "
    "The video is not publishable because it has no real narration or stock footage, but "
    "the file structure, duration, audio stream, and resolution are verified. This run "
    "also confirms that the target-tree entrypoint imports resolve. No API key was read, "
    "no research request was sent, and no upload or approval step was triggered. Keep the "
    "dry run separate from production metadata and review queues."
)


def _dry_run_background(output_path: Path, duration: float) -> None:
    seconds = int(duration) + 3
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=0x070b14:s=720x1280:r=30:d={seconds}",
        "-vf", "noise=alls=6:allf=t+u,drawgrid=width=90:height=90:thickness=1:color=0x22d3ee@0.10",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-t", str(seconds), str(output_path),
    ], check=True)


def run_dry_run(work_dir: Path, metadata_file: Path) -> dict:
    """Exercise the local render path without LLM, research, stock, or upload calls.

    Dry-run visuals are procedural and have no human-reviewed storyboard, so the
    same fail-closed gate applies. Use STORYBOARD_GATE=warn only for an explicit
    local render-mechanics benchmark; this does not make the artifact publishable.
    """
    from app.visuals.storyboard import enforce_review_gate

    enforce_review_gate({
        "review_status": "needs_review",
        "review_reasons": [
            "procedural dry-run visuals have no human-reviewed storyboard"
        ],
    })

    from app.voice import provider as voice_provider
    from app.render.subtitles import make_kinetic_ass

    work_dir.mkdir(parents=True, exist_ok=True)
    audio_path = work_dir / "voice.mp3"
    background_path = work_dir / "background.mp4"
    ass_path = work_dir / "subtitles.ass"
    video_path = work_dir / "output_short.mp4"

    print("[*] DRY_RUN=1: skipping LLM, research, stock, archive, and upload stages.")
    voice = voice_provider.synthesize(DRY_RUN_TEXT, audio_path, provider="silent")
    if not voice.get("path"):
        raise RuntimeError(f"Dry-run silent voice failed: {voice.get('error')}")
    duration = float(voice_provider.probe_duration(audio_path) or voice.get("duration_hint") or 0)
    if duration <= 0:
        raise RuntimeError("Dry-run voice track has no measurable duration.")

    _dry_run_background(background_path, duration)
    words = strong_pipeline.estimated_words(DRY_RUN_TEXT, duration)
    make_kinetic_ass(words, ass_path)
    render_final_short(background_path, audio_path, ass_path, video_path)

    metadata = {
        "dry_run": True,
        "quality": "dry_run",
        "title": "DRY RUN - local pipeline check",
        "topic": "DRY_RUN local verification",
        "hook": "Local dry run proves the short pipeline can move from script to voice to background to captions to a checked vertical render without calling a paid model.",
        "voice_text": DRY_RUN_TEXT,
        "word_count": len(DRY_RUN_TEXT.split()),
        "duration_seconds": duration,
        "broll_query": "local procedural background",
        "visuals": {"mode": "procedural_dry_run", "asset_count": 0},
        "human_review_status": "not_for_publish",
        "governance": _draft_governance("dry_run"),
        "source_urls": [],
        "video_path": str(video_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def run_standard_pipeline(topic: str, *, audio_file: Path, bg_video_file: Path,
                          ass_sub_file: Path, output_mp4: Path,
                          metadata_file: Path) -> dict:
    """Legacy single-pass generation, kept for deliberate explicit use only.

    A Strong Pipeline failure never lands here: Option A (strict fail-closed)
    stops the run instead, so no failed generation can be replaced by a legacy
    video that carries no research verdict, ledger or evidence linkage.
    """
    # 1. Script
    data = generate_script(topic)
    data["governance"] = _draft_governance("standard-legacy")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # 2. Voiceover
    generate_voiceover(data["voice_text"], audio_file)

    # 3. Background video
    # Determine audio length using ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)],
        capture_output=True, text=True, check=True
    )
    duration = float(probe.stdout.strip())
    data["visuals"] = get_background_video(data.get("broll_query", "moody aesthetic"), bg_video_file, duration)
    metadata_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # 4. Subtitles
    generate_subtitles(audio_file, ass_sub_file)

    # 5. Final render
    render_final_short(bg_video_file, audio_file, ass_sub_file, output_mp4)
    record_topic(data.get("topic", data["title"]))
    archived_video = archive_video(output_mp4, metadata_file, SCRIPT_DIR, "shorts", data["title"])
    print(f"[+] Archived Short: {archived_video.resolve()}")
    with open(SCRIPT_DIR / "data" / "recent_formats.txt", "a", encoding="utf-8") as formats:
        formats.write(data["content_pillar"] + "\n")
    return data


def main():
    parser = argparse.ArgumentParser(description="Autonomous Shorts & Reels Generator")
    parser.add_argument("--topic", type=str, default="", help="Specific topic or keyword")
    parser.add_argument(
        "--quality",
        type=str,
        default=os.getenv("VIDEO_QUALITY", "strong").strip().lower(),
        choices=["strong", "standard"],
        help="strong = researched multi-shot editorial pipeline; standard = legacy single-pass path",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="accepted for compatibility; failing closed is now the default behaviour",
    )
    parser.add_argument(
        "--allow-standard",
        action="store_true",
        help="deliberately run the legacy single-pass path (never an automatic fallback)",
    )
    args = parser.parse_args()

    work_dir = SCRIPT_DIR / "outputs"
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_file = work_dir / "voice.mp3"
    bg_video_file = work_dir / "background.mp4"
    ass_sub_file = work_dir / "subtitles.ass"
    output_mp4 = work_dir / "output_short.mp4"
    metadata_file = SCRIPT_DIR / "data" / "metadata.json"
    metadata_file.parent.mkdir(parents=True, exist_ok=True)

    if os.getenv("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}:
        dry_dir = work_dir / "dry_run"
        dry_metadata = SCRIPT_DIR / "data" / "metadata_dry_run.json"
        data = run_dry_run(dry_dir, dry_metadata)
        print(json.dumps({
            "status": "success",
            "dry_run": True,
            "title": data["title"],
            "video_path": data["video_path"],
            "duration_seconds": data["duration_seconds"],
            "word_count": data["word_count"],
            "metadata_path": str(dry_metadata),
        }))
        return

    if args.quality != "strong" and not args.allow_standard:
        # VIDEO_QUALITY=standard and --quality standard are no longer silent bypasses.
        _record_failure("quality_gate",
                        "production generation is strong-only", args.quality)
        print(f"[!] Refusing quality '{args.quality}': production generation is strong-only. "
              "Pass --allow-standard to run the legacy path deliberately.")
        raise SystemExit(2)

    if args.quality == "strong":
        tracker = None
        stage = "strong_pipeline"
        try:
            tracker = start_run(
                args.topic,
                runs_root=work_dir / "runs",
                index_path=SCRIPT_DIR / "data" / "runs" / "index.jsonl",
                quality="strong",
            )
            print(f"[*] Run directory: {tracker.run_dir}")
            # Phase 10.4: the run directory is the sole work_dir, so every
            # strong artifact (research, shots, render) lands inside it.
            data = run_strong_pipeline(args.topic, tracker.run_dir, tracker.run_dir / "metadata.json")
            # Promotion: validate, record, then atomically move the validated
            # artifacts into the legacy slots.  The run is only marked ``ok``
            # AFTER the promotion journal reports ``completed`` — a crash
            # mid-promotion can never look like a finished success.
            data["run_id"] = tracker.run_id
            data["governance"] = {
                "entry": "orchestrated",
                "publishable": True,
                "run_id": tracker.run_id,
                "stamped_at": datetime.now(timezone.utc).isoformat(),
            }
            (tracker.run_dir / "metadata.json").write_text(
                json.dumps(data, indent=2) + "\n", encoding="utf-8")
            tracker.record_artifact("metadata", tracker.run_dir / "metadata.json", stage="strong_pipeline")
            video_source = Path(data.get("video_path") or tracker.run_dir / "output_short.mp4")
            if not video_source.is_absolute():
                video_source = tracker.run_dir / video_source.name
            tracker.record_artifact("video", video_source, stage="render")  # containment enforced in run_tracker
            tracker.record_stage("strong_pipeline",
                                 started_at=tracker.manifest.get("started_at"),
                                 finished_at=datetime.now(timezone.utc).isoformat())
            stage = "promotion"
            tracker.promote_slots({
                "video": output_mp4,
                "metadata": metadata_file,
            })
            tracker.mark_ok()
        except KeyboardInterrupt:
            # Operator abort: leave the run exactly as it is (in_progress).
            raise
        except SystemExit as exc:
            # Aborted from inside the pipeline: keep the original exit code
            # but still record a genuine failure — never a silent zero.
            if tracker is not None:
                with contextlib.suppress(Exception):
                    tracker.mark_failed(stage=stage, exc=exc,
                                        error_category="unknown")
            _record_failure("strong_pipeline", exc, "strong")
            print(f"[!] Strong pipeline aborted from inside ({type(exc).__name__}); "
                  "stopping without a fallback.")
            raise
        except Exception as exc:
            # Fail closed: no legacy generation, no success payload, no metadata
            # overwrite - the previous successful run stays exactly as it was.
            if tracker is not None:
                category = "io" if stage == "promotion" else "unknown"
                with contextlib.suppress(Exception):
                    tracker.mark_failed(stage=stage, exc=exc, error_category=category)
            _record_failure("strong_pipeline", exc, "strong")
            print(f"[!] Strong pipeline failed ({type(exc).__name__}: {_redact(exc)}); "
                  "stopping without a fallback.")
            raise SystemExit(1) from None
        record_topic(data.get("topic", data.get("title", "")))
        archived_video = archive_video(output_mp4, metadata_file, SCRIPT_DIR, "shorts", data["title"])
        print(f"[+] Archived Short: {archived_video.resolve()}")
        with open(SCRIPT_DIR / "data" / "recent_formats.txt", "a", encoding="utf-8") as formats:
            formats.write(data.get("content_pillar", "What Changed") + "\n")
        print(json.dumps({
            "status": "success",
            "quality": "strong",
            "run_id": data.get("run_id", ""),
            "title": data["title"],
            "video_path": str(output_mp4),
            "tags": data.get("tags", []),
            "source_urls": data.get("source_urls", []),
            "word_count": data.get("word_count"),
            "shots": len(data.get("shots", [])),
            "duration_seconds": data.get("duration_seconds"),
        }))
        return

    data = run_standard_pipeline(
        args.topic, audio_file=audio_file, bg_video_file=bg_video_file,
        ass_sub_file=ass_sub_file, output_mp4=output_mp4, metadata_file=metadata_file)
    # Output metadata for the caller
    print(json.dumps({
        "status": "success",
        "quality": "standard",
        "legacy": True,
        "title": data["title"],
        "video_path": str(output_mp4),
        "tags": data.get("tags", []),
        "source_urls": data.get("source_urls", []),
        "word_count": data.get("word_count")
    }))

if __name__ == "__main__":
    main()
