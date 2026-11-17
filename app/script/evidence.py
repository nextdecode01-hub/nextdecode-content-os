"""Evidence-to-script mapping and proportionality checks.

Deterministic string/statistics work only: no model calls.  The point is to
show, per sentence, which claim record backs it and where the wording has run
ahead of the evidence (correlation stated as causation, a forecast stated as
fact, a number that appears in no source).
"""
from __future__ import annotations

import re

_STOPWORDS = frozenset("""
a an and are as at be been but by can could did do does for from had has have he her
his how i if in into is it its may might more most must no not of on or our out over
she should so some such than that the their them then there these they this those to
too up us was we were what when where which while who why will with would you your
""".split())

_NUMBER_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?(?:\s?(?:%|percent|per cent|million|billion|thousand|bn|m))?",
    re.I,
)

# Wording that asserts more than a single source, or more than evidence of one kind.
_CAUSAL = re.compile(r"\b(causes?|caused|leads? to|led to|proves?|proven|confirms?|"
                     r"guarantees?|ensures?|because of|as a result)\b", re.I)
_FORECAST_AS_FACT = re.compile(r"\b(will|is going to|definitely|always|never)\b", re.I)
_HEDGES = re.compile(
    r"\b(could|may|might|can|reportedly|according to|suggests?|estimated|"
    r"appears?|is expected to|is projected to|typical|typically|often|in some cases|"
    r"(?:the|an) (?:arxiv )?paper (?:reports?|says|found|describes?)|"
    r"(?:the )?authors? (?:report|reports|say|says|found)|"
    r"in some configurations|in this model|in this configuration|in this architecture|"
    r"for mixtral|in the mixtral configuration|mistral's (?:published )?mixtral design|"
    r"for this example|for that token)\b",
    re.I,
)

# An assertion about what a named body does is a fact claim even without a
# number or a year: "auditors and governance teams use the AI RMF as a benchmark"
# was classified as opinion purely because it matches none of the patterns above.
_SOURCE_ATTRIBUTION_RE = re.compile(
    r"\b(the paper|the source|the study|the report|researchers|nature)\s+"
    r"(said|says|states?|describes?|described|reported|reports|measured|found|showed|shows|matched)\b",
    re.I,
)
_PRACTICE_RE = re.compile(
    r"\b(us(?:e|es|ed|ing)|adopt(?:s|ed|ion)?|rely|relies|relied|cite[sd]?|require[sd]?|"
    r"recommend[s]?|report(?:s|ed)?|find[s]?|show[s]?|benchmark(?:s|ed)?|"
    r"describ(?:e|es|ed|ing)|propos(?:e|es|ed|ing)|design(?:s|ed|ing)?|"
    r"accelerat(?:e|es|ed|ing)|generat(?:e|es|ed|ing)|refin(?:e|es|ed|ing)|"
    r"provid(?:e|es|ed|ing)|support(?:s|ed|ing)?)\b", re.I)
_ENTITY_RE = re.compile(r"\b[A-Z]{2,}\b|\b[A-Z][a-z]+(?:\s+(?:of|and|for|the)\s+)?(?:[A-Z][a-z]+\b){1,3}")
_CONCEPT_ENTITY_RE = re.compile(r"\b(?:workflow|system|model|tool|assistant|agent|agents|platform|product)\b", re.I)
_PUBLICATION_ATTRIBUTION_RE = re.compile(
    r"\b(?:nature|science|cell)\s+(?:has\s+)?(?:described|reported|found|says|said)\b", re.I
)


def content_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9\-]+", str(text or "").lower())
    return {word for word in words if word not in _STOPWORDS and len(word) > 2}


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", str(text or "").strip())
    return [part.strip() for part in parts if part.strip()]


def _score(sentence: str, claim: dict) -> float:
    sentence_tokens = content_tokens(sentence)
    if not sentence_tokens:
        return 0.0
    claim_tokens = content_tokens(
        f"{claim.get('narration') or ''} {claim.get('quote') or ''}"
    )
    if not claim_tokens:
        return 0.0
    overlap = len(sentence_tokens & claim_tokens) / len(sentence_tokens)
    # A shared number is a strong hint that this sentence carries that claim.
    sentence_numbers = set(_NUMBER_RE.findall(sentence))
    claim_numbers = set(_NUMBER_RE.findall(claim.get("quote") or claim.get("narration") or ""))
    if sentence_numbers and sentence_numbers & claim_numbers:
        overlap = min(1.0, overlap + 0.15)
    return round(overlap, 3)


