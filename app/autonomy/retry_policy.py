"""Shared bounded retry scheduling for the local autonomy runtime."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

BASE_DELAY_SECONDS = 5
MAX_DELAY_SECONDS = 300

def retry_delay_seconds(attempt: int) -> int:
    """Return bounded exponential delay for the completed attempt (1-based)."""
    number = max(1, int(attempt))
    return min(MAX_DELAY_SECONDS, BASE_DELAY_SECONDS * (2 ** min(number - 1, 16)))

def retry_not_before(attempt: int, now: datetime | None = None) -> tuple[str, int]:
    """Return the UTC eligibility timestamp and delay for an attempt retry."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("retry scheduling requires a timezone-aware datetime")
    delay = retry_delay_seconds(attempt)
    return (current.astimezone(timezone.utc) + timedelta(seconds=delay)).isoformat(), delay
