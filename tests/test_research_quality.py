"""Phase 10.1 research-quality hardening.

Fixtures are the real Phase 10 NIST research bundle, so every test here is a
regression guard against the seven defects found in that run: boilerplate in
claim 1, one source for all 14 claims, unattached NIST evidence, compound
claims, a misclassified factual sentence, empty retrieval timestamps and the
HTTP 406 PDF refusals.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.research import atomic, claims, desk, lineage
from app.script import evidence
from app.visuals import cutouts

FIXTURE = Path(__file__).parent / "fixtures" / "phase10_nist_research.json"
AIRIA = "https://airia.com/blog/nist-ai-risk-management-framework-ai-rmf-explained"
RMF_CLAIM = (
    "The NIST AI Risk Management Framework (AI RMF 1.0), released by the National "
    "Institute of Standards and Technology in January 2023, is a voluntary framework "
    "designed to help organizations manage risks associated with AI systems "
    "throughout their lifecycle."
)
NIST_RMF_PAGE = (
    "The AI Risk Management Framework is a voluntary framework. "
    "The NIST AI Risk Management Framework (AI RMF 1.0) was released on "
    "January 26, 2023 by the National Institute of Standards and Technology. "
    "It helps organizations manage risks associated with AI systems throughout "
    "their lifecycle."
)


def _bundle() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _cleaned_claims(research: dict) -> list[dict]:
    pool = []
    for source in research["sources"]:
        cleaned = desk.clean_article_text(source.get("text", ""), source.get("title", ""))
        pool.extend(desk.extract_claims(cleaned, source_url=source["url"]))
    return desk.merge_duplicate_claims(pool)


class BoilerplateTests(unittest.TestCase):
    def test_nav_and_byline_are_removed_from_the_leading_run(self):
        airia = next(source for source in _bundle()["sources"] if "airia" in source["url"])
        cleaned = desk.clean_article_text(airia["text"], airia.get("title", ""))
        self.assertFalse(cleaned.lower().startswith("all posts"))
        self.assertNotIn("Written by", cleaned[:200])
        self.assertTrue(cleaned.startswith("The NIST AI Risk Management Framework"))

    def test_no_claim_carries_page_furniture(self):
        for claim in _cleaned_claims(_bundle()):
            text = claim["claim"]
            lowered = text.lower()
            self.assertFalse(lowered.startswith("all posts"), text[:60])
            self.assertFalse(lowered.startswith("skip to"), text[:60])
            self.assertFalse(lowered.startswith("menu"), text[:60])
            self.assertNotIn("written by", lowered, text[:60])
            self.assertLess(text.count("Menu"), 2, text[:60])
            if not claim.get("atomic_of"):
                # A parent sentence must read as prose; an atomic clause may
                # legitimately start with its predicate.
                self.assertFalse(text[:1].islower(), text[:60])

    def test_citation_fragments_are_rejected(self):
        self.assertTrue(desk.is_boilerplate("116-283), the goal of the AI RMF is clear enough"))
        self.assertFalse(desk.is_boilerplate(
            "The AI RMF was developed in an open, transparent, consensus-driven process."))

    def test_government_banner_is_stripped(self):
        nist = next(source for source in _bundle()["sources"]
                    if source["url"].endswith("ai-risk-management-framework"))
        cleaned = desk.clean_article_text(nist["text"], nist.get("title", ""))
        self.assertNotIn("Skip to main content", cleaned)
        self.assertNotIn("Here’s how you know", cleaned)
        self.assertNotIn("https://", cleaned[:300])


class RetrievalTests(unittest.TestCase):
    def test_every_source_records_when_it_was_fetched(self):
        class Response:
            status_code = 200
            headers = {"Content-Type": "text/html"}
            text = "<html><body><p>Acme released the tool in 2025.</p></body></html>"

        with patch.object(desk.requests, "get", return_value=Response()):
            result = desk.fetch_url("https://example.com/a")
        self.assertTrue(result["retrieved_at"])
        self.assertTrue(result["ok"])

    def test_ledger_source_records_keep_the_timestamp(self):
        research = _bundle()
        for source in research["sources"]:
            source["retrieved_at"] = "2026-10-30T00:00:00+00:00"
        ledger = claims.build_ledger(research)
        self.assertTrue(all(record["retrieved_at"] for record in ledger["sources"]))

    def test_refused_pdf_is_retried_then_sent_to_manual_review(self):
        class Response:
            status_code = 406
            headers: dict = {}
            text = ""

        seen: list[str] = []

        def fake_get(url, headers=None, timeout=None, allow_redirects=None):
            seen.append((headers or {}).get("Accept", ""))
            return Response()

        with patch.object(desk.requests, "get", side_effect=fake_get):
            result = desk.fetch_url("https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf")

        self.assertEqual(len(seen), 2, "expected one plain and one document negotiation attempt")
        self.assertIn("application/pdf", seen[1])
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])
        self.assertTrue(result["manual_review_required"])
        self.assertIn("manual review", result["error"])
        # Nothing is invented for a page that was never read.
        self.assertEqual(result["text"], "")

    def test_unrelated_http_error_is_not_reported_as_a_refusal(self):
        class Response:
            status_code = 500
            headers: dict = {}
            text = ""

        with patch.object(desk.requests, "get", return_value=Response()):
            result = desk.fetch_url("https://example.com/broken")
        self.assertEqual(result["error"], "HTTP 500")
        self.assertFalse(result["manual_review_required"])


class SourceSpreadTests(unittest.TestCase):
    def test_claims_come_from_more_than_one_publisher(self):
        pool = _cleaned_claims(_bundle())
        interleaved: list[dict] = []
        per_source = []
        for source in _bundle()["sources"]:
            items = desk.extract_claims(
                desk.clean_article_text(source["text"], source.get("title", "")),
                source_url=source["url"])[:desk.PER_SOURCE_CLAIM_CAP]
            if items:
                per_source.append(items)
        for index in range(max(len(items) for items in per_source)):
            for items in per_source:
                if index < len(items):
                    interleaved.append(items[index])
        merged = desk.merge_duplicate_claims(interleaved)[:desk.MAX_CLAIMS]
        publishers = {lineage.publisher_of(item["source_url"]) for item in merged}
        self.assertGreater(len(publishers), 1)
        self.assertEqual(pool and True, True)

    def test_duplicate_fact_from_two_publishers_becomes_one_claim(self):
        sentence = "The AI RMF 1.0 was released on January 26, 2023."
        merged = desk.merge_duplicate_claims([
            {"claim": sentence, "quote": sentence, "source_url": "https://a.example.com/x"},
            {"claim": sentence, "quote": sentence, "source_url": "https://b.example.org/y"},
        ])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["also_reported_by"], ["https://b.example.org/y"])


class CorroborationTests(unittest.TestCase):
    def test_nist_wording_fully_matches_the_airia_claim(self):
        support = lineage.anchor_support(RMF_CLAIM, NIST_RMF_PAGE)
        self.assertEqual(support["strength"], "full")
        self.assertTrue(support["excerpts"])
        self.assertIn("January 26, 2023", support["excerpts"][0]["excerpt"])

    def test_page_without_the_decisive_date_does_not_corroborate(self):
        weak = ("The AI Risk Management Framework is a voluntary framework used by "
                "many organizations to think about risk.")
        support = lineage.anchor_support(RMF_CLAIM, weak)
        self.assertNotEqual(support["strength"], "full")

    def test_different_date_on_the_same_subject_is_a_conflict(self):
        contradicting = (
            "The NIST AI Risk Management Framework (AI RMF 1.0) was released on "
            "March 30, 2024 by the National Institute of Standards and Technology."
        )
        support = lineage.anchor_support(RMF_CLAIM, contradicting)
        self.assertTrue(support["conflicts"], support)
        self.assertEqual(support["conflicts"][0]["expected"], "2023")
        self.assertEqual(support["conflicts"][0]["found"], "2024")
        self.assertNotEqual(support["strength"], "full")

    def test_real_bundle_now_has_independent_corroboration(self):
        research = _bundle()
        for source in research["sources"]:
            source["text"] = desk.clean_article_text(source["text"], source.get("title", ""))
        per_source = []
        for source in research["sources"]:
            items = desk.extract_claims(source["text"], source_url=source["url"])[
                :desk.PER_SOURCE_CLAIM_CAP]
            if items:
                per_source.append(items)
        pool: list[dict] = []
        for index in range(max(len(items) for items in per_source)):
            for items in per_source:
                if index < len(items):
                    pool.append(items[index])
        research["claims"] = desk.merge_duplicate_claims(pool)[:desk.MAX_CLAIMS]
        ledger = claims.build_ledger(research)
        self.assertGreater(ledger["summary"]["by_status"]["supported"], 0)
        self.assertGreater(ledger["summary"]["independently_corroborated"], 0)
        corroborated = [
            record for record in ledger["claims"]
            if record["verification"]["status"] == "supported"
        ][0]
        self.assertTrue(
            any(entry["relation"] == "corroboration" and "nist.gov" in entry["publisher"]
                for entry in corroborated["support"]),
            corroborated["support"],
        )
        self.assertTrue(all(entry.get("excerpt") for entry in corroborated["support"]))

    def test_more_urls_alone_never_upgrade_a_claim(self):
        research = _bundle()
        lone = {
            "url": "https://unrelated.example.com/other",
            "publisher": "unrelated.example.com",
            "title": "Other",
            "text": "A cooking recipe for pasta with tomato sauce and basil leaves.",
            "published": "2025-01-01",
        }
        base = claims.build_ledger({**research, "claims": [
            {"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}]})
        widened = claims.build_ledger({**research, "claims": [
            {"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}],
            "sources": [*research["sources"], lone]})
        self.assertEqual(base["claims"][0]["verification"]["status"],
                         widened["claims"][0]["verification"]["status"])


class AtomicClaimTests(unittest.TestCase):
    def test_compound_claim_splits_into_verbatim_clauses(self):
        pieces = atomic.split_atomic(RMF_CLAIM)
        self.assertGreaterEqual(len(pieces), 2)
        for piece in pieces:
            self.assertTrue(atomic.is_substring_of(piece, RMF_CLAIM), piece)
        self.assertTrue(any("January 2023" in piece for piece in pieces))
        self.assertTrue(any("voluntary" in piece for piece in pieces))

    def test_simple_sentence_is_not_split(self):
        self.assertEqual(atomic.split_atomic("The tool is available now."), [])

    def test_truncated_clause_is_dropped(self):
        sentence = ("The framework was written with many groups, including academic "
                    "institutions, companies of every size, and civil society.")
        for piece in atomic.split_atomic(sentence):
            self.assertFalse(piece.lower().endswith(" of"), piece)


class FactualClassificationTests(unittest.TestCase):
    def test_institutional_practice_sentence_is_factual(self):
        self.assertTrue(evidence.looks_factual(
            "And many auditors, assessors, and governance teams increasingly use "
            "the AI RMF as a benchmark when evaluating AI risk management practices."))

    def test_opinion_sentence_is_not_factual(self):
        self.assertFalse(evidence.looks_factual("The office lights hum at night."))

    def test_pure_prose_without_a_named_body_is_not_factual(self):
        self.assertFalse(evidence.looks_factual("We think this is a good idea overall."))


class ConflictRecordTests(unittest.TestCase):
    def test_value_conflict_is_stored_with_both_excerpts(self):
        research = {
            "topic": "AI RMF",
            "verdict": "sufficient",
            "sources": [
                {"url": AIRIA, "publisher": "airia.com", "text": RMF_CLAIM,
                 "published": "2026-04-25", "retrieved_at": "2026-10-30T00:00:00+00:00"},
                {"url": "https://www.nist.gov/itl/ai-risk-management-framework",
                 "publisher": "www.nist.gov", "text":
                     "The NIST AI Risk Management Framework (AI RMF 1.0) was released on "
                     "March 30, 2024 by the National Institute of Standards and Technology, "
                     "a voluntary framework designed to help organizations manage risks "
                     "associated with AI systems throughout their lifecycle.",
                 "published": "2024-03-30", "retrieved_at": "2026-10-30T00:00:00+00:00"},
            ],
            "claims": [{"claim": RMF_CLAIM, "quote": RMF_CLAIM, "source_url": AIRIA}],
            "contradictions": [],
            "errors": [],
        }
        record = claims.build_ledger(research)["claims"][0]
        self.assertEqual(record["verification"]["status"], "conflicting")
        self.assertEqual(record["decision"], "research_more")
        conflict = record["contradict"][0]
        self.assertEqual(conflict["kind"], "value_conflict")
        self.assertEqual(conflict["expected"], "2023")
        self.assertTrue(conflict["excerpt"])


class TocContaminationTests(unittest.TestCase):
    """Phase 10.1.1 Task 1: navigation and card metadata fused onto real prose."""

    @classmethod
    def setUpClass(cls):
        cls.polluted = (FIXTURE.parent / "polluted_nist_guide.txt").read_text(
            encoding="utf-8").strip()

    def test_markers_are_recognised_as_furniture(self):
        self.assertTrue(desk._is_toc_or_metadata("Table of Contents Overview of the AI RMF"))
        self.assertTrue(desk._is_toc_or_metadata("governance 7 sections Last updated : March 28, 2026"))
        self.assertTrue(desk._is_toc_or_metadata("Frequently Asked Questions"))

    def test_prose_using_the_same_words_is_not_furniture(self):
        # The guard is the multi-word marker, not a single common word: an article
        # may legitimately count its own sections or say something was updated.
        self.assertFalse(desk._is_toc_or_metadata(
            "The report has 7 sections of guidance for practitioners."))
        self.assertFalse(desk._is_toc_or_metadata(
            "The framework was updated twice in the past year."))
        self.assertFalse(desk._is_toc_or_metadata(
            "Its contents describe how teams should govern AI systems."))

    def test_a_sentence_about_the_page_toc_is_furniture(self):
        # Deliberate: prose whose subject is the navigation block is navigation.
        self.assertTrue(desk._is_toc_or_metadata(
            "Table of Contents Overview of the NIST AI Risk Management Framework"))

    def test_polluted_run_is_split_and_the_navigation_dropped(self):
        cleaned = desk.clean_article_text(self.polluted, "")
        self.assertNotIn("Table of Contents", cleaned)
        self.assertNotIn("Last updated", cleaned)
        self.assertNotIn("Frequently Asked Questions", cleaned)
        self.assertNotIn("7 sections", cleaned)

    def test_genuine_prose_before_and_after_the_block_survives(self):
        cleaned = desk.clean_article_text(self.polluted, "")
        self.assertIn("four core functions", cleaned)
        self.assertIn("maturity level", cleaned)
        self.assertIn("voluntary approach", cleaned)

    def test_no_extracted_claim_carries_navigation_text(self):
        cleaned = desk.clean_article_text(self.polluted, "")
        for claim in desk.extract_claims(cleaned, source_url="https://guide.example.com/a"):
            lowered = claim["claim"].lower()
            self.assertNotIn("table of contents", lowered)
            self.assertNotIn("last updated", lowered)
            self.assertNotIn("frequently asked questions", lowered)
            self.assertNotIn("7 sections", lowered)

    def test_real_bundle_produces_no_polluted_claims(self):
        research = _bundle()
        for source in research["sources"]:
            source["text"] = desk.clean_article_text(source["text"], source.get("title", ""))
        for claim in _cleaned_claims(research):
            lowered = claim["claim"].lower()
            self.assertNotIn("table of contents", lowered)
            self.assertNotIn("last updated", lowered)
            self.assertNotIn("frequently asked questions", lowered)


class RightsAndCutoutTests(unittest.TestCase):
    """The cutout quotes the claim, so a clean claim is a clean card."""

    def test_card_excerpt_follows_the_cleaned_quote(self):
        """The cutout quotes the claim verbatim, so a clean claim is a clean card."""
        research = _bundle()
        for source in research["sources"]:
            source["text"] = desk.clean_article_text(source["text"], source.get("title", ""))
        pool = _cleaned_claims(research)
        self.assertTrue(pool, "expected claims from the cleaned bundle")
        records = [
            {
                "claim_id": f"clm_card_{index}",
                "quote": item["quote"],
                "publisher": lineage.publisher_of(item["source_url"]),
                "published": "2026-03-28",
                "source_url": item["source_url"],
            }
            for index, item in enumerate(pool)
        ]
        with tempfile.TemporaryDirectory() as td:
            for record in records:
                card = cutouts.build_source_card(record, Path(td))
                excerpt = card["excerpt"].lower()
                self.assertNotIn("table of contents", excerpt, record["claim_id"])
                self.assertNotIn("last updated", excerpt, record["claim_id"])
                self.assertNotIn("frequently asked questions", excerpt, record["claim_id"])


if __name__ == "__main__":
    unittest.main()


class SubjectScopedNumericConflictTests(unittest.TestCase):
    def test_unrelated_model_parameter_count_is_not_a_conflict_for_generic_moe_claim(self):
        claim = (
            "The key insight: You can have a model with 256 billion total parameters "
            "but only activate ~8 billion for any given token."
        )
        unrelated_model = (
            "The key insight is that Google explored this with GShard, which explores "
            "scaling up transformers beyond 600 billion parameters."
        )
        support = lineage.anchor_support(claim, unrelated_model)
        self.assertEqual(support["conflicts"], [])
        self.assertNotEqual(support["strength"], "full")

    def test_different_parameter_count_for_same_named_model_remains_a_conflict(self):
        claim = "DeepSeek-V3 has 671 billion total parameters."
        source = "DeepSeek-V3 has 600 billion total parameters."
        support = lineage.anchor_support(claim, source)
        self.assertTrue(support["conflicts"], support)
        self.assertEqual(support["conflicts"][0]["expected"], "671 billion")
        self.assertEqual(support["conflicts"][0]["found"], "600 billion")
