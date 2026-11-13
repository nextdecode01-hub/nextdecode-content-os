"""Split compound sentences into atomic, separately checkable claims.

"The framework, released in January 2023, is voluntary and covers the whole
lifecycle" states three facts with three different evidence requirements.  Left
joined, one missing date drags the whole sentence down to "partially supported"
and hides which part is unproven.

Every returned piece is a verbatim substring of the input: nothing is rephrased,
reordered or supplied, so an atomic claim can always be traced back to the page.
"""
from __future__ import annotations

import re

# Clause boundaries that carry a new assertion rather than a continuation.
_BOUNDARY = re.compile(
    r"(?<=[,;])\s+(?=(?:and\s+)?(?:which|that|who|whose|released|launched|announced|published|"
    r"designed|intended|introduced|provides|providing|includes|including|covers|allowing|"
    r"enabling|helping|making|used|based|written|built|offered|requires?|is|are|was|were|has|have|"
    r"will|would|can|could|but\s+also)\b)",
    re.I,
)
_COORDINATED = re.compile(r"(?<=\w),\s+and\s+(?=\w)")
_MIN_WORDS = 5
_MAX_CLAUSES = 4
_STOP = frozenset("a an the of and or but to in for on with by from as at it its this that is are "
                  "was were be been being who whom whose which what when where how not no yes".split())

# A clause may legitimately start with its predicate, but not with an orphan of
# the previous phrase ("multistakeholder manner over an 18-month ...").
_CLAUSE_STARTS = frozenset(
    "released launched announced published designed intended introduced provides providing "
    "includes including covers allowing enabling helping making used based written built "
    "offered requires require is are was were has have will would can could but and which "
    "that who whose".split())


_TRUNCATED_END = re.compile(r"\b(?:of|and|the|to|in|for|that|with|by|as|is|are|was|including)\W*$", re.I)


def _starts_a_clause(piece: str) -> bool:
    first = re.match(r"[A-Za-z]+", piece)
    if not first:
        return False
    if _TRUNCATED_END.search(piece):
        return False
    return piece[0].isupper() or first.group(0).lower() in _CLAUSE_STARTS


def _predicate_words(piece: str) -> int:
    """Count meaningful lowercase words, so a bare subject is not a claim."""
    return sum(1 for word in re.findall(r"[a-z]{3,}", piece.lower()) if word not in _STOP)


def split_atomic(text: str) -> list[str]:
    """Return the atomic clauses of a sentence, or ``[]`` when it is already atomic."""
    sentence = re.sub(r"\s+", " ", str(text or "")).strip()
    if not sentence:
        return []
    pieces: list[str] = []
    for chunk in _BOUNDARY.split(sentence):
        for part in _COORDINATED.split(chunk):
            part = part.strip(" ,;")
            if part:
                pieces.append(part)
    if len(pieces) < 2:
        return []
    pieces = [
        piece for piece in pieces
        if len(piece.split()) >= _MIN_WORDS and _predicate_words(piece) >= 2
        and _starts_a_clause(piece)
    ]
    if len(pieces) < 2:
        return []
    lowered = {piece.lower() for piece in pieces}
    if sentence.lower() in lowered:
        # Splitting produced the original back; nothing was gained.
        return []
    return pieces[:_MAX_CLAUSES]


def is_substring_of(piece: str, sentence: str) -> bool:
    """Guard used by the ledger: an atomic claim must come from its parent."""
    needle = re.sub(r"\s+", " ", str(piece or "")).strip().lower()
    haystack = re.sub(r"\s+", " ", str(sentence or "")).strip().lower()
    return bool(needle) and needle in haystack
