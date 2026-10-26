#!/usr/bin/env python3
"""Report setup readiness without revealing credential values or publishing."""
from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

def env_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    return value

def command_available(name: str) -> bool:
    if shutil.which(name) is not None:
        return True
    bundled = ROOT / "venv" / "bin" / name
    return bundled.exists() or bundled.with_suffix(".exe").exists()

def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError):
        return False

checks: list[tuple[str, bool, str, bool]] = []
def add(label: str, ready: bool, required: str, *, optional: bool = False) -> None:
    checks.append((label, bool(ready), required, optional))

add(
    "AI script provider",
    bool(env_value("GEMINI_API_KEY") or env_value("GROQ_API_KEY") or env_value("OMNIROUTE_API_KEY") or env_value("OLLAMA_BASE_URL")),
    "Set OMNIROUTE_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, or OLLAMA_BASE_URL in .env",
)
for command in ("ffmpeg", "ffprobe", "edge-tts"):
    add(f"Command: {command}", command_available(command), f"Install {command} in WSL")
for module in ("requests", "dotenv", "faster_whisper"):
    add(f"Python module: {module}", module_available(module), f"Install {module} in the project virtual environment")

add("YouTube client ID", bool(env_value("YOUTUBE_CLIENT_ID")), "Set YOUTUBE_CLIENT_ID in .env")
add("YouTube client secret", bool(env_value("YOUTUBE_CLIENT_SECRET")), "Set YOUTUBE_CLIENT_SECRET in .env")
add("YouTube refresh token file", (ROOT / "youtube_token.json").is_file(), "Complete YouTube OAuth and save youtube_token.json")

for key in ("META_GRAPH_API_VERSION", "FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN"):
    add(f"Facebook: {key}", bool(env_value(key)), f"Configure {key} in .env")
for key in ("META_GRAPH_API_VERSION", "INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN"):
    add(f"Instagram: {key}", bool(env_value(key)), f"Configure {key} in .env")
instagram_host_ready = bool(env_value("INSTAGRAM_VIDEO_URL")) or (
    env_value("INSTAGRAM_TUNNEL_FALLBACK").lower() == "true" and command_available("cloudflared")
)
add(
    "Instagram: public media host",
    instagram_host_ready,
    "Configure INSTAGRAM_VIDEO_URL, or set INSTAGRAM_TUNNEL_FALLBACK=true with cloudflared installed for a per-run tunnel",
)

# New modules importable
for module in ("visual_assets", "voice_provider", "app.research.trends", "publish_social", "workspace_sync", "analytics_collect"):
    add(f"Python module: {module}", module_available(module), f"Install {module} in the project virtual environment")

# Strong pipeline modules
for module in ("app.research.selector", "app.research.desk", "app.script.studio", "app.script.voice_guide", "motion_director", "motion_render", "stock_fetcher", "model_health", "strong_pipeline"):
    add(f"Strong pipeline: {module}", module_available(module), f"Install {module} in the project virtual environment")

add(
    "Strong pipeline: provider health",
    (ROOT / "data" / "model_health.json").is_file(),
    "Run ./venv/bin/python model_health.py --probe --prune to record which models actually work",
)
add(
    "Strong pipeline: image sources",
    bool(env_value("PEXELS_API_KEY") or env_value("PIXABAY_API_KEY")) or bool(env_value("GEMINI_API_KEY")),
    "Optional: set PIXABAY_API_KEY or PEXELS_API_KEY for licensed stock; Wikimedia Commons works without a key",
    optional=True,
)


# Voice
add("Voice: ELEVENLABS_API_KEY", bool(env_value("ELEVENLABS_API_KEY")), "Optional free tier: set ELEVENLABS_API_KEY in .env", optional=True)
add("Voice: CARTESIA_API_KEY", bool(env_value("CARTESIA_API_KEY")), "Optional free tier: set CARTESIA_API_KEY in .env", optional=True)

# Visuals
add("Visuals: GEMINI_API_KEY", bool(env_value("GEMINI_API_KEY")), "Optional: set GEMINI_API_KEY in .env for AI visuals", optional=True)
add("Visuals: FAL_KEY", bool(env_value("FAL_KEY")), "Optional: set FAL_KEY in .env", optional=True)
add("Visuals: REPLICATE_API_TOKEN", bool(env_value("REPLICATE_API_TOKEN")), "Optional: set REPLICATE_API_TOKEN in .env", optional=True)
add("Visuals: OPENAI_API_KEY", bool(env_value("OPENAI_API_KEY")), "Optional: set OPENAI_API_KEY in .env", optional=True)
add("Visuals: THUMBNAIL_PROVIDER", bool(env_value("THUMBNAIL_PROVIDER")), "Optional: set THUMBNAIL_PROVIDER in .env", optional=True)

# Trending
add("Trending: YOUTUBE_DATA_API_KEY", bool(env_value("YOUTUBE_DATA_API_KEY")), "Optional: set YOUTUBE_DATA_API_KEY in .env for YouTube trend signals", optional=True)
add("Trending: TRENDS_API_KEY", bool(env_value("TRENDS_API_KEY")), "Optional free tier: set TRENDS_API_KEY in .env", optional=True)
add("Trending: REDDIT_CLIENT_ID+SECRET", bool(env_value("REDDIT_CLIENT_ID") and env_value("REDDIT_CLIENT_SECRET")), "Optional: set both REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env", optional=True)

