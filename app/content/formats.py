"""Validated channel content-format routing contract."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class FormatCapability:
    format_id: str
    producer: str | None
    status: str
    platforms: tuple[str, ...]
    description: str

# Only end-to-end video producers currently present are executable. Post and
# carousel formats fail closed until artifact, QA and approval paths exist.
_FORMATS = {
    "youtube_shorts": FormatCapability("youtube_shorts", "short_video", "supported", ("youtube",), "Vertical short-form video"),
    "instagram_reels": FormatCapability("instagram_reels", "short_video", "supported", ("instagram",), "Vertical Instagram Reel"),
    "facebook_reels": FormatCapability("facebook_reels", "short_video", "supported", ("facebook",), "Vertical Facebook Reel"),
    "youtube_longform": FormatCapability("youtube_longform", "long_video", "supported", ("youtube",), "Horizontal long-form video"),
    "youtube_community_posts": FormatCapability("youtube_community_posts", None, "not_implemented", ("youtube",), "Community post workflow is not implemented"),
    "instagram_posts": FormatCapability("instagram_posts", None, "not_implemented", ("instagram",), "Image post workflow is not implemented"),
    "instagram_carousels": FormatCapability("instagram_carousels", None, "not_implemented", ("instagram",), "Carousel slide-pack workflow is not implemented"),
    "facebook_posts": FormatCapability("facebook_posts", None, "not_implemented", ("facebook",), "Post workflow is not implemented"),
    "linkedin_posts": FormatCapability("linkedin_posts", None, "not_implemented", ("linkedin",), "Post workflow is not implemented"),
    "x_posts": FormatCapability("x_posts", None, "not_implemented", ("x",), "Post/thread workflow is not implemented"),
}

def get_format_capability(format_id: str) -> FormatCapability:
    if not isinstance(format_id, str) or format_id not in _FORMATS:
        raise ValueError(f"Unknown content_format: {format_id!r}")
    return _FORMATS[format_id]

def list_format_capabilities() -> list[dict]:
    return [cap.__dict__.copy() for cap in _FORMATS.values()]

def executable_format_ids() -> tuple[str, ...]:
    return tuple(key for key, value in _FORMATS.items() if value.status == "supported")


def resolve_content_format(content_format: str | None = None, *, producer: str) -> dict:
    """Validate a requested content format for a producer, fail-closed.

    The channel profile declares every format NEXTDECODE will eventually
    publish, but only formats with a complete end-to-end producer may execute.
    A declared-but-unimplemented format is rejected here rather than being
    silently rendered as a video, and a format is never handed to the wrong
    producer (for example long-form through the short pipeline).
    """
    from app.research.channel_profile import enabled_content_formats, load_channel_profile

    requested = str(content_format or "youtube_shorts").strip() or "youtube_shorts"
    capability = get_format_capability(requested)  # ValueError on an unknown id
    if capability.status != "supported" or not capability.producer:
        raise RuntimeError(
            f"content_format {requested} is declared in the channel profile but has no "
            f"producer yet ({capability.status}): {capability.description}"
        )
    if capability.producer != producer:
        raise RuntimeError(
            f"content_format {requested} is produced by the {capability.producer} pipeline, "
            f"not the {producer} pipeline; route it to the correct producer"
        )
    enabled = enabled_content_formats()
    if requested not in enabled:
        raise RuntimeError(
            f"content_format {requested} is not enabled in the active channel profile"
        )
    profile = load_channel_profile()
    return {
        "format_id": capability.format_id,
        "producer": capability.producer,
        "status": capability.status,
        "platforms": list(capability.platforms),
        "description": capability.description,
        "channel_id": profile.get("channel_id"),
        "declared_formats": enabled,
    }


def producer_for_format(format_id: str) -> str | None:
    """Which producer owns a format id; None means no producer exists yet."""
    capability = get_format_capability(str(format_id or "").strip())
    if capability.status != "supported":
        return None
    return capability.producer
