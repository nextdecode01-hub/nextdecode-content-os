"""Regression tests for ID-safe editorial judge response mapping."""

from app.research import selector


def test_judgements_are_mapped_by_explicit_id_not_response_order():
    candidates = [{"title": "first"}, {"title": "second"}, {"title": "third"}]
    response = {
        "judgements": [
            {"id": "C3", "fit_score": 93},
            {"id": "C1", "fit_score": 71},
            {"id": "C2", "fit_score": 82},
        ]
    }

    mapped = selector._map_judgements(response, candidates)

    assert mapped["C1"]["fit_score"] == 71
    assert mapped["C2"]["fit_score"] == 82
    assert mapped["C3"]["fit_score"] == 93
    assert "__warnings__" not in mapped


def test_duplicate_id_is_rejected_and_reported_instead_of_overwritten():
    candidates = [{"title": "first"}, {"title": "second"}]
    response = [
        {"id": "C1", "fit_score": 10},
        {"id": "C1", "fit_score": 99},
        {"id": "C2", "fit_score": 55},
    ]

    mapped = selector._map_judgements(response, candidates)

    assert "C1" not in mapped
    assert mapped["C2"]["fit_score"] == 55
    assert "duplicate candidate ID(s): C1" in mapped["__warnings__"]
    assert "missing judgement(s) for C1" in mapped["__warnings__"]


def test_missing_unknown_and_unidentified_judgements_are_reported():
    candidates = [{"title": "first"}, {"title": "second"}, {"title": "third"}]
    response = [
        {"id": "C1", "fit_score": 80},
        {"id": "C99", "fit_score": 100},
        {"fit_score": 45},
    ]

    mapped = selector._map_judgements(response, candidates)

    assert mapped["C1"]["fit_score"] == 80
    assert "C2" not in mapped
    assert "C3" not in mapped
    warning = mapped["__warnings__"]
    assert "unknown candidate ID(s): C99" in warning
    assert "1 judgement(s) had no candidate ID" in warning
    assert "missing judgement(s) for C2, C3" in warning


def test_rank_topics_retains_candidates_whose_scoring_raises():
    from unittest.mock import patch

    candidates = [
        {"title": "A useful AI topic", "source": "feed"},
        {"title": "Another AI topic", "source": "feed"},
    ]

    def score(candidate, **kwargs):
        if candidate["title"].startswith("A useful"):
            raise RuntimeError("judge transport unavailable")
        return {"topic": candidate["title"], "total_score": 72.0, "dimensions": {}, "errors": {}}

    with patch.object(selector, "_ensure_judgements", return_value={}), \
         patch.object(selector, "score_candidate", side_effect=score):
        ranked = selector.rank_topics(candidates, past_performance={"applied": False})

    assert len(ranked) == 2
    failed = next(item for item in ranked if item["topic"] == "A useful AI topic")
    assert failed["total_score"] == 0.0
    assert failed["score_type"] == "unknown"
    assert failed["errors"]["scoring"] == "RuntimeError: judge transport unavailable"
