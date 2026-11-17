"""NEXTDECODE niche contract: stay inside the niche, rotate the pillar."""
from __future__ import annotations

import json
from contextlib import contextmanager
from unittest.mock import patch

import pytest

from app.research import selector
from app.research.channel_profile import PRIMARY_LANES, channel_topic_relevance


AI_TOPIC = "New AI model sets a benchmark record on coding tasks"
AI_AGENT_TOPIC = "AI agents automate developer workflows end to end"
STARTUP_TOPIC = "Startup raises a funding round to build data centres"
OUT_OF_NICHE_TOPIC = "The Lost Tomb of an Ancient King"


def _candidate(title, summary=""):
    return {"title": title, "summary": summary, "source": "news"}


@contextmanager
def _offline_scoring():
    """Score candidates without live judges, YouTube probes or stored history."""
    with patch.multiple(
        selector,
        derive_past_performance=lambda: {},
        load_used_topics=lambda: [],
        _ensure_judgements=lambda candidates, used: None,
        _youtube_total_results=lambda query: (None, "probe disabled in test", []),
        _image_provider_available=lambda: False,
        _JUDGE_CACHE={},
    ):
        yield


def test_all_six_owner_pillars_are_recognised():
    examples = {
        "artificial_intelligence": "New AI model beats every benchmark",
        "technology_innovation": "New software platform changes computing",
        "startups_entrepreneurship": "Startup raises venture capital in a funding round",
        "business_economics": "The economics of the battery supply chain",
        "markets_industry_shifts": "Stock market rally lifts the semiconductor industry",
        "future_trends": "Moonshot 2040: scenario planning for the long term",
    }
    for lane, title in examples.items():
        result = channel_topic_relevance(title)
        assert result["eligible"], (lane, title, result)
        assert result["primary_niche_lane"] == lane, (lane, title, result)
    assert set(examples) == set(PRIMARY_LANES)


def test_out_of_niche_story_is_rejected_even_when_it_scores_well():
    with _offline_scoring():
        result = selector.select_best(
            [_candidate(OUT_OF_NICHE_TOPIC), _candidate(AI_TOPIC)],
            min_score=0,
            recent_niche_lanes=[],
        )
    assert result["selected"]["topic"] == AI_TOPIC
    rejected = {item["topic"]: item["reason"] for item in result["rejected"]}
    assert OUT_OF_NICHE_TOPIC in rejected
    assert "outside the NEXTDECODE channel niche" in rejected[OUT_OF_NICHE_TOPIC]


def test_previous_pillar_is_rotated_when_an_alternative_is_close():
    entries = [
        {"topic": AI_TOPIC, "total_score": 80.0, "niche_lane": "artificial_intelligence"},
        {"topic": STARTUP_TOPIC, "total_score": 75.0, "niche_lane": "startups_entrepreneurship"},
    ]
    ordered, rotation = selector.apply_niche_rotation(
        entries, ["artificial_intelligence"], tolerance=10.0
    )
    assert ordered[0]["topic"] == STARTUP_TOPIC
    assert ordered[1]["topic"] == AI_TOPIC
    assert rotation["deferred"] is False
    assert rotation["score_delta"] == 5.0
    # The rotated-in story keeps its real score; rotation never edits the scorecard.
    assert ordered[0]["total_score"] == 75.0


def test_a_clearly_stronger_same_pillar_story_is_not_sacrificed():
    entries = [
        {"topic": AI_TOPIC, "total_score": 80.0, "niche_lane": "artificial_intelligence"},
        {"topic": STARTUP_TOPIC, "total_score": 60.0, "niche_lane": "startups_entrepreneurship"},
    ]
    ordered, rotation = selector.apply_niche_rotation(
        entries, ["artificial_intelligence"], tolerance=10.0
    )
    assert ordered[0]["topic"] == AI_TOPIC
    assert rotation["deferred"] is True


