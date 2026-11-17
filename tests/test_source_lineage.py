"""Source lineage: syndicated copies are one voice, not corroboration."""

from __future__ import annotations

import unittest

from app.research import claims, lineage

RELEASE = (
    "FOR IMMEDIATE RELEASE. Acme announced today that its AI code review tool "
    "catches 84% of security issues before merge. The tool is available now for teams."
)
DERIVATIVE = (
    "Acme says its AI code review tool catches 84% of security issues before merge, "
    "according to a company announcement this week."
)
INDEPENDENT = (
    "Our replication shows Acme's AI code review tool catches 84% of security issues "
    "before merge, measured across 900 pull requests."
)
UNRELATED = (
    "The university lab studied 1,200 pull requests and found that AI review tools "
    "miss about 30% of logic bugs in large codebases."
)


def _source(url, text, published="2025-03-04"):
    return {"url": url, "publisher": lineage.publisher_of(url), "text": text, "published": published}


class CanonicalUrlTests(unittest.TestCase):
    def test_tracking_and_fragments_are_removed(self):
        self.assertEqual(
            lineage.canonical_url("https://www.Example.com/Story/?utm_source=x&id=4#top"),
            "https://example.com/Story?id=4",
        )

    def test_trailing_slash_and_case(self):
        # The scheme is preserved: canonicalising identity must not claim a site
        # serves https when the source only gave http.
        self.assertEqual(
            lineage.canonical_url("http://WWW.example.com/path/"),
            "http://example.com/path",
        )

    def test_publisher_strips_www(self):
        self.assertEqual(lineage.publisher_of("https://www.reuters.com/x"), "reuters.com")


class SourceTypeTests(unittest.TestCase):
    def test_wire_host(self):
        self.assertEqual(lineage.source_type("https://prnewswire.com/x"), "wire")

    def test_government(self):
        self.assertEqual(lineage.source_type("https://www.nist.gov/report"), "government")

    def test_release_marker(self):
        self.assertEqual(lineage.source_type("https://acme.example.com/news", RELEASE), "press_release")


class SyndicationTests(unittest.TestCase):
    def test_identical_text_on_two_hosts_is_one_cluster(self):
        body = (
            "Acme announced that its code review tool catches 84% of security issues "
            "before merge and is available for engineering teams worldwide."
        )
        first = _source("https://wire.example.com/a", body)
        second = _source("https://mirror.example.net/a", body)
        result = lineage.cluster_sources([first, second])
        self.assertEqual(len(result["clusters"]), 1)
        cluster = result["clusters"][0]
        self.assertTrue(cluster["syndicated"])
        self.assertFalse(cluster["independent"])
        self.assertEqual(cluster["source_count"], 2)
        self.assertEqual(result["by_url"][lineage.canonical_url(first["url"])],
                         result["by_url"][lineage.canonical_url(second["url"])])

    def test_distinct_texts_stay_separate(self):
        result = lineage.cluster_sources([
            _source("https://a.example.com/x", RELEASE),
            _source("https://b.example.org/y", UNRELATED),
        ])
        self.assertEqual(len(result["clusters"]), 2)
        # Distinct texts keep their own clusters, but a press release is the
        # issuer's voice, not editorial corroboration: only the independent
        # research source may count as its own source.
        by_url = {cluster["hosts"][0]: cluster for cluster in result["clusters"]}
        self.assertFalse(by_url["a.example.com"]["independent"])
        self.assertTrue(by_url["b.example.org"]["independent"])


class IndependenceTests(unittest.TestCase):
    def setUp(self):
        self.release = _source("https://prnewswire.com/acme", RELEASE)
        self.derivative = _source("https://techdaily.example.com/acme", DERIVATIVE)
        self.independent = _source("https://lab.example.org/replication", INDEPENDENT)
        self.claim = {
            "claim": "Acme's AI code review tool catches 84% of security issues before merge.",
            "quote": "its AI code review tool catches 84% of security issues before merge",
            "source_url": self.release["url"],
        }

    def test_derivative_coverage_does_not_count(self):
        result = lineage.independent_confirmations(
            self.claim, [self.release, self.derivative]
        )
        self.assertEqual(result["distinct_clusters"], 0)
        self.assertEqual(result["dependent_clusters"], 1)
        self.assertTrue(result["matches"][0]["dependent"])

    def test_independent_replication_counts(self):
        result = lineage.independent_confirmations(
            self.claim, [self.release, self.derivative, self.independent]
        )
        self.assertGreaterEqual(result["distinct_clusters"], 1)
        self.assertTrue(any(not match["dependent"] for match in result["matches"]))

    def test_ledger_marks_derivative_only_claim_as_partial(self):
        research = {
            "topic": "AI code review",
            "verdict": "sufficient",
            "sources": [self.release, self.derivative],
            "claims": [self.claim],
            "contradictions": [],
            "errors": [],
        }
        ledger = claims.build_ledger(research)
        record = ledger["claims"][0]
        self.assertEqual(record["verification"]["status"], "partially_supported")
        self.assertIn("one voice", record["verification"]["reason"])
        self.assertEqual(record["decision"], "qualify")

    def test_ledger_marks_independent_claim_as_supported(self):
        research = {
            "topic": "AI code review",
            "verdict": "sufficient",
            "sources": [self.release, self.independent],
            "claims": [self.claim],
            "contradictions": [],
            "errors": [],
        }
        ledger = claims.build_ledger(research)
        self.assertEqual(ledger["claims"][0]["verification"]["status"], "supported")
        self.assertEqual(ledger["claims"][0]["decision"], "include")


if __name__ == "__main__":
    unittest.main()
