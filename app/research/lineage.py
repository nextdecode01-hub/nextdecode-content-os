"""Source lineage and independence checks.

Multiple outlets republishing the same press release or wire story are one
source, not several confirmations.  Everything here is deterministic and
offline: URLs are canonicalised, near-duplicate texts are clustered by shingle
overlap, and only distinct clusters count toward corroboration.

No network access, no confidence scores pretending to be truth.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse, urlunparse

WIRE_HOSTS = frozenset({
    "prnewswire.com", "businesswire.com", "globenewswire.com", "accesswire.com",
    "newsfilecorp.com", "einpresswire.com", "reuters.com", "apnews.com",
})

TRACKING_PREFIXES = ("utm_", "gclid", "fbclid", "mc_cid", "mc_eid", "ref", "source")

RELEASE_MARKERS = (
    "for immediate release",
    "press release",
    "this press release",
    "originally published",
    "syndicated from",
    "reprinted with permission",
    "all rights reserved. this material may not be published",
)

PRIMARY_HOSTS = frozenset({
    "arxiv.org", "doi.org", "sec.gov", "nist.gov", "who.int", "europa.eu",
    "github.com", "openai.com", "anthropic.com", "googleblog.com",
})

PUBLIC_DOMAIN_SUFFIXES = (".gov", ".mil", ".gov.uk", ".europa.eu")


def canonical_url(url: str) -> str:
    """Lowercase host, drop tracking params, fragments and trailing slashes."""
    raw = str(url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+$", "", parsed.path or "")
    query_parts = []
    for part in (parsed.query or "").split("&"):
        if not part:
            continue
        key = part.split("=", 1)[0].lower()
        if any(key.startswith(prefix) for prefix in TRACKING_PREFIXES):
            continue
        query_parts.append(part)
    return urlunparse((parsed.scheme or "https", host, path, "", "&".join(query_parts), ""))


def publisher_of(url: str) -> str:
    """Readable publisher name from the host, without ``www.``."""
    host = urlparse(str(url or "")).hostname or ""
    return host[4:] if host.lower().startswith("www.") else host


def source_type(url: str, text: str = "") -> str:
    """Coarse source class.  Unknown stays unknown rather than being guessed."""
    host = publisher_of(url).lower()
    haystack = (text or "").lower()[:4000]
    if host in WIRE_HOSTS:
        return "wire"
    if any(marker in haystack for marker in RELEASE_MARKERS[:2]):
        return "press_release"
    if host.endswith(".gov") or host.endswith(".gov.uk") or host.endswith(".mil"):
        return "government"
    if host in PRIMARY_HOSTS or host.endswith(".edu"):
        return "primary"
    if host.startswith("docs.") or "/docs/" in url:
        return "documentation"
    if host in {"medium.com", "substack.com"} or "/blog/" in url:
        return "blog"
    return "reporting"


def is_wire_or_release(url: str, text: str = "") -> bool:
    kind = source_type(url, text)
    return kind in {"wire", "press_release"}


def normalize_text(text: str) -> str:
    value = (text or "").lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def shingles(text: str, size: int = 5) -> set[str]:
    words = normalize_text(text).split()
    if len(words) < size:
        return {" ".join(words)} if words else set()
    return {" ".join(words[index:index + size]) for index in range(len(words) - size + 1)}


def similarity(first: str, second: str, size: int = 5) -> float:
    """Jaccard overlap of word shingles (0 = unrelated, 1 = identical)."""
    a = shingles(first, size)
    b = shingles(second, size)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _find(parent: dict[str, str], key: str) -> str:
    while parent[key] != key:
        parent[key] = parent[parent[key]]
        key = parent[key]
    return key


def _union(parent: dict[str, str], first: str, second: str) -> None:
    root_a, root_b = _find(parent, first), _find(parent, second)
    if root_a != root_b:
        parent[root_b] = root_a


def cluster_sources(sources: list[dict], *, threshold: float = 0.45) -> dict:
    """Group sources that reproduce the same underlying text.

    Returns ``{"clusters": [...], "by_url": {canonical_url: cluster_id}}``.
    A cluster is one voice, however many outlets carry it.
    """
    entries = []
    for source in sources or []:
        url = str(source.get("url") or "")
        if not url:
            continue
        entries.append({
            "url": url,
            "canonical": canonical_url(url),
            "host": publisher_of(url),
            "text": str(source.get("text") or ""),
        })
    if not entries:
        return {"clusters": [], "by_url": {}}

    parent = {entry["canonical"]: entry["canonical"] for entry in entries}
    for index, first in enumerate(entries):
        for second in entries[index + 1:]:
            if first["canonical"] == second["canonical"]:
                _union(parent, first["canonical"], second["canonical"])
                continue
            if first["host"] == second["host"]:
                continue
            score = similarity(first["text"], second["text"], size=5)
            if score >= threshold:
                _union(parent, first["canonical"], second["canonical"])

    grouped: dict[str, list[dict]] = {}
    for entry in entries:
        grouped.setdefault(_find(parent, entry["canonical"]), []).append(entry)

    clusters = []
    by_url: dict[str, str] = {}
    for position, (root, members) in enumerate(
        sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])), start=1
    ):
        cluster_id = f"src_cluster_{position:02d}"
        hosts = sorted({member["host"] for member in members})
        digest = hashlib.sha1("|".join(sorted(m["canonical"] for m in members)).encode()).hexdigest()[:8]
        # Clustering already means near-identical text, so any multi-host cluster
        # is one voice republished.  A lone outlet is one independent voice.
        syndicated = len(hosts) > 1 or _has_release_marker(members)
        clusters.append({
            "cluster_id": cluster_id,
            "source_count": len(members),
            "hosts": hosts,
            "independent": len(members) == 1,
            "syndicated": syndicated,
            "digest": digest,
            "urls": [member["url"] for member in members],
            "note": (
                "one text republished across " + ", ".join(hosts)
                if syndicated
                else "single outlet, distinct text"
            ),
        })
        for member in members:
            by_url[member["canonical"]] = cluster_id
    return {"clusters": clusters, "by_url": by_url}


def _has_release_marker(members: list[dict]) -> bool:
    sample = " ".join(member["text"] for member in members).lower()[:20000]
    return any(marker in sample for marker in RELEASE_MARKERS)


DERIVATIVE_MARKERS = (
    "according to a company announcement",
    "according to the announcement",
    "the company said",
    "the company announced",
    "in a statement",
    "according to the press release",
    "per the announcement",
    "announced today",
    "said in a release",
)


# ---------------------------------------------------------------------------
# Anchor-level corroboration
#
# A narration sentence usually paraphrases its source, so whole-page n-gram
# overlap is the wrong test: it scored a genuine NIST confirmation of an Airia
# claim at 0.006 against a 0.18 threshold.  What carries a fact is its decisive
# anchors - the date, the number, the named entity - so corroboration is decided
# on those, and the page sentence holding them is kept as the supporting excerpt.
# ---------------------------------------------------------------------------

_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|"
    "November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
_DATE_RE = re.compile(rf"\b(?:{_MONTHS})\.?\s+\d{{1,2}},?\s+(20\d{{2}})\b")
_ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_PERCENT_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:%|percent|per cent)(?![\w.])", re.I)
_MEASURE_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:million|billion|thousand|milliseconds|seconds|minutes|"
    r"hours|days|weeks|months|years|fold|x)(?![\w])", re.I)
_VERSION_RE = re.compile(r"\b\d+\.\d+(?:\.\d+)?\b")
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,}(?:\s+[A-Z]{2,})*(?:\s+\d+(?:\.\d+)?)?\b")
_PROPER_RE = re.compile(
    r"\b[A-Z][\w&'.-]*(?:\s+(?:of|and|for|the|to|de|la)\s+[A-Z][\w&'.-]*"
    r"|\s+[A-Z][\w&'.-]*)*"
)

VALUE_KINDS = ("date", "iso_date", "year", "percent", "measure", "version")
# Half a claim is not a confirmation.  Both bars must clear before a page can
# upgrade a claim, and the shortfall is reported instead of being smoothed over.
ENTITY_MIN_COVERAGE = 0.6
KEYWORD_MIN_COVERAGE = 0.6
_ABBREVIATED_MONTHS = {
    "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "May": "May",
    "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September", "Sept": "September",
    "Oct": "October", "Nov": "November", "Dec": "December",
}

_KEYWORD_STOP = frozenset("""
about above after again against all also any are been before being between both called
cannot could does doing down each from have here hers him his into itself just like made
make many more most much must none such than that their them then there these they this
those through too under until very want well were what when where which while whose with
without would being using used use based given going across among because however
""".split())


def _match_key(text: str) -> str:
    """Lowercase, expand "%" and strip punctuation so anchors and pages compare.

    Percent signs are spelled out because a page writing "84%" and a claim
    quoting "84 percent" must still match; stripping the symbol silently lost
    every percentage anchor.
    """
    value = re.sub(r"\s+", " ", str(text or "")).lower()
    value = value.replace("%", " percent ")
    value = re.sub(r"[^a-z0-9 .&/-]", " ", value)
    return re.sub(r"\s{2,}", " ", value).strip()


def _canonical_anchor(kind: str, value: str) -> str:
    """Normalize an anchor so "84%" and "84 percent" compare equal."""
    text = re.sub(r"\s+", " ", str(value or "")).strip().strip(".,;:()\"'”“")
    lowered = text.lower()
    if kind == "date":
        match = re.match(rf"({_MONTHS})\.?\s+(\d{{1,2}}),?\s+(20\d{{2}})", lowered, re.I)
        if match:
            month = _ABBREVIATED_MONTHS.get(match.group(1).title(), match.group(1).title())
            return f"{month} {int(match.group(2))}, {match.group(3)}"
        return lowered
    if kind in {"percent", "measure"}:
        number = re.match(r"(\d+(?:[.,]\d+)?)", lowered)
        if not number:
            return lowered
        unit = re.sub(r"[\d.,\s]+", "", lowered)
        unit = {"pct": "percent", "percentage": "percent", "pc": "percent"}.get(unit, unit)
        if kind == "percent":
            unit = "percent"
        unit = {"bn": "billion", "m": "million"}.get(unit, unit)
        return f"{number.group(1).replace(',', '.')} {unit}".strip()
    if kind == "entity":
        return _match_key(text)
    return lowered


def extract_anchors(text: str) -> list[dict]:
    """Pull the elements a reader would check to decide whether the sentence is true."""
    value = str(text or "")
    found: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, raw: str, decisive: bool) -> None:
        canonical = _canonical_anchor(kind, raw)
        if not canonical or (kind, canonical) in seen:
            return
        seen.add((kind, canonical))
        found.append({"kind": kind, "value": str(raw).strip(),
                      "canonical": canonical, "decisive": decisive})

    for match in _DATE_RE.finditer(value):
        add("date", match.group(0), True)
    for match in _ISO_DATE_RE.finditer(value):
        add("iso_date", match.group(0), True)
    for match in _PERCENT_RE.finditer(value):
        add("percent", match.group(0), True)
    for match in _MEASURE_RE.finditer(value):
        add("measure", match.group(0), True)
    for match in _VERSION_RE.finditer(value):
        add("version", match.group(0), True)
    for match in _YEAR_RE.finditer(value):
        add("year", match.group(0), True)
    entities: list[str] = []
    for pattern in (_PROPER_RE, _ACRONYM_RE):
        for match in pattern.finditer(value):
            token = re.sub(r"\s+", " ", match.group(0)).strip()
            token = re.sub(r"^(?:The|A|An)\s+", "", token, flags=re.I)
            if len(token) < 3:
                continue
            # "January 2023" is a date, not a second subject to be matched twice.
            if token.split()[0].lower() in _MONTH_NAMES and len(token.split()) <= 2:
                continue
            entities.append(token)
    kept: list[str] = []
    for token in sorted(set(entities), key=len, reverse=True):
        # Keep maximal names only: "AI Risk" inside "AI Risk Management Framework"
        # would otherwise demand a second, noisier match.
        lowered = _match_key(token)
        if any(lowered != _match_key(longer)
               and lowered in _match_key(longer) for longer in kept):
            continue
        kept.append(token)
    for token in kept:
        add("entity", token, True)
    for word in re.findall(r"[a-z]{6,}", value):
        if word not in _KEYWORD_STOP:
            add("keyword", word, False)
    return found


def page_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", str(text or ""))
    return [part.strip() for part in parts if part.strip()]


PUBLIC_SUFFIXES = frozenset({
    "gov.uk", "co.uk", "ac.uk", "org.uk", "me.uk", "judiciary.uk",
    "com.au", "net.au", "org.au", "gov.au", "edu.au",
    "co.in", "gov.in", "ac.in", "org.in",
    "co.jp", "or.jp", "ne.jp", "ac.jp", "go.jp",
    "co.nz", "govt.nz", "org.nz", "ac.nz",
    "com.br", "gov.br", "org.br", "edu.br",
    "co.za", "org.za", "gov.za", "ac.za",
    "com.cn", "org.cn", "gov.cn", "net.cn",
})

# Sites that host many unrelated organisations: collapsing their subdomains
# would merge different publishers into one.
MULTI_LABEL_HOSTS = frozenset({
    "github.io", "blogspot.com", "substack.com", "medium.com", "wordpress.com",
    "weebly.com", "wixsite.com", "pages.dev", "workers.dev", "readthedocs.io",
    "googlepages.com", "zendesk.com", "helpscout.com", "notion.site",
})


def registrable_host(host: str) -> str:
    """Reduce a host to the organisation that owns it.

    ``www.nist.gov``, ``airc.nist.gov`` and ``nist.gov`` are one publisher, but
    ``acme.github.io`` and ``other.github.io`` are not: platform hosts keep
    their subdomain so unrelated organisations are never merged.
    """
    value = str(host or "").lower().strip().rstrip(".")
    if not value:
        return ""
    if value.startswith("www."):
        value = value[4:]
    labels = [label for label in value.split(".") if label]
    if len(labels) < 2:
        return value
    tail = ".".join(labels[-2:])
    if tail in MULTI_LABEL_HOSTS:
        return value
    # "metro.co.uk" or "department.gov.uk": the suffix is two labels, so the
    # organisation is the label to the left of it as well.
    if tail in PUBLIC_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return tail


def institution_of(url_or_host: str) -> str:
    """The organisation behind a URL, for independence counting."""
    value = str(url_or_host or "")
    host = urlparse(value).hostname if "://" in value else value
    return registrable_host(host or "")


def same_institution(first: str, second: str) -> bool:
    a, b = institution_of(first), institution_of(second)
    return bool(a) and a == b


_MONTH_NAMES = {name.lower() for name in _MONTHS.split("|")} | {
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct",
    "nov", "dec",
}


def entity_groups(entities: list[dict]) -> list[list[dict]]:
    """Merge entity anchors that name the same thing at different lengths.

    "AI RMF" inside "NIST AI Risk Management Framework" is one subject, not two
    requirements.  Distinct subjects stay separate, which is what makes a
    relationship claim ("as part of the White House AI Action Plan") verifiable
    rather than half-matched.
    """
    ordered = sorted(entities, key=lambda item: len(item["canonical"]), reverse=True)
    groups: list[list[dict]] = []
    for entity in ordered:
        placed = False
        for group in groups:
            head = group[0]["canonical"]
            if entity["canonical"] in head or head in entity["canonical"]:
                group.append(entity)
                placed = True
                break
        if not placed:
            groups.append([entity])
    return groups


def anchor_support(claim_text: str, page_text: str) -> dict:
    """Match a claim's anchors against one page and keep the supporting sentences."""
    anchors = extract_anchors(claim_text)
    decisive = [anchor for anchor in anchors if anchor["decisive"]]
    values = [anchor for anchor in anchors if anchor["kind"] in VALUE_KINDS]
    entities = [anchor for anchor in anchors if anchor["kind"] == "entity"]
    keywords = [anchor for anchor in anchors if anchor["kind"] == "keyword"]
    sentences = page_sentences(page_text)
    sentence_keys = [(_match_key(sentence), sentence) for sentence in sentences]

    matched: list[dict] = []
    missing: list[dict] = []
    excerpts: list[dict] = []
    seen_excerpt: set[str] = set()
    for anchor in anchors:
        hit = next((original for key, original in sentence_keys if anchor["canonical"] in key), None)
        if hit is None:
            missing.append(anchor)
            continue
        matched.append(anchor)
        if hit not in seen_excerpt:
            seen_excerpt.add(hit)
            excerpts.append({"anchor": anchor["value"], "anchor_kind": anchor["kind"],
                             "decisive": bool(anchor["decisive"]), "excerpt": hit[:400]})
    # A decisive sentence is the excerpt worth quoting; keyword-only hits are the
    # fallback when a page confirms the wording but not a number.
    excerpts.sort(key=lambda item: not item["decisive"])

    matched_set = {anchor["kind"] + "|" + anchor["canonical"] for anchor in matched}

    def is_matched(anchor: dict) -> bool:
        return anchor["kind"] + "|" + anchor["canonical"] in matched_set

    matched_decisive = [anchor for anchor in decisive if is_matched(anchor)]
    # Completeness, not best-effort matching.  Every value anchor must appear,
    # every distinct subject must appear, and enough of the predicate must
    # appear.  A page confirming half a claim is partial evidence, never proof of
    # the whole sentence - "the AI RMF is being revised" does not establish that
    # it is being revised *as part of the White House AI Action Plan*.
    value_anchors = [anchor for anchor in decisive if anchor["kind"] != "entity"]
    entity_anchors = [anchor for anchor in decisive if anchor["kind"] == "entity"]
    groups = entity_groups(entity_anchors)
    groups_satisfied = [
        group for group in groups if any(is_matched(anchor) for anchor in group)
    ]
    entity_coverage = (len(groups_satisfied) / len(groups)) if groups else 1.0
    values_ok = all(is_matched(anchor) for anchor in value_anchors)
    missing_values = [anchor["value"] for anchor in value_anchors if not is_matched(anchor)]
    missing_entities = [
        group[0]["value"] for group in groups
        if not any(is_matched(anchor) for anchor in group)
    ]

    conflicts: list[dict] = []
    for anchor in values:
        if is_matched(anchor):
            continue
        # Only a sentence about the same subject can contradict the claim: two
        # dates on one page usually describe two different events.
        primary = max(entities, key=lambda item: len(item["canonical"]), default=None)
        near = [
            sentence for sentence in sentences
            if primary is not None
            and primary["canonical"] in _match_key(sentence)
        ]
        for sentence in near:
            others = [
                other for other in extract_anchors(sentence)
                if other["kind"] == anchor["kind"]
                and other["canonical"] != anchor["canonical"]
                and other["decisive"]
            ]
            if others:
                conflicts.append({"expected": anchor["value"], "found": others[0]["value"],
                                  "kind": anchor["kind"], "excerpt": sentence[:400]})
                break

    keyword_hits = len([anchor for anchor in keywords if is_matched(anchor)])
    keyword_coverage = (keyword_hits / len(keywords)) if keywords else 1.0
    missing_keywords = [anchor["value"] for anchor in keywords if not is_matched(anchor)]

    strong_enough = (
        values_ok
        and entity_coverage >= ENTITY_MIN_COVERAGE
        and keyword_coverage >= KEYWORD_MIN_COVERAGE
        and not conflicts
    )
    if not decisive and not keywords:
        strength = "none"
    elif strong_enough and (decisive or keywords):
        strength = "full"
    elif matched_decisive or keyword_hits:
        strength = "partial"
    else:
        strength = "none"

    return {
        "strength": strength,
        "decisive_total": len(decisive),
        "decisive_matched": len(matched_decisive),
        "entity_groups": len(groups),
        "entity_coverage": round(entity_coverage, 3),
        "keyword_coverage": round(keyword_coverage, 3),
        "missing": [anchor["value"] for anchor in missing],
        "missing_values": missing_values,
        "missing_entities": missing_entities,
        "missing_keywords": missing_keywords[:8],
        "matched": [anchor["value"] for anchor in matched],
        "excerpts": excerpts[:3],
        "conflicts": conflicts[:3],
    }


