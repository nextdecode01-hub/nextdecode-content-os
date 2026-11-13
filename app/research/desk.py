#!/usr/bin/env python3
"""Research desk - reads sources and extracts claims with verification."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

from . import atomic
from . import topics as topic_research

SCRIPT_NAME = "app/research/desk.py"
USER_AGENT = "NextdecodeShortsResearchDesk/1.0"
DEFAULT_TIMEOUT = 25
DEFAULT_MAX_CHARS = 12000
MAX_SOURCES_DEFAULT = 5
MAX_CLAIMS = 14
PER_SOURCE_CLAIM_CAP = 5

# Feed fetchers – placeholders that return empty lists when network access is unavailable.
def _fetch_trends() -> list[dict]:
    """Return a list of candidate items from Google Trends.
    In the sandbox environment network calls are blocked, so this returns an empty list.
    """
    return []

def _fetch_hacker_news() -> list[dict]:
    """Return a list of candidate items from Hacker News.
    Stub implementation – returns empty list.
    """
    return []

def _fetch_reddit(subreddit: str) -> list[dict]:
    """Return a list of candidate items from a Reddit subreddit.
    Stub implementation – returns empty list.
    """
    return []

def _fetch_arxiv() -> list[dict]:
    """Return a list of candidate items from arXiv.
    Stub implementation – returns empty list.
    """
    return []


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._texts = []
        self._skip = False
        self._skip_tags = {"script", "style", "noscript"}
        self.title = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in self._skip_tags:
            self._skip = True
        if tag == "title":
            self._in_title = True
        else:
            self._in_title = getattr(self, "_in_title", False)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._skip_tags:
            self._skip = False
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if getattr(self, "_in_title", False):
            self.title += data
            return
        text = data.strip()
        if text:
            self._texts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._texts)


_BOILERPLATE_PATTERNS = tuple(re.compile(pattern, re.I) for pattern in (
    r"\bskip to (?:main )?(?:content|navigation|search)\b",
    r"\ban official website of the (?:united states|us) government\b",
    r"\bhere'?s how you know\b",
    r"\bofficial websites use \.gov\b",
    r"\ba \.gov website belongs to an official government organization\b[^.]*\.?",
    r"\bsecure \.gov websites use https\b",
    r"\ba lock \([^)]*\)\s*or https:// means\b[^.]*\.?",
    r"\bshare sensitive information only on official,? secure websites\.?",
    r"\ball posts\b",
    r"\bwritten by\b[^.|]{0,60}?\b(?:contributor|guest post|staff|author|senior editor|editor)\b",
    r"\b(?:read|share|subscribe|follow|sign up|log ?in|register)\b[^.]{0,60}",
    r"\brelated (?:articles|posts|stories|content)\b",
    r"\b(?:privacy policy|terms of (?:service|use)|cookie (?:policy|preferences|settings))\b",
    r"\ball rights reserved\b",
    r"\bcopyright\s*(?:©|\(c\))?\s*\d{4}[^.]{0,40}",
    r"\bwas this page helpful\??",
    r"\b\d+ shares?\b",
    r"\b(?:min|minute)s? read\b",
))

# Markers that still mean a leftover navigation fragment.
_BOILERPLATE_MARKERS = (
    "skip to main", "all posts", "written by", "here's how you know",
    "cookie", "subscribe", "related articles", "all rights reserved",
)

# A breadcrumb such as "AI April 25, 2026" sits between the nav bar and the real
# headline, and it blocks the title-echo strip below.
_BREADCRUMB_RE = re.compile(
    r"^\s*(?:[A-Za-z][\w'-]*\s+)?"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\s+",
    re.I,
)


# Navigation and card metadata fused onto the end of a real sentence, because
# ``_sentence_split`` only breaks before a capital letter and the block starts
# with lowercase "governance".  Markers are deliberately multi-word so ordinary
# prose that happens to use one of these words is never treated as furniture.
_TOC_MARKERS = (
    "table of contents",
    "frequently asked questions",
    "faq",
    "key takeaways",
    "on this page",
    "jump to section",
)
_TOC_BREAK_RE = re.compile(
    r"(?=\btable of contents\b)|(?<=\btable of contents\b)|(?=\bfrequently asked questions\b)"
    r"|(?<=\bfrequently asked questions\b)|(?=\bfaq\b)|(?<=\bfaq\b)|(?=\bkey takeaways\b)"
    r"|(?<=\bkey takeaways\b)|(?=\bon this page\b)|(?<=\bon this page\b)"
    r"|(?=\b\d+\s+sections?\b)",
    re.I,
)
_TOC_METADATA_RE = re.compile(r"\b\d+\s+sections?\b", re.I)


def _is_toc_or_metadata(text: str) -> bool:
    """True for a table of contents, an FAQ heading or a card-metadata line."""
    lowered = str(text or "").lower().strip()
    if not lowered:
        return False
    if any(marker in lowered for marker in _TOC_MARKERS):
        return True
    # "governance 7 sections Last updated : March 28, 2026" is card chrome, and
    # the pairing is required so "the report has 7 sections of guidance" survives.
    return bool(_TOC_METADATA_RE.search(lowered)) and "last updated" in lowered


def is_boilerplate(text: str) -> bool:
    """True when a line is page furniture rather than article prose."""
    lowered = str(text or "").lower().strip()
    if not lowered:
        return True
    if any(marker in lowered for marker in _BOILERPLATE_MARKERS):
        return True
    if _is_toc_or_metadata(text):
        return True
    # A fragment that starts mid-sentence ("116-283), the goal of ...") is an
    # extraction artifact rather than a claim.
    if re.match(r"^(?:[\)\.,;]|\d[\d.,\s-]{0,10}\))", str(text or "").strip()):
        return True
    # Government sites interleave the nav bar with the article, so a line built
    # out of menu words is never prose.  Two are required, which keeps ordinary
    # sentences such as "home ownership" intact.
    words = re.findall(r"[a-z][\w'-]*", lowered)
    nav = sum(1 for word in words if word in _NAV_WORDS)
    if nav >= 4 or (nav >= 2 and len(words) < 25):
        return True
    return _looks_like_furniture(str(text or ""))


_NAV_WORDS = frozenset(
    "search menu close home back skip next previous login sign publications topics areas "
    "what we do about contact news events careers publications".split())


def _is_lead_noise(sentence: str) -> bool:
    """Leading page furniture: a leftover banner fragment, a bare URL or a nav run."""
    text = str(sentence or "").strip()
    if not text:
        return True
    if re.fullmatch(r"(?:\.?gov website\.?|https?://\S+)", text, re.I):
        return True
    words = re.findall(r"[A-Za-z][\w'-]*", text)
    if not words:
        return True
    if len(words) <= 8 and sum(1 for word in words if word.lower() in _NAV_WORDS) >= max(2, len(words) // 2):
        return True
    return _looks_like_furniture(text)


def _looks_like_furniture(sentence: str) -> bool:
    """Headline and nav runs are mostly capitalised; prose is not.

    Only the opening 25 words are judged, because a nav bar and an article
    opening are fused into one long unpunctuated run after HTML stripping.
    """
    words = [word for word in re.findall(r"[A-Za-z][\w'-]*", str(sentence or ""))][:25]
    if len(words) < 4:
        return False
    capitalised = sum(1 for word in words if word[:1].isupper())
    return capitalised / len(words) >= 0.6


def clean_article_text(text: str, title: str = "") -> str:
    """Strip navigation, bylines and consent banners before claim extraction.

    ``_strip_html`` concatenates every visible element, so a headline, its
    byline and the nav bar arrive fused into the first "sentence".  Left in, that
    noise became claim 1 of the Phase 10 example.
    """
    value = str(text or "").replace("\u2019", "'").replace("\u2018", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        return ""
    for pattern in _BOILERPLATE_PATTERNS:
        value = pattern.sub(" ", value)
    # Bare URLs are not prose; the ledger records the source URL separately.
    value = re.sub(r"https?://\S+", " ", value)
    value = _BREADCRUMB_RE.sub(" ", value, count=1)
    headline = re.sub(r"\s+", " ", str(title or "")).strip()
    for candidate in (headline, headline.split("|")[0].strip()):
        if not candidate:
            continue
        escaped = re.escape(candidate)
        # The echo can sit behind a leftover category word, so allow a short lead.
        value = re.sub(rf"^\s*(?:[A-Za-z][\w'-]{{1,20}}\s+){{0,2}}{escaped}\s*[:\-|]?\s*",
                       " ", value, count=1, flags=re.I)
    sentences = _sentence_split(value)
    trimmed = 0
    while trimmed < 6 and sentences and _is_lead_noise(sentences[0]):
        sentences.pop(0)
        trimmed += 1
    value = " ".join(sentences) if sentences else value
    # Give the navigation block its own sentence boundaries, then drop it.  A TOC
    # arrives glued to the end of a real sentence, so without this break the
    # whole run - prose and furniture together - becomes one claim.
    value = _TOC_BREAK_RE.sub(". ", f" {value} ").strip()
    sentences = [sentence for sentence in _sentence_split(value)
                 if not _is_toc_or_metadata(sentence) and len(sentence.split()) >= 4]
    value = " ".join(sentences)
    value = re.sub(r"\s*\.\s*(?=\.\s|\Z)", "", value)
    value = re.sub(r"\s{2,}", " ", value)
    return value.strip()


def _strip_html(html: str) -> tuple[str, str]:
    if not html:
        return "", ""
    parser = _HTMLTextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    text = parser.get_text()
    text = re.sub(r"\s+", " ", text).strip()
    return text, parser.title.strip()


def _extract_arxiv_abs(html: str, url: str) -> tuple[str, str, str]:
    text, title = _strip_html(html)
    published = ""
    m = re.search(r'([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})', html)
    if m:
        published = m.group(1)
    m2 = re.search(r'Abstract[^a-zA-Z0-9]+(.{50,800})', html, re.I | re.S)
    if m2:
        cand = re.sub(r"\s+", " ", m2.group(1)).strip()
        if len(cand) > len(text) * 0.1:
            text = cand
    if not title:
        title = text[:80]
    return text, title, published


def fetch_url(url: str, *, timeout: int = DEFAULT_TIMEOUT, max_chars: int = DEFAULT_MAX_CHARS) -> dict:
    """Fetch one public URL.

    A 401/403/406 is retried once with a document-style ``Accept`` header,
    because servers often refuse the HTML-only content negotiation rather than
    the page itself.  That is ordinary negotiation on the same public URL: no
    paywall, login, robots rule or rate limit is worked around.  If the server
    still refuses, the source is reported as ``blocked`` for manual review with
    no text, instead of being dropped silently or filled in from memory.
    """
    result = {
        "url": url,
        "ok": False,
        "status_code": None,
        "title": "",
        "text": "",
        "published": "",
        "publisher": "",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "error": "",
        "blocked": False,
        "manual_review_required": False,
    }
    refusals = (401, 403, 406)
    attempts = (
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "application/pdf,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
    )
    try:
        resp = None
        for accept in attempts:
            resp = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": accept},
                timeout=timeout,
                allow_redirects=True,
            )
            if resp.status_code < 400 or resp.status_code not in refusals:
                break
        result["status_code"] = resp.status_code
        if resp.status_code >= 400:
            result["error"] = f"HTTP {resp.status_code}"
            if resp.status_code in refusals:
                result["error"] = (
                    f"HTTP {resp.status_code} after {len(attempts)} retrieval attempts - "
                    "server refused automated access, manual review required"
                )
                result["blocked"] = True
                result["manual_review_required"] = True
            return result
        content_type = (resp.headers.get("Content-Type", "") or "").lower()
        if content_type and not any(kind in content_type for kind in ("text/html", "application/xhtml", "text/plain", "application/xml", "text/xml")):
            result["error"] = f"unsupported content-type: {content_type.split(';')[0]}"
            if "pdf" in content_type:
                result["error"] += " - PDF is not parsed here, read it manually before citing"
                result["blocked"] = True
                result["manual_review_required"] = True
            return result
        html = resp.text or ""
        parsed = urlparse(url)
        publisher = parsed.netloc
        result["publisher"] = publisher
        if "arxiv.org" in publisher and "/abs/" in url:
            text, title, published = _extract_arxiv_abs(html, url)
            result["title"] = title
            result["text"] = text[:max_chars] if max_chars else text
            result["published"] = published
            result["ok"] = bool(result["text"])
            if not result["ok"]:
                result["error"] = "empty content"
            return result
        text, title = _strip_html(html)
        result["title"] = title
        result["text"] = clean_article_text(text, title)[:max_chars] if max_chars else clean_article_text(text, title)
        result["ok"] = bool(result["text"])
        if not result["ok"]:
            result["error"] = "empty content"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def _sentence_split(text: str) -> list[str]:
    # simple sentence split
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9\(])', text)
    return [p.strip() for p in parts if p.strip()]


def extract_claims(text: str, *, source_url: str, min_quote_words: int = 8) -> list[dict]:
    claims = []
    if not text:
        return claims
    sentences = _sentence_split(text)
    for sent in sentences:
        s = sent.strip()
        if not s:
            continue
        if is_boilerplate(s):
            continue
        # A lowercase start means the splitter caught the tail of a citation or a
        # numbered reference ("116-283), the goal of ..."), not a sentence.
        if s[:1].islower():
            continue
        # must contain concrete technical claim: number or named model/system/metric
        has_number = bool(re.search(r'\b\d+(\.\d+)?%?\b|\b\d+x\b|\bten-fold\b|\bhundred-fold\b|\bthousand-fold\b', s, re.I))
        has_named = bool(re.search(r'\b(GPT|LLM|BERT|Transformer|Claude|Gemini|LLaMA|DeepSeek|model|system|benchmark|F1|accuracy|BLEU|perplexity)\b', s, re.I))
        if not (has_number or has_named):
            continue
        # find verbatim quote - try to find a substring of reasonable length in text
        # look for a chunk that contains the key info
        quote = None
        # try the sentence itself if it's reasonable length
        if len(s.split()) >= min_quote_words:
            # check it's substring
            if s in text:
                quote = s
        if quote is None:
            # try to find a contiguous substring of the sentence in text
            # search for first N words sequence
            words = s.split()
            for length in range(min(len(words), 40), min_quote_words - 1, -1):
                cand = " ".join(words[:length])
                if cand in text:
                    quote = cand
                    break
            if quote is None:
                for start in range(0, max(1, len(words) - min_quote_words + 1)):
                    for length in range(min(len(words) - start, 40), min_quote_words - 1, -1):
                        cand = " ".join(words[start:start + length])
                        if cand in text:
                            quote = cand
                            break
                    if quote:
                        break
        if quote is None or quote not in text:
            continue  # drop if no verbatim quote
        confidence = 0.7
        claims.append({
            "claim": s,
            "quote": quote,
            "source_url": source_url,
            "confidence": confidence,
        })
        # A compound sentence hides which half is unproven, so each clause that
        # survives as a verbatim substring also becomes its own claim record.
        for piece in atomic.split_atomic(s):
            if piece not in text:
                continue
            claims.append({
                "claim": piece,
                "quote": piece,
                "source_url": source_url,
                "confidence": confidence,
                "atomic_of": s,
            })
    return claims


STOPWORDS = frozenset(
    {
        "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with", "is",
        "are", "was", "were", "be", "been", "being", "it", "its", "this", "that", "these",
        "those", "as", "at", "by", "from", "how", "why", "what", "when", "which", "who",
        "not", "no", "can", "will", "would", "should", "could", "if", "so", "than", "then",
        "there", "here", "you", "your", "we", "our", "they", "their", "he", "she", "his",
        "her", "about", "into", "over", "after", "before", "more", "most", "some", "any",
        "using", "use", "used", "bad", "idea", "why", "does", "do", "did", "make", "made",
    }
)


def _topic_terms(topic: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", str(topic or "").lower())
    return {word for word in words if word not in STOPWORDS}


def _topic_anchors(topic: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", str(topic or "").lower())
    anchors = []
    for word in words:
        if word not in STOPWORDS and word not in anchors:
            anchors.append(word)
    return anchors[:2]


def _relevance(topic: str, page: dict) -> float:
    """Share of the topic's distinctive terms that appear in a fetched page."""
    terms = _topic_terms(topic)
    if not terms:
        return 1.0
    haystack = f"{page.get('title', '')} {page.get('text', '')[:4000]}".lower()
    hits = sum(1 for term in terms if term in haystack)
    return hits / len(terms)


