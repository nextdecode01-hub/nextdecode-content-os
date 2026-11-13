"""Offline audio diagnostics for scene boundaries.

The renderer cuts video on exact shot boundaries, but the audio mix is one
continuous stream.  A click, pop, whoosh or other unintended transition sound
therefore shows up as a short-lived change in the waveform right after a cut.
This module measures short windows around every boundary and compares them with
the middle of the same shot, so a regression is visible in metadata instead of
being hidden behind a passing loudness check.

Pure stdlib + FFmpeg.  No numpy, no network, no new dependency.
"""
from __future__ import annotations

import array
import json
import math
import statistics
import subprocess
from pathlib import Path

SAMPLE_RATE = 44100
FULL_SCALE = 32768.0
DEFAULT_PRE = (0.40, 0.10)
DEFAULT_POST = (0.10, 0.45)
DEFAULT_ONSET = 0.05

# A sustained high-frequency lift after the cut is the signature of a noise
# whoosh or an un-faded audio splice.  Speech sibilance is brief and also
# present before the cut, so the excess is measured against the shot's own
# control window rather than an absolute threshold alone.
HF_EXCESS_DB = 8.0
HF_AUDIBLE_DB = -27.0
HF_SUSTAIN_SECONDS = 0.25
ONSET_RATIO = 6.0
ONSET_PEAK_DB = -18.0


def _db(value: float) -> float:
    return 20.0 * math.log10(max(value, 1e-9))


def decode_mono(path: Path, *, sr: int = SAMPLE_RATE, timeout: int = 300) -> array.array:
    """Decode any FFmpeg-readable file to mono s16 samples."""
    command = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-f", "s16le", "-ac", "1", "-ar", str(int(sr)), "-",
    ]
    completed = subprocess.run(command, capture_output=True, timeout=timeout)
    if completed.returncode != 0 or not completed.stdout:
        return array.array("h")
    raw = completed.stdout
    if len(raw) % 2:
        raw = raw[:-1]
    samples = array.array("h")
    samples.frombytes(raw)
    return samples


def _window(samples: array.array, sr: int, start: float, end: float) -> dict:
    """RMS, first-difference (high-band proxy) and peak for one time window."""
    first = max(0, int(round(start * sr)))
    last = min(len(samples), int(round(end * sr)))
    count = last - first
    if count <= 1:
        return {"rms_db": -120.0, "hf_db": -120.0, "peak_db": -120.0,
                "max_delta": 0.0, "delta_p95": 0.0}
    energy = 0.0
    diff_energy = 0.0
    peak = 0
    previous = samples[first]
    max_delta = 0
    deltas: list[int] = []
    for index in range(first, last):
        value = samples[index]
        energy += value * value
        abs_value = abs(value)
        if abs_value > peak:
            peak = abs_value
        if index > first:
            delta = value - previous
            diff_energy += delta * delta
            abs_delta = abs(delta)
            deltas.append(abs_delta)
            if abs_delta > max_delta:
                max_delta = abs_delta
        previous = value
    deltas.sort()
    p95 = deltas[int(0.95 * (len(deltas) - 1))] if deltas else 0
    return {
        "rms_db": round(_db(math.sqrt(energy / count) / FULL_SCALE), 1),
        "hf_db": round(_db(math.sqrt(diff_energy / (count - 1)) / FULL_SCALE), 1),
        "peak_db": round(_db(peak / FULL_SCALE), 1),
        "max_delta": max_delta,
        "delta_p95": p95,
    }


def _median(values: list[float], fallback: float) -> float:
    values = [value for value in values if value > -119.0]
    return float(statistics.median(values)) if values else fallback


