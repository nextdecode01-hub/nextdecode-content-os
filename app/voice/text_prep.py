"""Speech-friendly text preparation for the Edge TTS narration path.

Edge TTS does not accept arbitrary SSML from this project: the CLI only exposes
``--rate``, ``--pitch`` and ``--volume`` and wraps the escaped text in a single
``<prosody>`` element.  Pauses therefore have to come from punctuation and
paragraph boundaries, not from ``<break>`` or ``<mstts:express-as>`` tags.

These helpers only change how the same words are written for the synthesizer;
they do not add, remove or reinterpret claims.
"""
from __future__ import annotations

import hashlib
import re

# Letter-by-letter forms for acronyms that a neural voice may otherwise read as
# a word ("API" as "appy", "SQL" as "sequel").  AI is left alone because Edge
# already says "A I" correctly.
_ACRONYMS = (
    ("APIs", "A P Is"),
    ("API", "A P I"),
    ("SQL", "S Q L"),
    ("GPUs", "G P Us"),
    ("GPU", "G P U"),
    ("CPUs", "C P Us"),
    ("CPU", "C P U"),
    ("LLMs", "L L Ms"),
    ("LLM", "L L M"),
)

_ABBREVIATIONS = (
    (r"\be\.g\.", "for example"),
    (r"\bi\.e\.", "that is"),
    (r"\bvs\.", "versus"),
    (r"\betc\.", "et cetera"),
    (r"\bapprox\.", "approximately"),
)


def normalize_for_speech(text: str) -> str:
    """Normalize symbols, abbreviations and pauses without changing meaning."""
    value = str(text or "")
    value = re.sub(r"[*_`#>]+", "", value)
    value = value.replace("\u2014", ", ").replace("\u2013", ", ")
    value = value.replace("\u2192", " to ").replace("&", " and ")
    for pattern, replacement in _ABBREVIATIONS:
        value = re.sub(pattern, replacement, value, flags=re.I)

    # "N+1" is spoken as "N plus one"; a bare "+" is not a pause.
    value = re.sub(r"\bN\s*\+\s*1\b", "N plus one", value, flags=re.I)
    value = re.sub(r"\s*%\s*", " percent ", value)
    value = re.sub(r"\s*\+\s*", " plus ", value)

    for acronym, spoken in _ACRONYMS:
        value = re.sub(rf"\b{re.escape(acronym)}\b", spoken, value)

    # Currency and common unit symbols.
    value = re.sub(r"\$\s*(\d[\d,]*(?:\.\d+)?)", r"\1 dollars", value)
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\s*\n\s*", "\n", value)
    return value.strip()


def split_long_sentences(text: str, max_words: int = 28) -> str:
    """Split only genuinely long sentences at existing clause boundaries.

    No words are added or reordered.  Short sentences are left untouched.
    """
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", str(text or "")) if part.strip()]
    output: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) <= max_words:
            output.append(sentence)
            continue

        # Prefer a comma before a coordinating conjunction, then a semicolon.
        pieces = re.split(r"(?<=,)\s+(?=(?:but|yet|so|and|because|while)\b)", sentence)
        if len(pieces) == 1:
            pieces = [part.strip() for part in sentence.split(";") if part.strip()]
        if len(pieces) == 1:
            output.append(sentence)
            continue

        for index, piece in enumerate(pieces):
            piece = piece.strip()
            if not piece:
                continue
            if index < len(pieces) - 1 and not piece.endswith((".", "!", "?")):
                piece += "."
            if piece:
                output.append(piece[0].upper() + piece[1:] if piece else piece)
    return " ".join(output)


def prepare_narration(text: str, *, max_words: int = 28) -> str:
    """Normalize each paragraph, split long sentences, and keep paragraph breaks.

    Paragraph breaks are the only reliable pause control available through the
    Edge TTS CLI; they are preserved rather than collapsed.
    """
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", str(text or "")) if part.strip()]
    if not paragraphs:
        return ""
    prepared: list[str] = []
    for paragraph in paragraphs:
        normalized = normalize_for_speech(paragraph)
        prepared.append(split_long_sentences(normalized, max_words=max_words))
    return "\n\n".join(prepared)


def script_sha256(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()