def _rank_pages(topic: str, pages: list[dict]) -> list[dict]:
    """Keep pages that contain a leading subject anchor and relevant detail."""
    if not pages:
        return []
    anchors = _topic_anchors(topic)
    scored = []
    for index, page in enumerate(pages):
        haystack = f"{page.get('title', '')} {page.get('text', '')[:4000]}".lower()
        if anchors and not any(anchor in haystack for anchor in anchors):
            continue
        scored.append((_relevance(topic, page), index, page))
    if not scored:
        return []
    scored.sort(key=lambda item: (-item[0], item[1]))
    best = scored[0][0]
    if best <= 0:
        return []
    return [page for score, _, page in scored if score >= max(0.2, best * 0.5)]


def find_contradictions(claims: list[dict]) -> list[dict]:
    """Flag claims that genuinely disagree.

    A contradiction needs three things: two different sources, a shared
    specific entity, and a shared metric whose values or polarity conflict.
    Anything looser produced dozens of false positives on ordinary prose.
    """
    contradictions: list[dict] = []
    if not claims or len(claims) < 2:
        return contradictions

    generic = {
        "the", "this", "that", "these", "those", "model", "models", "system", "systems",
        "task", "tasks", "benchmark", "accuracy", "result", "results", "work", "big",
        "does", "not", "achieves", "reaches", "using", "used", "use", "new", "also",
        "however", "there", "their", "these", "they", "when", "what", "why", "how",
    }

    def entities(claim: dict) -> set[str]:
        found: set[str] = set()
        for match in re.findall(r"\bModel\s+([A-Z][A-Za-z0-9]*)\b", claim.get("claim", "")):
            found.add(match)
        for match in re.findall(r"\b([A-Z][A-Za-z0-9]{2,})\b", claim.get("claim", "")):
            if match.lower() in generic:
                continue
            found.add(match)
        return found

    def metrics(claim: dict) -> set[str]:
        return {
            match.lower()
            for match in re.findall(
                r"\b(F1|accuracy|BLEU|perplexity|error rate|latency|score|precision|recall)\b",
                claim.get("claim", ""),
                re.I,
            )
        }

    negation = re.compile(r"\b(no|not|fails|cannot|never|does not|doesn't|did not|without)\b", re.I)

    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            first, second = claims[i], claims[j]
            if first.get("source_url") == second.get("source_url"):
                continue
            shared_entities = entities(first) & entities(second)
            if not shared_entities:
                continue
            shared_metrics = metrics(first) & metrics(second)
            if not shared_metrics:
                continue
            first_text = first.get("claim", "")
            second_text = second.get("claim", "")
            first_numbers = set(re.findall(r"(\d+(?:\.\d+)?)", first_text))
            second_numbers = set(re.findall(r"(\d+(?:\.\d+)?)", second_text))
            values_conflict = bool(first_numbers and second_numbers and first_numbers != second_numbers)
            polarity_conflict = bool(negation.search(first_text)) != bool(negation.search(second_text))
            if not (values_conflict or polarity_conflict):
                continue
            key = sorted(shared_entities)[0]
            metric = sorted(shared_metrics)[0]
            contradictions.append({
                "claim": first_text,
                "source_a": first.get("source_url", ""),
                "source_b": second.get("source_url", ""),
                "note": f"Conflicting {metric} for {key}",
            })
            if len(contradictions) >= 5:
                return contradictions
    return contradictions


