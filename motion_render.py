#!/usr/bin/env python3
"""Motion renderer - Ken Burns multi-shot ffmpeg pipeline for vertical shorts.

Public API:
    build_ken_burns_filter(shot, *, width, height, fps) -> str
    render_shot(shot, asset_path, work_dir, *, fps, width, height) -> Path
    build_concat_filter(shots) -> str
    make_kinetic_ass(transcript_words, out_path, *, width, height) -> Path
    synthesize_music_bed(work_dir, duration, *, path=None) -> Path
    synthesize_sfx(kind, work_dir, *, path=None) -> Path | None
    render_video(shots, audio_path, out_path, *, work_dir, ass_path=None,
                 width, height, fps) -> dict
    qa_video(path, *, width, height, min_duration, max_duration) -> dict
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import visual_assets
import stock_fetcher
from motion_director import SAFE_ZONE_BOTTOM, SAFE_ZONE_TOP

FFMPEG_TIMEOUT = 300
WIDTH = 1080
HEIGHT = 1920
FPS = 30
AUDIO_RATE = 44100

_ZERO_AUDIO = "anullsrc=r=44100:cl=mono"


def _run(cmd: list[str], timeout: int = FFMPEG_TIMEOUT) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)


def _ffprobe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_entries", "format=duration:stream=codec_type,width,height",
        str(path),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if completed.returncode != 0:
        return {}
    try:
        return json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return {}


def _probe_duration(path: Path) -> float:
    data = _ffprobe(path)
    try:
        return float(data.get("format", {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def build_ken_burns_filter(shot: dict, *, width: int = 1080, height: int = 1920,
                           fps: int = 30) -> str:
    """ffmpeg zoompan filter string: distinct slow zoom + subtle pan per shot."""
    duration = float(shot.get("duration", 3.0))
    frames = max(1, int(round(duration * fps)))
    z_from = float(shot.get("zoom_from", 1.0))
    z_to = float(shot.get("zoom_to", 1.14))
    pan = shot.get("pan") or {}
    px0 = float(pan.get("x0", pan.get("x", 0.0)))
    py0 = float(pan.get("y0", pan.get("y", 0.0)))
    px1 = float(pan.get("x1", -px0))
    py1 = float(pan.get("y1", -py0))
    z = f"if(lte(on,1),{z_from},zoom+({z_to}-{z_from})/{frames})"
    x = f"iw/2-(iw/zoom)/2+if(lte(on,1),{px0},{px0}+({px1}-{px0})*on/{frames})"
    y = f"ih/2-(ih/zoom)/2+if(lte(on,1),{py0},{py0}+({py1}-{py0})*on/{frames})"
    return f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={width}x{height}:fps={fps}"


def _procedural_source(work_dir: Path, shot: dict, duration: float,
                       width: int = WIDTH, height: int = HEIGHT) -> Path:
    index = int(shot.get("index", 0))
    import colorsys
    hue = (index * 0.41) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.35, 0.55)
    color = "0x%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
    out = work_dir / f"proc_{index:03d}.mp4"
    _run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={color}:s={width}x{height}:r={fps}:d={duration}",
        "-vf", f"noise=alls=6:allf=t,zoompan=z='1.0':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':d=1:s={width}x{height}:fps={fps}",
        "-frames:v", "1", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-t", str(duration), "-an", str(out),
    ])
    return out


def _looks_like_video(path: Path | None) -> bool:
    return bool(path) and Path(path).is_file() and Path(path).suffix.lower() in (
        ".mp4", ".mov", ".mkv", ".webm", ".avi",
    )


def _looks_like_image(path: Path | None) -> bool:
    return bool(path) and Path(path).is_file() and Path(path).suffix.lower() in (
        ".jpg", ".jpeg", ".png", ".webp", ".bmp",
    )


def resolve_asset_detail(shot: dict, work_dir: Path, used_titles: set[str] | None = None) -> dict:
    """Resolve a shot asset to a local file and report where it came from.

    Returns a dict with ``path`` (may be None), ``provider`` and, for real
    photographs, ``license``/``author``/``page_url`` for attribution.
    """
    source = shot.get("source", "procedural")
    work_dir = Path(work_dir)
    index = int(shot.get("index", 0) or 0)
    query = shot.get("asset_query") or shot.get("visual") or ""

    def wikimedia() -> dict:
        variants = shot.get("asset_query_variants") or []
        try:
            asset = stock_fetcher.fetch_shot_image(
                query, work_dir, index=index, used_titles=used_titles,
                extra_queries=[str(item) for item in variants],
            )
        except Exception:
            asset = None
        if asset and asset.get("path"):
            return {"path": asset["path"], "provider": "wikimedia", **{k: v for k, v in asset.items() if k != "path"}}
        return {"path": None, "provider": "wikimedia"}

    def ai_image() -> dict:
        try:
            res = visual_assets.generate_image(shot.get("visual", ""), work_dir, aspect="9:16")
        except Exception:
            return {"path": None, "provider": "ai_image"}
        if not res or not res.get("path") or not Path(res["path"]).exists():
            return {"path": None, "provider": "ai_image"}
        provider = str(res.get("provider", "ai_image"))
        if provider == "local":
            return {"path": None, "provider": "ai_image"}
        return {"path": res["path"], "provider": provider}

    if source == "demo":
        demo = os.getenv("DEMO_VIDEO_PATH", "").strip()
        if demo and Path(demo).is_file():
            return {"path": demo, "provider": "demo"}
        return {"path": None, "provider": "demo"}

    if source == "wikimedia":
        return wikimedia()

    if source == "ai_image":
        result = ai_image()
        if result["path"]:
            return result
        return wikimedia()

    if source in ("pexels", "pixabay"):
        key = os.getenv("PEXELS_API_KEY") if source == "pexels" else os.getenv("PIXABAY_API_KEY")
        if key:
            try:
                found = _download_stock(shot, source, key, work_dir)
            except Exception:
                found = None
            if found:
                return {"path": str(found), "provider": source}
        result = wikimedia()
        if result["path"]:
            return result
        result = ai_image()
        if result["path"]:
            return result
        return {"path": None, "provider": source}

    return {"path": None, "provider": "procedural"}


def resolve_asset(shot: dict, work_dir: Path) -> Path | None:
    """Resolve a shot asset to a local file, degrading to None (procedural)."""
    detail = resolve_asset_detail(shot, work_dir)
    path = detail.get("path")
    if path and Path(path).exists():
        return Path(path)
    return None
def _download_stock(shot: dict, source: str, key: str, work_dir: Path) -> Path | None:
    query = urllib.parse.quote(shot.get("asset_query") or shot.get("visual") or "short")
    if source == "pexels":
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=3"
        req = urllib.request.Request(url, headers={"Authorization": key})
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        candidates = []
        for video in data.get("videos", [])[:3]:
            for item in video.get("video_files", []) or []:
                width, height, link = item.get("width") or 0, item.get("height") or 0, item.get("link")
                if width > 0 and height > 0 and link:
                    ratio = width / height
                    score = 3.0 - abs(ratio - (9 / 16)) * 4 + min(height, 1920) / 1920
                    candidates.append((score, link))
        if not candidates:
            return None
        _, download_url = max(candidates, key=lambda item: item[0])
    else:
        url = f"https://pixabay.com/api/videos/?key={key}&q={query}&per_page=3"
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        hits = data.get("hits") or []
        if not hits:
            return None
        videos = hits[0].get("videos") or {}
        medium = videos.get("medium") or {}
        download_url = medium.get("url") or videos.get("large", {}).get("url")
        if not download_url:
            return None

    out = work_dir / f"stock_{source}_{int(shot.get('index', 0)):03d}.mp4"
    try:
        with urllib.request.urlopen(download_url, timeout=60) as response, open(out, "wb") as handle:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                handle.write(chunk)
    except Exception:
        out.unlink(missing_ok=True)
        return None
    if out.stat().st_size < 100_000:
        out.unlink(missing_ok=True)
        return None
    return out


def render_shot(shot: dict, asset_path: Path | None, work_dir: Path, *,
                fps: int = 30, width: int = WIDTH, height: int = HEIGHT) -> Path:
    """Render one Ken Burns shot segment to work_dir/shot_NNN.mp4 (video only)."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    index = int(shot.get("index", 0))
    duration = float(shot.get("duration", 3.0))
    frames = max(1, int(round(duration * fps)))
    out = work_dir / f"shot_{index:03d}.mp4"
    filter_str = build_ken_burns_filter(shot, width=width, height=height, fps=fps)

    def _build(cmd: list[str]) -> None:
        _run(cmd)

    try:
        if _looks_like_video(asset_path):
            _build([
                "ffmpeg", "-y", "-i", str(asset_path),
                "-filter_complex", filter_str,
                "-frames:v", str(frames), "-r", str(fps),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-t", str(duration), "-an", str(out),
            ])
        elif _looks_like_image(asset_path):
            _build([
                "ffmpeg", "-y", "-loop", "1", "-r", str(fps), "-i", str(asset_path),
                "-filter_complex", filter_str,
                "-frames:v", str(frames), "-r", str(fps),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-t", str(duration), "-an", str(out),
            ])
        else:
            _build([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c=0x202030:s={width}x{height}:r={fps}:d={duration}",
                "-vf", f"noise=alls=6:allf=t,{filter_str}",
                "-frames:v", str(frames), "-r", str(fps),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-t", str(duration), "-an", str(out),
            ])
    except Exception:
        # Fall back to a procedural gradient segment for THIS shot only.
        fallback = _procedural_source(work_dir, shot, duration, width=width, height=height)
        if fallback != out:
            try:
                fallback.replace(out)
            except Exception:
                import shutil
                shutil.copy(fallback, out)
    return out


