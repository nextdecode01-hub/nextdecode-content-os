"""Validation for complete, beat-aligned short-form production storyboards."""
from __future__ import annotations

ALLOWED_VISUAL_TYPES = {
    "real_event_footage", "original_speech", "natural_sound", "primary_document",
    "licensed_stock", "archival_photo", "existing_gif", "generated_image",
    "custom_animation", "motion_graphic",
}
REQUIRED_FIELDS = (
    "phase", "viewer_purpose", "visual_type", "visual_action", "asset_search",
    "on_screen_text", "audio_direction", "edit_direction", "rights_notes", "fallback",
)

def validate_production_storyboard(storyboard, voice_text: str, target_seconds: float) -> list[dict]:
    """Reject incomplete timing, missing visual/audio direction, or invented narration snippets."""
    if not isinstance(storyboard, list) or not 3 <= len(storyboard) <= 10:
        raise RuntimeError("Production storyboard must contain 3-10 complete timed phases.")
    normalized = []
    cursor = 0.0
    spoken = " ".join(str(voice_text or "").split())
    for index, raw in enumerate(storyboard):
        if not isinstance(raw, dict):
            raise RuntimeError(f"Storyboard phase {index + 1} is not an object.")
        missing = [key for key in REQUIRED_FIELDS if not str(raw.get(key) or "").strip()]
        if missing:
            raise RuntimeError(f"Storyboard phase {index + 1} is missing: {', '.join(missing)}.")
        try:
            start, end = float(raw.get("start_seconds")), float(raw.get("end_seconds"))
        except (TypeError, ValueError):
            raise RuntimeError(f"Storyboard phase {index + 1} has invalid timecodes.") from None
        if start < 0 or end <= start or abs(start - cursor) > 0.15 or end > float(target_seconds) + 0.15:
            raise RuntimeError(f"Storyboard phase {index + 1} has a gap, overlap, or out-of-range timecode.")
        visual_type = str(raw.get("visual_type") or "").strip()
        if visual_type not in ALLOWED_VISUAL_TYPES:
            raise RuntimeError(f"Storyboard phase {index + 1} has unsupported visual_type: {visual_type}.")
        narration = " ".join(str(raw.get("narration") or "").split())
        if narration and narration not in spoken:
            raise RuntimeError(f"Storyboard phase {index + 1} narration is not an exact excerpt of the final voiceover.")
        if not narration and visual_type not in {"original_speech", "natural_sound"}:
            raise RuntimeError(f"Storyboard phase {index + 1} must map to spoken narration or an intentional real-audio beat.")
        item = dict(raw)
        item["start_seconds"] = round(start, 3)
        item["end_seconds"] = round(end, 3)
        item["duration_seconds"] = round(end - start, 3)
        item["narration"] = narration
        item["rights_status"] = "review_required"
        normalized.append(item)
        cursor = end
    if abs(cursor - float(target_seconds)) > 0.75:
        raise RuntimeError("Production storyboard must cover the complete target runtime.")
    return normalized