def _normalize_multiplier(s: str) -> str:
    s2 = s.lower()
    # map spelled forms
    mapping = {
        "ten-fold": "10x",
        "tenfold": "10x",
        "hundred-fold": "100x",
        "hundredfold": "100x",
        "thousand-fold": "1000x",
        "thousandfold": "1000x",
        "two-fold": "2x",
        "double": "2x",
        "three-fold": "3x",
        "triple": "3x",
        "four-fold": "4x",
        "five-fold": "5x",
    }
    if s2 in mapping:
        return mapping[s2]
    # 10x form
    m = re.match(r'(\d+(?:\.\d+)?)x', s2)
    if m:
        return f"{m.group(1)}x"
    # digit form like 10 times -> 10x style
    return s2


def find_unsupported_numbers(text: str, source_text: str) -> list[str]:
    if not text:
        return []
    # find numeric/multiplier tokens in text
    tokens = []
    # spelled forms
    for m in re.findall(r'\b(ten-fold|hundred-fold|thousand-fold|two-fold|three-fold|four-fold|five-fold|double|triple|tenfold|hundredfold|thousandfold)\b', text, re.I):
        tokens.append(m)
    # digit forms like 10x, 3.5%
    for m in re.findall(r'\b\d+(?:\.\d+)?x\b|\b\d+(?:\.\d+)?%\b', text, re.I):
        tokens.append(m)
    unsupported = []
    source_norm = source_text.lower() if source_text else ""
    for t in tokens:
        tnorm = _normalize_multiplier(t)
        # check if present in source (either form)
        if tnorm in source_norm:
            continue
        # check original forms
        if t.lower() in source_norm:
            continue
        # check digit form equivalence
        m = re.match(r'(\d+(?:\.\d+)?)x', tnorm)
        if m:
            # look for same number or spelled form
            num = m.group(1)
            if num in source_norm:
                continue
        unsupported.append(t)
    # deduplicate preserving order
    seen = set()
    result = []
    for u in unsupported:
        key = u.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(u)
    return result


