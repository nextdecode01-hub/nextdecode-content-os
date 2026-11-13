"""Unit tests for research feed dependencies and production reliability.

Tests for:
- RSS/Atom feed parsing
- HTTP error handling and retry behavior
- XML security (DTD/entity rejection)
- Duplicate entry deduplication
- Missing publication date handling
- Research desk integration with actual feed fetchers
- CLI --bundle behavior verification
"""
import json
import re
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import xml.etree.ElementTree as ET

from app.research import desk
from app.research import topics as topic_research

# --------------------------------------------------------------------------- #
# Fixtures and Helper Functions
# --------------------------------------------------------------------------- #

SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Test Feed</title>
  <link>https://example.com</link>
  <description>Test RSS feed</description>
  <item>
    <title>Test Article 1</title>
    <link>https://example.com/article1</link>
    <description>Test article one</description>
    <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Test Article 2</title>
    <link>https://example.com/article2</link>
    <description>Test article two</description>
    <pubDate>Tue, 02 Jan 2024 00:00:00 GMT</pubDate>
  </item>
</channel>
</rss>"""

SAMPLE_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <link href="https://example.com"/>
  <updated>2024-01-01T00:00:00Z</updated>
  <author>
    <name>Test Author</name>
  </author>
  <id>urn:test:feed</id>
  <entry>
    <title>Test Entry 1</title>
    <link href="https://example.com/entry1"/>
    <id>urn:test:entry1</id>
    <updated>2024-01-01T00:00:00Z</updated>
    <summary>Test entry one</summary>
  </entry>
  <entry>
    <title>Test Entry 2</title>
    <link href="https://example.com/entry2"/>
    <id>urn:test:entry2</id>
    <updated>2024-01-02T00:00:00Z</updated>
    <summary>Test entry two</summary>
  </entry>
</feed>"""

MALFORMED_XML_WITH_DTD = """<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ELEMENT foo ANY >
  <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
<rss><channel><title>Test</title></channel></rss>"""

MALFORMED_XML_WITH_ENTITY = """<?xml version="1.0"?>
<!ENTITY xxe SYSTEM "file:///etc/passwd">
<rss><channel><title>Test</title></channel></rss>"""

# --------------------------------------------------------------------------- #
# Test Implementation
# --------------------------------------------------------------------------- #

