"""Lightweight daily topic research for Nextdecode. All feeds are best-effort."""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
HEADERS = {"User-Agent": "NextdecodeShortsStudio/1.0 (daily topic research)"}
TECH_TERMS = re.compile(
    r"\b(ai|artificial intelligence|machine learning|robot|robotics|startup|technology|tech|"
    r"chip|semiconductor|quantum|space|nasa|computer|software|open source|cyber|data center|"
    r"model|llm|neural|battery|electric vehicle|autonomous|biotech|future|research|science)\b",
    re.I,
)
ATOM = "{http://www.w3.org/2005/Atom}"


def _get(url: str, **kwargs):
    return requests.get(url, headers=HEADERS, timeout=12, **kwargs)


def _item(title: str, summary: str, source: str, url: str, published: str = "", score: float = 0):
    title = re.sub(r"\s+", " ", (title or "")).strip()
    summary = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", summary or "")).strip()
    if not title or not url:
        return None
    title_relevance = len(TECH_TERMS.findall(title))
    source_relevance = {"Google Trends": 4, "Hacker News": 3, "Reddit": 2, "arXiv": 2}.get(source, 0)
    summary_relevance = min(3, len(TECH_TERMS.findall(summary)))
    try:
        if published.isdigit():
            published_at = datetime.fromtimestamp(float(published), timezone.utc)
        else:
            try:
                published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except ValueError:
                published_at = parsedate_to_datetime(published)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_days = max(
            0.0,
            (datetime.now(timezone.utc) - published_at.astimezone(timezone.utc)).total_seconds() / 86400,
        )
        freshness = max(0.0, 6.0 - age_days / 5)
    except (TypeError, ValueError, OverflowError):
        freshness = 0.0
    engagement = min(12.0, math.log1p(max(0.0, float(score))) * 1.5)
    rank = title_relevance * 4 + summary_relevance + source_relevance + freshness + engagement
    return {
        "title": title[:240], "summary": summary[:700], "source": source,
        "url": url, "published": published, "score": float(score),
        "rank": round(rank, 2),
        "signals": {
            "title_relevance": title_relevance,
            "source_relevance": source_relevance,
            "summary_relevance": summary_relevance,
            "freshness": round(freshness, 2),
            "engagement": round(engagement, 2),
        },
    }


def _fetch_hacker_news():
    ids = _get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:24]
    out = []
    def fetch(story_id):
        data = _get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json").json()
        if not data or data.get("dead") or data.get("deleted"):
            return None
        return _item(data.get("title"), "", "Hacker News", data.get("url") or f"https://news.ycombinator.com/item?id={story_id}", str(data.get("time", "")), data.get("score", 0))
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch, item_id) for item_id in ids]
        for future in as_completed(futures):
            try:
                found = future.result()
                if found and found["rank"] >= 5:
                    out.append(found)
            except Exception:
                continue
    return out


def _fetch_arxiv():
    query = "cat:cs.AI OR cat:cs.CL OR cat:cs.CV OR cat:cs.LG"
    url = "https://export.arxiv.org/api/query?" + urlencode({"search_query": query, "sortBy": "submittedDate", "sortOrder": "descending", "max_results": 12})
    root = ET.fromstring(_get(url).text)
    out = []
    for entry in root.findall(f"{ATOM}entry"):
        title = entry.findtext(f"{ATOM}title", default="").strip()
        summary = entry.findtext(f"{ATOM}summary", default="").strip()
        link = next((node.attrib.get("href", "") for node in entry.findall(f"{ATOM}link") if node.attrib.get("rel") == "alternate"), "")
        published = entry.findtext(f"{ATOM}published", default="")
        found = _item(title, summary, "arXiv", link, published, 0)
        if found:
            out.append(found)
    return out


def _fetch_reddit(subreddit: str):
    url = f"https://www.reddit.com/r/{subreddit}/.rss?limit=15"
    root = ET.fromstring(_get(url).text)
    out = []
    for entry in root.findall(f"{ATOM}entry"):
        title = entry.findtext(f"{ATOM}title", default="").strip()
        summary = entry.findtext(f"{ATOM}content", default="").strip()
        link = next((node.attrib.get("href", "") for node in entry.findall(f"{ATOM}link") if node.attrib.get("rel") == "alternate"), "")
        published = entry.findtext(f"{ATOM}updated", default="")
        found = _item(title, summary, "Reddit", link, published, 0)
        if found and found["rank"] >= 5:
            out.append(found)
    return out


def _fetch_trends():
    # Google exposes a Trends API in limited preview; the public RSS feed is an optional fallback.
    url = "https://trends.google.com/trending/rss?geo=IN"
    root = ET.fromstring(_get(url).text)
    out = []
    for entry in root.findall(".//item"):
        title = entry.findtext("title", default="").strip()
        description = entry.findtext("description", default="").strip()
        link = entry.findtext("link", default="").strip()
        found = _item(title, description, "Google Trends", link, entry.findtext("pubDate", default=""), 0)
        if found and found["rank"] >= 5:
            out.append(found)
    return out


def search_related_news(query: str, limit: int = 8) -> list[dict]:
    """Find recent publisher coverage for one selected research topic."""
    url = "https://news.google.com/rss/search?" + urlencode({
        "q": query[:120],
        "hl": "en-IN",
        "gl": "IN",
        "ceid": "IN:en",
    })
    root = ET.fromstring(_get(url).text)
    out = []
    for entry in root.findall(".//item"):
        title = entry.findtext("title", default="").strip()
        summary = entry.findtext("description", default="").strip()
        link = entry.findtext("link", default="").strip()
        published = entry.findtext("pubDate", default="")
        publisher = entry.findtext("source", default="").strip()
        found = _item(title, summary, "Google News", link, published, 0)
        if found:
            found["publisher"] = publisher
            out.append(found)
    return sorted(out, key=lambda item: (item["rank"], item["published"]), reverse=True)[:limit]


def _recent_titles(path: Path):
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()][-100:]


def discover_topics(used_topics_file: Path | None = None, limit: int = 6):
    """Collect current AI/tech angles; one failed source never blocks other sources."""
    used = _recent_titles(used_topics_file or (SCRIPT_DIR / "used_topics.txt"))
    jobs = [_fetch_hacker_news, _fetch_arxiv, _fetch_trends]
    jobs.extend(lambda name=name: _fetch_reddit(name) for name in ("technology", "MachineLearning", "artificial"))
    collected = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(job) for job in jobs]
        for future in as_completed(futures):
            try:
                collected.extend(future.result())
            except Exception:
                continue
    unique = {}
    for entry in collected:
        norm = re.sub(r"[^a-z0-9]+", " ", entry["title"].lower()).strip()
        if not norm or any(SequenceMatcher(None, norm, re.sub(r"[^a-z0-9]+", " ", old.lower()).strip()).ratio() >= 0.76 for old in used):
            continue
        if norm not in unique or entry["rank"] > unique[norm]["rank"]:
            unique[norm] = entry
    ranked = sorted(unique.values(), key=lambda item: (item["rank"], item["published"]), reverse=True)
    return ranked[:limit]
