import unittest
from unittest.mock import patch

import research_desk


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

    def test_verbatim_quote_guarantee(self):
        text = "The new model achieves 95% accuracy on the benchmark. This is a big improvement over previous work which had 80% accuracy."
        claims = research_desk.extract_claims(text, source_url="http://example.com")
        for c in claims:
            self.assertIn(c["quote"], text)
            self.assertGreaterEqual(len(c["quote"].split()), 8)

    def test_verdict_insufficient_when_fetch_fails(self):
        with patch.object(research_desk, "fetch_url") as mock_fetch:
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
        with patch.object(research_desk, "fetch_url", side_effect=lambda url: pages[url]):
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
