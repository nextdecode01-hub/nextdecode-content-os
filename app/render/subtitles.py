"""Kinetic ASS subtitle generation.

Moved verbatim from motion_render.py in Phase 7B; logic unchanged.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

from app.visuals.motion_director import SAFE_ZONE_BOTTOM, SAFE_ZONE_TOP

def _ass_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hrs}:{mins:02d}:{secs:05.2f}"


NO_SPACE_BEFORE = set(".,!?;:%)}]-…’”")
NO_SPACE_AFTER = set("([{‘“$£€#@/-")


def _needs_space(previous: str, current: str, before_previous: str = "") -> bool:
    """Whether two karaoke tokens should be separated by a visible space."""
    if not previous or not current:
        return False
    # Decimal separators ("0", ".", "1") belong to one figure, unlike a sentence
    # period which is followed by a space.
    if previous in {".", ","} and before_previous[:1].isdigit() and current[:1].isdigit():
        return False
    if current[0] in NO_SPACE_BEFORE:
        return False
    if previous[-1] in NO_SPACE_AFTER:
        return False
    if current.lower().startswith(("'s", "’s", "n't", "’t", "'re", "'ll", "'ve", "'d", "'m")):
        return False
    return True


def _caption_key(text: str) -> str:
    return re.sub(r"[^a-z0-9%]+", "", str(text or "").lower())


def align_script_to_asr(script_text: str, asr_words: list[dict]) -> list[dict]:
    """Use script spelling with ASR word timings.

    Whisper can mishear names (“GrigApps” for “GrayGaps”) even when the timing
    is good.  Align the script tokens against the ASR token stream and borrow
    the ASR timestamps, so captions keep the authored spelling.
    """
    script_tokens = re.findall(r"\S+", str(script_text or ""))
    if not script_tokens or not asr_words:
        return []

    asr_keys = [_caption_key(item.get("word", "")) for item in asr_words]
    script_keys = [_caption_key(token) for token in script_tokens]
    matcher = SequenceMatcher(None, asr_keys, script_keys, autojunk=False)
    mapped: list[tuple[float, float] | None] = [None] * len(script_tokens)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(j2 - j1):
                word = asr_words[i1 + offset]
                mapped[j1 + offset] = (float(word.get("start", 0.0)), float(word.get("end", 0.0)))
        elif tag == "replace" and i2 > i1 and j2 > j1:
            start = float(asr_words[i1].get("start", 0.0))
            end = float(asr_words[i2 - 1].get("end", start))
            count = j2 - j1
            if (i2 - i1) == count:
                for offset in range(count):
                    word = asr_words[i1 + offset]
                    mapped[j1 + offset] = (
                        float(word.get("start", start)),
                        float(word.get("end", end)),
                    )
            else:
                step = max(0.05, (end - start) / count)
                for offset in range(count):
                    mapped[j1 + offset] = (start + offset * step, start + (offset + 1) * step)

    # Fill script tokens that the ASR stream omitted by interpolating between
    # the nearest mapped neighbours.
    index = 0
    while index < len(mapped):
        if mapped[index] is not None:
            index += 1
            continue
        block_start = index
        while index < len(mapped) and mapped[index] is None:
            index += 1
        block_end = index
        count = block_end - block_start
        previous_end = mapped[block_start - 1][1] if block_start > 0 else 0.0
        next_start = (
            mapped[block_end][0]
            if block_end < len(mapped)
            else previous_end + 0.3 * count
        )
        if next_start <= previous_end:
            next_start = previous_end + 0.3 * count
        step = max(0.05, (next_start - previous_end) / count)
        for offset in range(count):
            start = previous_end + offset * step
            mapped[block_start + offset] = (start, start + step)

    aligned: list[dict] = []
    previous_end = 0.0
    for token, timing in zip(script_tokens, mapped):
        if timing is None:
            continue
        start, end = timing
        if aligned and start < previous_end:
            start = previous_end
        if end <= start:
            end = start + 0.08
        aligned.append({"word": token, "start": round(start, 3), "end": round(end, 3)})
        previous_end = end
    return aligned


def make_kinetic_ass(transcript_words: list[dict], out_path: Path, *,
                     width: int = 1080, height: int = 1920) -> Path:
    r"""ASS with per-word {\k} highlighting, 2-3 words per line, safe-zone margins."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    words = sorted(transcript_words, key=lambda w: float(w.get("start", 0.0)))

    # Build visible tokens first so line breaks never split a decimal figure
    # ("0", ".", "1") or attach punctuation to the wrong line.
    tokens: list[tuple[dict, str, bool]] = []
    previous_text = ""
    before_previous = ""
    for word in words:
        text = str(word.get("word", "") or "").strip()
        if not text:
            continue
        space = _needs_space(previous_text, text, before_previous)
        tokens.append((word, text, space))
        before_previous, previous_text = previous_text, text

    lines: list[list[tuple[dict, str, bool]]] = []
    current: list[tuple[dict, str, bool]] = []
    visible_width = 0
    for token in tokens:
        _word, text, space = token
        if current and space and (len(current) >= 3 or visible_width + 1 + len(text) > 24):
            lines.append(current)
            current = []
            visible_width = 0
        used_space = bool(current) and space
        current.append((token[0], text, used_space))
        visible_width += len(text) + (1 if used_space else 0)
    if current:
        lines.append(current)

    margin_l = max(20, int(width * 0.05))
    # Keep captions in the lower phone-safe band.  The previous 18% bottom
    # margin placed subtitles over the central content of full-screen diagrams.
    margin_v = max(72, int(height * 0.055))
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
        start = _ass_timestamp(float(line[0][0].get("start", 0.0)))
        end = _ass_timestamp(float(line[-1][0].get("end", 0.0)))
        parts: list[str] = []
        last_end = float(line[0][0].get("start", 0.0))
        for word, text, space in line:
            w_start = float(word.get("start", last_end))
            w_end = float(word.get("end", w_start + 0.4))
            cs = max(1, int(round((w_end - w_start) * 100)))
            parts.append(f"{' ' if space else ''}{{\\k{cs}}}{text}")
            last_end = w_end
        events.append(f"Dialogue: 0,{start},{end},Kinetic,,{margin_l},{margin_l},{margin_v},,"
                       + "".join(parts))

    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return out_path
