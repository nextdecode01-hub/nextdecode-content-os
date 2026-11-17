import unittest
from unittest.mock import patch

from app.research import desk as research_desk


class DummyResponse:
    def __init__(self, text="", status_code=200, content_type="text/html"):
        self.text = text
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}


class ResearchDeskTests(unittest.TestCase):
    def test_unsupported_number_detection_ten_fold_vs_tenx(self):
        text = "This gives a ten-fold improvement over the baseline."
        source_text = "The model achieves 10x better results."
        # ten-fold should not be considered unsupported if equivalent 10x exists in source
        unsupported = research_desk.find_unsupported_numbers(text, source_text)
        # Our normalization maps ten-fold to 10x and checks for presence
        self.assertNotIn("ten-fold", [u.lower() for u in unsupported])
        self.assertNotIn("10x", [u.lower() for u in unsupported])

    def test_unsupported_number_detection_digit_only(self):
        text = "It achieves 3.5% better accuracy and 2x speedup."
        source_text = "Different results reported elsewhere."
        unsupported = research_desk.find_unsupported_numbers(text, source_text)
        self.assertTrue(any("3.5" in u or "%" in u or "2x" in u for u in unsupported))

    def test_extractor_keeps_exact_moe_router_mechanism_sentence(self):
        text = (
            "At every layer, for every token, a router network chooses two experts "
            "to process the token and combine their output additively. "
            "This sentence is included to check that the full excerpt remains verbatim."
        )
        claims = research_desk.extract_claims(
            text, source_url="https://mistral.ai/news/mixtral-of-experts/"
        )
        matching = [item for item in claims if "router network chooses two experts" in item["quote"]]
        self.assertTrue(matching)
        self.assertTrue(all(item["quote"] in text for item in matching))
        self.assertGreaterEqual(len(matching[0]["quote"].split()), 8)

    def test_extractor_does_not_invent_or_paraphrase_router_quotes(self):
        text = "A router selects experts based on the token."
        claims = research_desk.extract_claims(text, source_url="https://example.com")
        for claim in claims:
            self.assertIn(claim["quote"], text)
            self.assertGreaterEqual(len(claim["quote"].split()), 8)
        self.assertEqual(
            [claim["quote"] for claim in claims],
            ["A router selects experts based on the token."],
        )

    def test_verbatim_quote_guarantee(self):
        text = "The new model achieves 95% accuracy on the benchmark. This is a big improvement over previous work which had 80% accuracy."
        claims = research_desk.extract_claims(text, source_url="http://example.com")
        for c in claims:
            self.assertIn(c["quote"], text)
            self.assertGreaterEqual(len(c["quote"].split()), 8)

    def test_arxiv_abstract_uses_og_description_not_raw_head_markup(self):
        html = """<html><head>
        <title>Can AI agents conduct open-ended AI research?</title>
        <meta property="og:title" content="Can AI agents conduct open-ended AI research?" />
        <meta property="og:description" content="Forecasts of explosive AI progress hinge on agents automating AI research. In two shadow evaluations, agents completed engineering but could not make substantial progress on the research questions." />
        <meta name="citation_publication_date" content="2026-07-29" />
        </head><body><main><h1>Can AI agents conduct open-ended AI research?</h1></main></body></html>"""
        text, title, published = research_desk._extract_arxiv_abs(html, "https://arxiv.org/abs/2607.27191")
        self.assertIn("Forecasts of explosive AI progress", text)
        self.assertIn("could not make substantial progress", text)
        self.assertNotIn("<meta", text)
        self.assertIn("Can AI agents conduct open-ended AI research", title)
        self.assertEqual(published, "2026-07-29")

    def test_extracts_open_ended_agent_research_outcome_as_verbatim_claim(self):
        text = (
            "The agents completed all of the engineering without human help, yet could not make "
            "substantial progress towards answering the research questions. "
            "Both papers were unambiguously rejected by the authors."
        )
        claims = research_desk.extract_claims(
            text, source_url="https://arxiv.org/abs/2607.27191"
        )
        self.assertTrue(any(
            "could not make substantial progress" in item["quote"]
            and item["quote"] in text
            for item in claims
        ))

    def test_topic_ranked_claims_keep_open_ended_research_result_before_source_cap(self):
        claims = [
            {"claim": "A research team tested six deployments with five replicas.",
             "quote": "A research team tested six deployments with five replicas."},
            {"claim": "The agents completed engineering but could not make substantial progress on the research questions.",
             "quote": "The agents completed all of the engineering without human help, yet could not make substantial progress towards answering the research questions."},
            {"claim": "The report includes expert reviews and logs.",
             "quote": "We release the expert reviews, survey responses, agent repositories, and logs."},
        ]
        ranked = research_desk._rank_claims_for_topic(
            "Can AI agents conduct open-ended AI research?", claims
        )
        self.assertIn("substantial progress", ranked[0]["quote"])

    def test_verdict_insufficient_when_fetch_fails(self):
        with patch.object(research_desk.topic_research, "search_web", return_value=[]), \
             patch.object(research_desk, "fetch_url") as mock_fetch:
            mock_fetch.return_value = {"url": "http://bad", "ok": False, "error": "timeout"}
            res = research_desk.research_topic("test topic", source_urls=["http://bad"])
            self.assertEqual(res["verdict"], "insufficient")
            self.assertIsNotNone(res)
            self.assertIn("topic", res)

    def test_off_topic_sources_are_rejected_instead_of_becoming_primary(self):
        pages = {
            "https://example.com/kimi": {
                "url": "https://example.com/kimi",
                "ok": True,
                "title": "Kimi model research report",
                "text": "The Kimi model achieved 95% accuracy in a research report.",
                "publisher": "example.com",
            },
            "https://example.com/perplexity": {
                "url": "https://example.com/perplexity",
                "ok": True,
                "title": "Perplexity Pages shareable reports",
                "text": "Perplexity Pages can create a shareable research report with 12 sources.",
                "publisher": "example.com",
            },
        }
        with patch.object(research_desk.topic_research, "search_web", return_value=[]), \
             patch.object(research_desk, "fetch_url", side_effect=lambda url: pages[url]):
            result = research_desk.research_topic(
                "Using Perplexity Pages to create a shareable research report",
                source_urls=list(pages),
            )

        self.assertEqual(result["primary"]["url"], "https://example.com/perplexity")
        self.assertEqual([page["url"] for page in result["sources"]], ["https://example.com/perplexity"])

    def test_contradiction_detection_clear_contradiction(self):
        claims = [
            {"claim": "Model X achieves 90% accuracy on task A.", "quote": "Model X achieves 90% accuracy on task A.", "source_url": "http://a.com", "confidence": 0.7},
            {"claim": "Model X does not achieve 90% accuracy on task A; it only reaches 60% accuracy.", "quote": "Model X does not achieve 90% accuracy on task A; it only reaches 60% accuracy.", "source_url": "http://b.com", "confidence": 0.7},
        ]
        contradictions = research_desk.find_contradictions(claims)
        self.assertGreaterEqual(len(contradictions), 1)

    def test_contradiction_detection_clear_non_contradiction(self):
        claims = [
            {"claim": "Model X achieves 90% accuracy on task A.", "quote": "Model X achieves 90% accuracy on task A.", "source_url": "http://a.com", "confidence": 0.7},
            {"claim": "Model Y achieves 85% accuracy on task B.", "quote": "Model Y achieves 85% accuracy on task B.", "source_url": "http://b.com", "confidence": 0.7},
        ]
        contradictions = research_desk.find_contradictions(claims)
        self.assertEqual(len(contradictions), 0)

    def test_report_renders(self):
        research = {
            "topic": "AI test",
            "primary": {"url": "http://a.com", "publisher": "a.com", "title": "Test"},
            "secondary": [{"url": "http://b.com", "publisher": "b.com"}],
            "claims": [{"claim": "Claim one here with details", "quote": "Claim one here with details enough"}],
            "contradictions": [],
            "unsupported_numbers": [],
            "limitations": [],
            "verdict": "ok",
            "fetched_at": "2026-01-01T00:00:00Z",
            "sources": [],
            "errors": [],
        }
        report = research_desk.render_report(research)
        self.assertIn("RESEARCH REPORT", report)
        self.assertIn("PRIMARY", report)
        self.assertIn("CLAIMS", report)


