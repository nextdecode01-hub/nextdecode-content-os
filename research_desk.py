#!/usr/bin/env python3
"""Research desk - reads sources and extracts claims with verification."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import quote_plus, urlparse

import requests

import topic_research

SCRIPT_NAME = "research_desk.py"
USER_AGENT = "NextdecodeShortsResearchDesk/1.0"
DEFAULT_TIMEOUT = 25
DEFAULT_MAX_CHARS = 12000
MAX_SOURCES_DEFAULT = 5
MAX_CLAIMS = 14


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
    result = {
        "url": url,
        "ok": False,
        "status_code": None,
        "title": "",
        "text": "",
        "published": "",
        "publisher": "",
        "error": "",
    }
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=timeout,
            allow_redirects=True,
        )
        result["status_code"] = resp.status_code
        content_type = resp.headers.get("Content-Type", "")
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
        result["text"] = text[:max_chars] if max_chars else text
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


def _build_arxiv_search_url(topic: str) -> str:
    q = quote_plus(f"all:{topic}")
    return f"https://export.arxiv.org/api/query?search_query={q}&sortBy=relevance&sortOrder=descending&max_results=5"


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
            # derive from discover_topics and build arxiv search URL
            try:
                candidates = topic_research.discover_topics(limit=10)
                for c in candidates:
                    u = c.get("url") or c.get("source_url")
                    if u and u not in urls_to_fetch:
                        urls_to_fetch.append(u)
            except Exception as e:
                result["errors"].append(f"discover_topics error: {e}")
            arxiv_url = _build_arxiv_search_url(topic)
            if arxiv_url not in urls_to_fetch:
                urls_to_fetch.append(arxiv_url)
        fetched_pages = []
        for url in urls_to_fetch[:max_sources * 2]:  # allow some slack
            if len(fetched_pages) >= max_sources:
                break
            page = fetch_url(url)
            if page.get("ok") and page.get("text"):
                fetched_pages.append(page)
                result["sources"].append(page)
            else:
                if page.get("error"):
                    result["errors"].append(f"{url}: {page['error']}")
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
        # extract claims from the primary source and at most one independent secondary
        claim_sources = [primary] + result["secondary"][:1]
        all_claims = []
        for p in claim_sources:
            txt = p.get("text", "") or ""
            all_claims.extend(extract_claims(txt, source_url=p.get("url", "")))
        result["claims"] = all_claims[:MAX_CLAIMS]
        # contradictions
        try:
            result["contradictions"] = find_contradictions(result["claims"])
        except Exception as e:
            result["errors"].append(f"contradictions error: {e}")
            result["contradictions"] = []
        # unsupported numbers - the topic's own figures must appear in the sources
        try:
            combined_sources = "\n".join([p.get("text", "") for p in claim_sources])
            unsupported = find_unsupported_numbers(topic, combined_sources)
            result["unsupported_numbers"] = unsupported
        except Exception as e:
            result["errors"].append(f"unsupported numbers error: {e}")
            result["unsupported_numbers"] = []
        # limitations
        try:
            lims = []
            for p in claim_sources:
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Research desk")
    parser.add_argument("topic", nargs="?", help="Topic to research")
    parser.add_argument("--urls", nargs="*", default=None, help="Source URLs")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)
    if not args.topic:
        parser.print_help()
        return 1
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
