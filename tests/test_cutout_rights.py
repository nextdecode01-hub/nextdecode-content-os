"""Balanced source cutouts, reuse-rights gate, attribution and approval safety."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.visuals import cutouts, storyboard

HAS_FFMPEG = bool(shutil.which("ffmpeg"))


def _claims():
    return [
        {
            "claim_id": "clm_supported",
            "narration": "Acme's tool catches 84% of security issues before merge.",
            "quote": "its AI code review tool catches 84% of security issues before merge",
            "publisher": "wire.example.com",
            "published": "2025-03-04",
            "source_url": "https://wire.example.com/release",
            "claim_type": "statistic",
            "verification": {"status": "supported"},
        },
        {
            "claim_id": "clm_weak",
            "narration": "The tool will replace all manual review.",
            "quote": "the tool will replace all manual review",
            "publisher": "blog.example.org",
            "published": "",
            "source_url": "https://blog.example.org/post",
            "claim_type": "forecast",
            "verification": {"status": "unverified"},
        },
    ]


class RightsTests(unittest.TestCase):
    def test_unknown_rights_are_not_publish_ready(self):
        rights = cutouts.reuse_rights({"url": "https://example.com/a", "publisher": "example.com"})
        self.assertEqual(rights["status"], "unknown")
        self.assertIn("do not publish", rights["basis"])

    def test_government_source_is_permitted(self):
        rights = cutouts.reuse_rights({"url": "https://www.nist.gov/report.pdf",
                                       "publisher": "nist.gov", "published": "2024-01-01"})
        self.assertEqual(rights["status"], "permitted")

    def test_open_licence_marker_is_permitted(self):
        rights = cutouts.reuse_rights({
            "url": "https://data.example.org/set", "publisher": "data.example.org",
            "text": "This dataset is published under CC BY 4.0.",
        })
        self.assertEqual(rights["status"], "permitted")

    def test_attribution_contains_publisher_date_and_url(self):
        claim = _claims()[0]
        lines = cutouts.attribution_lines(claim)
        self.assertEqual(lines[0], "wire.example.com")
        self.assertEqual(lines[1], "2025-03-04")
        self.assertIn("wire.example.com/release", lines[2])

    def test_missing_date_is_labelled_not_invented(self):
        lines = cutouts.attribution_lines(_claims()[1])
        self.assertEqual(lines[1], "date not provided")

    def test_rights_gate_blocks_unknown(self):
        gate = cutouts.rights_gate([
            {"claim_id": "a", "reuse_rights": {"status": "unknown"}},
            {"claim_id": "b", "reuse_rights": {"status": "permitted"}},
        ])
        self.assertFalse(gate["publish_ready"])
        self.assertEqual(gate["blocked_claim_ids"], ["a"])

    def test_rights_gate_passes_when_all_permitted(self):
        gate = cutouts.rights_gate([{"claim_id": "a", "reuse_rights": {"status": "permitted"}}])
        self.assertTrue(gate["publish_ready"])


class SelectionTests(unittest.TestCase):
    def test_cutout_budget_is_balanced(self):
        scene_claims = {index: [_claims()[0]] for index in range(10)}
        result = cutouts.select_cutout_scenes({}, scene_claims, max_ratio=0.3)
        self.assertLessEqual(len(result["selected"]), 3)
        self.assertGreaterEqual(len(result["selected"]), 1)

    def test_two_cutouts_never_sit_back_to_back(self):
        scene_claims = {index: [_claims()[0]] for index in range(8)}
        result = cutouts.select_cutout_scenes({}, scene_claims, max_ratio=0.5)
        indices = [item["scene_index"] for item in result["selected"]]
        for left, right in zip(indices, indices[1:]):
            self.assertGreater(right - left, 1)

    def test_weak_claims_are_not_selected(self):
        scene_claims = {index: [_claims()[1]] for index in range(6)}
        result = cutouts.select_cutout_scenes({}, scene_claims)
        self.assertEqual(result["selected"], [])


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
class CardRenderTests(unittest.TestCase):
    def test_card_renders_with_attribution(self):
        with tempfile.TemporaryDirectory() as td:
            card = cutouts.build_source_card(_claims()[0], Path(td))
            self.assertTrue(card["rendered"], card["warnings"])
            self.assertTrue(Path(card["path"]).is_file())
            self.assertGreater(len(card["content_sha256"]), 20)
            self.assertFalse(card["publish_ready"])
            self.assertEqual(card["attribution_lines"][0], "wire.example.com")

    def test_card_text_stays_inside_the_frame(self):
        with tempfile.TemporaryDirectory() as td:
            card = cutouts.build_source_card(_claims()[0], Path(td), excerpt_words=42)
            self.assertLessEqual(len(card["excerpt"]), 280)


def _run(cmd):
    subprocess.run([shutil.which("ffmpeg"), "-y", *cmd], check=True,
                   capture_output=True, text=True, timeout=60)


def _png(path: Path) -> Path:
    _run(["-f", "lavfi", "-i", "color=c=0x22d3ee:s=270x480:r=1", "-frames:v", "1", str(path)])
    return path


def _shots(count: int) -> list[dict]:
    return [{
        "index": index,
        "start": index * 3.1,
        "end": (index + 1) * 3.1,
        "duration": 3.1,
        "claim": f"claim number {index}",
        "caption": f"caption {index}",
        "asset_query": "data center servers",
        "visual": "data center servers",
    } for index in range(count)]


def _detail(index: int, path: Path) -> dict:
    return {
        "path": str(path), "provider": "motion_graphic", "visual_type": "motion_graphic",
        "scene_type": "typography", "asset_id": f"motion_graphic:{index}",
        "query": "data center servers", "relevance": "generated_from_narration",
        "relevance_confidence": "high", "semantic_review": False, "review_reason": "",
    }


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg required")
class StoryboardEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _build(self, evidence=None):
        shots = _shots(3)
        details = [_detail(index, _png(self.dir / f"a{index}.png")) for index in range(3)]
        return storyboard.build_storyboard(shots, details, self.dir / "work",
                                           evidence=evidence)

    def test_scene_records_carry_claim_and_evidence(self):
        claim = _claims()[0]
        payload = self._build({
            "scene_claims": {0: [claim]},
            "script_sha256": "scripthash",
            "ledger_sha256": "ledgerhash",
        })
        scene = payload["scenes"][0]
        self.assertEqual(scene["claim_ids"], ["clm_supported"])
        self.assertEqual(scene["evidence"][0]["status"], "supported")
        self.assertEqual(payload["script_sha256"], "scripthash")
        self.assertEqual(payload["ledger_sha256"], "ledgerhash")
        self.assertEqual(payload["evidence"]["scenes_with_claims"], 1)

    def test_weak_evidence_requires_review(self):
        payload = self._build({"scene_claims": {0: [_claims()[1]]},
                               "script_sha256": "s", "ledger_sha256": "l"})
        self.assertNotEqual(payload["review_status"], "auto_approved")
        self.assertTrue(any("weak evidence" in reason for reason in payload["review_reasons"]))

    def test_duplicate_claim_across_scenes_is_flagged(self):
        claim = _claims()[0]
        payload = self._build({"scene_claims": {0: [claim], 1: [claim]},
                               "script_sha256": "s", "ledger_sha256": "l"})
        self.assertTrue(any("already used by" in reason for reason in payload["review_reasons"]))

    def test_approval_is_invalidated_by_a_new_script_hash(self):
        payload = self._build({"scene_claims": {}, "script_sha256": "script-v1",
                               "ledger_sha256": "ledger-v1"})
        json_path = Path(payload["json_path"])
        storyboard.approve_storyboard(json_path, "owner")
        self.assertTrue(storyboard._approval_valid(payload))

        payload["script_sha256"] = "script-v2"
        self.assertFalse(storyboard._approval_valid(payload))

    def test_approval_is_invalidated_by_a_new_ledger_hash(self):
        payload = self._build({"scene_claims": {}, "script_sha256": "s", "ledger_sha256": "l1"})
        storyboard.approve_storyboard(Path(payload["json_path"]), "owner")
        payload["ledger_sha256"] = "l2"
        self.assertFalse(storyboard._approval_valid(payload))

    def test_blocked_cutout_rights_show_up_in_review(self):
        claim = _claims()[0]
        cutout = cutouts.build_source_card(claim, self.dir / "work")
        payload = self._build({
            "scene_claims": {0: [claim]},
            "cutouts": {0: cutout},
            "script_sha256": "s", "ledger_sha256": "l",
        })
        self.assertEqual(payload["scenes"][0]["evidence_visual"], cutout["path"])
        self.assertEqual(payload["scenes"][0]["reuse_rights"]["status"], "unknown")
        self.assertTrue(any("reuse rights unknown" in reason
                            for reason in payload["review_reasons"]))
        self.assertEqual(payload["evidence"]["cutouts_blocked_by_rights"], 1)


class RendererRightsSerializationTests(unittest.TestCase):
    """Renderer metadata must preserve the structured rights contract."""

    def test_permitted_rights_survive_renderer_serialization_and_authorization(self):
        from app.render import assembly
        from app.publish.authorization import _rights_violations

        rights = {"status": "permitted", "basis": "public_domain",
                  "source_url": "https://example.gov/source"}
        card = {"claim_id": "claim-1", "path": "cutout.png",
                "publish_ready": True, "reuse_rights": rights,
                "attribution_lines": ["Example publisher", "2025", "https://example.gov/source"]}
        persisted = assembly._serialize_cutout_evidence({0: card})
        self.assertEqual(persisted[0]["reuse_rights"], rights)
        self.assertEqual(_rights_violations({"evidence": {"cutouts": persisted}}), [])

    def test_unknown_rights_remain_blocked_after_renderer_serialization(self):
        from app.render import assembly
        from app.publish.authorization import _rights_violations

        card = {"claim_id": "claim-2", "reuse_rights": {"status": "unknown"}}
        persisted = assembly._serialize_cutout_evidence({0: card})
        violations = _rights_violations({"evidence": {"cutouts": persisted}})
        self.assertTrue(any("not a permitted basis" in item for item in violations))


if __name__ == "__main__":
    unittest.main()
