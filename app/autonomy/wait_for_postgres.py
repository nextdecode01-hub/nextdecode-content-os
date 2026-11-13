"""Deadline-bounded readiness probe for the local autonomy PostgreSQL runtime."""
from __future__ import annotations

import math
import os
import sys
import time

import psycopg


def _positive_setting(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive number") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


def main() -> int:
    dsn = os.environ.get("DATABASE_URL", "").strip()
    if not dsn:
        print("DATABASE_URL is required for PostgreSQL readiness", file=sys.stderr)
        return 2
    try:
        timeout_seconds = _positive_setting("WAIT_FOR_POSTGRES_TIMEOUT_SECONDS", 90.0)
        connect_timeout = _positive_setting("WAIT_FOR_POSTGRES_CONNECT_TIMEOUT_SECONDS", 2.0)
        retry_interval = _positive_setting("WAIT_FOR_POSTGRES_RETRY_INTERVAL_SECONDS", 1.0)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        attempt_timeout = max(1, math.ceil(min(connect_timeout, remaining)))
        try:
            with psycopg.connect(dsn, connect_timeout=attempt_timeout) as connection:
                connection.execute("SELECT 1")
            return 0
        except psycopg.OperationalError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(retry_interval, remaining))

    print(f"PostgreSQL did not become ready within {timeout_seconds:g} seconds", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
