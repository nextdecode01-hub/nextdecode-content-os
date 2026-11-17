"""Free, key-free image sourcing for short-form shots.

Stock video APIs (Coverr, Pixabay) need an account and the AI image providers on
this project are quota-limited, which left the renderer falling back to flat
gradients.  Wikimedia Commons serves freely licensed photographs and diagrams
through an open API that needs no key, so it is used as the reliable real-image
source.

Every asset records its licence, author, and file page so the published video
can carry proper attribution.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "NextdecodeShortsBot/1.0 (automated short-form video pipeline)"
MIN_WIDTH = 640
MIN_HEIGHT = 480
DOWNLOAD_TIMEOUT = 45
SEARCH_TIMEOUT = 20
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache" / "wikimedia"
CACHE_TTL_SECONDS = 24 * 60 * 60

QUERY_STOPWORDS = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "into", "are", "was",
    "were", "has", "have", "had", "not", "but", "you", "your", "our", "their",
    "they", "its", "why", "how", "what", "when", "which", "who", "does", "did",
    "can", "will", "would", "should", "could", "using", "use", "used", "about",
    "illustrating", "point", "line", "context", "close", "alternate", "angle",
    "diagram", "explanation", "summary", "scene", "shot", "wide", "detail",
})


def _term_stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


def _query_terms(query: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", str(query or "").lower())
    terms = []
    for word in words:
        if len(word) < 3 or word in QUERY_STOPWORDS:
            continue
        stem = _term_stem(word)
        if stem not in terms:
            terms.append(stem)
    return terms


def _query_match(item: dict, query: str) -> bool:
    terms = _query_terms(query)
    if not terms:
        return False
    metadata = " ".join(str(item.get(key) or "") for key in ("title", "object_name", "description"))
    metadata_terms = {
        _term_stem(word)
        for word in re.findall(r"[a-z0-9]+", metadata.lower())
    }
    matches = sum(1 for term in terms if term in metadata_terms)
    if len(terms) == 1:
        return matches == 1
    # At least two meaningful subject terms must be present; generic one-word
    # overlap is not enough to select a Wikimedia still for this beat.
    return matches >= 2 and matches / len(terms) >= 0.6


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def search_images(query: str, *, limit: int = 6, min_width: int = MIN_WIDTH,
                  min_height: int = MIN_HEIGHT) -> list[dict]:
    """Search Wikimedia Commons for usable stills.

    Returns a list of dicts with ``url``, ``thumb_url``, ``title``, ``width``,
    ``height``, ``license``, ``author``, ``license_url`` and ``page_url``.
    """
    cleaned = re.sub(r"[^\w\s-]", " ", str(query or "")).strip()
    if len(cleaned) < 3:
        return []
    searches = [f'filetype:bitmap "{cleaned}"'] if " " in cleaned else []
    searches.append(f"filetype:bitmap {cleaned}")

    pages: dict[str, dict] = {}
    for search in searches:
        for page in _cached_search_pages(search, limit=limit):
            if page["width"] < min_width or page["height"] < min_height:
                continue
            pages.setdefault(page.get("title", ""), page)
        if pages:
            break
    results = list(pages.values())
    results.sort(key=_score, reverse=True)
    return results[:limit]


def _search_pages(search: str, *, limit: int) -> list[dict]:
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search,
        "gsrnamespace": 6,
        "gsrlimit": max(1, int(limit)),
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|mime",
        "iiurlwidth": 1200,
        "format": "json",
    }
    url = f"{COMMONS_API}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=SEARCH_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []

    pages = (payload.get("query") or {}).get("pages") or {}
    results: list[dict] = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        mime = str(info.get("mime") or "")
        if mime and not mime.startswith("image/"):
            continue
        width = int(info.get("width") or 0)
        height = int(info.get("height") or 0)
        meta = info.get("extmetadata") or {}
        results.append({
            "title": str(page.get("title", "")),
            "object_name": _strip_html((meta.get("ObjectName") or {}).get("value", ""))[:180],
            "description": _strip_html((meta.get("ImageDescription") or {}).get("value", ""))[:600],
            "url": str(info.get("url") or ""),
            "thumb_url": str(info.get("thumburl") or info.get("url") or ""),
            "descriptionurl": str(info.get("descriptionurl") or ""),
            "width": width,
            "height": height,
            "license": _strip_html((meta.get("LicenseShortName") or {}).get("value", "")),
            "license_url": _strip_html((meta.get("LicenseUrl") or {}).get("value", "")),
            "author": _strip_html((meta.get("Artist") or {}).get("value", ""))[:120],
            "credit": _strip_html((meta.get("Credit") or {}).get("value", ""))[:160],
        })
    return results


def _cached_search_pages(search: str, *, limit: int) -> list[dict]:
    normalized = " ".join(str(search or "").lower().split())
    digest = hashlib.sha256(f"wikimedia-search-v1:{normalized}:{int(limit)}".encode("utf-8")).hexdigest()[:20]
    cache_path = CACHE_DIR / f"{digest}.json"
    try:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if time.time() - float(cached.get("fetched_at", 0)) < CACHE_TTL_SECONDS:
            return list(cached.get("results") or [])
    except (OSError, ValueError, TypeError):
        pass
    results = _search_pages(search, limit=limit)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"fetched_at": time.time(), "query": normalized, "results": results}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass
    return results


def _score(item: dict) -> tuple:
    width = int(item.get("width") or 0)
    height = int(item.get("height") or 0)
    if width <= 0 or height <= 0:
        return (0, 0)
    ratio = width / height
    portrait = 1 if ratio < 1.0 else 0
    vertical_fit = 1 if 0.45 <= ratio <= 0.85 else 0
    resolution = min(width, 1920) / 1920
    return (portrait + vertical_fit, resolution)


def download_image(url: str, out_path: Path) -> Path | None:
    """Download one image to disk. Returns None on failure."""
    if not url:
        return None
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
            payload = response.read()
    except Exception:
        return None
    if len(payload) < 8_000:
        return None
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return out


def fetch_shot_image(query: str, work_dir: Path, *, index: int = 0,
                      used_titles: set[str] | None = None,
                      extra_queries: list[str] | None = None) -> dict[str, Any] | None:
    """Fetch a query-matched, previously unused still instead of a generic fallback."""
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    attempts: list[str] = []
    for candidate in list(extra_queries or []) + [query]:
        candidate = str(candidate or "").strip()
        if candidate and candidate not in attempts:
            attempts.append(candidate)
    used = used_titles if used_titles is not None else set()
    for candidate in attempts:
        hits = search_images(candidate, limit=8)
        for chosen in hits:
            if chosen["title"] in used or not _query_match(chosen, candidate):
                continue
            suffix = ".jpg" if ".jpg" in chosen["url"].lower() else ".png"
            out = work / f"wikimedia_{int(index):03d}{suffix}"
            if not download_image(chosen["thumb_url"] or chosen["url"], out):
                continue
            return {
                "path": str(out),
                "provider": "wikimedia",
                "title": chosen["title"],
                "object_name": chosen.get("object_name", ""),
                "description": chosen.get("description", ""),
                "license": chosen["license"],
                "license_url": chosen["license_url"],
                "author": chosen["author"],
                "credit": chosen["credit"],
                "page_url": chosen["descriptionurl"],
                "source_url": chosen["url"],
                "width": chosen["width"],
                "height": chosen["height"],
                "query": candidate,
                "query_matched": True,
            }
    return None


def credit_lines(assets: list[dict]) -> list[str]:
    """Human-readable attribution lines for the used assets."""
    lines: list[str] = []
    for asset in assets or []:
        if not isinstance(asset, dict):
            continue
        title = str(asset.get("title", "")).replace("File:", "").strip()
        author = str(asset.get("author", "")).strip()
        licence = str(asset.get("license", "")).strip()
        page = str(asset.get("page_url", "")).strip()
        if not title:
            continue
        parts = [title]
        if author:
            parts.append(f"by {author}")
        if licence:
            parts.append(f"({licence})")
        line = " — ".join(parts)
        if page:
            line = f"{line} — {page}"
        lines.append(line)
    return lines