def extract_limitations(text: str) -> list[str]:
    if not text:
        return []
    limitations = []
    sentences = _sentence_split(text)
    for sent in sentences:
        s = sent.strip()
        if not s:
            continue
        sl = s.lower()
        if any(k in sl for k in ["caveat", "limitation", "future work", "does not", "do not", "only", "not sufficient", "unclear", "remains unknown"]):
            limitations.append(s)
    return limitations


_FETCHABLE_SCHEMES = {"http", "https"}


def fetchable_url(url: object) -> str:
    """Return the candidate only when it can actually be fetched, else ``""``.

    The desk reads public web pages, so anything that is not an absolute http(s)
    URL - a bare host, ``file:``, ``data:``, ``javascript:`` - is refused here
    instead of reaching the HTTP client, where it would surface as an opaque
    ``requests`` exception.
    """
    value = str(url or "").strip()
    if not value:
        return ""
    try:
        parsed = urlparse(value)
    except ValueError:
        return ""
    if parsed.scheme.lower() not in _FETCHABLE_SCHEMES or not parsed.netloc:
        return ""
    return value


def _dedupe_source_urls(urls: list[str]) -> list[str]:
    """Keep fetchable http(s) URLs and collapse mirrors of the same document.

    Validation happens before de-duplication so a rejected entry can never mask
    an identical accepted one; the caller reports what was dropped.
    """
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        url = fetchable_url(url)
        if not url:
            continue
        match = re.search(r"arxiv\.org/(?:abs|html|pdf)/([^/?#]+)", url, re.I)
        key = f"arxiv:{re.sub(r'v\d+$', '', match.group(1))}" if match else url.split("#")[0].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(url)
    return out


