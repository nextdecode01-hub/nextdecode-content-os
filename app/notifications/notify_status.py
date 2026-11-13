#!/usr/bin/env python3
"""Send safe pipeline status alerts to the configured Telegram chat."""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)

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
