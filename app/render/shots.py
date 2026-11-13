"""Per-shot Ken Burns rendering and procedural fallbacks.

Moved verbatim from motion_render.py in Phase 7B; logic unchanged.
"""
from __future__ import annotations

from pathlib import Path

from app.render.ffmpeg_tools import (
    FPS,
    HEIGHT,
    WIDTH,
    _run,
    build_ken_burns_filter,
)

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
        "-i", f"color=c={color}:s={width}x{height}:r={FPS}:d={duration}",
        "-vf", f"noise=alls=6:allf=t,zoompan=z='1.0':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':d=1:s={width}x{height}:fps={FPS}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
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


def _valid_output(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 1000


def render_shot(shot: dict, asset_path: Path | None, work_dir: Path, *,
                fps: int = 30, width: int = WIDTH, height: int = HEIGHT,
                diagnostics: list[dict] | None = None) -> Path:
    """Render one Ken Burns shot segment to work_dir/shot_NNN.mp4 (video only)."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    index = int(shot.get("index", 0))
    duration = float(shot.get("duration", 3.0))
    frames = max(1, int(round(duration * fps)))
    out = work_dir / f"shot_{index:03d}.mp4"
    filter_str = build_ken_burns_filter(shot, width=width, height=height, fps=fps)
    has_video_asset = _looks_like_video(asset_path)
    has_image_asset = _looks_like_image(asset_path)

    if diagnostics is not None and not (has_video_asset or has_image_asset):
        diagnostics.append({
            "index": index,
            "fallback": "procedural_source",
            "reason": "no usable asset path reached the renderer",
        })

    def _build(cmd: list[str]) -> None:
        _run(cmd)

    try:
        if has_video_asset:
            # Loop the source so a clip shorter than the shot cannot silently
            # truncate the segment (and desynchronise the whole video).  The
            # frame/timestamp limits below still stop at the shot duration.
            _build([
                "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(asset_path),
                "-filter_complex", filter_str,
                "-frames:v", str(frames), "-r", str(fps),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-t", str(duration), "-an", str(out),
            ])
        elif has_image_asset:
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
        if not _valid_output(out):
            raise RuntimeError("shot output missing or too small")
    except Exception as exc:
        # Fall back to a procedural gradient segment for THIS shot only.
        if diagnostics is not None:
            diagnostics.append({
                "index": index,
                "fallback": "procedural_source",
                "reason": f"{type(exc).__name__}: {exc}"[:240],
            })
        fallback = _procedural_source(work_dir, shot, duration, width=width, height=height)
        if not _valid_output(fallback):
            raise RuntimeError(f"shot {index} failed and the procedural fallback was empty")
        if fallback != out:
            try:
                fallback.replace(out)
            except Exception:
                import shutil
                shutil.copy(fallback, out)
    return out
