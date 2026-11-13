"""ShotPlan traceability: metadata ids, storyboard records and tile labels.

The plan is consumed read-only: annotation must not mutate the timeline shots,
must be deterministic, and every render shot must resolve to a stable id plus
its beat/evidence references.  Storyboard tiles and scene records must carry the
same id so metadata, review package and plan agree.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.visuals import motion_director, shotplan, storyboard

SENTENCES = [
    "NIST released the AI RMF 1.0 on January 26, 2023.",
    "The framework defines four core functions for managing risk.",
    "Teams use it to govern AI systems across the enterprise.",
]


def _script() -> dict:
    return {
        "topic": "NIST AI RMF",
        "voice_text": " ".join(SENTENCES),
        "shots": [
            {"caption": sentence[:42], "claim": sentence,
             "asset_query": "nist ai risk framework"}
            for sentence in SENTENCES
        ],
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


def _plan() -> dict:
    return shotplan.plan_shot_plan(_script(), ledger=_ledger(), audio_duration=12.0)


def _shots() -> list[dict]:
    return motion_director.plan_shots(_script(), audio_duration=12.0)


class ShotAnnotationTests(unittest.TestCase):
    def test_every_shot_gets_a_unique_stable_id(self):
        annotated = shotplan.annotate_shots(_shots(), _plan())
        ids = [shot["shot_id"] for shot in annotated]
        self.assertEqual(ids, [f"s{index:02d}" for index in range(len(annotated))])
        self.assertEqual(len(ids), len(set(ids)))

    def test_annotation_does_not_mutate_the_timeline(self):
        shots = _shots()
        before = [dict(shot) for shot in shots]
        shotplan.annotate_shots(shots, _plan())
        self.assertEqual(shots, before)
        self.assertNotIn("shot_id", shots[0])

    def test_annotation_is_deterministic(self):
        first = shotplan.annotate_shots(_shots(), _plan())
        second = shotplan.annotate_shots(_shots(), _plan())
        self.assertEqual(first, second)

    def test_claim_references_come_from_the_plan(self):
        plan = _plan()
        entry_claims = {
            ref["shot_index"]: entry["evidence"]["claim_ids"]
            for entry in plan["beats"] for ref in entry["shots"]
        }
        for shot in shotplan.annotate_shots(_shots(), plan):
            self.assertTrue(shot["shot_plan_ref"])
            self.assertEqual(shot["evidence_claim_ids"],
                             entry_claims[shot["index"]])
        claim_ids = {cid for shot in shotplan.annotate_shots(_shots(), plan)
                     for cid in shot["evidence_claim_ids"]}
        self.assertEqual(claim_ids, {"clm_a", "clm_b"})

    def test_shot_outside_the_plan_keeps_an_id_with_empty_references(self):
        annotated = shotplan.annotate_shots([{"index": 99, "duration": 1.0}], _plan())
        self.assertEqual(annotated[0]["shot_id"], "s99")
        self.assertEqual(annotated[0]["shot_plan_ref"], "")
        self.assertEqual(annotated[0]["evidence_claim_ids"], [])
        self.assertEqual(annotated[0]["narration_ref"], {})

    def test_plan_summary_is_deterministic_and_path_bound(self):
        plan = _plan()
        first = shotplan.plan_summary(plan, path=Path("work/shot_plan.json"))
        second = shotplan.plan_summary(plan, path="work/shot_plan.json")
        self.assertEqual(first, second)
        self.assertEqual(first["path"], "work/shot_plan.json")
        self.assertEqual(first["shot_count"], plan["shot_count"])
        self.assertEqual(first["coverage"], plan["coverage"])
        self.assertFalse(first["coverage"]["uncovered"])


class StoryboardTraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _build(self, shots):
        labels: list[str] = []

        def fake_thumb(asset_path, out_path, label, provider, confidence):
            labels.append(str(label))
            return False

        details = [{"provider": "procedural"} for _ in shots]
        with patch.object(storyboard, "_make_thumb", side_effect=fake_thumb), \
                patch.object(storyboard, "_blank_thumb", return_value=None), \
                patch.object(storyboard, "_make_contact_sheet", return_value=False):
            payload = storyboard.build_storyboard(
                shots, details, self.dir, planner={"scenes": {}}, title="T")
        return payload, labels

    def test_records_carry_shot_and_evidence_references(self):
        plan = _plan()
        shots = shotplan.annotate_shots(_shots(), plan)
        payload, labels = self._build(shots)
        plan_ids = {entry["shot_id"] for entry in plan["beats"]}
        self.assertEqual(len(payload["scenes"]), len(shots))
        for record, shot in zip(payload["scenes"], shots):
            self.assertEqual(record["shot_id"], shot["shot_id"])
            self.assertEqual(record["scene_id"], shot["shot_id"])
            self.assertEqual(record["shot_plan_ref"], shot["shot_plan_ref"])
            self.assertIn(record["shot_plan_ref"], plan_ids)
            self.assertEqual(record["narration_ref"], shot["narration_ref"])
            self.assertTrue(record["narration_ref"]["text"])
            self.assertEqual(record["plan_claim_ids"], shot["evidence_claim_ids"])
            self.assertTrue(record["subject"])

    def test_tiles_are_labelled_with_the_shot_id(self):
        shots = shotplan.annotate_shots(_shots(), _plan())
        payload, labels = self._build(shots)
        self.assertEqual(labels, [record["shot_id"] for record in payload["scenes"]])
        self.assertEqual(labels, [shot["shot_id"] for shot in shots])

    def test_plain_shots_still_get_snn_labels(self):
        shots = _shots()
        payload, labels = self._build(shots)
        self.assertEqual(labels, [f"s{record['index']:02d}" for record in payload["scenes"]])
        for record in payload["scenes"]:
            self.assertEqual(record["shot_id"], record["scene_id"])
            self.assertEqual(record["plan_claim_ids"], [])

    def test_scene_digest_is_stable_across_identical_builds(self):
        shots = shotplan.annotate_shots(_shots(), _plan())
        first, _ = self._build(shots)
        second, _ = self._build(shots)
        self.assertEqual(first["scene_digest"], second["scene_digest"])


if __name__ == "__main__":
    unittest.main()
