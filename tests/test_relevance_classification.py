"""Relevance classification preserves emerging and uncertain tech topics."""

from app.research import trends


def test_core_topic_is_classified_with_high_confidence():
    result = trends.classify_relevance({"title": "New AI reasoning model"})
    assert result["category"] == "core"
    assert result["confidence"] >= 0.9
    assert "ai" in result["matched_terms"]


def test_emerging_technology_is_not_rejected_by_core_keyword_gap():
    candidate = {"title": "Neuromorphic photonic computing reaches new milestone"}
    result = trends.classify_relevance(candidate)
    assert result["category"] == "experimental"
    assert trends._is_relevant(candidate)


def test_adjacent_technology_sector_is_retained():
    candidate = {"title": "New smart grid energy storage platform"}
    result = trends.classify_relevance(candidate)
    assert result["category"] == "adjacent"
    assert trends._is_relevant(candidate)


def test_unknown_topic_is_retained_for_editorial_review():
    candidate = {"title": "A new technical architecture changes system design"}
    result = trends.classify_relevance(candidate)
    assert result["category"] == "unclassified"
    assert result["confidence"] < 0.5
    assert trends._is_relevant(candidate)


def test_clear_non_technology_noise_is_still_filtered():
    candidate = {"title": "Cricket match results and highlights"}
    assert trends.classify_relevance(candidate)["category"] == "unrelated"
    assert not trends._is_relevant(candidate)


def test_candidate_and_ranked_output_retain_relevance_provenance(tmp_path):
    candidate = trends._candidate(
        "AI model adoption grows",
        "https://example.com/mcp",
        "hackernews",
        rank=3,
    )
    assert candidate["relevance"]["category"] == "core"

    ranked = trends.rank_candidates(
        [candidate],
        used_topics_file=tmp_path / "used_topics.txt",
        update_history=False,
    )
    assert len(ranked) == 1
    assert ranked[0]["relevance"]["category"] == "core"
    assert ranked[0]["relevance"]["confidence"] >= 0.9


def test_fetch_all_keeps_unclassified_for_review_and_still_excludes_wikipedia():
    from unittest.mock import patch

    candidates = [
        {"title": "New technical architecture", "url": "https://example.com/a",
         "source_url": "https://example.com/a", "source": "hackernews"},
        {"title": "Wikipedia technology page", "url": "https://en.wikipedia.org/wiki/AI",
         "source_url": "https://en.wikipedia.org/wiki/AI", "source": "aggregator"},
    ]
    with (patch.object(trends, "_normalize_source_list", return_value=(["hackernews"], [])),
          patch.object(trends, "_run_source", return_value=(candidates, ""))):
        result = trends.fetch_all()
    assert [item["title"] for item in result["candidates"]] == ["New technical architecture"]
    assert result["candidates"][0]["relevance"]["category"] == "unclassified"
    assert "wikipedia_filter" in result["errors"]
