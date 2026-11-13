from __future__ import annotations

import psycopg

from app.autonomy import wait_for_postgres


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _query):
        return None


def test_probe_returns_success_when_database_is_ready(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    calls = []

    def connect(dsn, *, connect_timeout):
        calls.append((dsn, connect_timeout))
        return _Connection()

    monkeypatch.setattr(wait_for_postgres.psycopg, "connect", connect)
    assert wait_for_postgres.main() == 0
    assert calls == [("postgresql://example.invalid/db", 2)]


def test_probe_uses_elapsed_deadline_and_retries(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    monkeypatch.setenv("WAIT_FOR_POSTGRES_TIMEOUT_SECONDS", "2")
    monkeypatch.setenv("WAIT_FOR_POSTGRES_CONNECT_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WAIT_FOR_POSTGRES_RETRY_INTERVAL_SECONDS", "1")
    clock = [0.0]
    calls = []

    def connect(_dsn, *, connect_timeout):
        calls.append(connect_timeout)
        raise psycopg.OperationalError("not ready")

    monkeypatch.setattr(wait_for_postgres.psycopg, "connect", connect)
    monkeypatch.setattr(wait_for_postgres.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        wait_for_postgres.time,
        "sleep",
        lambda delay: clock.__setitem__(0, clock[0] + delay),
    )
    assert wait_for_postgres.main() == 1
    assert calls == [1, 1]
    assert clock[0] == 2.0


def test_probe_fails_closed_for_invalid_timeout(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    monkeypatch.setenv("WAIT_FOR_POSTGRES_TIMEOUT_SECONDS", "0")
    assert wait_for_postgres.main() == 2
    assert "WAIT_FOR_POSTGRES_TIMEOUT_SECONDS" in capsys.readouterr().err


def test_probe_requires_database_url(monkeypatch, capsys):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert wait_for_postgres.main() == 2
    assert "DATABASE_URL is required" in capsys.readouterr().err