def merge_duplicate_claims(claims: list[dict], *, threshold: float = 0.6) -> list[dict]:
    """Collapse the same fact reported by several pages into one record.

    Two outlets stating one fact produce one claim with two sources.  Counting
    them as two claims would inflate the ledger and fake corroboration.
    """
    from app.research import lineage

    merged: list[dict] = []
    for claim in claims or []:
        text = str(claim.get("claim") or "")
        twin = None
        for existing in merged:
            if lineage.similarity(text, str(existing.get("claim") or ""), size=3) >= threshold:
                twin = existing
                break
        if twin is None:
            record = dict(claim)
            record["also_reported_by"] = []
            merged.append(record)
            continue
        url = str(claim.get("source_url") or "")
        if url and url not in twin["also_reported_by"] and url != twin.get("source_url"):
            twin["also_reported_by"].append(url)
    return merged


def research_topic(topic: str, *, source_urls: list[str] | None = None, max_sources: int = MAX_SOURCES_DEFAULT) -> dict:
    result = {
        "topic": topic,
        "primary": None,
        "secondary": [],
        "claims": [],
        "contradictions": [],
        "unsupported_numbers": [],
        "limitations": [],
        "verdict": "insufficient",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": [],
        "errors": [],
    }
    try:
        urls_to_fetch = []
        if source_urls:
            urls_to_fetch.extend([u for u in source_urls if u])
        else:
            # Search for this exact topic. Deriving URLs from feed discovery
            # pulled unrelated front-page stories into the script.
            try:
                for hit in topic_research.search_web(topic, limit=max_sources * 2):
                    u = hit.get("url")
                    if u and u not in urls_to_fetch:
                        urls_to_fetch.append(u)
            except Exception as e:
                result["errors"].append(f"search_web error: {e}")
        rejected = [str(u) for u in urls_to_fetch if not fetchable_url(u)]
        urls_to_fetch = _dedupe_source_urls(urls_to_fetch)
        if rejected:
            # Dropped candidates are reported, never hidden: a feed or search
            # result that is not a fetchable page is a data-quality failure.
            preview = ", ".join(item[:120] for item in rejected[:5])
            result["errors"].append(
                f"rejected {len(rejected)} non-fetchable candidate URL(s): {preview}")
        if not urls_to_fetch:
            result["errors"].append("no candidate source URLs for topic")
            return result
        fetched_pages = []
        candidates = list(dict.fromkeys(urls_to_fetch))[:max_sources * 2]
        with ThreadPoolExecutor(max_workers=min(6, max(1, len(candidates)))) as pool:
            pages = list(pool.map(fetch_url, candidates))
        for page in pages:
            if len(fetched_pages) >= max_sources:
                break
            if page.get("ok") and page.get("text"):
                fetched_pages.append(page)
                result["sources"].append(page)
            elif page.get("error"):
                result["errors"].append(f"{page.get('url', '')}: {page['error']}")
        if not fetched_pages:
            result["verdict"] = "insufficient"
            return result
        # Keep only the pages that are actually about the topic.
        relevant = _rank_pages(topic, fetched_pages)
        dropped = [page.get("url", "") for page in fetched_pages if page not in relevant]
        if dropped:
            result["errors"].append("dropped off-topic sources: " + ", ".join(dropped))
        fetched_pages = relevant
        result["sources"] = fetched_pages
        if not fetched_pages:
            result["errors"].append(f"no fetched source matched topic anchors: {_topic_anchors(topic)}")
            result["verdict"] = "insufficient"
            return result
        # pick primary - most relevant successful page
        primary = fetched_pages[0]
        result["primary"] = primary
        secondary = []
        primary_host = urlparse(primary.get("url", "")).netloc
        for p in fetched_pages[1:]:
            p_host = urlparse(p.get("url", "")).netloc
            if p_host and p_host != primary_host:
                secondary.append(p)
            elif not secondary:  # if no different domain yet, still add if space
                secondary.append(p)
        # prefer secondary on different domain
        # ensure we only take up to what makes sense
        result["secondary"] = secondary[:2]
        # Extract from every relevant page, not just the first two.  Reading only
        # the primary plus one secondary left all 14 Phase 10 claims attached to a
        # single blog while four NIST pages sat unused in the manifest.
        # Round-robin across sources with a per-page cap, otherwise the longest
        # article fills every slot and the ledger still has one voice.
        per_source: list[list[dict]] = []
        for p in fetched_pages:
            txt = p.get("text", "") or ""
            items = extract_claims(txt, source_url=p.get("url", ""))[:PER_SOURCE_CLAIM_CAP]
            for item in items:
                item["source_published"] = p.get("published", "")
            if items:
                per_source.append(items)
        interleaved: list[dict] = []
        for index in range(max((len(items) for items in per_source), default=0)):
            for items in per_source:
                if index < len(items):
                    interleaved.append(items[index])
        result["claims"] = merge_duplicate_claims(interleaved)[:MAX_CLAIMS]
        # contradictions
        try:
            result["contradictions"] = find_contradictions(result["claims"])
        except Exception as e:
            result["errors"].append(f"contradictions error: {e}")
            result["contradictions"] = []
        # unsupported numbers - the topic's own figures must appear in the sources
        try:
            combined_sources = "\n".join([p.get("text", "") for p in fetched_pages])
            unsupported = find_unsupported_numbers(topic, combined_sources)
            result["unsupported_numbers"] = unsupported
        except Exception as e:
            result["errors"].append(f"unsupported numbers error: {e}")
            result["unsupported_numbers"] = []
        # limitations
        try:
            lims = []
            for p in fetched_pages:
                lims.extend(extract_limitations(p.get("text", "")))
            # deduplicate
            seen = set()
            out_lims = []
            for l in lims:
                k = l.lower()
                if k in seen:
                    continue
                seen.add(k)
                out_lims.append(l)
            result["limitations"] = out_lims
        except Exception as e:
            result["errors"].append(f"limitations error: {e}")
            result["limitations"] = []
        if not result["primary"] or len(result["claims"]) == 0:
            result["verdict"] = "insufficient"
        else:
            result["verdict"] = "sufficient"
        return result
    except Exception as e:
        result["errors"].append(str(e))
        result["verdict"] = "insufficient"
        return result