def analyze_boundaries(path: Path, boundaries: list[float], *,
                       sr: int = SAMPLE_RATE) -> dict:
    """Measure every cut and report likely click/pop/whoosh artefacts.

    ``boundaries`` are the start times of shots 2..N (the first shot needs no
    cut).  The result is JSON-safe and intended for render metadata.
    """
    path = Path(path)
    samples = decode_mono(path, sr=sr)
    if not samples:
        return {"checked": False, "reason": "could not decode audio",
                "boundary_count": 0, "flagged": 0, "boundaries": []}
    duration = len(samples) / float(sr)
    cuts = sorted({round(float(value), 3) for value in boundaries
                   if 0.15 < float(value) < duration - 0.15})
    if not cuts:
        return {"checked": True, "duration": round(duration, 3),
                "boundary_count": 0, "flagged": 0, "boundaries": []}

    metrics: list[dict] = []
    for position, cut in enumerate(cuts):
        next_cut = cuts[position + 1] if position + 1 < len(cuts) else duration
        pre = _window(samples, sr, cut - DEFAULT_PRE[0], cut - DEFAULT_PRE[1])
        post = _window(samples, sr, cut + DEFAULT_POST[0], cut + DEFAULT_POST[1])
        onset = _window(samples, sr, cut, cut + DEFAULT_ONSET)
        control_end = min(cut + 1.75, next_cut - 0.08)
        control_start = max(cut + 0.90, control_end - 0.50)
        if control_end - control_start < 0.20:
            control_start = cut + 0.55
            control_end = min(next_cut - 0.05, cut + 0.85)
        control = _window(samples, sr, control_start, control_end)
        subwindows: list[dict] = []
        cursor = cut + 0.05
        limit = min(cut + 0.65, next_cut - 0.03)
        while cursor + 0.05 <= limit:
            subwindows.append({
                "time": round(cursor, 3),
                **_window(samples, sr, cursor, cursor + 0.05),
            })
            cursor += 0.05
        metrics.append({
            "time": cut,
            "pre": pre,
            "post": post,
            "onset": onset,
            "control": control,
            "subwindows": subwindows,
        })

    baseline = _median([item["control"]["hf_db"] for item in metrics],
                       fallback=_median([item["pre"]["hf_db"] for item in metrics], -120.0))

    flagged = 0
    for item in metrics:
        hf_excess = item["post"]["hf_db"] - baseline
        rms_delta = item["post"]["rms_db"] - item["pre"]["rms_db"]
        onset_ratio = item["onset"]["max_delta"] / max(1.0, item["pre"]["max_delta"])
        spike_ratio = item["onset"]["max_delta"] / max(1.0, item["onset"]["delta_p95"])
        elevated_run = 0
        longest_run = 0
        for window in item["subwindows"]:
            if (window["hf_db"] - baseline >= HF_EXCESS_DB
                    and window["hf_db"] >= HF_AUDIBLE_DB):
                elevated_run += 1
                longest_run = max(longest_run, elevated_run)
            else:
                elevated_run = 0
        sustained = round(longest_run * 0.05, 2)
        # A whoosh/noise burst lasts several hundred milliseconds.  A spoken
        # "s" can lift the same band for ~100 ms, so require sustained energy
        # before calling the cut defective.
        burst = bool(sustained >= HF_SUSTAIN_SECONDS)
        click = bool(
            onset_ratio >= ONSET_RATIO
            and item["onset"]["peak_db"] >= ONSET_PEAK_DB
            and item["onset"]["max_delta"] >= 600
            # A natural speech onset has many similar-size slopes.  An edit
            # click is an isolated sample jump far above the local 95th
            # percentile, so this separates the two.
            and spike_ratio >= 8.0
        )
        item.update({
            "hf_excess_db": round(hf_excess, 1),
            "rms_delta_db": round(rms_delta, 1),
            "onset_ratio": round(onset_ratio, 1),
            "onset_spike_ratio": round(spike_ratio, 1),
            "sustained_hf_seconds": sustained,
            "burst_like": burst,
            "click_like": click,
            "flagged": burst or click,
        })
        if item["flagged"]:
            flagged += 1

    return {
        "checked": True,
        "duration": round(duration, 3),
        "sample_rate": sr,
        "boundary_count": len(metrics),
        "flagged": flagged,
        "status": "warning" if flagged else "pass",
        "baseline_hf_db": round(baseline, 1),
        "thresholds": {
            "hf_excess_db": HF_EXCESS_DB,
            "hf_audible_db": HF_AUDIBLE_DB,
            "hf_sustain_seconds": HF_SUSTAIN_SECONDS,
            "onset_ratio": ONSET_RATIO,
            "onset_peak_db": ONSET_PEAK_DB,
        },
        "boundaries": metrics,
    }


def summarize(result: dict) -> str:
    if not result.get("checked"):
        return "audio boundaries: not checked"
    count = int(result.get("boundary_count") or 0)
    flagged = int(result.get("flagged") or 0)
    if not count:
        return "audio boundaries: no cuts to inspect"
    if not flagged:
        return f"audio boundaries: {count} cut(s), no click/whoosh signature"
    times = ", ".join(f"{item['time']:.2f}s" for item in result["boundaries"]
                      if item.get("flagged"))[:160]
    return f"audio boundaries: {flagged}/{count} cut(s) flagged ({times})"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect audio around video cuts")
    parser.add_argument("video", help="rendered video or audio file")
    parser.add_argument("--boundaries", required=True,
                        help="comma-separated cut times in seconds")
    parser.add_argument("--out", default="", help="optional JSON report path")
    args = parser.parse_args(argv)
    cuts = [float(part) for part in args.boundaries.split(",") if part.strip()]
    result = analyze_boundaries(Path(args.video), cuts)
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
