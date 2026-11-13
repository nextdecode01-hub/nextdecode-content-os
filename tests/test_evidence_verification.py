"""Phase 10.1.1 — evidence verification hardening.

Covers the five review findings: partial matches must not establish complete
support, subdomains of one organisation are one publisher, corroboration is
judged on the whole claim, historical facts are not marked outdated, and each
rule needs a negative case so it cannot be satisfied by accident.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.research import claims, lineage

RMF_CLAIM = (
    "The NIST AI Risk Management Framework (AI RMF 1.0), released by the National "
    "Institute of Standards and Technology in January 2023, is a voluntary framework "
    "designed to help organizations manage risks associated with AI systems "
    "throughout their lifecycle."
)
RELATION_CLAIM = "The AI RMF 1.0 is being revised as part of the White House AI Action Plan."
FULL_RELATION_PAGE = (
    "NIST says the AI RMF 1.0 is being revised as part of the White House AI Action Plan."
)
HALF_RELATION_PAGE = "The AI RMF 1.0 is being revised to address generative AI risks."
AIRIA = "https://airia.com/blog/nist-ai-risk-management-framework"
NIST_WWW = "https://www.nist.gov/itl/ai-risk-management-framework"
NIST_AIRC = "https://airc.nist.gov/airmf-resources/"
NIST_BARE = "https://nist.gov/top"


def _source(url: str, text: str, published: str = "2026-01-15") -> dict:
    return {"url": url, "publisher": lineage.publisher_of(url), "text": text,
            "published": published, "retrieved_at": "2026-10-30T00:00:00+00:00"}


def _ledger(claim_list: list[dict], sources: list[dict], *, now=None, stale_days: int = 730) -> dict:
    return claims.build_ledger(
        {
            "topic": "AI RMF",
            "verdict": "sufficient",
            "fetched_at": "2026-10-30T00:00:00+00:00",
            "sources": sources,
            "claims": claim_list,
            "contradictions": [],
            "errors": [],
        },
        now=now,
        stale_days=stale_days,
    )


class CompletenessTests(unittest.TestCase):
    def test_partial_page_does_not_confirm_a_relationship(self):
        support = lineage.anchor_support(RELATION_CLAIM, HALF_RELATION_PAGE)
        self.assertNotEqual(support["strength"], "full")
        self.assertIn("White House AI Action Plan.", support["missing_entities"])

    def test_page_naming_both_subjects_confirms_it(self):
        support = lineage.anchor_support(RELATION_CLAIM, FULL_RELATION_PAGE)
        self.assertEqual(support["strength"], "full")

    def test_missing_number_blocks_full_support(self):
        claim = "The survey found that 84% of teams adopted the framework."
        page = "The survey found that teams adopted the framework quickly."
        support = lineage.anchor_support(claim, page)
        self.assertNotEqual(support["strength"], "full")
        self.assertIn("84%", support["missing_values"])

    def test_partial_evidence_is_still_recorded(self):
        ledger = _ledger(
            [{"claim": RELATION_CLAIM, "quote": RELATION_CLAIM, "source_url": AIRIA}],
            [_source(AIRIA, RELATION_CLAIM), _source(NIST_WWW, HALF_RELATION_PAGE)],
        )
        record = ledger["claims"][0]
        self.assertEqual(record["verification"]["status"], "partially_supported")
        partial = [entry for entry in record["support"] if entry["relation"] == "partial_match"]
        self.assertTrue(partial)
        self.assertTrue(partial[0]["excerpt"])
        self.assertLess(partial[0]["entity_coverage"], 1.0)

    def test_same_numbers_different_subject_is_not_support(self):
        claim = "Acme's tool catches 84% of security issues before merge."
        page = "Another product catches 84% of bugs after merge, reported in 2020."
        support = lineage.anchor_support(claim, page)
        self.assertNotEqual(support["strength"], "full")

    def test_empty_page_supports_nothing(self):
        self.assertEqual(lineage.anchor_support(RMF_CLAIM, "")["strength"], "none")


class InstitutionTests(unittest.TestCase):
    def test_nist_subdomains_are_one_institution(self):
        hosts = {lineage.institution_of(url) for url in (NIST_BARE, NIST_WWW, NIST_AIRC)}
        self.assertEqual(hosts, {"nist.gov"})

    def test_www_prefix_is_not_a_second_publisher(self):
        self.assertEqual(lineage.institution_of("https://www.example.com/a"),
                         lineage.institution_of("https://example.com/b"))

    def test_platform_subdomains_are_not_merged(self):
        self.assertNotEqual(lineage.institution_of("https://acme.github.io/x"),
                            lineage.institution_of("https://rival.github.io/y"))
        self.assertEqual(lineage.institution_of("https://acme.github.io/x"), "acme.github.io")

    def test_second_level_public_suffixes_are_kept(self):
        self.assertEqual(lineage.institution_of("https://www.bbc.co.uk/news"), "bbc.co.uk")
        self.assertEqual(lineage.institution_of("https://metro.co.uk/x"), "metro.co.uk")

    def test_unrelated_organisations_stay_distinct(self):
        self.assertNotEqual(lineage.institution_of(NIST_WWW),
                            lineage.institution_of("https://www.acme.com/x"))

    def test_four_nist_pages_are_one_confirmation_at_most(self):
        text = RMF_CLAIM
        sources = [_source(AIRIA, text), _source(NIST_WWW, text), _source(NIST_AIRC, text),
                   _source(NIST_BARE, text)]
        ledger = _ledger([{"claim": text, "quote": text, "source_url": AIRIA}], sources)
        record = ledger["claims"][0]
        self.assertEqual(record["lineage"]["backing_institutions"], ["nist.gov"])
        self.assertEqual(record["lineage"]["distinct_clusters"], 1)

    def test_own_institution_pages_never_corroborate_themselves(self):
        sources = [_source(NIST_WWW, RMF_CLAIM), _source(NIST_AIRC, RMF_CLAIM)]
        ledger = _ledger([{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": NIST_WWW}],
                         sources)
        record = ledger["claims"][0]
        self.assertEqual(record["lineage"]["distinct_clusters"], 0)
        self.assertEqual(record["verification"]["status"], "partially_supported")

    def test_summary_counts_pages_and_institutions_separately(self):
        sources = [_source(AIRIA, RMF_CLAIM), _source(NIST_WWW, RMF_CLAIM),
                   _source(NIST_AIRC, RMF_CLAIM)]
        ledger = _ledger([{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}], sources)
        self.assertEqual(ledger["summary"]["source_pages"], 3)
        self.assertEqual(ledger["summary"]["source_institutions"], 2)


class FreshnessTests(unittest.TestCase):
    def test_historical_fact_is_not_outdated(self):
        sentence = ("NIST released the AI RMF 1.0 on January 26, 2023 after a "
                    "consensus process with many organisations.")
        self.assertEqual(claims.temporal_kind(sentence), "historical")
        ledger = _ledger(
            [{"claim": sentence, "quote": sentence, "source_url": NIST_WWW}],
            [_source(NIST_WWW, sentence, "2019-01-26")],
            now=datetime(2026, 10, 30, tzinfo=timezone.utc),
            stale_days=365,
        )
        record = ledger["claims"][0]
        self.assertNotEqual(record["verification"]["status"], "outdated")
        self.assertEqual(record["temporal"], "historical")

    def test_current_status_claim_does_go_outdated(self):
        sentence = "The framework is currently under revision for generative AI risks."
        self.assertEqual(claims.temporal_kind(sentence), "current")
        ledger = _ledger(
            [{"claim": sentence, "quote": sentence, "source_url": NIST_WWW}],
            [_source(NIST_WWW, sentence, "2019-01-26")],
            now=datetime(2026, 10, 30, tzinfo=timezone.utc),
            stale_days=365,
        )
        self.assertEqual(ledger["claims"][0]["verification"]["status"], "outdated")
        self.assertEqual(ledger["claims"][0]["decision"], "research_more")

    def test_forecast_uses_the_shorter_window(self):
        sentence = "NIST expects adoption to reach 50% of federal teams by 2027."
        self.assertEqual(claims.temporal_kind(sentence), "forecast")
        ledger = _ledger(
            [{"claim": sentence, "quote": sentence, "source_url": NIST_WWW}],
            [_source(NIST_WWW, sentence, "2024-06-01")],
            now=datetime(2026, 10, 30, tzinfo=timezone.utc),
            stale_days=3650,
        )
        self.assertEqual(ledger["claims"][0]["verification"]["status"], "outdated")

    def test_future_verb_in_a_relative_clause_does_not_make_it_a_forecast(self):
        sentence = ("On March 30, 2023, NIST launched the Trustworthy and Responsible AI "
                    "Resource Center, which will facilitate implementation of the framework.")
        self.assertEqual(claims.temporal_kind(sentence), "historical")
        ledger = _ledger(
            [{"claim": sentence, "quote": sentence, "source_url": NIST_WWW}],
            [_source(NIST_WWW, sentence, "2023-03-30")],
            now=datetime(2026, 10, 30, tzinfo=timezone.utc),
            stale_days=365,
        )
        self.assertNotEqual(ledger["claims"][0]["verification"]["status"], "outdated")

    def test_temporal_kind_rejects_a_bare_year_as_forecast(self):
        self.assertEqual(claims.temporal_kind("The report covers 2023 outcomes."), "historical")
        self.assertEqual(claims.temporal_kind("The tool is available today."), "current")


class ClaimLevelRecordTests(unittest.TestCase):
    def test_support_record_carries_coverage_and_excerpt(self):
        ledger = _ledger(
            [{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}],
            [_source(AIRIA, RMF_CLAIM), _source(NIST_WWW, RMF_CLAIM)],
        )
        support = ledger["claims"][0]["support"]
        corroboration = [entry for entry in support if entry["relation"] == "corroboration"]
        self.assertEqual(len(corroboration), 1)
        entry = corroboration[0]
        self.assertEqual(entry["institution"], "nist.gov")
        self.assertEqual(entry["strength"], "full")
        self.assertEqual(entry["entity_coverage"], 1.0)
        self.assertIn("voluntary", entry["excerpt"].lower())

    def test_conflict_keeps_both_values(self):
        claim = "NIST released the AI RMF 1.0 on January 26, 2023."
        contradicting = "NIST released the AI RMF 1.0 on March 30, 2024 after review."
        ledger = _ledger(
            [{"claim": claim, "quote": claim, "source_url": AIRIA}],
            [_source(AIRIA, claim), _source(NIST_WWW, contradicting)],
        )
        record = ledger["claims"][0]
        self.assertEqual(record["verification"]["status"], "conflicting")
        conflict = record["contradict"][0]
        self.assertEqual(conflict["kind"], "value_conflict")
        self.assertTrue(conflict["expected"] and conflict["found"])
        self.assertTrue(conflict["excerpt"])

    def test_lineage_note_states_the_rule(self):
        ledger = _ledger(
            [{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}],
            [_source(AIRIA, RMF_CLAIM)],
        )
        self.assertIn("by institution", ledger["claims"][0]["lineage"]["note"])


class CorroborationCounterTests(unittest.TestCase):
    """Task 2: the counter must mean *independent* institutions only."""

    def test_same_institution_alone_does_not_count(self):
        ledger = _ledger(
            [{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": NIST_WWW}],
            [_source(NIST_WWW, RMF_CLAIM), _source(NIST_AIRC, RMF_CLAIM),
             _source(NIST_BARE, RMF_CLAIM)],
        )
        self.assertEqual(ledger["summary"]["independently_corroborated"], 0)
        self.assertEqual(ledger["claims"][0]["lineage"]["backing_institutions"], [])

    def test_independent_institution_counts_once(self):
        ledger = _ledger(
            [{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}],
            [_source(AIRIA, RMF_CLAIM), _source(NIST_WWW, RMF_CLAIM)],
        )
        self.assertEqual(ledger["summary"]["independently_corroborated"], 1)

    def test_partial_evidence_never_inflates_the_counter(self):
        partial_page = ("The NIST AI Risk Management Framework is a voluntary framework "
                        "used by organizations to manage AI risk.")
        ledger = _ledger(
            [{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}],
            [_source(AIRIA, RMF_CLAIM), _source(NIST_WWW, partial_page)],
        )
        record = ledger["claims"][0]
        self.assertEqual(record["verification"]["status"], "partially_supported")
        self.assertEqual(ledger["summary"]["independently_corroborated"], 0)

    def test_many_pages_from_one_institution_count_as_one(self):
        ledger = _ledger(
            [{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}],
            [_source(AIRIA, RMF_CLAIM), _source(NIST_WWW, RMF_CLAIM),
             _source(NIST_AIRC, RMF_CLAIM), _source(NIST_BARE, RMF_CLAIM)],
        )
        self.assertEqual(ledger["summary"]["independently_corroborated"], 1)
        self.assertEqual(ledger["claims"][0]["lineage"]["backing_institutions"], ["nist.gov"])
        self.assertGreater(len(ledger["claims"][0]["support"]), 2)

    def test_counter_matches_the_per_claim_view(self):
        ledger = _ledger(
            [{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": NIST_WWW},
             {"claim": RELATION_CLAIM, "quote": RELATION_CLAIM, "source_url": AIRIA}],
            [_source(NIST_WWW, RMF_CLAIM), _source(NIST_AIRC, RMF_CLAIM),
             _source(AIRIA, RELATION_CLAIM), _source(NIST_WWW, FULL_RELATION_PAGE)],
        )
        counted = sum(1 for claim in ledger["claims"]
                      if claim["lineage"]["backing_institutions"])
        self.assertEqual(ledger["summary"]["independently_corroborated"], counted)


if __name__ == "__main__":
    unittest.main()
