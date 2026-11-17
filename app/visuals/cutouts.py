"""Balanced source cutouts for evidence-heavy scenes.

A cutout is a rendered card quoting the source excerpt with publisher, date and
URL.  It is used selectively - important statistics, announcements and disputed
claims - while the rest of the story keeps cinematic b-roll.

Reuse rights are not assumed.  Public-domain government material is marked
``permitted``; everything else stays ``unknown`` and is blocked from
publish-ready status until a human records the permission basis.  Attribution
alone is not permission.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import textwrap
from pathlib import Path

WIDTH = 1080
HEIGHT = 1920
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)

PUBLIC_DOMAIN_SUFFIXES = (".gov", ".gov.uk", ".mil", ".europa.eu")
OPEN_LICENSE_MARKERS = ("cc by", "cc-by", "creative commons", "public domain", "open government licence")

CUTOUT_CLAIM_TYPES = frozenset({"statistic", "funding", "forecast", "announcement", "quote",
                                "research", "date"})
BLOCKING_RIGHTS = frozenset({"unknown", "incompatible"})


def _font() -> str:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return ""


def reuse_rights(source: dict) -> dict:
    """Classify the reuse basis without inventing permission."""
    url = str(source.get("url") or "")
    host = str(source.get("publisher") or "")
    host = host.lower().split(":")[0]
    text = str(source.get("text") or "").lower()[:4000]
    attribution = (
        f"{host or 'unknown publisher'}"
        + (f", {source['published']}" if source.get("published") else ", date not provided")
        + (f" - {url}" if url else "")
    )
    if host.endswith(PUBLIC_DOMAIN_SUFFIXES):
        return {
            "status": "permitted",
            "basis": "government publication; public-domain reuse claimed",
            "attribution": attribution,
        }
    if any(marker in text for marker in OPEN_LICENSE_MARKERS):
        return {
            "status": "permitted",
            "basis": "source text carries an open-licence marker; verify the exact terms",
            "attribution": attribution,
        }
    return {
        "status": "unknown",
        "basis": "no licence or permission statement found; do not publish until confirmed",
        "attribution": attribution,
    }


def attribution_lines(claim: dict) -> list[str]:
    publisher = str(claim.get("publisher") or "unknown publisher")
    published = str(claim.get("published") or "")
    url = str(claim.get("source_url") or "")
    date_line = published if published else "date not provided"
    short_url = url.replace("https://", "").replace("http://", "")
    if len(short_url) > 58:
        short_url = short_url[:55] + "..."
    return [publisher, date_line, short_url]


def _write_textfile(path: Path, lines: list[str]) -> Path:
    """Write card text without a trailing newline (drawtext shows it as tofu)."""
    path.write_text("\n".join(line.rstrip() for line in lines if line is not None), encoding="utf-8")
    return path


def _drawtext_pass(source: Path, target: Path, lines: list[str], *, y: int, size: int,
                   color: str) -> tuple[bool, str]:
    """Draw a block of lines onto an image.  Returns ``(ok, error)``.

    Each line is its own drawtext: this ffmpeg build renders a newline inside a
    text file as a visible replacement glyph, so wrapped lines must not be joined
    with ``\\n``.  One block per pass also means a bad option loses only that
    block instead of blanking the whole card, and the failure is reported.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False, "ffmpeg not found"
    font = _font()
    font_arg = f"fontfile='{font}':" if font else ""
    filters = []
    line_height = int(size * 1.38)
    for index, line in enumerate(lines):
        text_file = target.with_name(f"{target.stem}.line{index}.txt")
        text_file.write_text(line, encoding="utf-8")
        filters.append(
            f"drawtext={font_arg}textfile='{text_file}':expansion=none:"
            f"fontcolor={color}:fontsize={size}:x=80:y={y + index * line_height}"
        )
    if not filters:
        return False, "no lines to draw"
    command = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(source),
        "-vf", ",".join(filters),
        "-frames:v", "1", str(target),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    finally:
        for index in range(len(lines)):
            (target.with_name(f"{target.stem}.line{index}.txt")).unlink(missing_ok=True)
    if completed.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
        return False, (completed.stderr or "drawtext produced no image").strip()[-300:]
    return True, ""


