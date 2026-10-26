import logging
import logging.handlers
import os
import re
import sys
from typing import Optional

_SECRET_ENV_VARS = frozenset({
    "API_KEY", "API_SECRET", "ACCESS_TOKEN", "SECRET", "PASSWORD", "TOKEN",
    "GEMINI_API_KEY", "GROQ_API_KEY", "OMNIROUTE_API_KEY", "ELEVENLABS_API_KEY",
    "CARTESIA_API_KEY", "OPENAI_API_KEY", "N8N_RUNNER_API_KEY", "TELEGRAM_BOT_TOKEN",
    "YOUTUBE_CLIENT_SECRET", "FACEBOOK_PAGE_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN",
    "R2_SECRET_ACCESS_KEY", "BLUESKY_APP_PASSWORD", "MASTODON_ACCESS_TOKEN",
    "RELAY_API_KEY", "UPLOAD_POST_API_KEY",
})


class SecretFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        for secret_name in _SECRET_ENV_VARS:
            msg = re.sub(
                r"(" + re.escape(secret_name) + r")=['\"]?[^'\"]+['\"]?",
                r"\1=***REDACTED***",
                msg,
                flags=re.IGNORECASE,
            )
        record.msg = msg
        record.args = ()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        import json
        from datetime import datetime, timezone
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(*, level=None, log_file=None, json_console=False):
    level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    root.setLevel(log_level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    secret_filter = SecretFilter()
    console = logging.StreamHandler(sys.stdout)
    console.addFilter(secret_filter)
    if json_console or os.getenv("LOG_JSON_CONSOLE", "").lower() in {"1", "true"}:
        console.setFormatter(_JsonFormatter())
    else:
        console.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S"))
    root.addHandler(console)
    if log_file or os.getenv("LOG_FILE"):
        path = log_file or os.getenv("LOG_FILE")
        fh = logging.handlers.RotatingFileHandler(path, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
        fh.addFilter(secret_filter)
        fh.setFormatter(_JsonFormatter())
        root.addHandler(fh)
    for noisy in ("urllib3", "requests", "httpx", "httpcore", "edge_tts"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name):
    if not logging.getLogger().handlers:
        setup_logging()
    return logging.getLogger(name)
