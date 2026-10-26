import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import topic_research


class FeedResponse:
    def __init__(self, text):
        self.text = text


class TopicResearchTests(unittest.TestCase):
    def test_rank_weights_title_relevance_and_real_engagement_without_counting_abstract_repetition(self):
        published = datetime.now(timezone.utc).isoformat()
        concise = topic_research._item(
            "AI agent beats a difficult benchmark",
            "The AI model achieved a result.",
            "Hacker News",
            "https://example.com/agent",
            published,
            100,
        )
        repetitive = topic_research._item(
            "New research",
            "AI research technology AI model research AI technology research AI model.",
            "arXiv",
            "https://example.com/paper",
            published,
            0,
        )

        self.assertGreater(concise["rank"], repetitive["rank"])
        self.assertEqual(repetitive["signals"]["summary_relevance"], 3)
        self.assertGreater(concise["signals"]["engagement"], 0)
        self.assertGreater(concise["signals"]["freshness"], 5)

    def test_rank_parses_hacker_news_unix_timestamps(self):
        current_timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        item = topic_research._item(
            "AI robotics benchmark",
            "",
            "Hacker News",
            "https://example.com/story",
            current_timestamp,
            10,
        )

        self.assertGreater(item["signals"]["freshness"], 5)

    def test_related_news_search_returns_publisher_attribution_and_source_link(self):
        feed = """<?xml version="1.0"?>
        <rss><channel><item>
          <title>AI consensus paper explained - Example News</title>
          <description>Independent coverage of a research result.</description>
          <link>https://news.google.com/rss/articles/example</link>
          <pubDate>Wed, 22 Oct 2026 10:00:00 GMT</pubDate>
          <source>Example News</source>
        </item></channel></rss>"""
        with patch("topic_research._get", return_value=FeedResponse(feed)) as get:
            results = topic_research.search_related_news("AI consensus paper")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["publisher"], "Example News")
        self.assertEqual(results[0]["url"], "https://news.google.com/rss/articles/example")
        self.assertIn("q=AI+consensus+paper", get.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
