import unittest
from unittest.mock import patch

from api import main as api_main
from app.research import desk
from app.research import topics
from app.visuals import visual_assets as visual_assets


class FakeResponse:
    def __init__(self, text="", status_code=200, content_type="text/html"):
        self.text = text
        self.content = text.encode()
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}


class WebSearchTests(unittest.TestCase):
    DDG_HTML = """
    <a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa&amp;rut=1">First &amp; Title</a>
    <a rel="nofollow" class="result__a" href="https://example.com/b">Second result</a>
    <a rel="nofollow" class="result__a" href="https://news.google.com/rss/articles/unreadable">Unreadable</a>
    """

    def test_search_web_unwraps_redirects_and_drops_google_news(self):
        with patch.object(topics, "_get", return_value=FakeResponse(self.DDG_HTML)):
            results = topics.search_web("AI data centers", limit=5)

        self.assertEqual([item["url"] for item in results], ["https://example.com/a", "https://example.com/b"])
        self.assertEqual(results[0]["title"], "First & Title")

    def test_search_web_dedupes_mirrored_urls(self):
        html = """
        <a class="result__a" href="https://example.com/a">One</a>
        <a class="result__a" href="https://www.example.com/a/">Two</a>
        """
        with patch.object(topics, "_get", return_value=FakeResponse(html)):
            results = topics.search_web("topic")

        self.assertEqual(len(results), 1)

    def test_search_web_falls_back_to_bing_news(self):
        feed = """<?xml version="1.0"?>
        <rss><channel><item>
          <title>Grid pressure from AI - Example</title>
          <description>Coverage.</description>
          <link>https://www.bing.com/news/apiclick.aspx?url=https%3A%2F%2Fexample.com%2Fstory&amp;c=1</link>
        </item></channel></rss>"""
        with patch.object(topics, "_duckduckgo_results", side_effect=RuntimeError("blocked")), patch.object(
            topics, "_get", return_value=FakeResponse(feed)
        ):
            results = topics.search_web("AI grid pressure")

        self.assertEqual(results[0]["url"], "https://example.com/story")

    def test_parse_xml_refuses_doctype_entities(self):
        with self.assertRaises(ValueError):
            topics._parse_xml('<!DOCTYPE rss [<!ENTITY x "y">]><rss/>')

    def test_search_web_rejects_tiny_queries(self):
        self.assertEqual(topics.search_web("a"), [])


class DeskSourceTests(unittest.TestCase):
    def test_topic_without_urls_searches_the_topic_instead_of_feeds(self):
        page = {
            "url": "https://example.com/ai-power",
            "ok": True,
            "title": "AI data centers and electricity demand",
            "text": "AI data centers consumed about 415 terawatt-hours of electricity in 2024, according to the grid report.",
            "publisher": "example.com",
        }
        with patch.object(topics, "search_web", return_value=[{"url": page["url"]}]), patch.object(
            desk, "fetch_url", return_value=page
        ), patch.object(topics, "discover_topics", side_effect=AssertionError("must not use feed discovery")):
            result = desk.research_topic("AI data centers and electricity demand")

        self.assertEqual([source["url"] for source in result["sources"]], [page["url"]])
        self.assertEqual(result["verdict"], "sufficient")

    def test_research_reports_insufficient_when_search_finds_nothing(self):
        with patch.object(topics, "search_web", return_value=[]):
            result = desk.research_topic("completely unknown topic")

        self.assertEqual(result["verdict"], "insufficient")
        self.assertIn("no candidate source URLs for topic", result["errors"])

    def test_fetch_url_rejects_http_errors(self):
        with patch.object(desk.requests, "get", return_value=FakeResponse("blocked", status_code=403)):
            result = desk.fetch_url("https://example.com/blocked")

        # Phase 10.1: a refusal is retried once with document content negotiation
        # and then reported for manual review instead of being silently dropped.
        self.assertFalse(result["ok"])
        self.assertTrue(result["error"].startswith("HTTP 403"))
        self.assertTrue(result["manual_review_required"])
        self.assertEqual(result["text"], "")

    def test_fetch_url_rejects_non_text_payloads(self):
        with patch.object(desk.requests, "get", return_value=FakeResponse("%PDF", content_type="application/pdf")):
            result = desk.fetch_url("https://example.com/paper.pdf")

        self.assertFalse(result["ok"])
        self.assertIn("unsupported content-type", result["error"])

    def test_dedupe_source_urls_collapses_arxiv_mirrors(self):
        urls = [
            "https://arxiv.org/abs/2509.07218",
            "https://arxiv.org/html/2509.07218v1",
            "https://arxiv.org/pdf/2509.07218",
            "https://example.com/a",
            "https://example.com/a/",
        ]
        self.assertEqual(desk._dedupe_source_urls(urls), ["https://arxiv.org/abs/2509.07218", "https://example.com/a"])