def map_sentences(voice_text: str, claims: list[dict], *,
                  threshold: float = 0.35) -> dict:
    """Map each narration sentence onto the claim records that support it."""
    claims = [claim for claim in claims if claim]
    # Prefer evidence the writer is permitted to use. A matching but conflicting
    # or outdated secondary excerpt must not displace a supported/qualified
    # primary-source excerpt for the same narration sentence. If no eligible
    # record matches, retain the best weak match so the gate can flag it.
    eligible_claims = [
        claim for claim in claims
        if str(claim.get("decision") or "") in {"include", "qualify"}
        and str((claim.get("verification") or {}).get("status") or "")
        in {"supported", "partially_supported"}
    ]
    rows: list[dict] = []
    unmapped: list[str] = []
    for sentence in split_sentences(voice_text):
        preferred = sorted(
            ((_score(sentence, claim), claim) for claim in eligible_claims),
            key=lambda item: -item[0],
        )
        scored = preferred if any(score >= threshold for score, _ in preferred) else sorted(
            ((_score(sentence, claim), claim) for claim in claims),
            key=lambda item: -item[0],
        )
        matches = [
            {"claim_id": claim.get("claim_id", ""), "score": score}
            for score, claim in scored[:2]
            if score >= threshold
        ]
        row = {
            "sentence": sentence,
            "claim_ids": [match["claim_id"] for match in matches],
            "score": matches[0]["score"] if matches else 0.0,
            "factual": looks_factual(sentence),
        }
        rows.append(row)
        if not matches and row["factual"]:
            unmapped.append(sentence)
    flags = proportionality_flags(rows, {claim.get("claim_id"): claim for claim in claims})
    return {"sentences": rows, "unmapped": unmapped, "flags": flags, "threshold": threshold}


def looks_factual(sentence: str) -> bool:
    """Numbers, dates, attributions or a named body doing something mark a fact claim."""
    text = str(sentence or "")
    if _NUMBER_RE.search(text):
        return True
    if re.search(r"\b(19|20)\d{2}\b", text):
        return True
    if re.search(r"\b(according to|study|survey|report|found|announced|released)\b", text, re.I):
        return True
    if _SOURCE_ATTRIBUTION_RE.search(text) or _PUBLICATION_ATTRIBUTION_RE.search(text):
        return True
    if _PRACTICE_RE.search(text) and (
        _ENTITY_RE.search(text) or _CONCEPT_ENTITY_RE.search(text)
    ):
        return True
    return False


def proportionality_flags(rows: list[dict], claims: dict[str, dict]) -> list[dict]:
    """Where the wording asserts more than the evidence record supports."""
    flags: list[dict] = []
    for row in rows:
        sentence = row["sentence"]
        for claim_id in row.get("claim_ids") or []:
            claim = claims.get(claim_id) or {}
            quote = f"{claim.get('quote') or ''} {claim.get('narration') or ''}"
            verification = (claim.get("verification") or {})
            status = str(verification.get("status") or "unverified")
            kind = str(claim.get("claim_type") or "statement")

            if _CAUSAL.search(sentence) and not _CAUSAL.search(quote):
                flags.append(_flag(sentence, claim_id, "causation",
                                   "narration asserts causation that the excerpt does not state"))
            if _FORECAST_AS_FACT.search(sentence) and kind == "forecast" and status != "supported":
                flags.append(_flag(sentence, claim_id, "forecast_as_fact",
                                   "forecast phrased as certainty while evidence is not confirmed"))
            sentence_numbers = set(_NUMBER_RE.findall(sentence))
            missing = {number for number in sentence_numbers
                       if number not in quote}
            if sentence_numbers and missing and not _HEDGES.search(sentence):
                flags.append(_flag(sentence, claim_id, "number_not_in_evidence",
                                   "number in narration does not appear in the excerpt"))
            if status in {"unverified", "conflicting", "outdated"} and not _HEDGES.search(sentence):
                flags.append(_flag(sentence, claim_id, f"unqualified_{status}",
                                   f"claim is {status} but the sentence states it plainly"))
            if status == "partially_supported" and not _HEDGES.search(sentence):
                flags.append(_flag(
                    sentence, claim_id, "unqualified_partially_supported",
                    "claim has only partial/single-source support but the narration states it plainly",
                ))
    # A factual sentence with no claim at all is itself a finding.
    for row in rows:
        if row.get("factual") and not row.get("claim_ids"):
            flags.append({
                "sentence": row["sentence"],
                "claim_id": "",
                "flag": "unsupported_factual",
                "detail": "factual sentence with no claim-ledger record",
            })
        elif not row.get("claim_ids") and _CAUSAL.search(row["sentence"]):
            flags.append({
                "sentence": row["sentence"],
                "claim_id": "",
                "flag": "unattributed_causation",
                "detail": "causal claim with no evidence record behind it",
            })
    return flags


def _flag(sentence: str, claim_id: str, name: str, detail: str) -> dict:
    return {"sentence": sentence, "claim_id": claim_id, "flag": name, "detail": detail}


def coverage(voice_text: str, flags: list[dict], mapping: dict | None = None) -> dict:
    mapping = mapping or map_sentences(voice_text, [])
    total = len(mapping.get("sentences") or [])
    mapped = sum(1 for row in mapping.get("sentences") or [] if row.get("claim_ids"))
    return {
        "sentences": total,
        "mapped": mapped,
        "unmapped_factual": len(mapping.get("unmapped") or []),
        "flags": len(flags),
        "traceability": round(mapped / total, 3) if total else 1.0,
    }
