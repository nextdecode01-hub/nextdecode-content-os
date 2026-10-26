"""Helpers for binding an owner approval to the exact generated files."""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def approved_today(approved_at: object, now: datetime | None = None) -> bool:
    if not isinstance(approved_at, str):
        return False
    try:
        timestamp = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if timestamp.tzinfo is None:
        return False
    current = now or datetime.now(IST)
    approved_local = timestamp.astimezone(IST)
    current_local = current.astimezone(IST)
    return approved_local.date() == current_local.date() and approved_local <= current_local


def upload_window_open(now: datetime | None = None) -> bool:
    current = now or datetime.now(IST)
    if current.tzinfo is None:
        return False
    current_local = current.astimezone(IST)
    return current_local.hour == 20
