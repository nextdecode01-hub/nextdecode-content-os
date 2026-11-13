from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.publish.authorization import PublishNotAuthorized, _approval_records
from governance_fixtures import build_sandbox


class ImmutableReviewPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.paths = build_sandbox(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_original_review_package_is_pending_and_separately_attested(self):
        approval, package = _approval_records(data_root=self.root, purpose="short")
        self.assertEqual(package["status"], "pending_human_review")
        self.assertTrue(approval["review_package_sha256"])
        self.assertTrue(approval["reviewer"])
        self.assertEqual(approval["destination"], "private")
        self.assertTrue(all(value is True for value in approval["checklist"].values()))

    def test_any_review_package_mutation_invalidates_approval(self):
        package_path = self.paths["package"]
        package = json.loads(package_path.read_text(encoding="utf-8"))
        package["notes"] = "changed after review"
        package_path.write_text(json.dumps(package), encoding="utf-8")
        with self.assertRaisesRegex(PublishNotAuthorized, "changed after human approval"):
            _approval_records(data_root=self.root, purpose="short")

    def test_decision_record_mutation_invalidates_approval_pointer(self):
        pointer = json.loads(self.paths["approval"].read_text(encoding="utf-8"))
        decision_path = Path(pointer["decision_record"])
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        decision["reviewer"] = "forged"
        decision_path.write_text(json.dumps(decision), encoding="utf-8")
        with self.assertRaisesRegex(PublishNotAuthorized, "decision record digest mismatch"):
            _approval_records(data_root=self.root, purpose="short")

    def test_missing_checklist_evidence_fails_closed(self):
        pointer = json.loads(self.paths["approval"].read_text(encoding="utf-8"))
        decision_path = Path(pointer["decision_record"])
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        decision["checklist"]["primary_source_checked"] = False
        decision_path.write_text(json.dumps(decision), encoding="utf-8")
        pointer["decision_record_sha256"] = __import__("hashlib").sha256(
            decision_path.read_bytes()).hexdigest()
        self.paths["approval"].write_text(json.dumps(pointer), encoding="utf-8")
        with self.assertRaisesRegex(PublishNotAuthorized, "checklist is incomplete"):
            _approval_records(data_root=self.root, purpose="short")


if __name__ == "__main__":
    unittest.main()
