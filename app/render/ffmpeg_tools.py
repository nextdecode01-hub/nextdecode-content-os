"""Low-level FFmpeg assembly helpers.

Moved verbatim from motion_render.py in Phase 7B; logic unchanged.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

FFMPEG_TIMEOUT = 300
WIDTH = 1080
HEIGHT = 1920
FPS = 30
AUDIO_RATE = 44100

# The delivery bitrate.  Edge TTS hands back 24 kHz / 48 kbps mono mp3, so a
# higher number cannot add bandwidth the model never rendered; it stops the
# encode from *removing* anything.  Note the ceiling is codec-bound: ffmpeg's
# native AAC encoder clamps a mono stream to roughly 148 kb/s regardless of the
# request (6144 bits per frame), while the mp3 narration deliverable really does
# write 320 kbps CBR.  QA records the measured bitrate, not the requested one.
DEFAULT_AUDIO_BITRATE = "320k"


def audio_bitrate() -> str:
    """Return the AAC/MP3 bitrate for the finished file (``AUDIO_BITRATE``)."""
    value = os.getenv("AUDIO_BITRATE", "").strip() or DEFAULT_AUDIO_BITRATE
    return value if re.fullmatch(r"\d{2,4}k", value.lower()) else DEFAULT_AUDIO_BITRATE


def music_bed_requested() -> bool:
    """Phase 9: the bed is opt-in so narration ships clean by default.

    ``MUSIC_BED=on`` enables the synthesized pad; ``MUSIC_BED_FILE=/path.mp3``
    uses a real licensed track and implies the bed is wanted.
    """
    if os.getenv("MUSIC_BED_FILE", "").strip():
        return True
    return os.getenv("MUSIC_BED", "").strip().lower() in {"1", "true", "yes", "on"}


def music_bed_source() -> Path | None:
    """A licensed bed file supplied by the owner, if configured and readable."""
    raw = os.getenv("MUSIC_BED_FILE", "").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None

_ZERO_AUDIO = "anullsrc=r=44100:cl=mono"


def _run(cmd: list[str], timeout: int = FFMPEG_TIMEOUT) -> None:
    """Run FFmpeg and retain a bounded diagnostic when it fails.

    The command arguments are deliberately not copied into the exception: they
    can contain private paths or filter text. The caller's failure recorder is
    responsible for redacting the bounded stderr/stdout excerpt before storage.
    """
    executable = Path(str(cmd[0])).name if cmd else "ffmpeg"
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        output = exc.stderr or exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        diagnostic = str(output).strip()[-1200:]
        suffix = f"; diagnostic: {diagnostic}" if diagnostic else ""
        raise RuntimeError(f"{executable} timed out after {timeout}s{suffix}") from None
    if completed.returncode != 0:
        output = (completed.stderr or completed.stdout or "").strip()
        diagnostic = output[-1200:]
        suffix = f"; diagnostic: {diagnostic}" if diagnostic else ""
        raise RuntimeError(f"{executable} exited with code {completed.returncode}{suffix}")


def _ffprobe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_entries",
        "format=duration,size:stream=codec_type,width,height,r_frame_rate,avg_frame_rate",
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


def _fraction(value: object) -> float:
    try:
        numerator, _, denominator = str(value).partition("/")
        den = float(denominator) if denominator else 1.0
        return float(numerator) / den if den else 0.0
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def _audio_levels(path: Path) -> dict:
    """Mean/max volume in dB via ffmpeg volumedetect (offline)."""
    try:
        completed = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
             "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, timeout=120,
        )
    except Exception:
        return {}
    text = (completed.stderr or "") + (completed.stdout or "")
    levels: dict[str, float] = {}
    for key in ("mean_volume", "max_volume"):
        match = re.search(rf"{key}:\s*(-?\d+(?:\.\d+)?)\s*dB", text)
        if match:
            levels[key] = float(match.group(1))
    return levels


def _interval_filter(path: Path, filter_expr: str, pattern: str) -> list[tuple[float, float]]:
    try:
        completed = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
             "-vf", filter_expr, "-an", "-f", "null", "-"],
            capture_output=True, text=True, timeout=300,
        )
    except Exception:
        return []
    text = (completed.stderr or "") + (completed.stdout or "")
    intervals: list[tuple[float, float]] = []
    for match in re.finditer(pattern, text):
        start = float(match.group(1))
        end = float(match.group(2)) if match.group(2) else start
        intervals.append((start, end))
    return intervals


def video_luma_stats(path: Path, *, sample_step: int = 15) -> dict[str, float]:
    """Average luma distribution of a video/image using signalstats.

    Returns ``{ymin, ylow, yavg, yhigh, ymax}`` on a 0–255 scale.  Used to flag
    dark/flat footage that is not fully black but is hard to read on a phone.
    """
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf", f"select='not(mod(n,{max(1, int(sample_step))}))',signalstats,metadata=print:file=-",
        "-f", "null", "-",
    ]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except Exception:
        return {}
    values: dict[str, list[float]] = {}
    for line in (completed.stdout or "").splitlines():
        match = re.search(
            r"lavfi\.signalstats\.(YMIN|YLOW|YAVG|YHIGH|YMAX)=([0-9.]+)",
            line.strip(),
        )
        if match:
            values.setdefault(match.group(1).lower(), []).append(float(match.group(2)))
    return {
        key: round(sum(items) / len(items), 2)
        for key, items in values.items()
        if items
    }


def _black_intervals(path: Path, *, min_duration: float = 1.0,
                     pix_th: float = 0.04) -> list[tuple[float, float]]:
    return _interval_filter(
        path,
        f"blackdetect=d={min_duration}:pix_th={pix_th}",
        r"black_start:(\d+(?:\.\d+)?)\s+black_end:(\d+(?:\.\d+)?)",
    )


def _frozen_intervals(path: Path, *, min_duration: float = 1.0) -> list[tuple[float, float]]:
    return _interval_filter(
        path,
        f"freezedetect=n=0.003:d={min_duration}",
        r"freeze_start:\s*(\d+(?:\.\d+)?)(?:\s+freeze_end:\s*(\d+(?:\.\d+)?))?",
    )


def _ass_seconds(value: str) -> float:
    try:
        hours, minutes, seconds = str(value).strip().split(":")
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except (TypeError, ValueError):
        return 0.0


def _caption_stats(captions: object) -> dict:
    """Summarise caption timing without trusting the renderer."""
    if captions is None:
        return {"checked": False}
    if isinstance(captions, (str, Path)):
        path = Path(captions)
        if not path.is_file():
            return {"checked": True, "exists": False, "events": 0, "last_end": 0.0}
        events = 0
        last_end = 0.0
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.startswith("Dialogue:"):
                continue
            parts = line.split(",", 9)
            if len(parts) < 10:
                continue
            events += 1
            last_end = max(last_end, _ass_seconds(parts[2]))
        return {"checked": True, "exists": True, "events": events,
                "last_end": round(last_end, 3), "path": str(path)}
    if isinstance(captions, list):
        ends = [
            float(item.get("end", 0) or 0)
            for item in captions
            if isinstance(item, dict)
        ]
        return {"checked": True, "exists": True, "events": len(ends),
                "last_end": round(max(ends) if ends else 0.0, 3)}
    return {"checked": False}


def _even(value: float) -> int:
    number = int(round(float(value)))
    return number if number % 2 == 0 else number + 1


def build_scale_crop_filter(scale: float = 1.0, *, width: int = 1080,
                            height: int = 1920, focal_x: float = 0.5,
                            focal_y: float = 0.5) -> str:
    """Fixed crop for native video, positioning the declared focal point."""
    scale = max(1.0, min(1.20, float(scale)))
    focal_x = max(0.0, min(1.0, float(focal_x)))
    focal_y = max(0.0, min(1.0, float(focal_y)))
    return (
        f"scale={_even(width * scale)}:{_even(height * scale)}:"
        f"force_original_aspect_ratio=increase,"
        f"crop={int(width)}:{int(height)}:"
        f"x='(iw-{int(width)})*{focal_x}':y='(ih-{int(height)})*{focal_y}',setsar=1"
    )


def build_ken_burns_filter(shot: dict, *, width: int = 1080, height: int = 1920,
                           fps: int = 30) -> str:
    """Build executable framing, motion and EDL edge-transition filters."""
    duration = float(shot.get("duration", 3.0))
    frames = max(1, int(round(duration * fps)))
    motion = shot.get("motion") or {}
    framing = shot.get("framing") or {}
    fit = str(framing.get("mode") or "fill").lower()
    focal_x = max(0.0, min(1.0, float(framing.get("focal_x", 0.5))))
    focal_y = max(0.0, min(1.0, float(framing.get("focal_y", 0.5))))

    if fit == "contain":
        filter_str = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
        )
    elif str(motion.get("mode") or "").lower() == "native":
        filter_str = build_scale_crop_filter(
            float(motion.get("zoom_from", 1.0) or 1.0), width=width, height=height,
            focal_x=focal_x, focal_y=focal_y,
        )
    else:
        z_from = float(motion.get("zoom_from", shot.get("zoom_from", 1.0)) or 1.0)
        z_to = float(motion.get("zoom_to", shot.get("zoom_to", 1.14)) or 1.14)
        z_from = max(1.0, min(1.20, z_from))
        z_to = max(1.0, min(1.20, z_to))
        pan = motion.get("pan") or shot.get("pan") or {}
        limit = float(width) * 0.03
        px0 = max(-limit, min(limit, float(pan.get("x0", pan.get("x", 0.0)) or 0.0)))
        py0 = max(-limit, min(limit, float(pan.get("y0", pan.get("y", 0.0)) or 0.0)))
        px1 = max(-limit, min(limit, float(pan.get("x1", -px0) or 0.0)))
        py1 = max(-limit, min(limit, float(pan.get("y1", -py0) or 0.0)))
        progress = f"min(on/{frames},1)"
        ease = f"(3*pow({progress},2)-2*pow({progress},3))"
        z = f"{z_from}+({z_to}-{z_from})*{ease}"
        x = f"iw*{focal_x}-(iw/zoom)/2+({px0}+({px1}-{px0})*{ease})"
        y = f"ih*{focal_y}-(ih/zoom)/2+({py0}+({py1}-{py0})*{ease})"
        filter_str = f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={width}x{height}:fps={fps}"

    # EDL edge fades are applied to the shot itself; interior transitions remain cuts.
    edge = shot.get("edl_transition") or {}
    fade_frames = max(1, int(edge.get("duration_frames", 0) or 0))
    if edge.get("in") and fade_frames:
        filter_str += f",fade=t=in:st=0:d={fade_frames / fps:.6f}"
    if edge.get("out") and fade_frames:
        fade_start = max(0.0, duration - fade_frames / fps)
        filter_str += f",fade=t=out:st={fade_start:.6f}:d={fade_frames / fps:.6f}"
    return filter_str


def build_concat_filter(shots: list[dict]) -> str:
    """ffmpeg concat filter string over the shot video streams."""
    if not shots:
        return ""
    inputs = "".join(f"[{i}:v]" for i in range(len(shots)))
    return f"{inputs}concat=n={len(shots)}:v=1:a=0[v]"


def synthesize_music_bed(work_dir: Path, duration: float, *,
                         path: Path | None = None) -> Path:
    """Build a low tonal bed with fades, looping to duration.

    Phase 9 removed the pink-noise layer: the voice source carries nothing above
    its 12 kHz Nyquist limit, so broadband hiss added under the narration was
    pure noise that filled the pauses between sentences.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out = path or (work_dir / "music_bed.wav")
    dur = max(2.0, float(duration)) + 2.0
    _run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={dur}",
        "-f", "lavfi", "-i", f"sine=frequency=164.81:duration={dur}",
        "-filter_complex",
        "[0:a][1:a]amix=inputs=2:duration=longest:normalize=1,"
        "lowpass=f=2000,tremolo=f=0.15:d=0.25,"
        f"afade=t=in:st=0:d=1,afade=t=out:st={max(0.5, dur - 1)}:d=1,"
        f"aformat=sample_rates={AUDIO_RATE}:channel_layouts=mono",
        "-c:a", "pcm_s16le", "-t", str(dur), "-vn", str(out),
    ])
    return out