def test_same_pillar_is_retained_when_no_alternative_exists_and_never_leaves_niche():
    with _offline_scoring():
        result = selector.select_best(
            [_candidate(AI_TOPIC), _candidate(AI_AGENT_TOPIC)],
            min_score=0,
            recent_niche_lanes=["artificial_intelligence"],
        )
    rotation = result["category_rotation"]
    assert result["selected"]["niche_lane"] == "artificial_intelligence"
    assert rotation["deferred"] is True
    assert "same pillar" in rotation["reason"]
    assert "inside the channel niche" in rotation["reason"]


def test_rotation_never_selects_an_out_of_niche_story_to_avoid_a_repeat():
    with _offline_scoring():
        result = selector.select_best(
            [_candidate(AI_TOPIC), _candidate(OUT_OF_NICHE_TOPIC)],
            min_score=0,
            recent_niche_lanes=["artificial_intelligence"],
        )
    assert result["selected"]["topic"] == AI_TOPIC
    assert result["category_rotation"]["deferred"] is True


def test_rotation_is_inert_without_a_delivered_history():
    with _offline_scoring():
        result = selector.select_best([_candidate(AI_TOPIC)], min_score=0, recent_niche_lanes=[])
    assert result["selected"]["topic"] == AI_TOPIC
    assert result["category_rotation"]["applied"] is False


def test_select_best_reads_the_delivered_history_by_default():
    with _offline_scoring(), patch.object(
        selector, "load_rotation_lanes", return_value=["artificial_intelligence"]
    ):
        result = selector.select_best([_candidate(AI_TOPIC)], min_score=0)
    assert result["category_rotation"]["previous_lane"] == "artificial_intelligence"


def test_rotation_uses_only_delivered_runs_and_keeps_newest_last(tmp_path):
    index = tmp_path / "index.jsonl"
    rows = [
        {"run_id": "1", "status": "ok", "topic": "AI model beats every benchmark"},
        {"run_id": "2", "status": "failed", "topic": "Startup raises venture capital"},
        {"run_id": "3", "status": "awaiting_review", "topic": "Stock market rally lifts chip industry"},
        {"run_id": "4", "status": "failed", "topic": ""},
        {"run_id": "5", "status": "published", "topic": "New software platform changes computing"},
    ]
    index.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    topics = selector.load_recent_run_topics(index, limit=3)
    assert topics == [
        "AI model beats every benchmark",
        "Stock market rally lifts chip industry",
        "New software platform changes computing",
    ]
    assert "Startup raises venture capital" not in topics

    lanes = selector.load_rotation_lanes(index, limit=3)
    assert lanes == [
        "artificial_intelligence",
        "markets_industry_shifts",
        "technology_innovation",
    ]


def test_explicit_topic_rotation_report_is_honest_about_niche_fit():
    entry = {
        "topic": AI_TOPIC,
        "total_score": 91.0,
        "topic_category": "technology_ai",
        "niche_lane": "artificial_intelligence",
        "niche_relevance": {"eligible": True, "matched_editorial_lanes": ["artificial_intelligence"]},
    }
    report = selector.niche_rotation_for_entry(entry, ["artificial_intelligence"])
    assert report["repeat"] is True
    assert report["previous_lane"] == "artificial_intelligence"
    assert report["in_niche"] is True

    off_niche = selector.niche_rotation_for_entry(
        {
            "topic": OUT_OF_NICHE_TOPIC,
            "niche_relevance": {"eligible": False, "matched_editorial_lanes": []},
        },
        ["artificial_intelligence"],
    )
    assert off_niche["repeat"] is False
    assert off_niche["in_niche"] is False


def test_unrelated_categories_stay_out_of_the_niche():
    for title in [
        "The Lost Tomb of an Ancient King",
        "Rare Birds Return to the Rainforest",
        "The Greatest Football Final in History",
        "A Celebrity's Private Life",
    ]:
        assert channel_topic_relevance(title)["eligible"] is False, title
