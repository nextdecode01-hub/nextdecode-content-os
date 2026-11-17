from app.research.topic_diversity import annotate_and_diversify, classify_topic, similarity
from app.script.production_storyboard import validate_production_storyboard
import pytest

def test_topic_taxonomy_spans_distinct_categories():
    assert classify_topic("NASA discovers a new planet") == "space_astronomy"
    assert classify_topic("Ancient city uncovered by archaeologists") == "history_mystery"
    assert classify_topic("Wildlife species returns to the ocean") == "nature_environment"
    assert classify_topic("AI chip startup raises funding") in {"technology_ai", "business_economy"}

def test_diversifier_rotates_categories_and_removes_near_duplicates():
    candidates = [
        {"title": "New AI model changes software coding", "rank": 100},
        {"title": "AI model changes software coding", "rank": 90},
        {"title": "Ancient shipwreck reveals lost history", "rank": 60},
        {"title": "Rare bird returns to protected wetland", "rank": 50},
    ]
    selected = annotate_and_diversify(candidates, ["Recent AI model release"], limit=3)
    categories = [item["topic_category"] for item in selected]
    assert len(selected) == 3
    assert len(set(categories)) >= 2
    assert all("topic_similarity" in item for item in selected)

def test_similarity_detects_same_story_family():
    assert similarity("AI agents bypass sandbox security", "Agents escape an AI test sandbox") > 0.4

def _phase(start, end, narration):
    return {
        "phase": "hook", "start_seconds": start, "end_seconds": end,
        "narration": narration, "viewer_purpose": "Establish the story",
        "visual_type": "real_event_footage", "visual_action": "Show the actual event",
        "asset_search": "official event footage", "on_screen_text": "THE EVENT",
        "audio_direction": "Original sound then narration", "edit_direction": "Cut to evidence",
        "rights_notes": "Verify licence and permission before publishing",
        "fallback": "Use an official still with attribution and rights review",
    }

def test_storyboard_requires_full_runtime_and_complete_phase_fields():
    voice = "The real event happened. The report explains why."
    phases = [_phase(0, 3, "The real event happened."), _phase(3, 7, "The report explains why."), _phase(7, 10, "")]
    phases[2]["visual_type"] = "natural_sound"
    result = validate_production_storyboard(phases, voice, 10)
    assert result[-1]["end_seconds"] == 10
    assert result[0]["rights_status"] == "review_required"

def test_storyboard_rejects_narration_not_in_final_script():
    phases = [_phase(0, 3, "Something invented happened."), _phase(3, 7, "The report explains why."), _phase(7, 10, "")]
    phases[2]["visual_type"] = "natural_sound"
    with pytest.raises(RuntimeError, match="exact excerpt"):
        validate_production_storyboard(phases, "The real event happened. The report explains why.", 10)

def test_storyboard_rejects_missing_rights_and_audio_direction():
    phases = [_phase(0, 3, "The real event happened."), _phase(3, 7, "The report explains why."), _phase(7, 10, "")]
    phases[2]["visual_type"] = "natural_sound"
    phases[0]["rights_notes"] = ""
    with pytest.raises(RuntimeError, match="rights_notes"):
        validate_production_storyboard(phases, "The real event happened. The report explains why.", 10)