def render_report(research: dict) -> str:
    lines = []
    lines.append(f"RESEARCH REPORT: {research.get('topic', '')}")
    lines.append(f"Verdict: {research.get('verdict', 'insufficient')}")
    lines.append(f"Fetched: {research.get('fetched_at', '')}")
    lines.append("")
    primary = research.get("primary")
    if primary:
        lines.append(f"PRIMARY: {primary.get('url')} [{primary.get('publisher','')}]")
        if primary.get("title"):
            lines.append(f"  Title: {primary.get('title')}")
    else:
        lines.append("PRIMARY: None")
    lines.append("")
    secondary = research.get("secondary") or []
    if secondary:
        lines.append(f"SECONDARY ({len(secondary)}):")
        for s in secondary:
            lines.append(f"  - {s.get('url')} [{s.get('publisher','')}]")
    else:
        lines.append("SECONDARY: None")
    lines.append("")
    claims = research.get("claims") or []
    lines.append(f"CLAIMS ({len(claims)}):")
    for i, c in enumerate(claims, 1):
        lines.append(f"  {i}. {c.get('claim')}")
        q = c.get("quote", "")
        if q:
            lines.append(f"     Quote: {q}")
    lines.append("")
    contradictions = research.get("contradictions") or []
    lines.append(f"CONTRADICTIONS ({len(contradictions)}):")
    if not contradictions:
        lines.append("  None")
    else:
        for i, c in enumerate(contradictions, 1):
            lines.append(f"  {i}. {c.get('note')}")
            lines.append(f"     A: {c.get('source_a')} | B: {c.get('source_b')}")
    lines.append("")
    unsupported = research.get("unsupported_numbers") or []
    lines.append(f"UNSUPPORTED NUMBERS ({len(unsupported)}):")
    if not unsupported:
        lines.append("  None")
    else:
        for u in unsupported:
            lines.append(f"  - {u}")
    lines.append("")
    limitations = research.get("limitations") or []
    lines.append(f"LIMITATIONS ({len(limitations)}):")
    if not limitations:
        lines.append("  None")
    else:
        for l in limitations:
            lines.append(f"  - {l}")
    lines.append("")
    errors = research.get("errors") or []
    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for e in errors:
            lines.append(f"  - {e}")
    return "\n".join(lines)


