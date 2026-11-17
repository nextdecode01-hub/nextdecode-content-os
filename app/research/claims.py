"""Claim ledger: one durable record per material factual claim.

Every record ties the narration sentence to a verbatim excerpt, its source, how
that source relates to the others (lineage), and a verification status.  Fields
that cannot be established stay empty and are reported - nothing is invented,
including URLs, dates and quotes.

Statuses: ``supported``, ``partially_supported``, ``conflicting``,
``unverified``, ``outdated``.
Decisions: ``include``, ``qualify``, ``research_more``, ``exclude``.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.research import lineage

LEDGER_VERSION = 1

STATUSES = ("supported", "partially_supported", "conflicting", "unverified", "outdated")
DECISIONS = ("include", "qualify", "research_more", "exclude")

# A claim whose value changes over time should not stay "fresh" forever.
TIME_SENSITIVE_TYPES = frozenset({"statistic", "forecast", "date", "funding"})
DEFAULT_STALE_DAYS = 730

_MONTHS = (
    "january|february|march|april|may|june|july|august|september|october|"
    "november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
)
_DATE_PATTERNS = (
    re.compile(rf"\b({_MONTHS})\.?\s+\d{{1,2}},?\s+(20\d{{2}})\b", re.I),
    re.compile(rf"\b\d{{1,2}}\s+({_MONTHS})\.?\s+(20\d{{2}})\b", re.I),
    re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b"),
)


def claim_type(text: str) -> str:
    """Classify the claim by the shape of its evidence, not by topic."""
    value = str(text or "")
    lowered = value.lower()
    if re.search(r"\b(will|expected to|projected|forecast|by 20\d{2}|predicts?)\b", lowered):
        return "forecast"
    if re.search(r"\$\s?\d|\b\d+(?:\.\d+)?\s?(million|billion|m|bn)\b.*\b(funding|raised|valuation)\b", lowered) \
            or re.search(r"\b(funding|raised|valuation)\b.*\$\s?\d", lowered):
        return "funding"
    if re.search(r"\b\d+(?:\.\d+)?\s?%|\bpercent\b|\bper cent\b", lowered):
        return "statistic"
    if re.search(rf"\b(?:{_MONTHS})\s+\d{{1,2}},?\s+20\d{{2}}\b", lowered):
        return "date"
    if '"' in value or "\u201c" in value:
        return "quote"
    if re.search(r"\b(found|study|paper|survey|report)\b", lowered):
        return "research"
    if re.search(r"\b(launch|launched|announce|announced|release|released|supports?|available)\b", lowered):
        return "announcement"
    if re.search(r"\b(can|enables|allows|works with|integrates)\b", lowered):
        return "capability"
    return "statement"


def publication_date(source: dict) -> tuple[str, str]:
    """Return ``(iso_date, confidence)`` from a source record.

    Only reads what the page actually provided: ``published`` metadata or an
    explicit date line.  No inference from the retrieval time.
    """
    published = str(source.get("published") or "").strip()
    if published:
        try:
            parsed = datetime.fromisoformat(published.replace("Z", "+00:00"))
            return parsed.date().isoformat(), "metadata"
        except ValueError:
            pass
        match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", published)
        if match:
            return match.group(0), "metadata"
    haystack = str(source.get("text") or "")[:4000]
    for pattern in _DATE_PATTERNS:
        match = pattern.search(haystack)
        if match:
            raw = match.group(0)
            for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(raw.replace(".", ""), fmt).date().isoformat(), "page_text"
                except ValueError:
                    continue
    return "", "unknown"


def _claim_id(topic: str, quote: str, url: str) -> str:
    digest = hashlib.sha1(f"{topic}\n{quote}\n{url}".encode("utf-8")).hexdigest()
    return f"clm_{digest[:10]}"


def _source_id(url: str) -> str:
    digest = hashlib.sha1(lineage.canonical_url(url).encode("utf-8")).hexdigest()
    return f"src_{digest[:8]}"


def _is_stale(published: str, now: datetime, stale_days: int) -> tuple[bool, int | None]:
    if not published:
        return False, None
    try:
        date = datetime.fromisoformat(published)
    except ValueError:
        return False, None
    age = (now.date() - date.date()).days
    return age > stale_days, age


def _quote_offset(text: str, quote: str) -> int | None:
    """Character offset of the excerpt inside the source text, if it is verbatim."""
    if not text or not quote:
        return None
    position = text.find(quote)
    return position if position >= 0 else None


# A date that has already happened does not rot.  "NIST released the AI RMF in
# January 2023" stays true forever; "the AI RMF is being revised" and "adoption
# will reach 50% by 2027" both go stale.  Treating every dated claim as
# time-sensitive marked correct history as outdated.
_FORECAST_RE = re.compile(
    r"\b(will|shall|going to|expected to|expects|projected|projects|forecast|forecasts|"
    r"planned to|plans to|is set to|are set to|by 20\d{2}|to reach|to be released)\b", re.I)
_PAST_RE = re.compile(
    r"\b(released|launched|published|founded|established|signed|announced|introduced|"
    r"opened|closed|acquired|sold|died|passed|approved|ratified|completed|ended|occurred)\b",
    re.I)
_PAST_COPULA_RE = re.compile(r"\b(was|were|had|has been)\b", re.I)
_CURRENT_RE = re.compile(
    r"\b(is|are|am|being|remains|continues|currently|now|today|ongoing|under way|"
    r"in progress|has yet|yet to|still)\b", re.I)
_COMPLETED_DATE_RE = re.compile(
    r"\bon\s+(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},?\s+20\d{2}\b|\bin\s+(?:January|February|March|April|May|"
    r"June|July|August|September|October|November|December)\s+20\d{2}\b|\b(?:January|February|"
    r"March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}\b",
    re.I)


def temporal_kind(text: str) -> str:
    """``forecast``, ``historical`` or ``current`` for one claim sentence."""
    value = str(text or "")
    # A future cue in a relative clause does not make the whole sentence a
    # forecast: "NIST launched the Center on March 30, 2023, which will help…"
    # is a completed event with a purpose attached.
    main_clause = re.split(r",\s*(?:which|that|who|as)\b", value, maxsplit=1)[0]
    if _FORECAST_RE.search(main_clause):
        return "forecast"
    has_completed_date = bool(_COMPLETED_DATE_RE.search(value))
    if has_completed_date and (_PAST_RE.search(value) or _PAST_COPULA_RE.search(value)):
        return "historical"
    if _PAST_RE.search(value) and not _CURRENT_RE.search(value):
        return "historical"
    if _CURRENT_RE.search(value):
        # "is currently under revision" describes a state that can expire, even
        # when the sentence also mentions an old date.
        return "current"
    if _FORECAST_RE.search(value):
        return "forecast"
    if re.search(r"\b(?:19|20)\d{2}\b", value):
        # A finished year with no present-state cue ("the report covers 2023
        # outcomes") describes something that cannot go out of date.
        return "historical"
    return "current"


# Only these temporal classes can go stale.
STALE_CLASSES = frozenset({"current", "forecast"})
FORECAST_STALE_DAYS = 365


def _record_for_source(source: dict) -> dict:
    url = str(source.get("url") or "")
    text = str(source.get("text") or "")
    published, date_confidence = publication_date(source)
    return {
        "source_id": _source_id(url),
        "url": url,
        "canonical_url": lineage.canonical_url(url),
        "publisher": str(source.get("publisher") or lineage.publisher_of(url)),
        "institution": lineage.institution_of(url),
        "source_type": lineage.source_type(url, text),
        "published": published,
        "date_confidence": date_confidence,
        "retrieved_at": str(source.get("retrieved_at") or ""),
        "title": str(source.get("title") or ""),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest() if text else "",
        "text_chars": len(text),
    }


def _contradictions_for(claim_id: str, claim: dict,
                        contradictions: list[dict]) -> list[dict]:
    found = []
    for item in contradictions or []:
        urls = {str(item.get("source_a") or ""), str(item.get("source_b") or "")}
        if str(claim.get("source_url") or "") in urls and \
                str(claim.get("claim") or "") in {str(item.get("claim") or ""), ""}:
            found.append(dict(item))
        elif str(claim.get("claim") or "") == str(item.get("claim") or ""):
            found.append(dict(item))
    return found


def _status_for(claim: dict, corroboration: dict, conflicts: list[dict],
                stale: bool, has_verbatim: bool) -> tuple[str, str]:
    if conflicts:
        return "conflicting", f"{len(conflicts)} conflicting report(s) on the same metric"
    if not has_verbatim:
        return "unverified", "no verbatim excerpt located in the source text"
    if corroboration.get("distinct_clusters", 0) >= 1:
        return "supported", (
            f"{corroboration['distinct_clusters']} independent source cluster(s) confirm it"
        )
    if stale:
        return "outdated", "time-sensitive claim older than the freshness window"
    if corroboration.get("dependent_clusters", 0) >= 1:
        return "partially_supported", (
            "coverage repeats the announcement; that is one voice, not corroboration"
        )
    if corroboration.get("matches"):
        return "partially_supported", (
            "only republished/syndicated copies back it, so it is one voice, not corroboration"
        )
    return "partially_supported", "single source; no independent confirmation"


_DECISION_BY_STATUS = {
    "supported": "include",
    "partially_supported": "qualify",
    "conflicting": "research_more",
    "unverified": "exclude",
    "outdated": "research_more",
}


def _support_records(claim: dict, corroboration: dict, own_record: dict) -> list[dict]:
    """Claim-level evidence: who supports it, with the exact supporting sentence."""
    records = [{
        "source_id": own_record.get("source_id", ""),
        "publisher": own_record.get("publisher") or lineage.publisher_of(str(claim.get("source_url") or "")),
        "url": str(claim.get("source_url") or ""),
        "relation": "origin",
        "strength": "full",
        "excerpt": str(claim.get("quote") or "")[:400],
        "offset": claim.get("excerpt_offset"),
    }]
    for match in corroboration.get("matches") or []:
        if match.get("dependent"):
            continue
        excerpt = (match.get("excerpts") or [{}])[0]
        records.append({
            "source_id": _source_id(match.get("url", "")),
            "publisher": match.get("publisher", ""),
            "institution": match.get("institution") or lineage.institution_of(match.get("url", "")),
            "url": str(match.get("url") or ""),
            "relation": "corroboration" if match.get("strength") == "full" else "partial_match",
            "strength": match.get("strength", "none"),
            "entity_coverage": match.get("entity_coverage"),
            "keyword_coverage": match.get("keyword_coverage"),
            "missing_entities": match.get("missing_entities", []),
            "missing_values": match.get("missing_values", []),
            "excerpt": str(excerpt.get("excerpt") or "")[:400],
            "anchor": str(excerpt.get("anchor") or ""),
            "matched": match.get("matched", [])[:8],
            "missing": match.get("missing", [])[:8],
        })
    return records


def _contradiction_records(claim: dict, desk_conflicts: list[dict],
                          corroboration: dict) -> list[dict]:
    records = [dict(item, kind="metric_conflict") for item in desk_conflicts]
    for item in corroboration.get("conflicts") or []:
        records.append({
            "kind": "value_conflict",
            "claim": str(claim.get("claim") or ""),
            "expected": item.get("expected", ""),
            "found": item.get("found", ""),
            "publisher": item.get("publisher", ""),
            "source_url": item.get("url", ""),
            "excerpt": item.get("excerpt", ""),
            "note": f"{item.get('kind', 'value')} differs: claim says "
                    f"{item.get('expected')}, source says {item.get('found')}",
        })
    return records


def build_ledger(research: dict, *, script_text: str = "", now: datetime | None = None,
                 stale_days: int = DEFAULT_STALE_DAYS) -> dict:
    """Turn a research bundle into a claim ledger.

    Never fabricates: every field comes from the research bundle, and anything
    the bundle did not provide is left empty and counted in ``summary.missing``.
    """
    now = now or datetime.now(timezone.utc)
    topic = str(research.get("topic") or "")
    sources = [source for source in (research.get("sources") or []) if source.get("url")]
    clusters = lineage.cluster_sources(sources)
    source_records = [_record_for_source(source) for source in sources]
    by_url = {record["canonical_url"]: record for record in source_records}

    claims: list[dict] = []
    for raw in research.get("claims") or []:
        quote = str(raw.get("quote") or "")
        url = str(raw.get("source_url") or "")
        text = next((str(s.get("text") or "") for s in sources
                     if lineage.canonical_url(str(s.get("url") or "")) == lineage.canonical_url(url)), "")
        offset = _quote_offset(text, quote)
        corroboration = lineage.independent_confirmations(raw, sources, clusters=clusters)
        source_record = by_url.get(lineage.canonical_url(url), {})
        conflicts = _contradiction_records(
            raw, _contradictions_for("", raw, research.get("contradictions") or []), corroboration
        )
        published = source_record.get("published", "")
        kind = claim_type(str(raw.get("claim") or ""))
        temporal = temporal_kind(str(raw.get("claim") or ""))
        window = stale_days if temporal != "forecast" else min(stale_days, FORECAST_STALE_DAYS)
        # Freshness follows the tense of the sentence, not its topic label: a
        # current-state or forecast claim can expire, a completed event cannot.
        if temporal in STALE_CLASSES:
            stale, age_days = _is_stale(published, now, window)
        else:
            stale, age_days = False, None
        status, reason = _status_for(raw, corroboration, conflicts, stale, offset is not None)
        decision = _DECISION_BY_STATUS[status]
        flags = []
        if kind in TIME_SENSITIVE_TYPES and not published:
            flags.append("publication date unknown; freshness cannot be verified")
        if age_days is not None and age_days > stale_days:
            flags.append(f"evidence is {age_days} days old")
        if not source_record:
            flags.append("claim source is not in the fetched source list")
        claims.append({
            "claim_id": _claim_id(topic, quote, url),
            "narration": str(raw.get("claim") or ""),
            "claim_type": kind,
            "temporal": temporal,
            "quote": quote,
            "excerpt_offset": offset,
            "source_id": source_record.get("source_id", _source_id(url)),
            "source_url": url,
            "publisher": source_record.get("publisher") or lineage.publisher_of(url),
            "source_type": source_record.get("source_type") or lineage.source_type(url),
            "published": published,
            "date_confidence": source_record.get("date_confidence", "unknown"),
            "retrieved_at": str(research.get("fetched_at") or ""),
            "lineage": {
                "cluster_id": corroboration.get("own_cluster", ""),
                "institution": lineage.institution_of(url),
                "own_institution": corroboration.get("own_institution", ""),
                "distinct_clusters": corroboration.get("distinct_clusters", 0),
                "backing_institutions": corroboration.get("backing_institutions", []),
                "dependent_clusters": corroboration.get("dependent_clusters", 0),
                "matches": corroboration.get("matches", []),
                "note": (
                    "independent confirmations counted by institution, not by page "
                    "or subdomain; a partial anchor match never upgrades a claim"
                ),
            },
            "verification": {
                "status": status,
                "reason": reason,
                "conflicting": conflicts,
            },
            "support": _support_records(raw, corroboration, source_record),
            "contradict": conflicts,
            "atomic_of": str(raw.get("atomic_of") or ""),
            "also_reported_by": list(raw.get("also_reported_by") or []),
            "decision": decision,
            "script": None,
            "scene": None,
            "flags": flags,
        })

    ledger = {
        "version": LEDGER_VERSION,
        "created_at": now.isoformat(),
        "topic": topic,
        "verdict": str(research.get("verdict") or ""),
        "script_sha256": "",
        "sources": source_records,
        "source_clusters": clusters.get("clusters", []),
        "claims": claims,
        "summary": {},
        "errors": list(research.get("errors") or []),
    }
    if script_text:
        bind_script(ledger, script_text)
    ledger["summary"] = summarize(ledger)
    ledger["ledger_sha256"] = ledger_digest(ledger)
    return ledger


def bind_script(ledger: dict, script_text: str) -> dict:
    """Map narration sentences to claim IDs; keeps only matched claims."""
    from app.script import evidence

    mapping = evidence.map_sentences(script_text, ledger.get("claims") or [])
    by_sentence = {item["sentence"]: item for item in mapping["sentences"]}
    for claim in ledger.get("claims") or []:
        match = by_sentence.get(claim.get("narration") or "")
        claim["script"] = dict(match) if match else None
    ledger["script_sha256"] = hashlib.sha256(str(script_text or "").encode("utf-8")).hexdigest()
    ledger["script_mapping"] = mapping
    ledger["summary"] = summarize(ledger)
    ledger["ledger_sha256"] = ledger_digest(ledger)
    return ledger


def _independently_corroborated(claim: dict) -> bool:
    """True when a *different* institution fully supports the claim.

    Same-institution pages are one newsroom: four NIST subpages confirming a NIST
    claim is self-agreement, not corroboration.  Partial matches never count.
    """
    own = str((claim.get("lineage") or {}).get("own_institution")
              or lineage.institution_of(claim.get("source_url", "")))
    for record in claim.get("support") or []:
        if record.get("relation") != "corroboration" or record.get("strength") != "full":
            continue
        institution = record.get("institution") or lineage.institution_of(record.get("url", ""))
        if institution and institution != own:
            return True
    return False


def summarize(ledger: dict) -> dict:
    claims = ledger.get("claims") or []
    statuses = {status: 0 for status in STATUSES}
    decisions = {decision: 0 for decision in DECISIONS}
    types: dict[str, int] = {}
    for claim in claims:
        statuses[claim["verification"]["status"]] = statuses.get(claim["verification"]["status"], 0) + 1
        decisions[claim["decision"]] = decisions.get(claim["decision"], 0) + 1
        types[claim["claim_type"]] = types.get(claim["claim_type"], 0) + 1
    temporal = {"historical": 0, "current": 0, "forecast": 0}
    for claim in claims:
        temporal[claim.get("temporal", "current")] = (
            temporal.get(claim.get("temporal", "current"), 0) + 1
        )
    institutions = {
        record.get("institution") for record in ledger.get("sources") or [] if record.get("institution")
    }
    missing_dates = sum(1 for claim in claims if not claim.get("published"))
    corroborated = sum(1 for claim in claims if _independently_corroborated(claim))
    with_conflicts = sum(1 for claim in claims if claim.get("contradict"))
    mapping = ledger.get("script_mapping") or {}
    return {
        "claims": len(claims),
        "by_status": statuses,
        "by_decision": decisions,
        "by_type": types,
        "by_temporal_kind": temporal,
        "source_pages": len(ledger.get("sources") or []),
        "source_institutions": len(institutions),
        "independently_corroborated": corroborated,
        "with_open_conflicts": with_conflicts,
        "without_publication_date": missing_dates,
        "unmatched_narration_sentences": len(mapping.get("unmapped") or []),
        "flagged_sentences": len(mapping.get("flags") or []),
    }


def ledger_digest(ledger: dict) -> str:
    payload = {key: value for key, value in ledger.items() if key != "ledger_sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def write_ledger(ledger: dict, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def load_ledger(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def claims_for_scene(ledger: dict, narration: str, *, threshold: float = 0.35) -> list[dict]:
    """Claims relevant to one scene's narration line."""
    from app.script import evidence

    tokens = evidence.content_tokens(narration)
    if not tokens:
        return []
    all_claims = [claim for claim in ledger.get("claims") or [] if isinstance(claim, dict)]
    eligible = [
        claim for claim in all_claims
        if str(claim.get("decision") or "") in {"include", "qualify"}
        and str((claim.get("verification") or {}).get("status") or "")
        in {"supported", "partially_supported"}
    ]

    def rank(candidates: list[dict]) -> list[tuple[float, dict]]:
        ranked = []
        for claim in candidates:
            claim_tokens = evidence.content_tokens(claim.get("narration") or claim.get("quote") or "")
            if not claim_tokens:
                continue
            overlap = len(tokens & claim_tokens) / max(1, len(tokens))
            if overlap >= threshold:
                ranked.append((overlap, claim))
        ranked.sort(key=lambda item: -item[0])
        return ranked

    preferred = rank(eligible)
    # Preserve a weak match only when no permitted evidence can support the
    # scene; downstream gates then surface the missing/weak link explicitly.
    ranked = preferred or rank(all_claims)
    return [claim for _, claim in ranked[:2]]
