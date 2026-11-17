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


class MoeVisualQueryTests(unittest.TestCase):
    def test_moe_visual_queries_are_beat_specific(self):
        route = shotplan._moe_visual_queries(
            "How Mixtral routes experts",
            "Mistral's router chooses two experts for every token at each layer.",
        )
        pool = shotplan._moe_visual_queries(
            "How Mixtral routes experts",
            "The selected experts process the token and their outputs combine.",
        )
        hardware = shotplan._moe_visual_queries(
            "How Mixtral routes experts",
            "Mixtral is a model with open weights.",
        )
        self.assertIn("routing", route[0].lower())
        self.assertTrue(any("processor" in item or "computing" in item for item in pool))
        self.assertTrue(any("server" in item or "gpu" in item for item in hardware))
        self.assertNotEqual(route[0], pool[0])
        self.assertNotEqual(pool[0], hardware[0])

    def test_non_moe_topic_has_no_moe_specific_query(self):
        self.assertEqual(
            shotplan._moe_visual_queries("NIST AI RMF", "A router selects two experts."),
            [],
        )


class BeatAnalysisTests(unittest.TestCase):
    def test_hook_question_does_not_require_claim_evidence_but_factual_workflow_does(self):
        hook = beats.analyse_beat("Can AI agents do real research?", 0)
        factual = beats.analyse_beat("Its multi-agent workflow proposes and ranks hypotheses.", 1)
        self.assertFalse(hook.evidence_required)
        self.assertTrue(factual.evidence_required)

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

    def test_merged_shot_covers_each_narration_beat_it_contains(self):
        sentences = [
            "DeepSeek released its reasoning model in January 2025.",
            "The paper reports a lower training cost than competitors.",
            "Independent benchmarks measured several reasoning tasks.",
        ]
        script = _script(sentences)
        # The script writer may merge adjacent short beats into one visual shot.
        script["shots"] = [
            {"claim": f"{sentences[0]} / {sentences[1]}",
             "caption": sentences[0], "asset_query": "DeepSeek reasoning model"},
            {"claim": sentences[2], "caption": sentences[2],
             "asset_query": "reasoning benchmarks"},
        ]
        plan = shotplan.plan_shot_plan(script, audio_duration=12.0)
        self.assertEqual(plan["coverage"]["ratio"], 1.0)
        self.assertEqual(plan["coverage"]["uncovered"], [])
        first_refs = {item["shot_index"] for item in plan["beats"][0]["shots"]}
        second_refs = {item["shot_index"] for item in plan["beats"][1]["shots"]}
        self.assertTrue(first_refs & second_refs)

    def test_plan_is_deterministic(self):
        first = shotplan.plan_shot_plan(_script(), ledger=_ledger(), audio_duration=12.0)
        second = shotplan.plan_shot_plan(_script(), ledger=_ledger(), audio_duration=12.0)
        self.assertEqual(first, second)

    def test_moe_visual_searches_are_specific_to_each_narration_beat(self):
        topic = "How AI Models Activate a Few Experts to Save Compute"
        self.assertIn("GPU memory modules close up", shotplan._moe_visual_queries(topic, "Inactive experts still occupy memory."))
        self.assertIn("GPU cluster interconnect cables", shotplan._moe_visual_queries(topic, "Communication overhead appears between GPUs."))
        self.assertIn("office team collaboration meeting", shotplan._moe_visual_queries(topic, "A company routes tasks to specialist teams."))
        self.assertIn("mixture of experts token routing diagram", shotplan._moe_visual_queries(topic, "A router sends each token to selected experts."))
        sparse_queries = shotplan._moe_visual_queries(topic, "Sparse routing selects a subset for each token.")
        self.assertEqual(sparse_queries[0], "sparse expert network router flowchart")
        self.assertIn("GPU accelerator cards close up", sparse_queries)
        router_queries = shotplan._moe_visual_queries(topic, "A router sends each token to selected experts.")
        self.assertIn("GPU server racks data center", router_queries)

    def test_generated_video_selection_survives_shot_planning_and_annotation(self):
        sentence = "Rows of servers power the model."
        sidecar = "clips/server-room.mp4.asset.json"
        script = {
            "topic": "AI infrastructure",
            "voice_text": sentence,
            "shots": [{
                "index": 0, "claim": sentence, "caption": sentence,
                "asset_query": "server room", "generated_video_asset": sidecar,
            }],
        }
        planned = motion_director.plan_shots(script, audio_duration=5.0)
        self.assertEqual(planned[0]["generated_video_asset"], sidecar)
        plan = shotplan.plan_shot_plan(script, audio_duration=5.0)
        annotated = shotplan.annotate_shots(planned, plan)
        self.assertEqual(annotated[0]["generated_video_asset"], sidecar)

    def test_annotate_shots_applies_semantic_search_queries(self):
        topic = "How AI Models Activate a Few Experts to Save Compute"
        sentence = "Inactive experts still occupy memory."
        script = {
            "topic": topic,
            "voice_text": sentence,
            "shots": [{"index": 0, "claim": sentence, "caption": sentence, "asset_query": "inactive experts"}],
        }
        plan = shotplan.plan_shot_plan(script, audio_duration=5.0)
        shots = motion_director.plan_shots(script, audio_duration=5.0)
        annotated = shotplan.annotate_shots(shots, plan)
        self.assertEqual(annotated[0]["narration"], sentence)
        self.assertEqual(annotated[0]["asset_query"], "GPU memory modules close up")
        self.assertIn("graphics card VRAM memory chips", annotated[0]["asset_query_variants"])


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

    def test_annotate_shots_preserves_creator_semantic_query_and_merges_evidence_variants(self):
        shots = [{"index": 0, "asset_query": "AI research agents laboratory",
                  "asset_query_variants": ["scientist reviewing AI paper"]}]
        plan = {"beats": [{
            "shot_id": "b00", "shots": [{"shot_index": 0}],
            "search": {"primary": "An agent takes on the central open-ended research question",
                       "variants": ["AI research agent evaluation"]},
            "evidence": {"claim_ids": ["c1"], "flags": []},
        }]}
        result = shotplan.annotate_shots(shots, plan)[0]
        self.assertEqual(result["asset_query"], "AI research agents laboratory")
        self.assertIn("AI research agent evaluation", result["asset_query_variants"])
        self.assertIn("An agent takes on the central open-ended research question", result["asset_query_variants"])

