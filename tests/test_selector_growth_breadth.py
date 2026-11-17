"""Regression tests for category-neutral NEXTDECODE topic scoring."""
from app.research import selector


def _fit(title: str, summary: str = "") -> dict:
    return selector._score_channel_fit({
        "candidate": {"title": title, "summary": summary},
        "judged": {},
        "past_performance": {},
    })


def test_non_technology_documentary_categories_are_not_penalized():
    examples = [
        ("Why the Panama Canal Changed Global Trade", "A geography and infrastructure story"),
        ("How the Roman Empire Lost Its Western Frontier", "History of a collapsing empire"),
        ("The Engineering Mystery Behind the Tacoma Narrows Bridge", "A bridge failure investigation"),
        ("How Nokia Lost the Mobile Phone Market", "A business rise and decline story"),
        ("Why the Amazon Rainforest Creates Its Own Weather", "A science and environment explainer"),
        ("The Forgotten Antarctic Machine Built for the Soviet Union", "A history of an unusual invention"),
    ]
    scores = [_fit(title, summary)["score"] for title, summary in examples]
    assert min(scores) >= 70, scores


def test_channel_fit_explains_category_neutral_heuristics():
    result = _fit("Why the Panama Canal Changed Global Trade")
    assert result["breakdown"]["topic_category"] == "world_geopolitics"
    assert "No subject category was penalized" in result["why"]
    assert result["score_type"] == "estimate"


def test_channel_gate_accepts_adjacent_business_and_technology_categories():
    for title in [
        "How the Semiconductor Supply Chain Shapes Global Trade",
        "Why the Panama Canal Matters to Global Technology Supply Chains",
        "The Business That Changed Global Shipping",
    ]:
        result = selector.niche_relevance({"title": title})
        assert result["eligible"], (title, result)


def test_channel_gate_does_not_admit_unrelated_history_or_nature():
    assert not selector.niche_relevance({"title": "Why the Roman Empire Collapsed"})["eligible"]
    assert not selector.niche_relevance({"title": "How the Amazon Rainforest Creates Rain"})["eligible"]


def test_unclassified_topic_is_reviewable_not_hard_rejected():
    result = selector.niche_relevance({"title": "An Unexpected Story"})
    assert result["eligible"] is False
    assert "editorial review" in result["reason"]


def test_short_ai_marker_does_not_match_inside_unrelated_words():
    assert selector.niche_relevance({"title": "How the Amazon Rainforest Creates Rain"})[
        "topic_category"
    ] == "nature_environment"
    assert selector.niche_relevance({"title": "How AI Changes Scientific Research"})[
        "topic_category"
    ] in {"technology_ai", "science_discovery"}
