"""Claim ledger: traceability, fabrication guards, conflicts, freshness."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.research import claims

TOPIC = "AI code review"


def _source(url, text, published="", publisher=""):
    return {"url": url, "text": text, "published": published, "publisher": publisher}


def _research(claim, sources, contradictions=None):
    return {
        "topic": TOPIC,
        "verdict": "sufficient",
        "fetched_at": "2025-06-01T00:00:00+00:00",
        "sources": sources,
        "claims": [claim],
        "contradictions": contradictions or [],
        "errors": [],
    }


QUOTE = "its AI code review tool catches 84% of security issues before merge"
NARRATION = "Acme's AI code review tool catches 84% of security issues before merge."
BODY = f"Acme announced that {QUOTE}. The tool is available now."


class TraceabilityTests(unittest.TestCase):
    def test_every_claim_has_a_stable_record(self):
        ledger = claims.build_ledger(_research(
            {"claim": NARRATION, "quote": QUOTE, "source_url": "https://acme.example.com/a"},
            [_source("https://acme.example.com/a", BODY, "2025-03-04")],
        ))
        record = ledger["claims"][0]
        self.assertRegex(record["claim_id"], r"^clm_[0-9a-f]{10}$")
        self.assertEqual(record["quote"], QUOTE)
        self.assertGreaterEqual(record["excerpt_offset"], 0)
        self.assertEqual(record["source_url"], "https://acme.example.com/a")
        self.assertIn(record["verification"]["status"], claims.STATUSES)
        self.assertIn(record["decision"], claims.DECISIONS)
        self.assertEqual(record["published"], "2025-03-04")
        self.assertEqual(record["date_confidence"], "metadata")

    def test_claim_ids_are_deterministic(self):
        research = _research(
            {"claim": NARRATION, "quote": QUOTE, "source_url": "https://acme.example.com/a"},
            [_source("https://acme.example.com/a", BODY, "2025-03-04")],
        )
        first = claims.build_ledger(research)["claims"][0]["claim_id"]
        second = claims.build_ledger(research)["claims"][0]["claim_id"]
        self.assertEqual(first, second)


class NoFabricationTests(unittest.TestCase):
    def test_missing_date_is_left_empty_and_flagged(self):
        ledger = claims.build_ledger(_research(
            {"claim": NARRATION, "quote": QUOTE, "source_url": "https://acme.example.com/a"},
            [_source("https://acme.example.com/a", BODY)],
        ))
        record = ledger["claims"][0]
        self.assertEqual(record["published"], "")
        self.assertEqual(record["date_confidence"], "unknown")
        self.assertTrue(any("publication date unknown" in flag for flag in record["flags"]))
        self.assertEqual(ledger["summary"]["without_publication_date"], 1)

    def test_quote_not_in_source_is_unverified_not_invented(self):
        ledger = claims.build_ledger(_research(
            {"claim": NARRATION, "quote": "a sentence that is not in the page",
             "source_url": "https://acme.example.com/a"},
            [_source("https://acme.example.com/a", BODY, "2025-03-04")],
        ))
        record = ledger["claims"][0]
        self.assertEqual(record["verification"]["status"], "unverified")
        self.assertEqual(record["decision"], "exclude")
        self.assertIsNone(record["excerpt_offset"])

    def test_claim_source_missing_from_sources_is_flagged(self):
        ledger = claims.build_ledger(_research(
            {"claim": NARRATION, "quote": QUOTE, "source_url": "https://ghost.example.com/a"},
            [_source("https://acme.example.com/a", BODY, "2025-03-04")],
        ))
        self.assertTrue(any("not in the fetched source list" in flag
                            for flag in ledger["claims"][0]["flags"]))


class ConflictTests(unittest.TestCase):
    def test_conflict_is_preserved_and_needs_more_research(self):
        research = _research(
            {"claim": NARRATION, "quote": QUOTE, "source_url": "https://acme.example.com/a"},
            [
                _source("https://acme.example.com/a", BODY, "2025-03-04"),
                _source("https://lab.example.org/study", "Independent testing found 61%.", "2025-03-05"),
            ],
            contradictions=[{
                "claim": NARRATION,
                "source_a": "https://acme.example.com/a",
                "source_b": "https://lab.example.org/study",
                "note": "Conflicting accuracy for Acme",
            }],
        )
        record = claims.build_ledger(research)["claims"][0]
        self.assertEqual(record["verification"]["status"], "conflicting")
        self.assertEqual(record["decision"], "research_more")
        self.assertEqual(record["verification"]["conflicting"][0]["source_b"],
                         "https://lab.example.org/study")


class FreshnessTests(unittest.TestCase):
    def test_old_statistic_is_outdated(self):
        ledger = claims.build_ledger(
            _research(
                {"claim": NARRATION, "quote": QUOTE, "source_url": "https://acme.example.com/a"},
                [_source("https://acme.example.com/a", BODY, "2019-01-01")],
            ),
            now=datetime(2025, 6, 1, tzinfo=timezone.utc),
            stale_days=365,
        )
        record = ledger["claims"][0]
        self.assertEqual(record["verification"]["status"], "outdated")
        self.assertEqual(record["decision"], "research_more")
        self.assertTrue(any("days old" in flag for flag in record["flags"]))

    def test_old_announcement_is_not_forced_stale(self):
        ledger = claims.build_ledger(
            _research(
                {"claim": "Acme released the tool for teams.",
                 "quote": "The tool is available now", "source_url": "https://acme.example.com/a"},
                [_source("https://acme.example.com/a", BODY, "2019-01-01")],
            ),
            now=datetime(2025, 6, 1, tzinfo=timezone.utc),
            stale_days=365,
        )
        self.assertNotEqual(ledger["claims"][0]["verification"]["status"], "outdated")


class ScriptBindingTests(unittest.TestCase):
    def _ledger(self, script=""):
        return claims.build_ledger(
            _research(
                {"claim": NARRATION, "quote": QUOTE, "source_url": "https://acme.example.com/a"},
                [_source("https://acme.example.com/a", BODY, "2025-03-04")],
            ),
            script_text=script,
        )

    def test_sentence_maps_to_claim(self):
        ledger = self._ledger(NARRATION)
        self.assertEqual(ledger["claims"][0]["script"]["claim_ids"][0],
                         ledger["claims"][0]["claim_id"])
        self.assertEqual(ledger["summary"]["unmatched_narration_sentences"], 0)

    def test_hash_changes_when_the_script_changes(self):
        first = self._ledger("Acme says its tool catches 84% of issues.")
        second = self._ledger("A different sentence entirely.")
        self.assertNotEqual(first["ledger_sha256"], second["ledger_sha256"])

    def test_claims_for_scene_links_on_narration(self):
        ledger = self._ledger()
        linked = claims.claims_for_scene(ledger, NARRATION)
        self.assertTrue(linked)
        self.assertEqual(linked[0]["claim_id"], ledger["claims"][0]["claim_id"])

    def test_unrelated_scene_has_no_claims(self):
        ledger = self._ledger()
        self.assertEqual(claims.claims_for_scene(ledger, "A calm shot of the sky at dusk."), [])


if __name__ == "__main__":
    unittest.main()
