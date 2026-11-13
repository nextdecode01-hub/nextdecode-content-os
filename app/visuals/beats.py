"""Deterministic narration-beat analysis for shot planning.

A beat is one narration sentence plus the four things a shot planner needs to
know about it: who/what the sentence is about, what happens, in which context,
and which editorial emotion the visual should carry.  Everything here is
rule-based and offline - no model call, no network - so a plan is reproducible
and a unit test can pin it.

This module does not decide visuals.  It only describes the narration; the
planner (`app.visuals.shotplan`) and the existing scene classifier keep that
responsibility.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

# Sentence boundaries, tolerant of abbreviations and decimals.  The lookbehind
# requires terminal punctuation and the lookahead an uppercase/digit/dquote
# start, which keeps "e.g. 84%" and "U.S. policy" in one sentence.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
_ABBREVIATIONS = frozenset({
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "inc", "ltd", "co", "corp",
    "vs", "etc", "e.g", "i.e", "u.s", "u.k", "no", "fig", "approx",
})
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,}[A-Za-z0-9]*\b")
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?%?|\b\d{4}\b")
_MONTHS = frozenset({
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
})

# Longest match first so "white house" wins over "house".
_ORGANISATIONS = (
    "white house", "european union", "united nations", "nist", "airc",
    "openai", "anthropic", "deepseek", "google", "deepmind", "microsoft",
    "nvidia", "apple", "amazon", "meta", "ibm", "intel", "amd", "tesla",
    "congress", "senate", "fda", "epa", "ftc", "sec", "who", "nasa", "arxiv",
)

_ACTION_VERBS = (
    "released", "launched", "announced", "published", "introduced", "adopted",
    "approved", "rejected", "blocked", "banned", "filed", "sued", "acquired",
    "raised", "invested", "cut", "reduced", "increased", "grew", "fell",
    "improved", "achieved", "reports", "report", "found", "shows", "show",
    "warns", "warned", "requires", "require", "recommends", "recommended",
    "manages", "manage", "governs", "maps", "measures", "defines", "describes",
    "uses", "use", "runs", "run", "builds", "built", "trains", "trained",
    "evaluates", "measures", "misses", "catches", "fails", "failing",
    "replaces", "replaced", "supports", "enables", "prevents", "protects",
)

_CONTEXT_PREPOSITIONS = (
    "in", "for", "across", "during", "with", "at", "on", "from", "over",
    "under", "inside", "within", "among", "after", "before", "through",
)

_EMOTION_HINTS = (
    ("urgent", ("now", "urgent", "immediately", "deadline", "must", "today")),
    ("cautionary", ("risk", "risks", "failure", "fail", "fails", "miss",
                    "misses", "warns", "warning", "threat", "danger",
                    "complacency", "leak", "vulnerability", "problem",
                    "problems")),
    ("optimistic", ("breakthrough", "faster", "cheaper", "improves",
                    "improved", "wins", "success", "record", "best")),
)

# Subjects that are too generic to identify a shot on their own.
_GENERIC_SUBJECTS = frozenset({
    "the", "this", "that", "it", "they", "we", "you", "researchers",
    "companies", "organizations", "organisations", "teams", "people",
    "developers", "users", "experts", "studies", "study", "research",
})

MIN_BEAT_WORDS = 4


@dataclass(frozen=True)
class NarrationBeat:
    """One narration sentence described for planning."""

    index: int
    sentence_index: int
    text: str
    word_count: int
    subject: str
    subject_type: str
    action: str
    context: str
    emotion: str
    evidence_required: bool
    flags: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["flags"] = list(self.flags)
        return payload


def _split_sentences(text: str) -> list[str]:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return []
    raw = _SENTENCE_BOUNDARY.split(value)
    merged: list[str] = []
    for part in raw:
        part = part.strip()
        if not part:
            continue
        last_word = re.sub(r"[^A-Za-z.]", "", merged[-1].split()[-1]).lower() if merged else ""
        if last_word.rstrip(".") in _ABBREVIATIONS:
            merged[-1] = f"{merged[-1]} {part}"
            continue
        merged.append(part)
    return merged


def _sentences(text: str) -> list[tuple[str, str]]:
    """Sentence units, merging fragments too short to be their own beat."""
    units: list[tuple[str, str]] = []
    for sentence in _split_sentences(text):
        words = sentence.split()
        if units and len(words) < MIN_BEAT_WORDS:
            units[-1] = (f"{units[-1][0]} {sentence}", units[-1][1])
            continue
        units.append((sentence, sentence))
    return units


def _subject(text: str) -> tuple[str, str]:
    low = text.lower()
    for name in _ORGANISATIONS:
        if re.search(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", low):
            return name.upper() if len(name) <= 4 else name.title(), "organisation"
    acronym = _ACRONYM_RE.search(text)
    if acronym and acronym.group(0).lower() not in _GENERIC_SUBJECTS:
        return acronym.group(0), "organisation"
    # First capitalised token that is not the sentence opener and not a filler.
    words = list(_WORD_RE.finditer(text))
    for position, match in enumerate(words):
        word = match.group(0)
        if position == 0:
            continue
        if word[:1].isupper() and word.lower() not in _GENERIC_SUBJECTS:
            return word, "concept"
    for match in words:
        word = match.group(0).lower()
        if word in _GENERIC_SUBJECTS or word in _ACTION_VERBS:
            continue
        if len(word) >= 4:
            return match.group(0), "concept"
    return "", "unknown"


def _action(text: str) -> str:
    low = text.lower()
    best = None
    for verb in _ACTION_VERBS:
        match = re.search(rf"(?<![A-Za-z]){verb}(?![A-Za-z])", low)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), verb)
    return best[1] if best else ""


def _context(text: str) -> str:
    low = text.lower()
    for preposition in _CONTEXT_PREPOSITIONS:
        match = re.search(rf"(?<![A-Za-z]){preposition}\s+([a-z0-9][^,.;:!?]*)", low)
        if not match:
            continue
        phrase = match.group(1).strip()
        words = phrase.split()[:6]
        if words:
            return f"{preposition} {' '.join(words)}"
    return ""


def _emotion(text: str) -> str:
    low = text.lower()
    for label, hints in _EMOTION_HINTS:
        if any(re.search(rf"(?<![A-Za-z]){re.escape(hint)}(?![A-Za-z])", low) for hint in hints):
            return label
    return "explanatory"


def _requires_evidence(text: str, subject_type: str, action: str) -> bool:
    low = text.lower()
    if _NUMBER_RE.search(text):
        return True
    if any(month in low for month in _MONTHS):
        return True
    if subject_type == "organisation":
        return True
    return bool(action)


def analyse_beat(text: str, index: int = 0) -> NarrationBeat:
    sentence = re.sub(r"\s+", " ", str(text or "")).strip()
    words = _WORD_RE.findall(sentence)
    subject, subject_type = _subject(sentence)
    action = _action(sentence)
    flags: list[str] = []
    if len(words) < MIN_BEAT_WORDS:
        flags.append("short_beat")
    if not subject:
        flags.append("no_subject")
    if not action:
        flags.append("no_action")
    return NarrationBeat(
        index=index,
        sentence_index=index,
        text=sentence,
        word_count=len(sentence.split()),
        subject=subject,
        subject_type=subject_type,
        action=action,
        context=_context(sentence),
        emotion=_emotion(sentence),
        evidence_required=_requires_evidence(sentence, subject_type, action),
        flags=tuple(flags),
    )


def analyse_narration(text: str) -> list[NarrationBeat]:
    """One beat per narration sentence, in order."""
    beats = []
    for index, (sentence, _reference) in enumerate(_sentences(text)):
        beats.append(analyse_beat(sentence, index))
    return beats


def split_narration(text: str) -> list[str]:
    return [beat.text for beat in analyse_narration(text)]