def bundle_topic_and_research(mode: str = "normal") -> dict:
    """Pick the highest‑ranked daily topic, fetch the article, extract claims, and return a JSON bundle.

    The function now supports a retry loop: it will attempt up to ``MAX_RETRIES`` times to find a
    candidate whose ``rank`` meets ``MIN_RANK`` (both configurable via environment variables).  If
    ``mode`` is ``"viral-hook"`` an additional ``viral_hook`` field is added to the output when the
    selected candidate contains a ``viral_hook`` key.
    """
    import os
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    min_rank = float(os.getenv("MIN_RANK", "0"))
    attempts = 0
    while attempts < max_retries:
        attempts += 1
        # Gather candidates from all feeds
        candidates = (
            _fetch_trends()
            + _fetch_hacker_news()
            + _fetch_reddit("technology")
            + _fetch_arxiv()
        )
        if not candidates:
            return {"error": "no candidates found"}
        # Choose the entry with the highest rank
        best = max(candidates, key=lambda itm: itm.get("rank", 0))
        if best.get("rank", 0) < min_rank:
            # Not good enough, try again
            continue
        chosen_url = best.get("url")
        # Pull the full article (HTML → plain text)
        article = fetch_url(chosen_url)
        # Extract claims using the existing routine
        claims = extract_claims(
            article.get("text", ""),
            source_url=chosen_url,
            min_quote_words=8,
        )
        # Assemble the bundle
        bundle = {
            "topic": best.get("title", ""),
            "source": best.get("source", ""),
            "url": chosen_url,
            "title": article.get("title", ""),
            "published": article.get("published", ""),
            "claims": claims,
        }
        if mode == "viral-hook" and best.get("viral_hook"):
            bundle["viral_hook"] = best["viral_hook"]
        return bundle
    # If we exit the loop without a suitable candidate
    return {"error": "no suitable candidate found after retries"}

    """Pick the highest‑ranked daily topic, fetch the article,
    extract claims, and return a ready‑to‑use JSON bundle.

    Output schema:
    {
        "topic": str,
        "source": str,
        "url": str,
        "title": str,
        "published": str,
        "claims": [
            {
                "claim": str,
                "quote": str,
                "confidence": float,
                "source_url": str,
                "published": str
            },
            ...
        ]
    }
    """
    # Gather candidates from all feeds
    candidates = (
        _fetch_trends()
        + _fetch_hacker_news()
        + _fetch_reddit("technology")
        + _fetch_arxiv()
    )
    if not candidates:
        return {"error": "no candidates found"}

    # Choose the entry with the highest rank
    best = max(candidates, key=lambda itm: itm.get("rank", 0))
    chosen_url = best.get("url")

    # Pull the full article (HTML → plain text)
    article = fetch_url(chosen_url)

    # Extract claims using the existing routine
    claims = extract_claims(
        article.get("text", ""),
        source_url=chosen_url,
        min_quote_words=8,
    )

    # Assemble the bundle
    return {
        "topic": best.get("title", ""),
        "source": best.get("source", ""),
        "url": chosen_url,
        "title": article.get("title", ""),
        "published": article.get("published", ""),
        "claims": claims,
    }



def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Research Desk CLI")
    parser.add_argument("--mode", choices=["normal", "viral-hook"], default="normal", help="Select operation mode: normal or viral-hook")
    parser.add_argument("--bundle", action="store_true", help="Output a JSON bundle of the best topic and extracted claims")

    parser.add_argument("topic", nargs="?", help="Topic to research")
    parser.add_argument("--urls", nargs="*", default=None, help="Source URLs")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)
    if not args.topic and not args.bundle:
        parser.print_help()
        return 1
    if args.bundle:
        print(json.dumps(bundle_topic_and_research(args.mode), indent=2))
        return 0
    research = research_topic(args.topic, source_urls=args.urls if args.urls else None)
    if args.json:
        print(json.dumps(research, indent=2))
    else:
        print(render_report(research))
    if research.get("verdict") == "insufficient":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
