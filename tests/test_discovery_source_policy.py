"""Regression tests for the Wikipedia/Wikimedia discovery-source exclusion (ND-ENG-002 item 9).

Hermetic: candidates are supplied directly, so nothing here fetches a feed or reads the
feed cache.  The rule must hold for default sources, aggregators and cached replays.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.research import selector, trends


def _candidate(title, url, source):
    return {"title": title, "url": url, "source": source, "rank": 5,
            "published": "2026-10-30T00:00:00+00:00", "platforms": [source]}


WIKIPEDIA_CASES = [
    ("NIST framework", "https://en.wikipedia.org/wiki/NIST", "wikipedia"),
    ("Trending pages", "https://en.wikipedia.org/wiki/Special:Trending", "wikipedia"),
    ("Wikimedia feed item", "https://api.wikimedia.org/feed/v1/wikipedia/en/trending", "wikipedia"),
    ("Mirror of a wiki article", "https://en.m.wikipedia.org/wiki/NIST", "aggregator"),
    ("Cached wiki entry", "https://en.wikipedia.org/wiki/AI", "aggregator"),
]

KEPT_CASES = [
    ("NIST publishes update", "https://www.nist.gov/itl/ai-risk-management-framework", "nist"),
    ("arXiv paper", "https://arxiv.org/abs/2601.00001", "arxiv"),
    ("HN thread", "https://news.ycombinator.com/item?id=1", "hackernews"),
]


@pytest.mark.parametrize("title,url,source", WIKIPEDIA_CASES)
def test_predicate_flags_wikipedia_and_wikimedia(title, url, source):
    assert selector.is_discovery_excluded({"title": title, "url": url, "source": source})


@pytest.mark.parametrize("title,url,source", KEPT_CASES)
def test_predicate_keeps_other_sources(title, url, source):
    assert not selector.is_discovery_excluded({"title": title, "url": url, "source": source})


def test_source_label_alone_is_enough_for_a_cache_replay():
    # A cached candidate may arrive without a URL at all.
    assert selector.is_discovery_excluded({"title": "Wiki item", "source": "wikipedia"})


def test_rank_topics_drops_wikipedia_candidates():
    candidates = [_candidate(title, url, source) for title, url, source in WIKIPEDIA_CASES]
    candidates += [_candidate(title, url, source) for title, url, source in KEPT_CASES]
    with patch.object(selector, "derive_past_performance", return_value={}), \
            patch.object(selector, "load_used_topics", return_value=[]), \
            patch.object(selector, "_ensure_judgements", return_value=None):
        scored = selector.rank_topics(candidates)
    titles = {entry.get("topic") for entry in scored}
    assert "NIST publishes update" in titles
    assert "arXiv paper" in titles
    assert not {"NIST framework", "Wikimedia feed item"} & titles


def test_rank_topics_reports_drops_instead_of_hiding_them(capsys):
    candidates = [_candidate("Wiki item", "https://en.wikipedia.org/wiki/X", "wikipedia")]
    with patch.object(selector, "derive_past_performance", return_value={}), \
            patch.object(selector, "load_used_topics", return_value=[]):
        scored = selector.rank_topics(candidates)
    assert scored == []
    assert "dropped 1 ineligible discovery candidate" in capsys.readouterr().out


def test_only_wikipedia_candidates_yields_no_selection(tmp_path):
    candidates = [_candidate(title, url, source) for title, url, source in WIKIPEDIA_CASES]
    with patch.object(selector, "derive_past_performance", return_value={}), \
            patch.object(selector, "load_used_topics", return_value=[]):
        result = selector.select_best(candidates)
    assert not result.get("selected")


def test_fetch_all_filters_wikipedia_from_aggregated_results():
    payloads = {
        "wikipedia": [_candidate("Wiki item", "https://en.wikipedia.org/wiki/NIST", "wikipedia")],
        "nist": [_candidate("NIST page", "https://www.nist.gov/ai", "nist")],
    }

    def fake_run_source(name):
        return payloads.get(name, []), None if name in payloads else "no candidates returned"

    with patch.object(trends, "_run_source", side_effect=fake_run_source), \
            patch.object(trends, "_normalize_source_list",
                         return_value=(["wikipedia", "nist"], [])), \
            patch.object(trends, "_is_relevant", return_value=True):
        result = trends.fetch_all()

    titles = {item["title"] for item in result["candidates"]}
    assert titles == {"NIST page"}
    assert "wikipedia_filter" in result["errors"]
    assert "excluded from discovery" in result["errors"]["wikipedia_filter"]

@pytest.mark.parametrize("candidate", [
    {"title": "Coffeehouses and the Rise of Science [pdf]", "source": "google_news"},
    {"title": "Research paper PDF download", "source": "hackernews"},
    {"title": "A research topic", "url": "https://example.org/files/paper.pdf", "source": "arxiv"},
])
def test_topic_selector_rejects_document_download_artifacts(candidate):
    assert selector.is_discovery_excluded(candidate)


def test_topic_selector_keeps_real_topics_about_pdf_or_research():
    assert not selector.is_discovery_excluded({"title": "How PDF compression works", "source": "hackernews"})
    assert not selector.is_discovery_excluded({"title": "AI research changes drug discovery", "source": "google_news"})
