"""Offline visual asset metadata, duration, duplicate and contact-sheet QA.

Inspects only existing files; never searches, downloads, renders a video or publishes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    return json.loads(result.stdout or "{}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fps(value: str) -> float:
    try:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator) if float(denominator) else 0.0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def _dhash(path: Path, *, seek_seconds: float = 0.0) -> int | None:
    """64-bit difference hash of a representative frame, decoded by FFmpeg."""
    command = ["ffmpeg", "-v", "error"]
    if seek_seconds > 0:
        command += ["-ss", f"{seek_seconds:.3f}"]
    command += ["-i", str(path), "-vf",
               "scale=9:8:flags=area,format=gray", "-frames:v", "1",
               "-f", "rawvideo", "pipe:1"]
    try:
        pixels = subprocess.run(command, capture_output=True, timeout=30, check=True).stdout
        if len(pixels) != 72:
            return None
        value = 0
        bit = 0
        for row in range(8):
            for col in range(8):
                if pixels[row * 9 + col] > pixels[row * 9 + col + 1]:
                    value |= 1 << bit
                bit += 1
        return value
    except Exception:
        return None


def inspect_asset(record: dict, index: int = 0) -> dict:
    raw_path = str(record.get("asset_path") or record.get("path") or "")
    path = Path(raw_path)
    provider_meta = record.get("provenance") or {}
    result = {
        "index": int(record.get("index", index) or index),
        "scene_id": str(record.get("scene_id") or record.get("shot_id") or f"s{index:02d}"),
        "provider": str(record.get("provider") or ""),
        "asset_id": str(record.get("asset_id") or ""),
        "title": str(record.get("title") or provider_meta.get("title") or ""),
        "description": str(record.get("description") or ""),
        "tags": str(record.get("tags") or provider_meta.get("tags") or ""),
        "query": str(record.get("query") or ""),
        "visual_intent": str(record.get("visual_intent") or record.get("visual_purpose") or ""),
        "narration": str(record.get("narration") or ""),
        "license": str(record.get("license") or ""),
        "credit_line": str(record.get("credit_line") or ""),
        "source_url": str(record.get("source_url") or ""),
        "asset_path": raw_path,
        "exists": path.is_file(),
    }
    if not path.is_file():
        result["probe_error"] = "asset file missing"
        return result

    stat = path.stat()
    is_video = path.suffix.lower() in VIDEO_SUFFIXES
    probe_error = ""
    try:
        probe = _probe(path)
    except Exception as exc:
        probe, probe_error = {}, f"ffprobe failed: {type(exc).__name__}"
    streams = probe.get("streams") or []
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    try:
        duration = float((probe.get("format") or {}).get("duration") or video.get("duration") or 0) if is_video else None
    except (ValueError, TypeError):
        duration = None
    expected = record.get("duration") or record.get("expected_duration")
    try:
        expected = float(expected) if expected is not None else None
    except (ValueError, TypeError):
        expected = None
    trim_start = max(0.0, float(record.get("trim_start_seconds") or 0.0))
    actual_usable = max(0.0, (duration or 0.0) - trim_start) if is_video else None
    usable = min(actual_usable, expected) if is_video and expected and actual_usable is not None else actual_usable
    coverage = min(1.0, usable / expected) if usable is not None and expected and expected > 0 else None
    dhash = _dhash(path, seek_seconds=(duration or 0.0) / 2.0 if is_video else 0.0)
    result.update({
        "sha256": _sha256(path),
        "file_size_bytes": stat.st_size,
        "media_type": "video" if is_video else "image" if path.suffix.lower() in IMAGE_SUFFIXES else "unknown",
        "duration_seconds": round(duration, 3) if duration is not None else None,
        "expected_duration_seconds": round(expected, 3) if expected is not None else None,
        "usable_duration_seconds": round(usable, 3) if usable is not None else None,
        "duration_coverage": round(coverage, 3) if coverage is not None else None,
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "fps": round(_fps(str(video.get("avg_frame_rate") or "0/1")), 3),
        "video_codec": str(video.get("codec_name") or ""),
        "has_audio_stream": bool(audio),
        "dhash64": f"{dhash:016x}" if dhash is not None else "",
        "probe_error": probe_error,
    })
    return result


def _thumbnail(asset: dict, output: Path) -> bool:
    path = Path(asset["asset_path"])
    video = asset.get("media_type") == "video"
    seek = max(0.0, float(asset.get("duration_seconds") or 0.0) / 2.0) if video else 0.0
    command = ["ffmpeg", "-y", "-v", "error"]
    if video:
        command += ["-ss", f"{seek:.3f}"]
    command += ["-i", str(path), "-frames:v", "1", "-vf",
                "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2",
                str(output)]
    try:
        subprocess.run(command, capture_output=True, timeout=30, check=True)
        return output.is_file() and output.stat().st_size > 1000
    except Exception:
        return False


def build_asset_qa(records: list[dict], output_dir: Path, *, dhash_threshold: int = 6) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir = output_dir / "asset_qa_thumbs"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    assets = [inspect_asset(record, index) for index, record in enumerate(records)]
    for index, asset in enumerate(assets):
        if asset.get("exists"):
            thumb = thumbs_dir / f"asset_{index:03d}.jpg"
            asset["thumbnail"] = str(thumb) if _thumbnail(asset, thumb) else ""
        else:
            asset["thumbnail"] = ""

    exact_pairs, composition_pairs = [], []
    for previous, current in zip(assets, assets[1:]):
        if previous.get("sha256") and previous["sha256"] == current.get("sha256"):
            exact_pairs.append([previous["scene_id"], current["scene_id"]])
        left = int(previous["dhash64"], 16) if previous.get("dhash64") else None
        right = int(current["dhash64"], 16) if current.get("dhash64") else None
        if left is not None and right is not None:
            distance = (left ^ right).bit_count()
            if distance <= dhash_threshold:
                composition_pairs.append({"scenes": [previous["scene_id"], current["scene_id"]],
                                          "hamming_distance": distance})

    thumbs = [Path(item["thumbnail"]) for item in assets if item.get("thumbnail")]
    contact = output_dir / "asset_qa_contact_sheet.jpg"
    contact_ok = False
    if thumbs:
        command = ["ffmpeg", "-y", "-v", "error"]
        for thumb in thumbs:
            command += ["-i", str(thumb)]
        layout = "|".join(f"{(i % 4) * 320}_{(i // 4) * 180}" for i in range(len(thumbs)))
        inputs = "".join(f"[{i}:v]" for i in range(len(thumbs)))
        command += ["-filter_complex", f"{inputs}xstack=inputs={len(thumbs)}:layout={layout}:fill=0x101820[out]",
                    "-map", "[out]", "-frames:v", "1", str(contact)]
        try:
            subprocess.run(command, capture_output=True, timeout=90, check=True)
            contact_ok = contact.is_file() and contact.stat().st_size > 1000
        except Exception:
            contact_ok = False

    providers, media_types = {}, {}
    for asset in assets:
        provider = asset.get("provider") or "unknown"
        media_type = asset.get("media_type") or "unknown"
        providers[provider] = providers.get(provider, 0) + 1
        media_types[media_type] = media_types.get(media_type, 0) + 1
    report = {
        "schema_version": 1,
        "asset_count": len(assets),
        "providers": providers,
        "media_types": media_types,
        "missing_assets": sum(not item.get("exists") for item in assets),
        "duration_shortfalls": [item["scene_id"] for item in assets
                                if item.get("duration_coverage") is not None and item["duration_coverage"] < 0.95],
        "adjacent_exact_duplicates": exact_pairs,
        "adjacent_composition_similarities": composition_pairs,
        "contact_sheet": str(contact) if contact_ok else "",
        "assets": assets,
    }
    report_path = output_dir / "asset_qa.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def load_storyboard(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return list(payload.get("scenes") or payload.get("records") or [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect existing storyboard assets; no network or render.")
    parser.add_argument("--storyboard", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    report = build_asset_qa(load_storyboard(args.storyboard), args.output_dir or args.storyboard.parent)
    keys = ("asset_count", "providers", "media_types", "missing_assets", "duration_shortfalls",
            "adjacent_exact_duplicates", "adjacent_composition_similarities", "contact_sheet", "report_path")
    print(json.dumps({key: report[key] for key in keys}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
