"""Evidence-to-script mapping and proportionality checks (deterministic)."""

from __future__ import annotations

import unittest

from app.script import evidence


def _claim(claim_id, narration, quote, *, kind="statistic", status="supported"):
    return {
        "claim_id": claim_id,
        "narration": narration,
        "quote": quote,
        "claim_type": kind,
        "verification": {"status": status},
    }


CLAIMS = [
    _claim(
        "clm_aaaaaaaaaa",
        "Acme's AI code review tool catches 84% of security issues before merge.",
        "its AI code review tool catches 84% of security issues before merge",
    ),
    _claim(
        "clm_bbbbbbbbbb",
        "AI code review tools will replace manual review by 2027.",
        "AI review adoption will grow, but the study says nothing about replacement",
        kind="forecast",
        status="partially_supported",
    ),
]


class MappingTests(unittest.TestCase):
    def test_sentence_maps_to_its_claim(self):
        result = evidence.map_sentences(
            "Acme's tool catches 84% of security issues before merge.", CLAIMS
        )
        self.assertEqual(result["sentences"][0]["claim_ids"], ["clm_aaaaaaaaaa"])

    def test_unrelated_sentence_stays_unmapped(self):
        result = evidence.map_sentences("The office lights hum at night.", CLAIMS)
        self.assertEqual(result["sentences"][0]["claim_ids"], [])
        self.assertTrue(result["sentences"][0]["factual"] is False)

    def test_source_attribution_is_factual_even_without_a_number(self):
        result = evidence.map_sentences(
            "The paper said it matched OpenAI o1 on most benchmarks.", CLAIMS
        )
        row = result["sentences"][0]
        self.assertTrue(row["factual"])
        self.assertIn(row["sentence"], result["unmapped"])

    def test_named_product_capability_and_workflow_actions_are_factual(self):
        sentences = [
            "Google DeepMind's Co-Scientist is designed to help scientists generate hypotheses.",
            "Its multi-agent workflow proposes ideas and ranks promising directions.",
            "Nature has described research assistants as tools for hypothesis generation.",
            "AI can accelerate parts of research through literature search.",
        ]
        for sentence in sentences:
            with self.subTest(sentence=sentence):
                self.assertTrue(evidence.looks_factual(sentence))

    def test_factual_sentence_without_claim_is_reported(self):
        result = evidence.map_sentences(
            "A separate survey found that 71% of teams changed tools last year.", CLAIMS
        )
        self.assertIn("A separate survey found that 71% of teams changed tools last year.",
                      result["unmapped"])
        self.assertTrue(any(flag["flag"] == "unsupported_factual" for flag in result["flags"]))


class ProportionalityTests(unittest.TestCase):
    def test_causation_not_in_excerpt_is_flagged(self):
        result = evidence.map_sentences(
            "Acme's tool catches 84% of security issues, which proves it prevents breaches.",
            CLAIMS,
        )
        flags = [flag["flag"] for flag in result["flags"]]
        self.assertIn("causation", flags)

    def test_forecast_stated_as_certainty_is_flagged(self):
        result = evidence.map_sentences(
            "AI code review tools will replace manual review by 2027 with certainty.",
            CLAIMS,
        )
        flags = [flag["flag"] for flag in result["flags"]]
        self.assertIn("forecast_as_fact", flags)

    def test_hedged_forecast_is_not_flagged(self):
        result = evidence.map_sentences(
            "AI code review tools may replace some manual review by 2027.",
            CLAIMS,
        )
        flags = [flag["flag"] for flag in result["flags"]]
        self.assertNotIn("forecast_as_fact", flags)

    def test_number_missing_from_evidence_is_flagged(self):
        result = evidence.map_sentences(
            "Acme's tool catches 97% of security issues before merge.", CLAIMS
        )
        flags = [flag["flag"] for flag in result["flags"]]
        self.assertIn("number_not_in_evidence", flags)

    def test_unqualified_partially_supported_claim_is_flagged(self):
        claims = [_claim(
            "clm_partial", "Acme's tool costs less than the alternative.",
            "Acme reported lower costs in one internal benchmark.",
            status="partially_supported",
        )]
        result = evidence.map_sentences(
            "Acme's tool costs less than the alternative.", claims
        )
        self.assertIn(
            "unqualified_partially_supported",
            [flag["flag"] for flag in result["flags"]],
        )

    def test_unqualified_unverified_claim_is_flagged(self):
        claims = [_claim("clm_cccccccccc", "Acme raised $50 million in funding.",
                         "Acme raised $50 million in funding.", kind="funding", status="unverified")]
        result = evidence.map_sentences("Acme raised $50 million in funding.", claims)
        flags = [flag["flag"] for flag in result["flags"]]
        self.assertIn("unqualified_unverified", flags)

    def test_unattributed_causation_is_flagged(self):
        result = evidence.map_sentences("That proves AI review is perfectly reliable.", CLAIMS)
        flags = [flag["flag"] for flag in result["flags"]]
        self.assertIn("unattributed_causation", flags)


class CoverageTests(unittest.TestCase):
    def test_coverage_counts_mapped_sentences(self):
        script = (
            "Acme's tool catches 84% of security issues before merge. "
            "The office lights hum at night."
        )
        result = evidence.map_sentences(script, CLAIMS)
        summary = evidence.coverage(script, result["flags"], result)
        self.assertEqual(summary["sentences"], 2)
        self.assertEqual(summary["mapped"], 1)
        self.assertEqual(summary["traceability"], 0.5)


if __name__ == "__main__":
    unittest.main()

def test_mapping_matches_paraphrased_numeric_claim_at_safe_threshold():
    claim = _claim(
        "clm_map139",
        "In practical terms, storing the 139GB world map with replication to most continents (5x) will run you about $5/month in storage fees.",
        "In practical terms, storing the 139GB world map with replication to most continents (5x) will run you about $5/month in storage fees.",
        status="partially_supported",
    )
    result = evidence.map_sentences(
        "The whole world vector set is about 139 GB; replicating it to five edge nodes costs roughly $5 a month in storage.",
        [claim],
    )
    assert result["sentences"][0]["claim_ids"] == ["clm_map139"]
