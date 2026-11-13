#!/usr/bin/env python3
"""Generate a research-led horizontal YouTube video for Nextdecode."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.script.longform import _visual_query, generate_script
from app.operations.video_archive import archive_video
load_dotenv(ROOT / ".env", override=True)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()
DEMO_VIDEO_PATH = os.getenv("DEMO_VIDEO_PATH", "").strip()
VOICE = os.getenv("TTS_VOICE", "en-US-ChristopherNeural").strip()
CLIPS_PER_CHAPTER = 2
MIN_STOCK_SCENES = 8
PIXABAY_CACHE_SECONDS = 24 * 60 * 60
MAX_STOCK_CLIP_BYTES = 100_000_000
MAX_MOTION_SCENE_SECONDS = 12


def voiceover(text: str, output: Path):
    executable = shutil.which("edge-tts")
    if executable is None:
        bundled = Path(sys.executable).with_name("edge-tts")
        if not bundled.is_file():
            raise FileNotFoundError("edge-tts is not available on PATH or beside the active Python interpreter.")
        executable = str(bundled)
    subprocess.run([executable, "--voice", VOICE, "--text", text, "--write-media", str(output)], check=True)


def _download_stock_clip(url: str, destination: Path) -> None:
    temporary = destination.with_suffix(".part")
    try:
        with requests.get(url, stream=True, timeout=90) as download:
            download.raise_for_status()
            with temporary.open("wb") as stream:
                size = 0
                for chunk in download.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        size += len(chunk)
                        if size > MAX_STOCK_CLIP_BYTES:
                            raise RuntimeError("Stock video exceeded the 100 MB per-clip safety limit.")
                        stream.write(chunk)
        if temporary.stat().st_size < 100_000:
            raise RuntimeError("Stock provider returned an empty or incomplete video.")
        os.replace(temporary, destination)
    except (OSError, requests.RequestException, RuntimeError):
        temporary.unlink(missing_ok=True)
        raise


def _find_pexels_clip(query: str, destination: Path, used_video_ids: set[int]) -> dict | None:
    response = requests.get(
        "https://api.pexels.com/videos/search",
        params={"query": query, "orientation": "landscape", "per_page": 8},
        headers={"Authorization": PEXELS_API_KEY},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    videos = payload.get("videos") if isinstance(payload, dict) else None
    if not isinstance(videos, list):
        raise RuntimeError("Pexels returned an invalid video search response.")
    candidates = []
    for video in videos:
        if not isinstance(video, dict):
            continue
        video_id = video.get("id")
        if not isinstance(video_id, int) or video_id in used_video_ids:
            continue
        video_files = video.get("video_files", [])
        if not isinstance(video_files, list):
            continue
        for video_file in video_files:
            if not isinstance(video_file, dict):
                continue
            try:
                width = int(video_file.get("width") or 0)
                height = int(video_file.get("height") or 0)
            except (TypeError, ValueError):
                continue
            link = video_file.get("link")
            if width <= 0 or height <= 0 or not isinstance(link, str) or not link.startswith("https://") or width < 640:
                continue
            ratio = width / height
            score = 3.0 - abs(ratio - (16 / 9)) * 4 + min(width, 1920) / 1920
            candidates.append((score, video, video_file))
    if not candidates:
        return None

    _, video, selected_file = max(candidates, key=lambda item: item[0])
    _download_stock_clip(selected_file["link"], destination)

    user = video.get("user")
    creator = user.get("name", "Unknown creator") if isinstance(user, dict) else "Unknown creator"
    return {
        "video_id": video["id"],
        "creator": creator,
        "page_url": video.get("url") or f"https://www.pexels.com/video/{video['id']}/",
        "query": query,
        "license": "Pexels License",
        "asset_path": str(destination),
    }


def _pixabay_search_results(query: str) -> list[dict]:
    cache_dir = ROOT / "outputs" / "videos" / "pixabay_search_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(query.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{cache_key}.json"
    now = datetime.now(timezone.utc)

    if cache_file.is_file():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(cached["cached_at"])
            age = (now - cached_at).total_seconds()
            if 0 <= age < PIXABAY_CACHE_SECONDS and isinstance(cached.get("hits"), list):
                return cached["hits"]
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Pixabay search cache is unreadable: {cache_file}") from exc

    response = requests.get(
        "https://pixabay.com/api/videos/",
        params={
            "key": PIXABAY_API_KEY,
            "q": query[:100],
            "video_type": "film",
            "min_width": 1280,
            "safesearch": "true",
            "per_page": 50,
            "order": "popular",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    hits = payload.get("hits") if isinstance(payload, dict) else None
    if not isinstance(hits, list):
        raise RuntimeError("Pixabay returned an invalid video search response.")

    temporary = cache_file.with_suffix(".tmp")
    try:
        temporary.write_text(
            json.dumps({"cached_at": now.isoformat(), "hits": hits}, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(temporary, cache_file)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
    return hits


def _find_pixabay_clip(query: str, destination: Path, used_video_ids: set[int]) -> dict | None:
    candidates = []
    for video in _pixabay_search_results(query):
        if not isinstance(video, dict):
            continue
        video_id = video.get("id")
        if not isinstance(video_id, int) or video_id in used_video_ids:
            continue
        variants = video.get("videos")
        if not isinstance(variants, dict):
            continue
        for variant_name, variant in variants.items():
            if not isinstance(variant, dict):
                continue
            try:
                width = int(variant.get("width") or 0)
                height = int(variant.get("height") or 0)
            except (TypeError, ValueError):
                continue
            url = variant.get("url")
            if width < 1280 or height <= 0 or not isinstance(url, str) or not url.startswith("https://"):
                continue
            ratio = width / height
            size = variant.get("size")
            try:
                size = int(size) if size is not None else None
            except (TypeError, ValueError):
                size = None
            if size is not None and size > MAX_STOCK_CLIP_BYTES:
                continue
            score = 3.0 - abs(ratio - (16 / 9)) * 4 + min(width, 1920) / 1920
            candidates.append((score, video, variant_name, variant))
    if not candidates:
        return None

    _, video, _, selected_file = max(candidates, key=lambda item: item[0])
    _download_stock_clip(selected_file["url"], destination)
    creator = str(video.get("user", "")).strip() or "Unknown creator"
    page_url = video.get("pageURL")
    if not isinstance(page_url, str) or not page_url.startswith("https://"):
        page_url = f"https://pixabay.com/videos/video-{video['id']}/"
    return {
        "video_id": video["id"],
        "creator": creator,
        "page_url": page_url,
        "creator_url": f"https://pixabay.com/users/{video.get('user')}-{video.get('user_id')}/",
        "query": query,
        "license": "Pixabay Content License",
        "asset_path": str(destination),
    }


def _render_stock_sequence(clips: list[dict], chapters: list[dict], output: Path, duration: float) -> None:
    inputs = []
    filters = []
    valid_clips = []
    ordered_clips = sorted(clips, key=lambda clip: clip["chapter_index"])
    grouped_clips = {}
    for clip in ordered_clips:
        grouped_clips.setdefault(clip["chapter_index"], []).append(clip)
    chapter_indexes = sorted(grouped_clips)

    for group_number, chapter_index in enumerate(chapter_indexes):
        start = 0 if group_number == 0 else chapters[chapter_index]["start_seconds"]
        next_chapter = chapter_indexes[group_number + 1] if group_number + 1 < len(chapter_indexes) else None
        end = chapters[next_chapter]["start_seconds"] if next_chapter is not None else duration
        scene_duration = (end - start) / len(grouped_clips[chapter_index])
        for clip in grouped_clips[chapter_index]:
            if scene_duration <= 0 or start >= duration:
                continue
            inputs.extend(["-stream_loop", "-1", "-i", clip["asset_path"]])
            filters.append(
                f"[{len(valid_clips)}:v]scale=1920:1080:force_original_aspect_ratio=increase,"
                f"crop=1920:1080,fps=30,setsar=1,trim=duration={scene_duration:.3f},"
                f"setpts=PTS-STARTPTS[v{len(valid_clips)}]"
            )
            valid_clips.append(clip)
            start += scene_duration

    if len(valid_clips) < MIN_STOCK_SCENES:
        raise RuntimeError("Not enough distinct stock scenes cover the planned chapters.")
    labels = "".join(f"[v{index}]" for index in range(len(valid_clips)))
    filters.append(f"{labels}concat=n={len(valid_clips)}:v=1:a=0[vout]")
    subprocess.run([
        "ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-t", str(duration), "-an", "-c:v", "libx264",
        "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p", str(output),
    ], check=True)


def landscape_background(query: str, output: Path, duration: float, chapters: list[dict]):
    if DEMO_VIDEO_PATH:
        demo = Path(DEMO_VIDEO_PATH).expanduser()
        if demo.is_file() and demo.stat().st_size > 100_000:
            subprocess.run(["ffmpeg", "-y", "-i", str(demo), "-c", "copy", str(output)], check=True)
            return {"mode": "owner_recorded", "asset_count": 1, "asset_path": str(output)}

    providers = []
    if PEXELS_API_KEY:
        providers.append(("pexels", _find_pexels_clip, "Pexels License"))
    if PIXABAY_API_KEY:
        providers.append(("pixabay", _find_pixabay_clip, "Pixabay Content License"))

    if providers:
        asset_dir = ROOT / "outputs" / "videos" / "longform_sources" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        asset_dir.mkdir(parents=True, exist_ok=True)
        clips = []
        used_video_ids = {provider: set() for provider, _, _ in providers}
        failures = []
        for index, chapter in enumerate(chapters):
            chapter_query = chapter.get("broll_query") or f"{query} {chapter['title']}"
            for clip_number in range(CLIPS_PER_CHAPTER):
                clip = None
                for provider, find_clip, _ in providers:
                    try:
                        clip = find_clip(
                            chapter_query,
                            asset_dir / f"scene_{index + 1:02d}_{clip_number + 1:02d}.mp4",
                            used_video_ids[provider],
                        )
                        if clip:
                            used_video_ids[provider].add(clip["video_id"])
                            clip["provider"] = provider
                            clip["chapter"] = chapter["title"]
                            clip["chapter_index"] = index
                            clips.append(clip)
                            break
                    except (OSError, requests.RequestException, ValueError, RuntimeError) as exc:
                        failures.append(f"{provider} chapter {index + 1}: {type(exc).__name__}.")
                        print(f"[!] {provider.title()} B-roll unavailable for chapter {index + 1} ({type(exc).__name__}).")
                if not clip:
                    failures.append(f"No additional licensed stock footage for chapter {index + 1}.")
                    break

        if len(clips) >= MIN_STOCK_SCENES:
            try:
                _render_stock_sequence(clips, chapters, output, duration)
                providers_used = sorted({clip["provider"] for clip in clips})
                return {
                    "mode": "pixabay_stock" if providers_used == ["pixabay"] else (
                        "pexels_stock" if providers_used == ["pexels"] else "licensed_stock"
                    ),
                    "asset_count": len(clips),
                    "asset_path": str(output),
                    "sources": clips,
                    "fallbacks": failures,
                }
            except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
                failures.append(f"Stock sequence render: {type(exc).__name__}.")
                print(f"[!] Pexels B-roll sequence could not be rendered ({type(exc).__name__}).")
        else:
            failures.append(f"Only {len(clips)} distinct stock scenes were found; {MIN_STOCK_SCENES} are required.")
            print(f"[!] Only {len(clips)} distinct stock scenes were found; keeping this video draft-only.")
        stock_fallbacks = failures
    else:
        stock_fallbacks = ["Neither PEXELS_API_KEY nor PIXABAY_API_KEY is configured."]

    scene_dir = ROOT / "outputs" / "videos" / "longform_motion_graphics" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    scene_dir.mkdir(parents=True, exist_ok=True)
    scenes = _render_motion_graphics(chapters, output, duration, scene_dir)
    return {
        "mode": "procedural_fallback",
        "asset_count": 0,
        "fallbacks": stock_fallbacks,
        "motion_graphics": True,
        "scene_count": scenes,
        "description": "Animated chapter-specific diagrams and labels; not licensed footage.",
    }


def _render_motion_graphics(chapters: list[dict], output: Path, duration: float, scene_dir: Path) -> int:
    palette = ("0x37D6E8", "0xA78BFA", "0xF6B94A", "0x56D6A2", "0xFF738A", "0x65A9FF", "0xE1A6FF", "0xB6E36A")
    center_labels = ("AGREE", "MODEL", "SYNTH", "CHECK", "SIGNAL", "TEST", "PROOF", "NEXT")
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not Path(font).is_file():
        raise FileNotFoundError(f"Motion graphics font is unavailable: {font}")

    inputs = []
    filters = []
    scene_count = 0
    for index, chapter in enumerate(chapters):
        start = float(chapter["start_seconds"])
        next_start = float(chapters[index + 1]["start_seconds"]) if index + 1 < len(chapters) else duration
        chapter_duration = min(duration, next_start) - start
        if chapter_duration <= 0:
            continue

        title_lines = textwrap.wrap(str(chapter["title"]).upper(), width=20, break_long_words=False) or [""]
        terms_lines = textwrap.wrap(
            _visual_query(chapter.get("broll_query") or chapter["title"]).upper(),
            width=24,
            break_long_words=False,
        ) or [""]
        title_draws = []
        for line_number, line in enumerate(title_lines):
            title_file = scene_dir / f"chapter_{index + 1:02d}_title_{line_number:02d}.txt"
            title_file.write_text(line, encoding="utf-8")
            title_draws.append(
                f"drawtext=fontfile={font}:textfile={title_file}:expansion=none:"
                f"fontcolor=white:fontsize=43:x=88:y={170 + line_number * 58}"
            )
        terms_draws = []
        for line_number, line in enumerate(terms_lines):
            terms_file = scene_dir / f"chapter_{index + 1:02d}_terms_{line_number:02d}.txt"
            terms_file.write_text(line, encoding="utf-8")
            terms_draws.append(
                f"drawtext=fontfile={font}:textfile={terms_file}:expansion=none:"
                f"fontcolor=0xC7D5E5:fontsize=24:x=92:y={420 + line_number * 39}"
            )

        variant_count = max(1, math.ceil(chapter_duration / MAX_MOTION_SCENE_SECONDS))
        for variant in range(variant_count):
            scene_duration = chapter_duration / variant_count
            accent = palette[(index + variant) % len(palette)]
            visual_type = chapter.get("visual_type", ("network", "process", "comparison", "evidence")[index % 4])
            diagram_stages, diagram_text = _motion_diagram_parts(visual_type, accent, index, variant)
            input_index = scene_count
            inputs.extend([
                "-f", "lavfi", "-i",
                f"color=c=0x08111F:s=1280x720:r=30:d={scene_duration:.3f}",
            ])
            stages = [
                f"[{input_index}:v]drawgrid=width=64:height=64:thickness=1:color={accent}@0.11",
                f"drawbox=x=680:y=112:w=520:h=470:color=0x0D1A2B@0.94:t=fill",
                f"drawbox=x=680:y=112:w=520:h=470:color={accent}@0.78:t=2",
                f"drawbox=x=90:y=390:w=490:h=2:color={accent}@0.48:t=fill",
                f"drawbox=x=720:y=166:w=440:h=2:color={accent}@0.62:t=fill",
                *diagram_stages,
                f"drawbox=x='mod(t*72+{index * 127 + variant * 53}\\,1320)-20':y=560:w=3:h=90:color={accent}@0.34:t=fill",
                f"drawtext=fontfile={font}:text='NEXTDECODE  /  AI EXPLAINED':fontcolor={accent}:fontsize=20:x=88:y=72",
                f"drawtext=fontfile={font}:text='CHAPTER {index + 1:02d}  /  {len(chapters):02d}':fontcolor=0xAFC2D7:fontsize=18:x=88:y=118",
                *title_draws,
                f"drawtext=fontfile={font}:text='THE IDEA':fontcolor={accent}:fontsize=17:x=92:y=348",
                *terms_draws,
                *diagram_text,
                f"drawtext=fontfile={font}:text='EVIDENCE  /  LIMITS  /  TAKEAWAY':fontcolor=0xAFC2D7:fontsize=15:x=720:y=520",
                f"drawbox=x=88:y=625:w=1104:h=3:color=0x35465A@0.85:t=fill",
                f"drawbox=x='88+mod(t*{180 + index * 17 + variant * 31}\\,1104)':y=622:w=88:h=9:color={accent}:t=fill",
                f"fps=30,format=yuv420p[scene{scene_count}]",
            ]
            filters.append(",".join(stages))
            scene_count += 1

    if scene_count < 2:
        raise RuntimeError("Motion graphics need at least one chapter.")
    labels = "".join(f"[scene{index}]" for index in range(scene_count))
    filters.append(f"{labels}concat=n={scene_count}:v=1:a=0,trim=duration={duration:.3f}[vout]")
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-t", str(duration), "-an", "-c:v", "libx264",
        "-preset", "ultrafast", "-crf", "22", "-pix_fmt", "yuv420p", str(output),
    ], check=True)
    return scene_count


def _motion_diagram_parts(visual_type: str, accent: str, index: int, variant: int) -> tuple[list[str], list[str]]:
    visual_type = visual_type if visual_type in {"network", "process", "comparison", "timeline", "evidence"} else "evidence"
    if visual_type == "network":
        shapes = [
            ("755", "224", "150", "70"), ("1000", "224", "150", "70"),
            ("755", "415", "150", "70"), ("1000", "415", "150", "70"),
        ]
        boxes = [
            f"drawbox=x=830:y=258:w=244:h=3:color={accent}@0.54:t=fill",
            f"drawbox=x=830:y=449:w=244:h=3:color={accent}@0.54:t=fill",
            f"drawbox=x=830:y=258:w=3:h=194:color={accent}@0.54:t=fill",
            f"drawbox=x=1071:y=258:w=3:h=194:color={accent}@0.54:t=fill",
            f"drawbox=x=950:y=258:w=3:h=194:color={accent}@0.54:t=fill",
            f"drawbox=x=830:y=353:w=244:h=3:color={accent}@0.54:t=fill",
            f"drawbox=x='830+mod(t*{95 + index * 11 + variant * 23}\\,244)':y=347:w=16:h=16:color={accent}:t=fill",
        ]
        labels = [
            ("NODE A", "775", "252"), ("NODE B", "1020", "252"),
            ("NODE C", "775", "443"), ("NODE D", "1020", "443"),
            ("AGREE", "910", "347"),
        ]
    elif visual_type == "process":
        shapes = [(str(x), "310", "96", "115") for x in (720, 840, 960, 1080)]
        boxes = [
            f"drawbox=x=816:y=364:w=25:h=3:color={accent}@0.8:t=fill",
            f"drawbox=x=936:y=364:w=25:h=3:color={accent}@0.8:t=fill",
            f"drawbox=x=1056:y=364:w=25:h=3:color={accent}@0.8:t=fill",
            f"drawbox=x='720+mod(t*90+{variant * 34}\\,440)':y=294:w=12:h=12:color={accent}:t=fill",
        ]
        labels = [
            ("INPUT", "733", "356"), ("PROCESS", "844", "356"),
            ("CHECK", "971", "356"), ("RESULT", "1087", "356"),
        ]
    elif visual_type == "comparison":
        shapes = [("750", "240", "180", "250"), ("970", "240", "180", "250")]
        boxes = [
            f"drawbox=x=780:y=345:w=42:h=105:color={accent}@0.75:t=fill",
            f"drawbox=x=840:y=290:w=42:h=160:color={accent}@0.75:t=fill",
            f"drawbox=x=1000:y=320:w=42:h=130:color={accent}@0.75:t=fill",
            f"drawbox=x=1060:y=260:w=42:h=190:color={accent}@0.75:t=fill",
            f"drawbox=x='780+mod(t*70+{variant * 40}\\,320)':y=465:w=8:h=8:color={accent}:t=fill",
        ]
        labels = [("BEFORE", "790", "258"), ("AFTER", "1018", "258"), ("COMPARE", "884", "510")]
    elif visual_type == "timeline":
        shapes = [(str(x), "320", "110", "100") for x in (730, 910, 1090)]
        boxes = [
            f"drawbox=x=840:y=369:w=70:h=3:color={accent}@0.8:t=fill",
            f"drawbox=x=1020:y=369:w=70:h=3:color={accent}@0.8:t=fill",
            f"drawbox=x='730+mod(t*100+{variant * 36}\\,460)':y=369:w=12:h=12:color={accent}:t=fill",
        ]
        labels = [("PAST", "760", "363"), ("NOW", "947", "363"), ("NEXT", "1121", "363")]
    else:
        shapes = [(str(x), "300", "95", "170") for x in (740, 910, 1080)]
        boxes = [
            f"drawbox=x=775:y=385:w=25:h=65:color={accent}@0.72:t=fill",
            f"drawbox=x=820:y=340:w=25:h=110:color={accent}@0.72:t=fill",
            f"drawbox=x=945:y=360:w=25:h=90:color={accent}@0.72:t=fill",
            f"drawbox=x=990:y=320:w=25:h=130:color={accent}@0.72:t=fill",
            f"drawbox=x=1115:y=405:w=25:h=45:color={accent}@0.72:t=fill",
            f"drawbox=x=1160:y=375:w=25:h=75:color={accent}@0.72:t=fill",
        ]
        labels = [("CLAIM", "757", "312"), ("TEST", "941", "312"), ("LIMIT", "1110", "312")]
    diagram = []
    for x, y, width, height in shapes:
        diagram.extend([
            f"drawbox=x={x}:y={y}:w={width}:h={height}:color=0x152A40@0.96:t=fill",
            f"drawbox=x={x}:y={y}:w={width}:h={height}:color={accent}@0.9:t=2",
        ])
    diagram.extend(boxes)
    text = [
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{label}':"
        f"fontcolor={accent if label in {'AGREE', 'COMPARE'} else 'white'}:fontsize=15:x={x}:y={y}"
        for label, x, y in labels
    ]
    return diagram, text


def subtitles(audio: Path, output: Path):
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio), word_timestamps=True)
    header = """[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,DejaVu Sans,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,80,80,70,1\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"""
    def stamp(sec: float) -> str:
        return f"{int(sec // 3600)}:{int((sec % 3600) // 60):02d}:{sec % 60:05.2f}"
    lines = []
    for segment in segments:
        if not segment.words:
            continue
        chunk = []
        for word in segment.words:
            chunk.append(word)
            if len(chunk) >= 5 or word.word.endswith((".", "!", "?", ",")):
                lines.append(f"Dialogue: 0,{stamp(chunk[0].start)},{stamp(chunk[-1].end)},Default,,0,0,0,,{' '.join(w.word.strip().upper() for w in chunk)}")
                chunk = []
    output.write_text(header + "\n".join(lines), encoding="utf-8")


def render(background: Path, audio: Path, ass: Path, output: Path):
    escaped = str(ass).replace("\\", "/").replace(":", "\\:")
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", str(background), "-i", str(audio),
        "-filter_complex", f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,subtitles='{escaped}'[v]",
        "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "fast", "-crf", "21",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000",
        "-movflags", "+faststart", "-shortest", str(output)
    ], check=True)
    probe = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=codec_type,width,height,sample_rate,channels,duration",
        "-of", "json", str(output),
    ], capture_output=True, text=True, check=True)
    details = json.loads(probe.stdout)
    video = next((stream for stream in details.get("streams", []) if stream.get("codec_type") == "video"), None)
    audio_stream = next((stream for stream in details.get("streams", []) if stream.get("codec_type") == "audio"), None)
    duration = float(details.get("format", {}).get("duration", 0))
    audio_duration = float(audio_stream.get("duration", 0)) if audio_stream else 0
    if (
        not video
        or (video.get("width"), video.get("height")) != (1920, 1080)
        or not audio_stream
        or audio_stream.get("sample_rate") != "48000"
        or audio_stream.get("channels") != 2
        or audio_duration < duration - 0.5
        or not 120 <= duration <= 600
    ):
        raise RuntimeError(
            f"Long-form QA failed: duration={duration:.1f}s, audio_duration={audio_duration:.1f}s, "
            f"dimensions={video}, audio={audio_stream}"
        )
    audio_check = subprocess.run([
        "ffmpeg", "-hide_banner", "-i", str(output), "-vn",
        "-af", "atrim=duration=20,volumedetect", "-f", "null", "-",
    ], capture_output=True, text=True, check=True)
    volume = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", audio_check.stderr)
    if not volume or float(volume.group(1)) < -35:
        raise RuntimeError("Long-form audio QA failed: the first 20 seconds are silent or too quiet.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="")
    args = parser.parse_args()
    data = generate_script(args.topic)
    data_dir = ROOT / "data"
    output_dir = ROOT / "outputs"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "longform_metadata.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (data_dir / "longform_script.txt").write_text(data["voice_text"] + "\n", encoding="utf-8")
    audio = output_dir / "longform_voice.mp3"
    background = output_dir / "longform_background.mp4"
    ass = output_dir / "longform_subtitles.ass"
    output = output_dir / "output_longform.mp4"
    voiceover(data["voice_text"], audio)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio)], capture_output=True, text=True, check=True)
    duration = float(probe.stdout.strip())
    data["visuals"] = landscape_background(data["broll_query"], background, duration, data["chapters"])
    stock_credits = [
        f"Video by {source['creator']} on "
        f"{'Pixabay' if source.get('provider') == 'pixabay' else 'Pexels'}: {source['page_url']}"
        for source in data["visuals"].get("sources", [])
    ]
    if stock_credits:
        data["description"] = (
            data["description"] + "\n\nStock video credits:\n" + "\n".join(stock_credits)
        )[:5000]
    (data_dir / "longform_metadata.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    subtitles(audio, ass)
    render(background, audio, ass, output)
    archived_video = archive_video(output, data_dir / "longform_metadata.json", ROOT, "longform", data["title"])
    print(f"Archived long-form video: {archived_video.resolve()}")
    print(json.dumps({"status": "success", "format": "youtube_longform", "title": data["title"], "word_count": data["word_count"], "video": str(output)}))


if __name__ == "__main__":
    main()