def build_concat_filter(shots: list[dict]) -> str:
    """ffmpeg concat filter string over the shot video streams."""
    if not shots:
        return ""
    inputs = "".join(f"[{i}:v]" for i in range(len(shots)))
    return f"{inputs}concat=n={len(shots)}:v=1:a=0[v]"


def _ass_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hrs}:{mins:02d}:{secs:05.2f}"


def make_kinetic_ass(transcript_words: list[dict], out_path: Path, *,
                     width: int = 1080, height: int = 1920) -> Path:
    r"""ASS with per-word {\k} highlighting, 2-3 words per line, safe-zone margins."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    words = sorted(transcript_words, key=lambda w: float(w.get("start", 0.0)))

    lines: list[list[dict]] = []
    current: list[dict] = []
    for word in words:
        current.append(word)
        if len(current) >= 3:
            lines.append(current)
            current = []
    if current:
        lines.append(current)

    margin_l = max(20, int(width * 0.05))
    margin_v = max(40, int(height * SAFE_ZONE_BOTTOM))
    margin_top = max(20, int(height * SAFE_ZONE_TOP))

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\n"
        f"PlayResY: {height}\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
        "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Kinetic,DejaVu Sans Bold,56,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        "-1,0,0,0,100,100,0,0,1,3,1,2,{margin_l},{margin_l},{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    ).format(margin_l=margin_l, margin_v=margin_v)

    events: list[str] = []
    for line in lines:
        start = _ass_timestamp(float(line[0].get("start", 0.0)))
        end = _ass_timestamp(float(line[-1].get("end", 0.0)))
        parts: list[str] = []
        last_end = float(line[0].get("start", 0.0))
        for word in line:
            w_start = float(word.get("start", last_end))
            w_end = float(word.get("end", w_start + 0.4))
            cs = max(1, int(round((w_end - w_start) * 100)))
            parts.append(f"{{\\k{cs}}}{word.get('word', '')}")
            last_end = w_end
        events.append(f"Dialogue: 0,{start},{end},Kinetic,,{margin_l},{margin_l},{margin_v},,"
                       + "".join(parts))

    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return out_path


def synthesize_music_bed(work_dir: Path, duration: float, *,
                         path: Path | None = None) -> Path:
    """Synthesize a low synth/noise music bed with fades, looping to duration."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out = path or (work_dir / "music_bed.wav")
    dur = max(2.0, float(duration)) + 2.0
    _run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={dur}",
        "-f", "lavfi", "-i", f"anoisesrc=duration={dur}:color=pink",
        "-filter_complex",
        "[1:a]volume=0.05[a_noise];[0:a][a_noise]amix=inputs=2:duration=longest,"
        f"afade=t=in:st=0:d=1,afade=t=out:st={max(0.5, dur - 1)}:d=1,"
        f"aformat=sample_rates={AUDIO_RATE}:channel_layouts=mono",
        "-c:a", "pcm_s16le", "-t", str(dur), "-vn", str(out),
    ])
    return out


