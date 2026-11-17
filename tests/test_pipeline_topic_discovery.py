"""Pipeline consumes the combined trend + topic discovery candidate pool."""

from unittest.mock import patch

from app.script import pipeline


def test_automatic_topic_selection_uses_combined_discovery_and_reports_sources():
    candidates = [
        {"title": "AI agents change software workflows", "source": "hackernews"},
        {"title": "Experimental photonic computing", "source": "arxiv"},
    ]
    selected = {"topic": candidates[0]["title"], "total_score": 81}
    discovery_notes = ["trend source: 8 candidates", "topic feeds: 4 candidates"]

    with (patch.object(pipeline.topic_selector, "discover_candidates",
                       return_value=(candidates, discovery_notes)) as discover,
          patch.object(pipeline.topic_selector, "select_best",
                       return_value={"selected": selected, "ranked": [selected],
                                     "rejected": [], "min_score": 60}) as score):
        result = pipeline.select_topic(None, limit=12, min_score=60)

    discover.assert_called_once_with(limit=12)
    score.assert_called_once_with(candidates, limit=1, min_score=60, channel_id=None)
    assert result["selected"] == selected