class TestResearchFeeds:
    """Tests for research feed parsing and validation."""

    def test_valid_rss_feed_parsing(self):
        """Valid RSS XML should be parsed and return items."""
        root = topic_research._parse_xml(SAMPLE_RSS_XML)

        assert root.tag == "rss"
        assert root.get("version") == "2.0"
        items = root.findall(".//item")
        assert len(items) == 2
        titles = [item.findtext("title") for item in items]
        links = [item.findtext("link") for item in items]
        assert titles == ["Test Article 1", "Test Article 2"]
        assert links == ["https://example.com/article1", "https://example.com/article2"]

        # The item builder must survive a real RFC-822 pubDate and keep the field.
        entry = topic_research._item(
            title=items[0].findtext("title"),
            summary=items[0].findtext("description"),
            source="Test Feed",
            url=items[0].findtext("link"),
            published=items[0].findtext("pubDate"),
        )
        assert entry is not None
        assert entry["published"] == "Mon, 01 Jan 2024 00:00:00 GMT"
        assert entry["url"] == "https://example.com/article1"
        # 2024 is far outside the freshness window, so the signal must decay to 0
        # rather than silently scoring the item as new.
        assert entry["signals"]["freshness"] == 0.0

    def test_valid_atom_feed_parsing(self):
        """Valid Atom XML should be parsed and return entries."""
        root = topic_research._parse_xml(SAMPLE_ATOM_XML)

        assert root.tag == topic_research.ATOM + "feed"
        entries = root.findall(f"{topic_research.ATOM}entry")
        assert len(entries) == 2
        ids = [entry.findtext(f"{topic_research.ATOM}id") for entry in entries]
        assert ids == ["urn:test:entry1", "urn:test:entry2"]
        hrefs = [
            entry.find(f"{topic_research.ATOM}link").get("href") for entry in entries
        ]
        assert hrefs == ["https://example.com/entry1", "https://example.com/entry2"]

        # An ISO-8601 Atom <updated> must parse without raising.
        entry = topic_research._item(
            title=entries[0].findtext(f"{topic_research.ATOM}title"),
            summary=entries[0].findtext(f"{topic_research.ATOM}summary"),
            source="Test Atom Feed",
            url=hrefs[0],
            published=entries[0].findtext(f"{topic_research.ATOM}updated"),
        )
        assert entry is not None
        assert entry["signals"]["freshness"] == 0.0

    def test_http_403_retry_with_different_accept(self):
        """HTTP 403 should trigger retry with different Accept header."""
        with patch('app.research.desk.requests.get') as mock_get:
            mock_response_403 = Mock()
            mock_response_403.status_code = 403
            mock_response_403.headers = {'Content-Type': 'text/html'}

            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_response_200.text = ('<html><body><p>The agency released the '
                                      'framework after a public comment period.</p></body></html>')
            mock_response_200.headers = {'Content-Type': 'text/html'}

            mock_get.side_effect = [mock_response_403, mock_response_200]

            result = desk.fetch_url('https://example.com/test')

            assert result['status_code'] == 200
            assert result['ok'] is True
            assert result['blocked'] is False
            assert mock_get.call_count == 2
            first_accept = mock_get.call_args_list[0][1]['headers']['Accept']
            second_accept = mock_get.call_args_list[1][1]['headers']['Accept']
            assert first_accept != second_accept
            assert 'application/pdf' in second_accept

    def test_persistent_refusal_is_reported_for_manual_review(self):
        """Two refusals stop the retry: blocked, no text, nothing invented."""
        with patch('app.research.desk.requests.get') as mock_get:
            refused = Mock(status_code=406, headers={'Content-Type': 'text/html'}, text='')
            mock_get.return_value = refused

            result = desk.fetch_url('https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf')

            assert mock_get.call_count == 2
            assert result['ok'] is False
            assert result['blocked'] is True
            assert result['manual_review_required'] is True
            assert result['text'] == ''
            assert 'manual review' in result['error']

    def test_http_500_immediate_failure(self):
        """HTTP 500 fails on the first request: a server error is not a refuser."""
        with patch('app.research.desk.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_get.return_value = mock_response

            result = desk.fetch_url('https://example.com/test')

            assert result['status_code'] == 500
            assert result['ok'] is False
            assert result['error'] == 'HTTP 500'
            assert result['blocked'] is False
            assert result['manual_review_required'] is False
            assert result['text'] == ''
            assert mock_get.call_count == 1

    def test_timeout_fails_closed_without_retry(self):
        """A timeout is reported with no text and no second attempt."""
        import requests

        with patch('app.research.desk.requests.get') as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout('timeout'),
                Mock(status_code=200, text='<html><body>Success</body></html>',
                     headers={'Content-Type': 'text/html'}),
            ]

            result = desk.fetch_url('https://example.com/test')

            assert result['ok'] is False
            assert result['text'] == ''
            assert result['status_code'] is None
            assert result['error'] == 'timeout'
            assert result['blocked'] is False
            assert mock_get.call_count == 1

    def test_malformed_xml_rejected(self):
        """XML with DTD or entity declarations should be rejected."""
        with pytest.raises(ValueError, match="refusing XML with DTD"):
            topic_research._parse_xml(MALFORMED_XML_WITH_DTD)

        with pytest.raises(ValueError, match="refusing XML with DTD"):
            topic_research._parse_xml(MALFORMED_XML_WITH_ENTITY)

        valid_root = topic_research._parse_xml(SAMPLE_RSS_XML)
        assert valid_root is not None

    def test_broken_xml_raises_parse_error(self):
        """Unclosed markup fails loudly instead of yielding a partial feed."""
        with pytest.raises(ET.ParseError):
            topic_research._parse_xml("<rss><channel><title>oops</channel></rss>")

    def test_empty_payload_is_not_a_feed(self):
        with pytest.raises(ET.ParseError):
            topic_research._parse_xml("")

    def test_duplicate_feed_entries_deduped(self):
        """Duplicate URLs should produce one output entry."""
        # Test the _dedupe_source_urls function
        urls = [
            'https://example.com/article',
            'https://example.com/article/',
            'https://example.com/article',
            'https://example.com/other'
        ]
        
        result = desk._dedupe_source_urls(urls)
        
        # The first spelling of each document is kept, in input order.
        assert result == ['https://example.com/article', 'https://example.com/other']

    def test_missing_publication_date(self):
        """Feed items without pubDate should have empty published field."""
        result = topic_research._item(
            title='Test Title',
            summary='Test Summary',
            source='Test Source',
            url='https://example.com/test',
            published='',  # Empty publication date
            score=0
        )

        assert result is not None
        assert result['published'] == ''
        # An unknown date must not be scored as fresh, and must not raise.
        assert result['signals']['freshness'] == 0.0
        assert result['url'] == 'https://example.com/test'

    def test_unparseable_publication_date_does_not_raise(self):
        """Garbage in the date field loses freshness, not the item."""
        result = topic_research._item(
            title='Test Title', summary='Test Summary', source='Test Source',
            url='https://example.com/test', published='not a date at all', score=1)
        assert result is not None
        assert result['published'] == 'not a date at all'
        assert result['signals']['freshness'] == 0.0

    def test_item_requires_a_title_and_a_url(self):
        """An entry with no link or no headline is dropped, not guessed."""
        assert topic_research._item(title='', summary='s', source='x',
                                    url='https://example.com/a') is None
        assert topic_research._item(title='t', summary='s', source='x', url='') is None

    def test_desk_feed_fetchers_not_empty(self):
        """bundle_topic_and_research() should return a complete bundle."""
        mock_candidate = {
            'title': 'Test Topic',
            'url': 'https://example.com/test',
            'rank': 10,
            'source': 'Test Source'
        }
        article = {
            'ok': True,
            'title': 'Test Article',
            'text': 'The new GPT-4 model achieves 95% accuracy on the benchmark test set.',
            'url': 'https://example.com/test',
            'published': '2024-01-01T00:00:00Z',
            'publisher': 'example.com',
            'error': '',
        }

        with patch.object(desk, '_fetch_trends', return_value=[mock_candidate]), \
             patch.object(desk, '_fetch_hacker_news', return_value=[mock_candidate]), \
             patch.object(desk, '_fetch_reddit', return_value=[mock_candidate]), \
             patch.object(desk, '_fetch_arxiv', return_value=[mock_candidate]), \
             patch.object(desk, 'fetch_url', return_value=article):

            result = desk.bundle_topic_and_research()

        # Unconditional schema: a mocked success must not be reported as an error.
        assert 'error' not in result, result
        assert result['topic'] == 'Test Topic'
        assert result['url'] == 'https://example.com/test'
        assert result['published'] == '2024-01-01T00:00:00Z'
        assert isinstance(result['claims'], list) and result['claims']
        for claim in result['claims']:
            assert claim['source_url'] == 'https://example.com/test'
            assert claim['quote'] in article['text']

    def test_bundle_reports_no_candidates_when_feeds_are_empty(self):
        """Empty feeds fail closed: an error bundle, no fetch, no invented topic."""
        with patch.object(desk, '_fetch_trends', return_value=[]), \
             patch.object(desk, '_fetch_hacker_news', return_value=[]), \
             patch.object(desk, '_fetch_reddit', return_value=[]), \
             patch.object(desk, '_fetch_arxiv', return_value=[]), \
             patch.object(desk, 'fetch_url') as mock_fetch_url, \
             patch.dict('os.environ', {'MAX_RETRIES': '3', 'MIN_RANK': '0'}):

            result = desk.bundle_topic_and_research()

        assert result == {'error': 'no candidates found'}
        mock_fetch_url.assert_not_called()

    def test_bundle_reports_no_suitable_candidate_after_retries(self):
        """A rank below MIN_RANK exhausts retries instead of being accepted."""
        weak = {'title': 'Weak Topic', 'url': 'https://example.com/weak',
                'rank': 1, 'source': 'Test Source'}
        with patch.object(desk, '_fetch_trends', return_value=[weak]), \
             patch.object(desk, '_fetch_hacker_news', return_value=[]), \
             patch.object(desk, '_fetch_reddit', return_value=[]), \
             patch.object(desk, '_fetch_arxiv', return_value=[]), \
             patch.object(desk, 'fetch_url') as mock_fetch_url, \
             patch.dict('os.environ', {'MAX_RETRIES': '2', 'MIN_RANK': '99'}):

            result = desk.bundle_topic_and_research()

        assert result == {'error': 'no suitable candidate found after retries'}
        mock_fetch_url.assert_not_called()

    def test_bundle_retries_until_rank_threshold_is_met(self):
        """The first attempt may be too weak; the retry must pick the better one."""
        weak = {'title': 'Weak Topic', 'url': 'https://example.com/weak',
                'rank': 1, 'source': 'Test Source'}
        strong = {'title': 'Strong Topic', 'url': 'https://example.com/strong',
                  'rank': 15, 'source': 'Test Source'}
        article = {'ok': True, 'title': 'Strong Article',
                   'text': 'The model reaches 95% accuracy on the benchmark.',
                   'url': 'https://example.com/strong',
                   'published': '2024-01-01T00:00:00Z'}
        with patch.dict('os.environ', {'MAX_RETRIES': '3', 'MIN_RANK': '5'}):
            with patch.object(desk, '_fetch_trends', side_effect=[[weak], [strong]]) as mock_trends, \
                 patch.object(desk, '_fetch_hacker_news', return_value=[]), \
                 patch.object(desk, '_fetch_reddit', return_value=[]), \
                 patch.object(desk, '_fetch_arxiv', return_value=[]), \
                 patch.object(desk, 'fetch_url', return_value=article) as mock_fetch_url:

                result = desk.bundle_topic_and_research(mode='normal')

        assert mock_trends.call_count == 2
        mock_fetch_url.assert_called_once_with('https://example.com/strong')
        assert 'error' not in result
        assert result['topic'] == 'Strong Topic'
        assert result['url'] == 'https://example.com/strong'
        assert result['title'] == 'Strong Article'
        assert result['published'] == '2024-01-01T00:00:00Z'
        assert result['claims']
        assert all(claim['source_url'] == 'https://example.com/strong'
                   for claim in result['claims'])

    # --------------------------------------------------------------------------- #
    # Additional Feed Integration Tests
    # --------------------------------------------------------------------------- #

    def test_feed_discovery_integration(self):
        """Discovery merges feeds, collapses duplicates and honours the limit."""
        def entry(title, url, source="Hacker News", score=10):
            return topic_research._item(title, "ai chip research", source, url, "", score)

        original = entry("Nvidia unveils new AI chip for data centers",
                         "https://a.example/article", score=100)
        repost = entry("Nvidia unveils new AI chip for data centers!",
                       "https://b.example/repost", score=80)
        quantum = entry("Quantum computing startup raises a funding round",
                        "https://c.example/quantum", source="arXiv", score=20)
        battery = entry("Battery research improves storage density",
                        "https://d.example/battery", source="Google Trends", score=5)

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(topic_research, "_fetch_hacker_news", return_value=[original, repost]), \
                 patch.object(topic_research, "_fetch_arxiv", return_value=[quantum]), \
                 patch.object(topic_research, "_fetch_trends", return_value=[battery]), \
                 patch.object(topic_research, "_fetch_reddit", return_value=[]):
                topics = topic_research.discover_topics(
                    used_topics_file=Path(tmp) / "used_topics.txt", limit=3)

        assert len(topics) == 3
        # The repost normalises to the same title, so only one survives - the
        # higher-ranked original URL, not the duplicate.
        nvidia = [topic for topic in topics if topic["title"].startswith("Nvidia")]
        assert [topic["url"] for topic in nvidia] == ["https://a.example/article"]
        for topic in topics:
            for key in ("title", "url", "source", "published", "rank", "signals"):
                assert key in topic
            assert set(topic["signals"]) == {
                "title_relevance", "source_relevance", "summary_relevance",
                "freshness", "engagement",
            }

    def test_fetch_url_error_handling(self):
        """Test fetch_url error handling for various HTTP errors."""
        import requests
        
        test_cases = [
            (401, True),
            (403, True),
            (406, True),
            (404, False),
            (500, False),
        ]
        
        for status_code, should_block in test_cases:
            with patch('app.research.desk.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_response.headers = {'Content-Type': 'text/html'}
                mock_get.return_value = mock_response
                
                result = desk.fetch_url('https://example.com/test')
                
                assert result['status_code'] == status_code
                
                # 401/403/406 should set blocked=True
                if should_block:
                    assert result.get('blocked', False) is True
                    assert result.get('manual_review_required', False) is True
                else:
                    assert result.get('blocked', False) is False
                    assert result.get('manual_review_required', False) is False
                    assert result['error'] == f'HTTP {status_code}'
                    assert result['text'] == ''

    def test_fetch_url_retry_behavior(self):
        """Test fetch_url retry on 401/403/406 with different Accept headers."""
        with patch('app.research.desk.requests.get') as mock_get:
            # First call 403 with HTML content
            mock_response_403 = Mock()
            mock_response_403.status_code = 403
            mock_response_403.headers = {'Content-Type': 'text/html'}
            
            # Second call 200 with text/plain
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_response_200.text = 'Plain text content'
            mock_response_200.headers = {'Content-Type': 'text/plain'}
            
            mock_get.side_effect = [mock_response_403, mock_response_200]
            
            result = desk.fetch_url('https://example.com/test')
            
            # Should have called get twice (initial + retry)
            assert mock_get.call_count == 2
            
            # Second call should have text/plain Accept header
            second_call_headers = mock_get.call_args_list[1][1]['headers']
            assert 'text/plain' in second_call_headers.get('Accept', '')

    def test_clean_article_text_boilerplate_removal(self):
        """Test that clean_article_text removes boilerplate correctly."""
        text_with_boilerplate = """
        <div class="article">
          <nav>All Posts Written by Staff</nav>
          <h1>The Main Article Title</h1>
          <div class="content">
            <p>This is the main content of the article. It contains important information about the topic.
            It should have multiple sentences and technical details.</p>
            <p>Another paragraph with more content to test the cleaning function.</p>
          </div>
          <div class="sidebar">
            <p>Skip to main content</p>
            <p>Share this article</p>
          </div>
        </div>
        """
        
        cleaned = desk.clean_article_text(text_with_boilerplate, "The Main Article Title")
        
        # Should not contain boilerplate markers
        assert 'all posts' not in cleaned.lower()
        assert 'written by' not in cleaned.lower()
        assert 'skip to main content' not in cleaned.lower()
        assert 'share this article' not in cleaned.lower()
        
        # Should contain main content
        assert 'main content' in cleaned.lower()
        assert 'article title' in cleaned.lower()

    def test_extract_claims_basic_functionality(self):
        """Test basic claim extraction from text."""
        text_with_claims = """
        The new GPT-4 model achieves 95% accuracy on the benchmark.
        This is a significant improvement over the previous version which had 80% accuracy.
        The study used 500 samples and was conducted over 6 months.
        """
        
        claims = desk.extract_claims(text_with_claims, source_url='https://example.com/study')

        # Each extracted claim must be traceable to the source text.
        assert claims
        for claim in claims:
            assert set(claim) >= {'claim', 'quote', 'source_url', 'confidence'}
            assert claim['source_url'] == 'https://example.com/study'
            assert claim['quote'] in text_with_claims
            assert claim['claim'] in text_with_claims or claim.get('atomic_of')

    def test_find_unsupported_numbers(self):
        """Test unsupported number detection."""
        text = "The model achieves 95% better accuracy and 2x speedup."
        source_text = "Some other comparison results."
        
        unsupported = desk.find_unsupported_numbers(text, source_text)
        
        # Multiplier tokens are matched.  Percentage tokens are currently not
        # captured by the extraction regex; that gap is reported in the Phase
        # 10.1.1 report as a residual limitation instead of being asserted away.
        assert unsupported == ['2x']
        # A number the source does contain is not reported.
        assert desk.find_unsupported_numbers('It improves 95% on the metric.',
                                             'the paper reports a 95% improvement') == []

    def test_research_topic_error_handling(self):
        """No candidate URLs must fail closed, with no invented sources."""
        with patch('app.research.topics.search_web', return_value=[]):
            result = desk.research_topic('Test Topic', source_urls=[])

        # The desk reports failures in the `errors` list; there is no singular
        # `error` key on a research bundle.
        assert result['verdict'] == 'insufficient'
        assert result['primary'] is None
        assert result['sources'] == []
        assert result['claims'] == []
        assert 'no candidate source URLs for topic' in result['errors']
        # Failing closed must not fabricate a citation.
        assert 'url' not in result or result.get('url') is None

    def test_research_topic_fetch_failures_are_recorded(self):
        """Every failed URL is reported, and nothing is claimed without a page."""
        failure = {'url': 'https://example.com/x', 'ok': False, 'text': '', 'title': '',
                   'error': 'HTTP 500', 'publisher': 'example.com', 'published': ''}
        with patch.object(desk, 'fetch_url', return_value=failure):
            result = desk.research_topic('Test Topic', source_urls=['https://example.com/x'])

        assert result['verdict'] == 'insufficient'
        assert result['claims'] == []
        assert any('HTTP 500' in message for message in result['errors'])

    def test_bundle_uses_the_highest_ranked_candidate(self):
        """Candidates are pooled across feeds; only the top-ranked one is fetched."""
        trends = [{'title': 'Trending AI chip story', 'url': 'https://trends.example/a',
                   'rank': 4, 'source': 'Google Trends'}]
        hn = [{'title': 'Hacker News AI model story', 'url': 'https://hn.example/b',
               'rank': 12, 'source': 'Hacker News'}]
        article = {
            'ok': True,
            'title': 'HN Article',
            'text': 'The AI model reaches 91% accuracy on the benchmark.',
            'url': 'https://hn.example/b',
            'published': '2024-01-01T00:00:00Z',
        }
        with patch.object(desk, '_fetch_trends', return_value=trends), \
             patch.object(desk, '_fetch_hacker_news', return_value=hn), \
             patch.object(desk, '_fetch_reddit', return_value=[]), \
             patch.object(desk, '_fetch_arxiv', return_value=[]), \
             patch.object(desk, 'fetch_url', return_value=article) as mock_fetch_url:

            result = desk.bundle_topic_and_research()

        mock_fetch_url.assert_called_once_with('https://hn.example/b')
        assert 'error' not in result
        assert result['topic'] == 'Hacker News AI model story'
        assert result['source'] == 'Hacker News'
        assert result['claims']
        assert result['claims'][0]['source_url'] == 'https://hn.example/b'

    # --------------------------------------------------------------------------- #
    # Edge Case Tests
    # --------------------------------------------------------------------------- #

    def test_empty_text_handling(self):
        """Test handling of empty or None text inputs."""
        # Test clean_article_text with empty input
        assert desk.clean_article_text('') == ''
        assert desk.clean_article_text(None) == ''
        
        # Test extract_claims with empty input
        empty_claims = desk.extract_claims('', source_url='https://example.com/test')
        assert empty_claims == []
        
        # Test find_unsupported_numbers with empty input
        unsupported = desk.find_unsupported_numbers('', '')
        assert unsupported == []

    def test_malformed_url_handling(self):
        """_dedupe_source_urls keeps fetchable http(s) URLs and collapses mirrors.

        The contract is validation plus de-duplication: empty and None entries are
        dropped, anything that is not an absolute http(s) URL is refused before it
        can reach the HTTP client, a trailing slash and a fragment are treated as
        the same document, and arXiv abs/html/pdf mirrors collapse onto the first
        form.
        """
        result = desk._dedupe_source_urls([
            'not-a-url',
            '',
            'https://example.com/valid',
            None,
            'https://example.com/duplicate/',
            'https://example.com/duplicate',
            'https://arxiv.org/abs/2509.07218',
            'https://arxiv.org/pdf/2509.07218v1',
        ])

        assert '' not in result and None not in result
        assert 'https://example.com/valid' in result
        # Trailing slash and duplicate collapse to one entry.
        assert sum(1 for url in result if url.startswith('https://example.com/duplicate')) == 1
        # arXiv mirrors collapse onto the first form.
        assert sum(1 for url in result if 'arxiv.org' in url) == 1
        # A schemeless string is never fetched.
        assert 'not-a-url' not in result
        assert len(result) == 3

    def test_fetchable_url_accepts_absolute_web_urls(self):
        for url in ('http://example.com/a', 'https://example.com/a',
                    'https://example.com:8443/paper?x=1#y', 'HTTPS://example.com/a',
                    '  https://example.com/padded  '):
            assert desk.fetchable_url(url) == url.strip()

    def test_fetchable_url_refers_non_web_schemes_and_broken_hosts(self):
        for url in ('not-a-url', 'example.com/a', '//example.com/a',
                    'file:///etc/passwd', 'data:text/html,<script>alert(1)</script>',
                    'javascript:alert(1)', 'ftp://example.com/a',
                    'https://', '', '   ', None, 0):
            assert desk.fetchable_url(url) == '', url

    def test_rejected_candidate_urls_are_reported_and_not_fetched(self):
        """A non-fetchable candidate becomes a recorded error, never a request."""
        page = {'url': 'https://example.com/real', 'ok': True, 'title': 'Real page',
                'text': 'The model reaches 91% accuracy across 500 test samples.',
                'publisher': 'example.com', 'published': '', 'error': ''}
        with patch.object(desk, 'fetch_url', return_value=page) as mock_fetch:
            result = desk.research_topic('AI model accuracy', source_urls=[
                'file:///etc/passwd', 'not-a-url', 'https://example.com/real'])

        assert [call.args[0] for call in mock_fetch.call_args_list] == ['https://example.com/real']
        assert any('non-fetchable' in message for message in result['errors'])
        assert 'file:///etc/passwd' in result['errors'][0]
        assert [source['url'] for source in result['sources']] == ['https://example.com/real']

    def test_all_candidates_rejected_fails_closed(self):
        """Nothing fetchable means no sources and no invented research."""
        with patch.object(desk, 'fetch_url') as mock_fetch:
            result = desk.research_topic('AI model accuracy',
                                         source_urls=['not-a-url', 'javascript:alert(1)'])

        mock_fetch.assert_not_called()
        assert result['verdict'] == 'insufficient'
        assert result['sources'] == []
        assert result['claims'] == []
        assert any('non-fetchable' in message for message in result['errors'])
        assert 'no candidate source URLs for topic' in result['errors']

    def test_claim_extraction_edge_cases(self):
        """Test claim extraction with edge cases."""
        # Text with no numbers or technical terms
        text_no_numbers = "This is a general discussion about something."
        claims = desk.extract_claims(text_no_numbers, source_url='https://example.com/test')
        assert claims == []
        
        # Text with only boilerplate
        boilerplate_text = "Skip to main content Written by Staff"
        claims = desk.extract_claims(boilerplate_text, source_url='https://example.com/test')
        assert claims == []

    def test_claim_extraction_attributes_each_source(self):
        """Every claim keeps the URL of the page it was taken from, verbatim."""
        sources = [
            (f'https://example.com/source{i}',
             f'The model benchmark reports 9{i}% accuracy across 500 samples.')
            for i in range(10)
        ]

        by_source = {
            url: desk.extract_claims(text, source_url=url) for url, text in sources
        }

        total = 0
        for url, text in sources:
            claims = by_source[url]
            assert claims, f'no claim extracted for {url}'
            for claim in claims:
                assert claim['source_url'] == url
                assert claim['quote'] in text
            total += len(claims)
        assert total == len(sources)