if __name__ == "__main__":
    unittest.main()

def test_extractor_discards_fused_table_of_contents_metadata():
    text = (
        "2026-11-15 // 4 min .net 3 Embedding the Map Â· Notes // contents "
        "1 Getting some Maps 2 Deploying to Bunny.net 3 Embedding the Map "
        "Â· Notes I came across Protomaps in research for my latest project, "
        "Mapboard. At $0.05/1k map loads this could be 100x cheaper than Mapbox."
    )
    claims = research_desk.extract_claims(text, source_url="https://example.com/protomaps")
    assert not any("contents 1 Getting some Maps" in item["quote"] for item in claims)
    assert any("$0.05/1k map loads" in item["quote"] for item in claims)

def test_research_source_selection_counts_unique_publishers_not_multiple_docs_pages():
    pages = {
        "https://docs.example.com/protomaps/overview": {
            "url": "https://docs.example.com/protomaps/overview", "ok": True,
            "title": "Protomaps map tiles documentation overview",
            "text": "Protomaps map tiles use PMTiles archives. Version 3 defines a portable archive format for vector map data.",
        },
        "https://docs.example.com/protomaps/format": {
            "url": "https://docs.example.com/protomaps/format", "ok": True,
            "title": "Protomaps map tiles format documentation",
            "text": "Protomaps map tiles support range requests and archive metadata. The PMTiles format includes a directory and tile data.",
        },
        "https://example.edu/research/protomaps": {
            "url": "https://example.edu/research/protomaps", "ok": True,
            "title": "Protomaps map tiles research",
            "text": "Protomaps map tiles are stored in a single archive. The research describes the map data access pattern and caching behavior.",
        },
        "https://independent.org/protomaps": {
            "url": "https://independent.org/protomaps", "ok": True,
            "title": "Protomaps map tiles deployment",
            "text": "Protomaps map tiles can be served from object storage. The deployment evaluation measured cache hit rate and latency.",
        },
    }
    urls = list(pages)
    with patch.object(research_desk.topic_research, "search_web", return_value=[]), \
         patch.object(research_desk, "fetch_url", side_effect=lambda url: pages[url]):
        result = research_desk.research_topic("Protomaps map tiles", source_urls=urls, max_sources=5)
    publishers = [research_desk.lineage.publisher_of(s["url"]) for s in result["sources"]]
    assert len(publishers) == len(set(publishers))
    assert len(publishers) == 3


def test_lineage_source_type_excludes_syndication_and_directories():
    assert research_desk.lineage.source_type(
        "https://agihunt.info/en/p/123", "", "Protomaps discussion · AGI Hunt"
    ) == "aggregator"
    assert research_desk.lineage.source_type(
        "https://wares.gg/apps/protomaps", "", "Protomaps app listing"
    ) == "directory"
    assert research_desk.lineage.source_type(
        "https://docs.protomaps.com/pmtiles/", "", "PMTiles Concepts | Protomaps Docs"
    ) == "documentation"
