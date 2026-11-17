#!/usr/bin/env python3
"""Send safe pipeline status alerts to the configured Telegram chat.

Outbound notification channel only. It never receives callbacks, polls for
updates or reads Telegram state; an approval must come from the local reviewer
flow, never from this module.
"""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_API_ENV = Path(os.path.expanduser("~/.config/nextdecode/api.env"))


def load_env() -> None:
    """Load ROOT/.env (repo secrets). Falls back to the API env file for
    TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID when they are absent there, so the
    API process starts cleanly without duplicated secrets."""
    load_dotenv(ROOT / ".env", override=True)
    if os.getenv("TELEGRAM_BOT_TOKEN", "").strip() and os.getenv("TELEGRAM_CHAT_ID", "").strip():
        return
    if DEFAULT_API_ENV.is_file():
        load_dotenv(DEFAULT_API_ENV, override=False)


load_env()


def env_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    return value


def send_status(message: str) -> bool:
    token = env_value("TELEGRAM_BOT_TOKEN")
    chat_id = env_value("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    payload = json.dumps({
        "chat_id": chat_id,
        "text": message[:3500],
        "disable_web_page_preview": True,
    }).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
            return response.status == 200 and result.get("ok") is True
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        # Never print the request URL: Telegram bot tokens are part of that URL.
        return False


if __name__ == "__main__":
    message = " ".join(sys.argv[1:]).strip()
    if not message:
        raise SystemExit(2)
    raise SystemExit(0 if send_status(message) else 1)
