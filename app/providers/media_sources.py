"""Free-first media discovery adapters for Coverr and Openverse."""
from __future__ import annotations
import os, re, requests
from typing import Any

_COVERR_TIMEOUT = (3, 10)
_OPENVERSE_TIMEOUT = (5, 20)
_COVERR = "https://api.coverr.co"
_OPENVERSE = "https://api.openverse.org/v1"

def _clean(value: Any, limit: int = 500) -> str:
    return re.sub(r"\\s+", " ", str(value or "")).strip()[:limit]

def search_coverr_videos(query: str, *, limit: int = 8, orientation: str | None = None) -> list[dict]:
    """Search Coverr stock video; free/demo key is limited to 50 calls/hour."""
    key = os.getenv("COVERR_API_KEY", "").strip()
    if not key or not _clean(query, 200): return []
    params = {"query": _clean(query, 200), "page_size": max(1, min(int(limit), 20))}
    if orientation in {"vertical", "horizontal", "square"}: params["orientation"] = orientation
    r = requests.get(f"{_COVERR}/videos", params=params, headers={"x-api-key": key}, timeout=_COVERR_TIMEOUT)
    r.raise_for_status()
    payload = r.json()
    raw = payload.get("hits") or payload.get("videos") or payload.get("data") or []
    out = []
    for x in raw:
        if not isinstance(x, dict): continue
        out.append({"provider":"coverr","id":_clean(x.get("id") or x.get("video_id"),120),
            "title":_clean(x.get("title") or x.get("name")),"description":_clean(x.get("description")),
            "tags":x.get("tags") if isinstance(x.get("tags"),list) else [],
            "duration":x.get("duration"),"width":x.get("width"),"height":x.get("height"),
            "preview_url":x.get("thumbnail") or x.get("thumbnail_url") or x.get("preview_url"),
            "download_url":x.get("download_url") or x.get("url") or x.get("video_url"),
            "source_url":x.get("page_url") or x.get("url"),"license":"Coverr API terms; verify current item terms",
            "attribution_required":True})
    return out[:max(1,min(int(limit),20))]

def search_openverse_images(query: str, *, limit: int = 10) -> list[dict]:
    """Search openly licensed images; preserve per-item license and attribution."""
    if not _clean(query,200): return []
    params={"q":_clean(query,200),"page_size":max(1,min(int(limit),20)),"mature":"false","filter_dead":"true"}
    r=requests.get(f"{_OPENVERSE}/images/",params=params,timeout=_OPENVERSE_TIMEOUT,
                   headers={"User-Agent":"NEXTDECODE-ContentOS/1.0"})
    r.raise_for_status()
    out=[]
    for x in r.json().get("results",[]):
        if not isinstance(x,dict): continue
        lic=_clean(x.get("license"),40).lower()
        out.append({"provider":"openverse","id":_clean(x.get("id"),120),"title":_clean(x.get("title")),
            "creator":_clean(x.get("creator")),"creator_url":x.get("creator_url"),
            "media_url":x.get("url"),"thumbnail_url":x.get("thumbnail"),
            "source_url":x.get("foreign_landing_url"),"license":lic,
            "license_version":_clean(x.get("license_version"),40),"license_url":x.get("license_url"),
            "attribution":_clean(x.get("attribution"),1000),"width":x.get("width"),"height":x.get("height"),
            "mature":bool(x.get("mature")),"commercial_use":lic in {"cc0","pdm","by","by-sa"},
            "requires_attribution":lic not in {"cc0","pdm"},"license_review_required":True})
    return out