def build_source_card(claim: dict, work_dir: Path, *, excerpt_words: int = 42,
                      width: int = WIDTH, height: int = HEIGHT) -> dict:
    """Render one source card to PNG.  Returns metadata, including rights state."""
    ffmpeg = shutil.which("ffmpeg")
    work = Path(work_dir) / "cutouts"
    work.mkdir(parents=True, exist_ok=True)
    claim_id = str(claim.get("claim_id") or "claim")
    out = work / f"{claim_id}.png"
    quote = str(claim.get("quote") or claim.get("narration") or "").strip()
    words = quote.split()
    excerpt = " ".join(words[:excerpt_words])
    if len(words) > excerpt_words:
        excerpt += " ..."
    publisher, date_line, short_url = attribution_lines(claim)

    # 30/52 characters keep 52 px and 36 px text inside the 1080 px frame.
    excerpt_lines = textwrap.wrap(excerpt, 30) or [""]
    url_lines = textwrap.wrap(short_url, 46) or [""]

    warnings: list[str] = []
    rendered = False
    if ffmpeg:
        base = work / f"{claim_id}.base.png"
        command = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", f"color=c=0x0b1220:s={width}x{height}:d=1",
            "-frames:v", "1", str(base),
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
            if completed.returncode != 0:
                warnings.append("background pass failed")
        except (OSError, subprocess.SubprocessError) as exc:
            warnings.append(f"background pass failed: {type(exc).__name__}")

        passes = [
            ("label", ["SOURCE"], 370, 40, "0x67e8f9"),
            ("attribution", [publisher, date_line], 460, 46, "0xffffff"),
            ("excerpt", excerpt_lines, 700, 52, "0xffffff"),
            ("url", url_lines, 1500, 36, "0x94a3b8"),
        ]
        current = base
        variant = 0
        for name, lines, y, size, color in passes:
            variant += 1
            target = work / f"{claim_id}.pass{variant}.png"
            source = current if current.exists() else base
            ok, error = _drawtext_pass(source, target, lines, y=y, size=size, color=color)
            if ok:
                current = target
            else:
                warnings.append(f"{name} block failed: {error}")
        if current.exists():
            shutil.copyfile(current, out)
        rendered = out.is_file() and out.stat().st_size > 0
        for temp in work.glob(f"{claim_id}.pass*.png"):
            temp.unlink(missing_ok=True)
        base.unlink(missing_ok=True)

    rights = reuse_rights(claim)
    digest = hashlib.sha256(out.read_bytes()).hexdigest() if rendered else ""
    return {
        "claim_id": claim_id,
        "path": str(out) if rendered else "",
        "rendered": rendered,
        "warnings": warnings,
        "width": width,
        "height": height,
        "content_sha256": digest,
        "excerpt": excerpt,
        "attribution": rights["attribution"],
        "attribution_lines": [publisher, date_line, short_url],
        "reuse_rights": rights,
        "publish_ready": rights["status"] == "permitted",
    }


def select_cutout_scenes(ledger: dict, scene_claims: dict[int, list[dict]], *,
                         max_ratio: float = 0.34) -> dict:
    """Pick a balanced set of scenes that deserve a source cutout.

    ``scene_claims`` maps scene index -> claims relevant to that scene.  At most
    ``max_ratio`` of the scenes get a cutout (minimum one when evidence exists),
    and two cutouts never sit back to back, so the video does not become a wall
    of screenshots.
    """
    total = len(scene_claims)
    if not total:
        return {"selected": [], "budget": 0, "reason": "no scenes"}
    budget = max(1, int(total * max_ratio)) if any(scene_claims.values()) else 0
    candidates = []
    seen_claims: set[str] = set()
    skipped_unknown_rights: list[str] = []
    for index in sorted(scene_claims):
        for claim in scene_claims[index]:
            claim_id = str(claim.get("claim_id") or "")
            status = str((claim.get("verification") or {}).get("status") or "unverified")
            kind = str(claim.get("claim_type") or "statement")
            # A source card reproduces a source excerpt. Unknown reuse rights
            # mean this is not an eligible visual asset; the scene can still use
            # independently licensed stock/AI visuals and retain the claim link.
            if not claim_id or claim_id in seen_claims:
                continue
            if reuse_rights(claim).get("status") != "permitted":
                skipped_unknown_rights.append(claim_id)
                continue
            if status not in {"supported", "partially_supported"}:
                continue
            if kind not in CUTOUT_CLAIM_TYPES:
                continue
            seen_claims.add(claim_id)
            priority = 0
            if kind in {"statistic", "funding", "forecast"}:
                priority += 2
            if status == "supported":
                priority += 1
            candidates.append((priority, index, claim))
    if not candidates:
        return {
            "selected": [], "budget": budget,
            "skipped_unknown_rights": sorted(set(skipped_unknown_rights)),
            "reason": "no claim with eligible verification and reuse rights",
        }
    candidates.sort(key=lambda item: (-item[0], item[1]))
    selected: list[dict] = []
    used_scenes: set[int] = set()
    for priority, index, claim in candidates:
        if len(selected) >= budget:
            break
        if index in used_scenes:
            continue
        if any(abs(index - other) <= 1 for other in used_scenes):
            continue
        used_scenes.add(index)
        selected.append({
            "scene_index": index,
            "claim_id": claim.get("claim_id", ""),
            "claim_type": claim.get("claim_type", ""),
            "status": (claim.get("verification") or {}).get("status", ""),
            "priority": priority,
        })
    return {
        "selected": sorted(selected, key=lambda item: item["scene_index"]),
        "budget": budget,
        "skipped_unknown_rights": sorted(set(skipped_unknown_rights)),
        "reason": f"{len(selected)} of {budget} cutout slot(s) used",
    }


def rights_gate(cutouts: list[dict]) -> dict:
    """Summarise whether every cutout may ship."""
    blocked = [item for item in cutouts if item.get("reuse_rights", {}).get("status") in BLOCKING_RIGHTS]
    return {
        "checked": len(cutouts),
        "blocked": len(blocked),
        "publish_ready": not blocked and bool(cutouts),
        "blocked_claim_ids": [item.get("claim_id", "") for item in blocked],
    }
