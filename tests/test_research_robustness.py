import unittest
from unittest.mock import patch, MagicMock
from app.research import desk
from app.research import topics


class TestResearchRobustness(unittest.TestCase):
    """Test research desk robustness for non-tech topics."""

    def test_research_topic_with_empty_search_returns_insufficient(self):
        """When search returns nothing, research should be insufficient."""
        with patch.object(topics, "search_web", return_value=[]):
            result = desk.research_topic("completely unknown topic")
        self.assertEqual(result["verdict"], "insufficient")
        self.assertIn("no candidate source URLs for topic", result["errors"])

    def test_research_topic_with_unfetchable_urls_reports_errors(self):
        """When all URLs are unfetchable, research should be insufficient."""
        with patch.object(topics, "search_web", return_value=[{"url": "https://example.com/blocked"}]), \
             patch.object(desk, "fetch_url", return_value={"ok": False, "error": "HTTP 403", "url": "https://example.com/blocked"}):
            result = desk.research_topic("test topic")
        self.assertEqual(result["verdict"], "insufficient")
        self.assertTrue(len(result["errors"]) > 0)

    def test_research_topic_with_no_claims_returns_insufficient(self):
        """When page fetches succeed but no claims extracted, verdict should be insufficient."""
        page = {
            "url": "https://example.com/page",
            "ok": True,
            "title": "Some page",
            "text": "This is some text without numbers or technical claims.",
            "publisher": "example.com",
        }
        with patch.object(topics, "search_web", return_value=[{"url": page["url"]}]), \
             patch.object(desk, "fetch_url", return_value=page), \
             patch.object(desk, "extract_claims", return_value=[]):
            result = desk.research_topic("test topic")
        self.assertEqual(result["verdict"], "insufficient")

    def test_research_requires_authoritative_or_multiple_editorial_sources(self):
        """A primary source plus independent reporting can support strong research."""
        pages = [
            {
                "url": "https://www.nist.gov/itl/ai-data-center-power",
                "ok": True,
                "title": "AI data center energy research",
                "text": "AI data centers consumed 415 TWh of electricity in 2024. AI data center energy use is measured across servers and cooling.",
                "publisher": "nist.gov",
            },
            {
                "url": "https://example.com/analysis/ai-data-center-energy",
                "ok": True,
                "title": "AI data center energy analysis",
                "text": "AI data centers require electricity for servers and cooling systems. The growth of AI computing changes data center planning.",
                "publisher": "example.com",
            },
        ]

        def fake_extract(text, source_url=""):
            sentence = (
                "AI data centers consumed 415 TWh of electricity in 2024."
                if "nist.gov" in source_url
                else "AI data centers require electricity for servers and cooling systems."
            )
            return [{"claim": sentence, "quote": sentence, "source_url": source_url}]

        with patch.object(topics, "search_web", return_value=[{"url": page["url"]} for page in pages]), \
             patch.object(desk, "fetch_url", side_effect=pages), \
             patch.object(desk, "extract_claims", side_effect=fake_extract):
            result = desk.research_topic("AI data centers")

        self.assertEqual(result["verdict"], "sufficient")
        self.assertTrue(result["claims"])
        self.assertEqual(result["source_quality"]["authoritative_source_count"], 1)
        self.assertEqual(result["source_quality"]["editorial_source_count"], 1)

    def test_single_reporting_source_is_not_sufficient_for_strong_production(self):
        page = {
            "url": "https://example.com/analysis/ai-data-center-energy",
            "ok": True,
            "title": "AI data center energy analysis",
            "text": "AI data centers require electricity for servers and cooling systems. The growth of AI computing changes data center planning.",
            "publisher": "example.com",
        }
        claim = "AI data centers require electricity for servers and cooling systems."
        with patch.object(topics, "search_web", return_value=[{"url": page["url"]}]), \
             patch.object(desk, "fetch_url", return_value=page), \
             patch.object(desk, "extract_claims", return_value=[{
                 "claim": claim, "quote": claim, "source_url": page["url"],
             }]):
            result = desk.research_topic("AI data centers")

        self.assertEqual(result["verdict"], "insufficient")
        self.assertEqual(result["source_quality"]["editorial_source_count"], 1)
        self.assertEqual(result["source_quality"]["independent_source_count"], 1)

    def test_reconciled_nov16_blog_heavy_source_mix_is_rejected(self):
        """Regression for the actual run: four blogs plus one reporting outlet."""
        urls = [
            "https://suhasbhairav.com/blog/can-ai-agents-audit-technical-documentation-for-factual-accuracy",
            "https://www.claramiai.com/blog/how-to-verify-claims-in-a-research-paper-a-systematic-guide-to-academic-accuracy",
            "https://aiqlabs.ai/blog/how-to-verify-data-source-accuracy-for-trusted-ai",
            "https://www.trysight.ai/blog/how-ai-models-verify-information-accuracy",
            "https://www.singlegrain.com/artificial-intelligence/ai-fact-verification-for-reliable-professional-use/",
        ]
        distinct_texts = [
            "AI agents audit technical documentation by cross-referencing content against trusted sources and knowledge graphs.",
            "Verifying claims in a research paper requires checking primary citations, provenance and the exact wording of source evidence.",
            "AI data accuracy depends on real-time multi-source cross-checking and clear records of where each factual statement originated.",
            "AI models verify information by comparing answer statements with retrieved source passages and identifying unsupported details.",
            "Professional fact verification workflows connect each claim to source material and send uncertain statements for human review.",
        ]
        pages = [{
            "url": url,
            "ok": True,
            "title": "AI agents verify claims against primary sources",
            "text": distinct_texts[index],
            "publisher": url.split("/")[2],
        } for index, url in enumerate(urls)]

        def fake_extract(text, source_url=""):
            sentence = (
                "AI agents verify claims against primary sources by checking technical documentation."
            )
            return [{"claim": sentence, "quote": sentence, "source_url": source_url}]

        with patch.object(desk, "fetch_url", side_effect=pages), \
             patch.object(desk, "extract_claims", side_effect=fake_extract):
            result = desk.research_topic(
                "How AI agents verify claims against primary sources",
                source_urls=urls,
            )

        self.assertEqual(result["independent_source_count"], 5)
        self.assertEqual(result["source_quality"]["authoritative_source_count"], 0)
        self.assertEqual(result["source_quality"]["editorial_source_count"], 1)
        self.assertEqual(result["verdict"], "insufficient")

    def test_blog_only_research_is_not_sufficient_for_strong_production(self):
        """Several independent SEO/blog pages are not an authoritative evidence base."""
        pages = [
            {
                "url": "https://example.ai/blog/ai-data-center-energy",
                "ok": True,
                "title": "AI data center energy guide",
                "text": "AI data centers consume electricity for servers and cooling systems. This affects data center energy demand.",
                "publisher": "example.ai",
            },
            {
                "url": "https://another.example/blog/ai-computing-energy",
                "ok": True,
                "title": "AI computing energy guide",
                "text": "AI computing requires electricity for data centers and cooling infrastructure. Operators monitor power use.",
                "publisher": "another.example",
            },
        ]

        def fake_extract(text, source_url=""):
            sentence = "AI data centers consume electricity for servers and cooling systems."
            return [{"claim": sentence, "quote": sentence, "source_url": source_url}]

        with patch.object(topics, "search_web", return_value=[{"url": page["url"]} for page in pages]), \
             patch.object(desk, "fetch_url", side_effect=pages), \
             patch.object(desk, "extract_claims", side_effect=fake_extract):
            result = desk.research_topic("AI data centers")

        self.assertEqual(result["verdict"], "insufficient")
        self.assertEqual(result["source_quality"]["authoritative_source_count"], 0)
        self.assertEqual(result["source_quality"]["editorial_source_count"], 0)
        self.assertTrue(any("source authority" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()