def independent_confirmations(claim: dict, sources: list[dict], *,
                              clusters: dict | None = None,
                              threshold: float = 0.45) -> dict:
    """How many *distinct* source clusters back a claim's own text.

    A report that merely repeats someone else's statement ("according to the
    announcement") is counted as a derivative, not as confirmation, when the
    claim's own source is a release or a primary announcement.
    """
    clusters = clusters or cluster_sources(sources, threshold=threshold)
    claim_text = str(claim.get("claim") or "")
    own_url = canonical_url(str(claim.get("source_url") or ""))
    own_cluster = clusters["by_url"].get(own_url, "")
    own_source = next(
        (source for source in sources or []
         if canonical_url(str(source.get("url") or "")) == own_url),
        {},
    )
    own_kind = source_type(own_url, str(own_source.get("text") or ""))
    own_is_announcement = own_kind in {"wire", "press_release", "primary", "government"}

    backing: set[str] = set()
    dependent_ids: set[str] = set()
    matches: list[dict] = []
    conflicts: list[dict] = []
    own_host = publisher_of(own_url)
    own_institution = institution_of(own_url)
    for source in sources or []:
        url = canonical_url(str(source.get("url") or ""))
        if not url or url == own_url:
            continue
        body = str(source.get("text") or "")
        support = anchor_support(claim_text, body)
        cluster_id = clusters["by_url"].get(url, "")
        if not cluster_id:
            continue
        host = publisher_of(url)
        institution = institution_of(url)
        derivative = own_is_announcement and any(
            marker in body.lower() for marker in DERIVATIVE_MARKERS)
        matches.append({
            "url": url,
            "cluster_id": cluster_id,
            "publisher": host,
            "institution": institution,
            "strength": support["strength"],
            "dependent": derivative,
            "entity_coverage": support["entity_coverage"],
            "keyword_coverage": support["keyword_coverage"],
            "missing_entities": support["missing_entities"],
            "missing_values": support["missing_values"],
            "matched": [value for value in support["matched"][:8]],
            "missing": [value for value in support["missing"][:8]],
            "excerpts": support["excerpts"],
        })
        if support["conflicts"] and institution and institution != own_institution:
            conflicts.extend(
                dict(item, publisher=host, institution=institution, url=url)
                for item in support["conflicts"][:1]
            )
        if derivative:
            dependent_ids.add(cluster_id)
        elif support["strength"] == "full" and institution and institution != own_institution:
            # Independence is counted per institution: www.nist.gov,
            # airc.nist.gov and nist.gov are one organisation, however many of
            # their pages are fetched.  Only a complete anchor match corroborates.
            backing.add(institution)
    return {
        "own_cluster": own_cluster,
        "own_institution": own_institution,
        "distinct_clusters": len(backing),
        "backing_institutions": sorted(backing),
        # Kept as an alias: the values are institutions, not hosts.  Naming it
        # honestly avoids reading four NIST subpages as four publishers.
        "backing_publishers": sorted(backing),
        "dependent_clusters": len(dependent_ids),
        "conflicts": conflicts[:3],
        "matches": matches[:8],
    }