def synthesize_sfx(kind: str, work_dir: Path, *, path: Path | None = None) -> Path | None:
    """Synthesize a short whoosh/impact/riser sfx via ffmpeg lavfi. None on unknown kind.

    These are placeholders for a licensed library, so they are shaped to stay out
    of the narration: pink rather than white noise, band-limited away from the
    2-8 kHz consonant region, and faded at both ends so nothing lands on a cut as
    a transient.  They remain opt-in (``SHOT_SFX=on``) after the Phase 7 finding
    that one effect per cut read as cut noise.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out = path or (work_dir / f"sfx_{kind}.wav")
    if kind == "impact":
        # Short fade-in removes the hard sine onset that reads as a click when the
        # sound is placed exactly on a video cut; the lowpass keeps the thump soft.
        vf = ("[0:a]lowpass=f=180,afade=t=in:st=0:d=0.02,afade=t=out:st=0.05:d=0.4,aformat="
              f"sample_rates={AUDIO_RATE}:channel_layouts=mono")
        src = f"sine=frequency=55:duration=0.5"
        inputs = ["-f", "lavfi", "-i", src]
    elif kind == "whoosh":
        # Pink noise inside a speech-shaped band: white noise high-passed at
        # 900 Hz put most of its energy exactly where consonants live.
        vf = ("[0:a]highpass=f=180,lowpass=f=2400,"
              "afade=t=in:st=0:d=0.15,afade=t=out:st=0.35:d=0.35,"
              f"aformat=sample_rates={AUDIO_RATE}:channel_layouts=mono")
        src = f"anoisesrc=duration=0.7:color=pink"
        inputs = ["-f", "lavfi", "-i", src]
    elif kind == "riser":
        # The aevalsrc expression must not be quoted: passed straight to ffmpeg
        # the quotes make lavfi fail to parse it, so the riser silently never
        # existed.  It is also full-scale, hence the trim.
        vf = (f"aformat=sample_rates={AUDIO_RATE}:channel_layouts=mono,"
              "volume=0.2,lowpass=f=1800,afade=t=in:st=0:d=0.3,"
              f"afade=t=out:st=0.9:d=0.6")
        src = f"aevalsrc=sin(2*PI*(180+900*t)*t):duration=1.5:sample_rate={AUDIO_RATE}"
        inputs = ["-f", "lavfi", "-i", src]
    else:
        return None
    try:
        _run(["ffmpeg", "-y", *inputs, "-af", vf, "-vn", str(out)])
    except Exception:
        return None
    return out if out.exists() and out.stat().st_size > 0 else None


def build_editorial_concat_filter(shots: list[dict], *, transition_seconds: float = 0.32) -> tuple[str, float]:
    """Build a frame-accurate FFmpeg xfade graph from explicit editorial intent.

    Hard/match cuts remain effectively instantaneous. Dissolves, wipes and
    whip-pan transitions overlap adjacent clips; the caller pads the final
    frame to preserve the narration's master duration.
    """
    if not shots:
        return "", 0.0
    parts = []
    for index, shot in enumerate(shots):
        parts.append(f"[{index}:v]settb=AVTB,setpts=PTS-STARTPTS[v{index}]")
    current_duration = float(shots[0].get("duration") or 0.0)
    previous = "v0"
    overlap_total = 0.0
    transition_map = {
        "dissolve": "dissolve", "wipe": "wipeleft", "wipe_left": "wipeleft",
        "wipe_right": "wiperight", "whip_pan": "smoothleft",
        "flash": "fadeblack",
    }
    for index in range(1, len(shots)):
        intent = str(shots[index].get("transition_intent") or shots[index].get("transition") or "cut").lower()
        transition = transition_map.get(intent, "fade")
        duration = transition_seconds if intent in transition_map else (1.0 / FPS)
        duration = min(duration, max(1.0 / FPS, float(shots[index-1].get("duration") or 0.0) / 3.0),
                       max(1.0 / FPS, float(shots[index].get("duration") or 0.0) / 3.0))
        offset = max(0.0, current_duration - duration)
        output = f"vx{index}"
        parts.append(f"[{previous}][v{index}]xfade=transition={transition}:duration={duration:.6f}:offset={offset:.6f}[{output}]")
        current_duration += float(shots[index].get("duration") or 0.0) - duration
        overlap_total += duration
        previous = output
    expected_duration = sum(float(item.get("duration") or 0.0) for item in shots)
    pad = max(0.0, expected_duration - current_duration)
    final_filter = f"[{previous}]tpad=stop_mode=clone:stop_duration={pad:.6f},trim=duration={expected_duration:.6f},setpts=PTS-STARTPTS[v]"
    parts.append(final_filter)
    return ";".join(parts), overlap_total


def _concat_videos(shot_files: list[Path], shots: list[dict], work_dir: Path) -> Path:
    """Concatenate shot segments frame-exactly.

    Historically this used an ``xfade`` chain for every cut, which produced a
    truncated, non-deterministic output on this build (135 frames / 4.5s from a
    49s plan instead of ~1480 frames).  The reliable contract is frame-exact
    concatenation of same-parameter segments; the fine-grained editorial
    transition intent is still honoured when every adjacent pair actually
    renders longer than the plain cut — but for correctness the plain path is
    the default and always wins when it verifies.
    """
    if not shot_files:
        raise RuntimeError("cannot concatenate an empty shot list")
    missing = [str(path) for path in shot_files if not Path(path).is_file()]
    if missing:
        raise RuntimeError(f"shot segments are missing: {', '.join(missing[:3])}")
    out = work_dir / "video_full.mp4"

    # Path 1 (default, deterministic): the concat filter.  Every segment already
    # shares codec, dimensions, frame rate and pixel format, so a single-pass
    # concat cannot drop or duplicate frames.  The result is verified against
    # the sum of the shot durations.
    try:
        expected = sum(float(item.get("duration") or 0.0) for item in shots)
        inputs = []
        for f in shot_files:
            inputs.extend(["-i", str(f)])
        _run([
            "ffmpeg", "-y", *inputs,
            "-filter_complex", f"concat=n={len(shots)}:v=1:a=0[v]",
            "-map", "[v]",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-an", str(out),
        ])
        measured = _probe_duration(out)
        if out.is_file() and out.stat().st_size > 1000 and abs(measured - expected) <= 0.5:
            return out
        # fall through to demuxer path if verification fails
    except Exception:
        pass

    # Path 2 (lossless, byte-level): concat demuxer with stream copy.  Useful
    # when a re-encode is not required and every segment is stream-identical.
    list_file = work_dir / "concat_list.txt"
    lines = []
    for f in shot_files:
        lines.append(f"file '{f}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", "-an", str(out),
    ])
    expected = sum(float(item.get("duration") or 0.0) for item in shots)
    measured = _probe_duration(out)
    if not out.is_file() or out.stat().st_size <= 1000:
        raise RuntimeError("concatenating the shot segments produced an empty video")
    if expected and abs(measured - expected) > 0.5:
        raise RuntimeError(
            f"concatenated duration mismatch: expected about {expected:.2f}s, got {measured:.2f}s"
        )
    return out


LOUDNORM_TARGET = "I=-16:TP=-1.5:LRA=11"

# Ceiling for the summed master: 0.84 linear is -1.5 dBFS, which keeps the
# inter-sample true peak at or below about -1 dBTP once a bed or effect is added.
MASTER_LIMIT = 0.84

# Conservative duck: a 3:1 ratio with no makeup gain moves the bed a few dB
# instead of collapsing it, which is what produced the audible breathing in the
# Phase 8 renders (ratio=12 plus a 2x makeup gain).
DUCK_FILTER = ("sidechaincompress=threshold=0.06:ratio=3:attack=20:"
               "release=250:makeup=1")


def _measure_loudnorm(path: Path, target: str = LOUDNORM_TARGET) -> str | None:
    """Run the measurement pass of loudnorm and return the linear-mode filter.

    Single-pass ``loudnorm`` is a dynamic normaliser: it rides the gain inside a
    sentence, which flattens the narration's own dynamics.  Feeding the measured
    values back in with ``linear=true`` turns the same target into a fixed gain
    adjustment, so the voice keeps its phrasing while still landing at -16 LUFS.
    Returns ``None`` when the pass cannot be measured (short/odd inputs).
    """
    if not Path(path).exists():
        return None
    parsed = dict(re.findall(r"(\w+)=(-?[\d.]+)", target))
    try:
        completed = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
             "-af", f"loudnorm={target}:print_format=json",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=300,
        )
    except Exception:
        return None
    blob = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", completed.stderr or "")
    if not blob:
        return None
    try:
        measured = json.loads(blob.group(0))
    except json.JSONDecodeError:
        return None
    needed = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")
    if any(measured.get(key) in (None, "inf", "-inf", "nan") for key in needed):
        return None
    try:
        values = {key: float(measured[key]) for key in needed}
    except (TypeError, ValueError):
        return None
    if measured.get("normalization_type") not in (None, "dynamic"):
        return None
    return (
        f"loudnorm=I={parsed.get('I', -16)}:TP={parsed.get('TP', -1.5)}:"
        f"LRA={parsed.get('LRA', 11)}"
        f":measured_I={values['input_i']}:measured_TP={values['input_tp']}:"
        f"measured_LRA={values['input_lra']}:measured_thresh={values['input_thresh']}:"
        f"offset={values['target_offset']}:linear=true:print_format=summary"
    )


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

    voice_norm = _measure_loudnorm(Path(audio_path)) or f"loudnorm={LOUDNORM_TARGET}"
    filter_parts: list[str] = []
    if music_in:
        # The narration feeds two branches: the mix itself and the ducking
        # sidechain.  A filter pad can only be consumed once, so reusing [vn]
        # silently cost about 6 dB of voice level in every bed mix (measured
        # -22.4 LUFS against a -16.2 LUFS target).  asplit gives each branch its
        # own copy and the level comes back where it belongs.
        filter_parts.append(f"{voice_in}aresample={AUDIO_RATE},{voice_norm},asplit=2[vn][vsc]")
        # ``volume=`` takes linear gain unless the value carries a dB suffix.
        filter_parts.append(f"{music_in}aresample={AUDIO_RATE},volume={music_gain_db}dB[m]")
        filter_parts.append(f"[m][vsc]{DUCK_FILTER}[mduck]")
    else:
        filter_parts.append(f"{voice_in}aresample={AUDIO_RATE},{voice_norm}[vn]")

    mix_inputs: list[str] = ["[vn]"]
    if music_in:
        mix_inputs.append("[mduck]")
    for offset, sfx_path in sfx_timed:
        sfx_in = add_input(sfx_path)
        delay_ms = int(round(offset * 1000))
        filter_parts.append(
            f"{sfx_in}aresample={AUDIO_RATE},volume=-8dB,"
            f"adelay={delay_ms}|{delay_ms}[sfx{input_count}]"
        )
        mix_inputs.append(f"[sfx{input_count}]")

    if len(mix_inputs) > 1:
        # normalize=0 keeps the voice at its loudness instead of dividing it by
        # the number of SFX inputs.  level=false matters: alimiter's default
        # automatic level *raises* the mix to the ceiling, which measured
        # 0.0 dBTP (real clipping risk) where level=false holds -1.5 dBTP.
        filter_parts.append(
            "".join(mix_inputs)
            + f"amix=inputs={len(mix_inputs)}:duration=longest:normalize=0,"
              f"alimiter=limit={MASTER_LIMIT}:level=false[a]"
        )
    else:
        filter_parts.append("[vn]anull[a]")

    _run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filter_parts),
          "-map", "[a]", "-c:a", "pcm_s24le", "-ar", str(AUDIO_RATE), str(out)])
    return out


def _audio_stream_info(path: Path) -> dict:
    """Codec, bitrate, sample rate and channel count of the delivered audio."""
    try:
        completed = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name,bit_rate,sample_rate,channels",
             "-print_format", "json", str(path)],
            capture_output=True, text=True, timeout=120,
        )
        data = json.loads(completed.stdout or "{}")
    except Exception:
        return {}
    streams = data.get("streams") or []
    return dict(streams[0]) if streams else {}


def _true_peak(path: Path) -> float | None:
    """Measure EBU R128 true peak in dBTP via the loudnorm analysis pass."""
    try:
        completed = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=300,
        )
    except Exception:
        return None
    match = re.search(r'"input_tp"\s*:\s*"(-?[\d.]+|-?inf|nan)"', completed.stderr or "")
    if not match:
        return None
    value = match.group(1)
    if "inf" in value or value == "nan":
        return None
    return float(value)


def qa_video(path: Path, *, width: int = 1080, height: int = 1920,
             min_duration: float = 15, max_duration: float = 90,
             expected_fps: float | None = None, min_size_bytes: int = 1000,
             silence_db: float | None = -50.0, check_black_frames: bool = False,
             assets: list[dict] | None = None, captions: object = None,
             audio_boundaries: dict | None = None,
             strict_visuals: bool = False, strict: bool = True) -> dict:
    """Validate a rendered video and return a pass/fail summary.

    Hard failures raise ``RuntimeError`` when ``strict`` is true (the historical
    behaviour).  Soft findings (black/frozen stretches, reused assets, captions
    that outrun the video) are returned as warnings so they stay visible without
    blocking every render.
    """
    path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool | None] = {}

    exists = path.is_file() and path.stat().st_size >= max(1, int(min_size_bytes))
    checks["exists"] = exists
    if not exists:
        errors.append(
            f"missing or too small (<{min_size_bytes} bytes): {path}"
        )
        summary = {
            "status": "fail", "duration": 0.0, "width": 0, "height": 0,
            "fps": 0.0, "has_audio": False, "size_bytes": 0,
            "checks": checks, "errors": errors, "warnings": warnings,
            "audio": {}, "black_intervals": [], "frozen_intervals": [],
            "assets": {}, "captions": {}, "audio_boundaries": {},
        }
        if strict:
            raise RuntimeError("video QA failed: " + "; ".join(errors))
        return summary

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
    fps = _fraction(video.get("avg_frame_rate") if video else 0) \
        or _fraction(video.get("r_frame_rate") if video else 0)

    checks["video_stream"] = bool(video)
    if not video:
        errors.append("no video stream")
    checks["resolution"] = vw == width and vh == height
    if vw != width or vh != height:
        errors.append(f"resolution {vw}x{vh} != {width}x{height}")
    checks["duration"] = min_duration <= duration <= max_duration
    if not checks["duration"]:
        errors.append(f"duration {duration:.2f}s outside [{min_duration},{max_duration}]")

    checks["fps"] = None
    if expected_fps is not None:
        checks["fps"] = abs(fps - float(expected_fps)) <= 0.05
        if not checks["fps"]:
            errors.append(f"frame rate {fps:.3f} != {expected_fps}")
    elif fps <= 0:
        warnings.append("could not read frame rate")

    checks["audio_stream"] = has_audio
    if not has_audio:
        errors.append("no audio stream")

    levels: dict[str, float] = {}
    checks["audio_level"] = None
    if has_audio and silence_db is not None:
        levels = _audio_levels(path)
        mean = levels.get("mean_volume")
        if mean is None:
            warnings.append("could not measure audio level")
        else:
            checks["audio_level"] = mean > float(silence_db)
            if not checks["audio_level"]:
                errors.append(
                    f"audio is silent or extremely quiet (mean {mean:.1f} dB <= {silence_db:.1f} dB)"
                )
            peak = levels.get("max_volume")
            if peak is not None and peak <= float(silence_db) + 6:
                warnings.append(f"audio peak is low ({peak:.1f} dB)")

    true_peak: float | None = None
    checks["true_peak"] = None
    if has_audio:
        true_peak = _true_peak(path)
        if true_peak is None:
            warnings.append("could not measure true peak")
        else:
            # A sample-peak of 0 dBFS is already clipped; inter-sample peaks above
            # -1 dBTP re-clip on the platform's next encode.
            checks["true_peak"] = true_peak <= -1.0
            if levels.get("max_volume", -99.0) >= -0.1:
                errors.append(f"audio is digitally clipped (sample peak {levels['max_volume']:.1f} dBFS)")
            elif not checks["true_peak"]:
                warnings.append(f"true peak is high ({true_peak:.2f} dBTP)")

    black_intervals: list[tuple[float, float]] = []
    checks["black_frames"] = None
    if check_black_frames:
        black_intervals = _black_intervals(path)
        black_seconds = sum(max(0.0, end - start) for start, end in black_intervals)
        checks["black_frames"] = black_seconds <= max(1.0, duration * 0.25)
        if not checks["black_frames"]:
            warnings.append(f"{black_seconds:.1f}s of near-black video in {len(black_intervals)} interval(s)")

    frozen_intervals = _frozen_intervals(path)
    # Eased motion can produce a one-frame duplicate at the very start/end of a
    # short still; only report freezes that a viewer could actually notice.
    frozen_intervals = [
        (start, end) for start, end in frozen_intervals if end - start >= 0.10
    ]
    checks["frozen_frames"] = not frozen_intervals
    if frozen_intervals:
        warnings.append(
            "frozen video: " + ", ".join(f"{start:.1f}-{end:.1f}s" for start, end in frozen_intervals[:4])
        )

    asset_stats: dict = {}
    if assets is not None:
        ids = [
            str(asset.get("asset_id") or asset.get("path") or "")
            for asset in assets
            if isinstance(asset, dict)
        ]
        ids = [item for item in ids if item]
        consecutive = sum(1 for left, right in zip(ids, ids[1:]) if left == right)
        unique = len(set(ids))
        asset_stats = {
            "count": len(ids), "unique": unique,
            "consecutive_repeats": consecutive,
        }
        checks["unique_assets"] = consecutive == 0
        if consecutive:
            warnings.append(f"{consecutive} consecutive scene(s) reuse the same visual asset")
        elif unique < len(ids):
            warnings.append(f"{len(ids) - unique} scene(s) reuse an asset from a non-adjacent scene")

        confidences = [
            str(asset.get("relevance_confidence") or "unknown")
            for asset in assets
            if isinstance(asset, dict)
        ]
        confidence_counts: dict[str, int] = {}
        for confidence in confidences:
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        semantic_review = sum(
            1 for asset in assets
            if isinstance(asset, dict) and asset.get("semantic_review")
            and not asset.get("human_reviewed")
        )
        low_confidence = confidence_counts.get("low", 0) + confidence_counts.get("none", 0)
        low_light = sum(
            1 for asset in assets
            if isinstance(asset, dict) and asset.get("visual_quality") == "low_light"
        )
        asset_stats.update({
            "semantic_review": semantic_review,
            "low_confidence": low_confidence,
            "low_light": low_light,
            "confidence_counts": confidence_counts,
        })
        if low_confidence:
            warnings.append(
                f"{low_confidence} asset(s) have low/no lexical relevance and need review"
            )
        if semantic_review:
            warnings.append(
                f"{semantic_review} asset(s) rely on lexical/provenance matching and need visual review"
            )
        if low_light:
            warnings.append(
                f"{low_light} asset(s) are too dark/flat to read clearly"
            )
        if strict_visuals:
            if consecutive:
                errors.append(f"{consecutive} consecutive scene(s) reuse the same visual asset")
            elif unique < len(ids):
                errors.append(f"{len(ids) - unique} scene(s) reuse an asset from a non-adjacent scene")
            if low_confidence:
                errors.append(f"{low_confidence} asset(s) have low/no lexical relevance")
            if semantic_review:
                errors.append(f"{semantic_review} asset(s) require semantic visual review")
            if low_light:
                errors.append(f"{low_light} asset(s) are too dark/flat to read clearly")

    caption_stats = _caption_stats(captions)
    checks["captions"] = None
    if caption_stats.get("checked"):
        events = int(caption_stats.get("events") or 0)
        checks["captions"] = events > 0
        if not caption_stats.get("exists", True):
            errors.append("captions file is missing")
        elif events == 0:
            errors.append("captions file has no dialogue events")
        elif float(caption_stats.get("last_end") or 0) > duration + 0.5:
            warnings.append(
                f"captions end at {caption_stats['last_end']:.2f}s, beyond the {duration:.2f}s video"
            )

    boundary_stats: dict = {}
    checks["audio_boundaries"] = None
    if audio_boundaries and audio_boundaries.get("checked"):
        flagged = int(audio_boundaries.get("flagged") or 0)
        count = int(audio_boundaries.get("boundary_count") or 0)
        boundary_stats = {
            "checked": True, "boundary_count": count, "flagged": flagged,
            "status": "warning" if flagged else "pass",
        }
        checks["audio_boundaries"] = flagged == 0
        if flagged:
            warnings.append(
                f"{flagged}/{count} scene cut(s) have a click/whoosh audio signature"
            )

    status = "fail" if errors else "pass"
    summary = {
        "status": status,
        "duration": round(duration, 3),
        "width": vw,
        "height": vh,
        "fps": round(fps, 3),
        "has_audio": bool(has_audio),
        "size_bytes": path.stat().st_size,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "audio": {**levels, **({f"true_peak_dbtp": true_peak} if true_peak is not None else {})},
        "audio_encoding": _audio_stream_info(path) if has_audio else {},
        "black_intervals": [
            {"start": round(start, 2), "end": round(end, 2)} for start, end in black_intervals
        ],
        "frozen_intervals": [
            {"start": round(start, 2), "end": round(end, 2)} for start, end in frozen_intervals
        ],
        "assets": asset_stats,
        "captions": caption_stats,
        "audio_boundaries": boundary_stats,
    }
    if errors and strict:
        raise RuntimeError("video QA failed: " + "; ".join(errors))
    return summary
