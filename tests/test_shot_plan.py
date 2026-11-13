"""I1 — structured shot planning.

Pins the plan contract: stable IDs, narration coverage, subject/action/context,
evidence links (and explicit flags when they are missing or invalid), timing
compatibility with the existing shot planner, and determinism.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.visuals import beats, motion_director, shotplan

SENTENCES = [
    "NIST released the AI RMF 1.0 on January 26, 2023.",
    "The framework defines four core functions for managing risk.",
    "Teams use it to govern AI systems across the enterprise.",
]
REQUIRED_FIELDS = {
    "shot_id", "index", "narration_ref", "subject", "action", "context",
    "emotion", "visual_objective", "visual_type", "scene_type",
    "expected_duration", "duration_basis", "search", "transition_intent",
    "evidence", "shots", "rationale", "flags",
}


def _script(sentences=None, *, claim_ids=None) -> dict:
    sentences = sentences or SENTENCES
    shots = [
        {"caption": sentence[:42], "claim": sentence,
         "asset_query": "nist ai risk framework"}
        for sentence in sentences
    ]
    if claim_ids:
        shots[0]["claim_ids"] = claim_ids
    return {
        "topic": "NIST AI RMF",
        "voice_text": " ".join(sentences),
        "shots": shots,
    }


def _ledger() -> dict:
    return {
        "claims": [
            {"claim_id": "clm_a", "narration": SENTENCES[0],
             "quote": SENTENCES[0], "verification": {"status": "supported"}},
            {"claim_id": "clm_b", "narration": SENTENCES[2],
             "quote": SENTENCES[2], "verification": {"status": "outdated"}},
        ]
    }


class BeatAnalysisTests(unittest.TestCase):
    def test_sentences_split_without_breaking_abbreviations(self):
        text = ("The paper reports a gain, e.g. 84% of teams. "
                "The AI RMF 1.0 was released in 2023.")
        parts = beats.split_narration(text)
        self.assertEqual(len(parts), 2)
        self.assertIn("e.g. 84%", parts[0])

    def test_beat_carries_subject_action_context_and_emotion(self):
        beat = beats.analyse_beat(SENTENCES[0])
        self.assertEqual(beat.subject, "NIST")
        self.assertEqual(beat.subject_type, "organisation")
        self.assertEqual(beat.action, "released")
        self.assertTrue(beat.context.startswith("on "))
        self.assertEqual(beat.emotion, "explanatory")
        self.assertTrue(beat.evidence_required)

    def test_cautionary_and_optimistic_language_is_detected(self):
        self.assertEqual(beats.analyse_beat(
            "Automated tools fail to catch context-dependent bugs.").emotion,
            "cautionary")
        self.assertEqual(beats.analyse_beat(
            "The breakthrough cuts review time by 40%.").emotion, "optimistic")

    def test_short_fragment_is_flagged_not_silently_dropped(self):
        result = beats.analyse_narration("NIST released the AI RMF 1.0. Yes.")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "NIST released the AI RMF 1.0. Yes.")


class ShotPlanContractTests(unittest.TestCase):
    def test_every_narration_sentence_has_a_plan_entry(self):
        script = _script()
        plan = shotplan.plan_shot_plan(script, audio_duration=12.0)
        self.assertEqual(plan["beat_count"], len(SENTENCES))
        self.assertEqual(plan["coverage"]["ratio"], 1.0)
        self.assertEqual(plan["coverage"]["uncovered"], [])
        coverage = shotplan.validate_coverage(plan, script["voice_text"])
        self.assertTrue(coverage["complete"], coverage)

    def test_entries_carry_the_required_fields(self):
        plan = shotplan.plan_shot_plan(_script(), audio_duration=12.0)
        for entry in plan["beats"]:
            self.assertTrue(REQUIRED_FIELDS.issubset(entry), REQUIRED_FIELDS - set(entry))
            self.assertEqual(entry["shot_id"], f"s{entry['index']:02d}")
            self.assertTrue(entry["rationale"])
            self.assertTrue(entry["visual_objective"])

    def test_timing_matches_the_existing_shot_planner(self):
        script = _script()
        direct = motion_director.plan_shots(script, audio_duration=12.0)
        plan = shotplan.plan_shot_plan(script, audio_duration=12.0)
        self.assertEqual(plan["shot_count"], len(direct))
        self.assertEqual(plan["timing"]["total_duration"],
                         round(sum(float(s["duration"]) for s in direct), 3))
        planned = {shot["shot_index"]: shot
                   for entry in plan["beats"] for shot in entry["shots"]}
        self.assertEqual(sorted(planned), [int(s["index"]) for s in direct])
        for shot in direct:
            entry = planned[int(shot["index"])]
            self.assertEqual(entry["start"], float(shot["start"]))
            self.assertEqual(entry["end"], float(shot["end"]))
            self.assertEqual(entry["duration"], float(shot["duration"]))

    def test_plan_is_deterministic(self):
        first = shotplan.plan_shot_plan(_script(), ledger=_ledger(), audio_duration=12.0)
        second = shotplan.plan_shot_plan(_script(), ledger=_ledger(), audio_duration=12.0)
        self.assertEqual(first, second)


class ShotPlanEvidenceTests(unittest.TestCase):
    def test_evidence_links_resolve_to_ledger_claims(self):
        plan = shotplan.plan_shot_plan(_script(), ledger=_ledger(), audio_duration=12.0)
        first, _second, third = plan["beats"]
        self.assertEqual(first["narration_ref"]["claim_ids"], ["clm_a"])
        self.assertEqual(first["evidence"]["statuses"], {"clm_a": "supported"})
        self.assertNotIn("evidence_missing", first["flags"])
        self.assertEqual(third["narration_ref"]["claim_ids"], ["clm_b"])
        self.assertIn("evidence_unsupported_status", third["flags"])
        self.assertIn("evidence_needs_review", third["flags"])

    def test_unlinked_factual_beat_is_flagged_not_invented(self):
        plan = shotplan.plan_shot_plan(_script(), ledger=_ledger(), audio_duration=12.0)
        middle = plan["beats"][1]
        self.assertTrue(middle["evidence"]["required"])
        self.assertEqual(middle["narration_ref"]["claim_ids"], [])
        self.assertIn("evidence_missing", middle["flags"])
        self.assertIn("s01", plan["evidence"]["missing"])

    def test_absent_ledger_is_reported(self):
        plan = shotplan.plan_shot_plan(_script(), audio_duration=12.0)
        self.assertFalse(plan["evidence"]["ledger_present"])
        self.assertTrue(all("evidence_ledger_absent" in entry["flags"]
                            for entry in plan["beats"]))

    def test_invalid_explicit_reference_is_flagged(self):
        plan = shotplan.plan_shot_plan(_script(claim_ids=["clm_ghost"]),
                                       ledger=_ledger(), audio_duration=12.0)
        first = plan["beats"][0]
        self.assertIn("evidence_reference_invalid", first["flags"])
        self.assertEqual(first["evidence"]["invalid_references"], ["clm_ghost"])
        self.assertIn("s00", plan["evidence"]["invalid_references"])

    def test_writer_round_trips(self):
        plan = shotplan.plan_shot_plan(_script(), ledger=_ledger(), audio_duration=12.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = shotplan.write_shot_plan(plan, Path(tmp) / "shot_plan.json")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), plan)


if __name__ == "__main__":
    unittest.main()