class CreativeDirectionHandoffTests(unittest.TestCase):
    def test_creative_beat_action_and_semantic_query_reach_shot_plan(self):
        script = {
            "topic": "AI research agents",
            "voice_text": "AI research agents evaluate an open-ended scientific question.",
            "beat_sheet": [{
                "label": "mechanism",
                "text": "AI research agents evaluate an open-ended scientific question.",
                "t_start": 0.0, "t_end": 8.0, "shot_hint": "AI research agents",
            }],
        }
        plan = shotplan.plan_shot_plan(script, audio_duration=8.0)
        self.assertTrue(plan["beats"])
        beat = plan["beats"][0]
        self.assertTrue(beat["action"])
        self.assertNotIn("no_action", beat["flags"])
        self.assertTrue(beat["search"]["primary"])
        self.assertLessEqual(len(beat["search"]["primary"].split()), 7)
        self.assertIn("diagram", beat["scene_type"])

    def test_annotate_shots_varies_repeated_coverage_queries(self):
        shots = [
            {"index": 0, "asset_query": "old generic query"},
            {"index": 1, "asset_query": "old generic query"},
            {"index": 2, "asset_query": "old generic query"},
        ]
        plan = {"beats": [{
            "shot_id": "s00", "index": 0,
            "narration_ref": {"text": "AI research agents evaluate a question."},
            "subject": {"name": "AI research agents"},
            "visual_subject": "AI research agents",
            "visual_action": "research agents evaluating a scientific question",
            "evidence": {"claim_ids": [], "flags": []},
            "search": {"primary": "AI research agents",
                       "variants": ["AI research agents", "scientist research lab", "research agent evaluation"]},
            "shots": [{"shot_index": 0}, {"shot_index": 1}, {"shot_index": 2}],
        }]}
        annotated = shotplan.annotate_shots(shots, plan)
        self.assertEqual(len({item["asset_query"] for item in annotated}), 3)