class VisualReliabilityTests(unittest.TestCase):
    def test_redact_hides_query_credentials(self):
        redacted = visual_assets._redact("GET https://x/y?key=sk_live_123&token=abc&z=1")
        self.assertNotIn("sk_live_123", redacted)
        self.assertNotIn("token=abc", redacted)
        self.assertIn("key=***", redacted)

    def test_image_signature_validation(self):
        self.assertTrue(visual_assets._looks_like_image(b"\x89PNG\r\n\x1a\n" + b"0" * 2000))
        self.assertTrue(visual_assets._looks_like_image(b"\xff\xd8\xff" + b"0" * 2000))
        self.assertFalse(visual_assets._looks_like_image(b"<html>rate limited</html>" * 100))

    def test_chain_skips_unconfigured_providers_but_keeps_keyless_pollinations(self):
        visual_assets._PROVIDER_COOLDOWN.clear()
        with patch.object(visual_assets, "FAL_KEY", ""), patch.object(visual_assets, "REPLICATE_TOKEN", ""), patch.object(
            visual_assets, "OPENAI_KEY", ""
        ):
            chain = visual_assets._chain()

        self.assertEqual(chain[0], "pollinations")
        self.assertNotIn("fal", chain)
        self.assertNotIn("replicate", chain)
        self.assertEqual(chain[-1], "local")

    def test_rate_limited_provider_is_skipped_for_later_shots(self):
        visual_assets._PROVIDER_COOLDOWN.clear()
        visual_assets._cool_down("pollinations", "HTTP 402 (provider rejected the request)")
        chain = visual_assets._chain()
        self.assertNotIn("pollinations", chain)
        self.assertEqual(chain[-1], "local")
        visual_assets._PROVIDER_COOLDOWN.clear()

    def test_wikimedia_query_uses_subject_after_style_prefix(self):
        prompt = (
            "dark moody corporate technology visual, NO nature, NO plants, NO outdoors: "
            "futuristic corporate executive boardroom at night, software engineers team whiteboard"
        )
        queries = visual_assets._wikimedia_queries(prompt)

        self.assertTrue(queries)
        self.assertNotIn("NO", queries[0])
        self.assertTrue(queries[0].startswith("futuristic corporate"))


class ApiResultTests(unittest.TestCase):
    def test_extracts_strong_pipeline_json(self):
        output = 'log line\n{"status": "success", "title": "T", "video_path": "outputs/strong/output_short.mp4"}\n'
        result = api_main._extract_result(output)
        self.assertEqual(result["video_path"], "outputs/strong/output_short.mp4")
        self.assertEqual(result["title"], "T")

    def test_extracts_standard_pipeline_marker(self):
        output = "noise\n[SUCCESS] Final Short Ready: /home/demon/shorts_studio/outputs/output_short.mp4\n"
        self.assertEqual(
            api_main._extract_result(output)["video_path"],
            "/home/demon/shorts_studio/outputs/output_short.mp4",
        )

    def test_extracts_archived_short_fallback(self):
        output = "[+] Archived Short: /mnt/d/shorts/clip.mp4\n"
        self.assertEqual(api_main._extract_result(output)["video_path"], "/mnt/d/shorts/clip.mp4")

    def test_returns_none_without_success_marker(self):
        self.assertIsNone(api_main._extract_result("Traceback\n[!] failed"))

    def test_api_redacts_log_tails(self):
        self.assertNotIn("sk_live_123", api_main._redact("url?key=sk_live_123"))


if __name__ == "__main__":
    unittest.main()