def synthesize_sfx(kind: str, work_dir: Path, *, path: Path | None = None) -> Path | None:
    """Synthesize a short whoosh/impact/riser sfx via ffmpeg lavfi. None on unknown kind."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out = path or (work_dir / f"sfx_{kind}.wav")
    if kind == "impact":
        vf = ("[0:a]afade=t=out:st=0.05:d=0.4,aformat="
              f"sample_rates={AUDIO_RATE}:channel_layouts=mono")
        src = f"sine=frequency=55:duration=0.5"
        inputs = ["-f", "lavfi", "-i", src]
    elif kind == "whoosh":
        vf = ("[0:a]highpass=f=900,afade=t=in:st=0:d=0.15,afade=t=out:st=0.35:d=0.35,"
              f"aformat=sample_rates={AUDIO_RATE}:channel_layouts=mono")
        src = f"anoisesrc=duration=0.7:color=white"
        inputs = ["-f", "lavfi", "-i", src]
    elif kind == "riser":
        vf = (f"aformat=sample_rates={AUDIO_RATE}:channel_layouts=mono,"
              f"afade=t=out:st=0.9:d=0.6")
        src = f"aevalsrc=\"sin(2*PI*(180+900*t)*t)\":duration=1.5:sample_rate={AUDIO_RATE}"
        inputs = ["-f", "lavfi", "-i", src]
    else:
        return None
    try:
        _run(["ffmpeg", "-y", *inputs, "-af", vf, "-vn", str(out)])
    except Exception:
        return None
    return out if out.exists() and out.stat().st_size > 0 else None


def _concat_videos(shot_files: list[Path], shots: list[dict], work_dir: Path) -> Path:
    out = work_dir / "video_full.mp4"
    # Prefer the concat filter API; fall back to the demuxer if anything goes wrong.
    try:
        filter_str = build_concat_filter(shots)
        inputs = []
        for f in shot_files:
            inputs.extend(["-i", str(f)])
        _run([
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-an", str(out),
        ])
        if out.exists() and out.stat().st_size > 1000:
            return out
    except Exception:
        pass
    list_file = work_dir / "concat_list.txt"
    lines = []
    for f in shot_files:
        lines.append(f"file '{f}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", "-an", str(out),
    ])
    return out


def _mix_audio(shots: list[dict], audio_path: Path, work_dir: Path,
               music_gain_db: float, music_bed: Path | None,
               sfx_timed: list[tuple[float, Path]]) -> Path:
    out = work_dir / "audio_mix.wav"
    inputs: list[str] = []
    input_count = 0

    def add_input(path: Path) -> str:
        nonlocal input_count
        index = input_count
        input_count += 1
        inputs.extend(["-i", str(path)])
        return f"[{index}:a]"

    voice_in = add_input(audio_path)
    music_in = add_input(music_bed) if music_bed else ""

    filter_parts: list[str] = []
    filter_parts.append(f"{voice_in}aresample={AUDIO_RATE},afifo,loudnorm=I=-16:TP=-1.5:LRA=11[vn]")
    if music_in:
        filter_parts.append(f"{music_in}aresample={AUDIO_RATE},afifo,volume={music_gain_db}[m]")
        filter_parts.append(f"[m][vn]sidechaincompress=threshold=0.04:ratio=12:attack=10:"
                            f"release=250:makeup=2[mduck]")
    else:
        filter_parts.append("[vn]anull[voicenull]")

    mix_inputs: list[str] = ["[vn]"]
    if music_in:
        mix_inputs.append("[mduck]")
    for offset, sfx_path in sfx_timed:
        sfx_in = add_input(sfx_path)
        delay_ms = int(round(offset * 1000))
        filter_parts.append(f"{sfx_in}aresample={AUDIO_RATE},afifo,adelay={delay_ms}|{delay_ms}[sfx{input_count}]")
        mix_inputs.append(f"[sfx{input_count}]")

    if len(mix_inputs) > 1:
        filter_parts.append(
            "".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:duration=longest[a]"
        )
    else:
        filter_parts.append("[vn]anull[a]")

    _run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filter_parts),
          "-map", "[a]", "-c:a", "pcm_s16le", str(out)])
    return out


def render_video(shots: list[dict], audio_path: Path, out_path: Path, *, work_dir: Path,
                 ass_path: Path | None = None, width: int = WIDTH, height: int = HEIGHT,
                 fps: int = FPS) -> dict:
    """Render a full multi-shot short. -> {'status','path','duration','shots','width',
    'height','music','sfx_count'}"""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(out_path)
    audio_path = Path(audio_path)

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

    for shot in shots:
        detail = resolve_asset_detail(shot, work_dir, used_titles=used_titles)
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
        try:
            shot_file = render_shot(shot, asset_path, work_dir, fps=fps, width=width, height=height)
        except Exception:
            shot_file = render_shot(shot, None, work_dir, fps=fps, width=width, height=height)
        shot_files.append(shot_file)
        kind = shot.get("sfx")
        if kind and kind != "none":
            sfx_path = synthesize_sfx(kind, work_dir)
            if sfx_path:
                sfx_timed.append((float(shot.get("start", 0.0)), sfx_path))

    video_full = _concat_videos(shot_files, shots, work_dir)

    sfx_count = len(sfx_timed)
    try:
        if total_duration > 0:
            music_bed = synthesize_music_bed(work_dir, total_duration)
        audio_mix = _mix_audio(shots, audio_path, work_dir, music_gain_db, music_bed, sfx_timed)
    except Exception:
        audio_mix = audio_path  # last resort: voice only

    _run([
        "ffmpeg", "-y", "-i", str(video_full), "-i", str(audio_mix),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", str(out_path),
    ])

    status = "ok" if out_path.exists() and out_path.stat().st_size > 1000 else "failed"
    duration = _probe_duration(out_path) if out_path.exists() else 0.0
    return {
        "status": status,
        "path": str(out_path),
        "duration": round(duration, 3),
        "shots": len(shots),
        "width": width,
        "height": height,
        "music": str(music_bed) if music_bed else None,
        "sfx_count": sfx_count,
        "assets": assets,
        "credits": stock_fetcher.credit_lines(assets),
    }


def qa_video(path: Path, *, width: int = 1080, height: int = 1920,
             min_duration: float = 15, max_duration: float = 90) -> dict:
    """ffprobe validation; raise RuntimeError on mismatch."""
    path = Path(path)
    data = _ffprobe(path)
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    try:
        duration = float(fmt.get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    vw = int(video.get("width") or 0) if video else 0
    vh = int(video.get("height") or 0) if video else 0
    errors: list[str] = []
    if not video:
        errors.append("no video stream")
    if vw != width or vh != height:
        errors.append(f"resolution {vw}x{vh} != {width}x{height}")
    if not (min_duration <= duration <= max_duration):
        errors.append(f"duration {duration:.2f}s outside [{min_duration},{max_duration}]")
    if not has_audio:
        errors.append("no audio stream")
    if errors:
        raise RuntimeError("video QA failed: " + "; ".join(errors))
    return {
        "duration": round(duration, 3),
        "width": vw,
        "height": vh,
        "has_audio": bool(has_audio),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Motion renderer demo")
    ap.add_argument("--demo", action="store_true", help="run a quick synthetic render")
    args = ap.parse_args()
    if not args.demo:
        ap.print_help()
        return

    import motion_director

    work_dir = Path(__file__).resolve().parent / "work_demo"
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