# Storage/Workspace
add("Storage: CLOUDINARY (all 3)", bool(env_value("CLOUDINARY_CLOUD_NAME") and env_value("CLOUDINARY_API_KEY") and env_value("CLOUDINARY_API_SECRET")), "Optional: set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET in .env", optional=True)
add("Storage: AIRTABLE (all 3)", bool(env_value("AIRTABLE_API_KEY") and env_value("AIRTABLE_BASE_ID") and env_value("AIRTABLE_TABLE")), "Optional: set AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE in .env", optional=True)
add("Storage: NOTION (both)", bool(env_value("NOTION_API_KEY") and env_value("NOTION_DATABASE_ID")), "Optional: set NOTION_API_KEY and NOTION_DATABASE_ID in .env", optional=True)
add("Storage: SUPABASE (both)", bool(env_value("SUPABASE_URL") and env_value("SUPABASE_SERVICE_KEY")), "Optional: set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env", optional=True)
add("Storage: R2 (all 4)", bool(env_value("R2_ACCOUNT_ID") and env_value("R2_ACCESS_KEY_ID") and env_value("R2_SECRET_ACCESS_KEY") and env_value("R2_BUCKET")), "Optional: set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET in .env", optional=True)

# Extra platforms
add("Platform: THREADS (both)", bool(env_value("THREADS_USER_ID") and env_value("THREADS_ACCESS_TOKEN")), "Optional: set THREADS_USER_ID and THREADS_ACCESS_TOKEN in .env", optional=True)
add("Platform: BLUESKY (both)", bool(env_value("BLUESKY_IDENTIFIER") and env_value("BLUESKY_APP_PASSWORD")), "Optional: set BLUESKY_IDENTIFIER and BLUESKY_APP_PASSWORD in .env", optional=True)
add("Platform: MASTODON (both)", bool(env_value("MASTODON_BASE_URL") and env_value("MASTODON_ACCESS_TOKEN")), "Optional: set MASTODON_BASE_URL and MASTODON_ACCESS_TOKEN in .env", optional=True)
add("Platform: DISCORD_WEBHOOK_URL", bool(env_value("DISCORD_WEBHOOK_URL")), "Optional: set DISCORD_WEBHOOK_URL in .env", optional=True)
add("Platform: PINTEREST (both)", bool(env_value("PINTEREST_ACCESS_TOKEN") and env_value("PINTEREST_BOARD_ID")), "Optional: set PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID in .env", optional=True)
add("Platform: UPLOAD_POST_API_KEY", bool(env_value("UPLOAD_POST_API_KEY")), "Optional: set UPLOAD_POST_API_KEY in .env", optional=True)
add("Platform: RELAY_API_KEY", bool(env_value("RELAY_API_KEY")), "Optional: set RELAY_API_KEY in .env", optional=True)

# Analytics
add("Analytics: GA4_MEASUREMENT_ID", bool(env_value("GA4_MEASUREMENT_ID")), "Optional: set GA4_MEASUREMENT_ID in .env", optional=True)
add("Analytics: YT_ANALYTICS_ENABLED", bool(env_value("YT_ANALYTICS_ENABLED")), "Optional: set YT_ANALYTICS_ENABLED in .env", optional=True)
optional = [
    (
        "Licensed stock B-roll",
        bool(env_value("PEXELS_API_KEY") or env_value("PIXABAY_API_KEY")),
        "Set PIXABAY_API_KEY from https://pixabay.com/api/docs/ or configure an existing PEXELS_API_KEY",
    ),
    ("Telegram status alerts", bool(env_value("TELEGRAM_BOT_TOKEN") and env_value("TELEGRAM_CHAT_ID")), "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to receive alerts"),
]


for label, ready, required in optional:
    add(label, ready, required, optional=True)


def format_report(items: list[tuple[str, bool, str, bool]]) -> tuple[list[str], int]:
    lines = []
    required_missing = [item for item in items if not item[1] and not item[3]]
    optional_missing = [item for item in items if not item[1] and item[3]]
    for label, ready, required, is_optional in items:
        mark = "READY" if ready else "OPTIONAL" if is_optional else "NEEDS SETUP"
        lines.append(f"[{mark}] {label}" + ("" if ready else f" — {required}"))

    if required_missing:
        lines.append(
            f"\nOverall: {len(required_missing)} required setup item(s) remain; "
            f"{len(optional_missing)} optional integration(s) are not configured. "
            "This check never publishes or prints secret values."
        )
        return lines, 2
    if optional_missing:
        lines.append(
            f"\nOverall: required credentials and local tools are present; "
            f"{len(optional_missing)} optional integration(s) are not configured. "
            "This check does not validate token permissions or publish."
        )
    else:
        lines.append(
            "\nOverall: required credentials and local tools are present. "
            "This check does not validate token permissions or publish."
        )
    return lines, 0


if __name__ == "__main__":
    report_lines, exit_code = format_report(checks)
    print("\n".join(report_lines))
    raise SystemExit(exit_code)
