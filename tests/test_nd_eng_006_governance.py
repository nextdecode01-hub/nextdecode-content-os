"""ND-ENG-006 / ND-ENG-006-R1 regression tests: fail-closed governance.

Covers the coordination of the approved design: producer stamps, the fail-closed
``_validate_governance`` flip, run-receipt cross-checks and the external
hash-chained legacy-backfill receipts.  Everything is hermetic: sandbox roots,
no network, no live publishing, no writes to the repository's live ``data/``
or ``outputs/`` slots.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.maintenance import backfill_governance as backfill_governance
from app.publish import authorization as publish_authorization
from app.publish.authorization import PublishNotAuthorized, authorize_publish
from governance_fixtures import build_sandbox

LARGE_VIDEO = b"rendered-short-payload" * 10_000


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_blocked(test, box, code="blocked_governance", purpose="short", platform="youtube"):
    with test.assertRaises(PublishNotAuthorized) as caught:
        authorize_publish(platform=platform, purpose=purpose, data_root=box.root)
    test.assertEqual(caught.exception.code, code)


def _assert_authorized(box, purpose="short", platform="youtube"):
    return authorize_publish(platform=platform, purpose=purpose, data_root=box.root)


def _rebind(box):
    """Model a fresh owner review after artifact changes; preserve the old snapshot."""
    meta_digest = _sha256(box.paths["metadata"])
    video_digest = _sha256(box.paths["video"])
    pointer = json.loads(box.paths["approval"].read_text(encoding="utf-8"))
    old_package = json.loads(box.paths["package"].read_text(encoding="utf-8"))
    package = dict(old_package)
    package["metadata_sha256"] = meta_digest
    package["video_sha256"] = video_digest
    package_path = box.root / "data" / "review_package_reapproved.json"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    decision_path = box.root / "data" / "review_approvals" / "reapproved.json"
    decision = json.loads(Path(pointer["decision_record"]).read_text(encoding="utf-8"))
    decision.update({
        "package": str(package_path),
        "review_package_sha256": _sha256(package_path),
        "metadata_sha256": meta_digest,
        "video_sha256": video_digest,
        "approved_at": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
    })
    decision_path.write_text(json.dumps(decision), encoding="utf-8")
    pointer.update({
        "package": str(package_path),
        "decision_record": str(decision_path),
        "decision_record_sha256": _sha256(decision_path),
    })
    box.paths["package"] = package_path
    box.paths["approval"].write_text(json.dumps(pointer), encoding="utf-8")


class _Box:
    """Approved sandbox + authorization pointed at a throwaway root."""

    def __init__(self, **kwargs):
        kwargs.setdefault("video_bytes", LARGE_VIDEO)
        self.kwargs = kwargs
        self._tmp = None
        self.root = None
        self.paths = None
        self._patcher = None

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.paths = build_sandbox(self.root, **self.kwargs)
        self._patcher = patch.object(publish_authorization, "ROOT", self.root)
        self._patcher.__enter__()
        return self

    def __exit__(self, *exc_info):
        self._patcher.__exit__(*exc_info)
        self._tmp.cleanup()
        return False


class FailClosedGovernanceTests(unittest.TestCase):
    """The former fail-open must now block, and valid stamps authorize."""

    def test_missing_governance_fails_closed(self):
        with _Box(stamp_governance=False) as box:
            _assert_blocked(self, box)

    def test_valid_orchestrated_stamp_with_run_receipt_authorizes(self):
        with _Box() as box:
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            self.assertEqual(payload["governance"]["entry"], "orchestrated")
            self.assertTrue(payload["governance"]["publishable"])
            decision = _assert_authorized(box)
        self.assertEqual(decision["status"], "authorized")

    def test_valid_fixture_run_receipt_records_the_stamped_bytes(self):
        with _Box() as box:
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            manifest = json.loads(
                (box.root / "outputs" / "runs" / payload["run_id"] / "manifest.json")
                .read_text(encoding="utf-8"))
            stamped_digest = _sha256(box.paths["metadata"])
        self.assertEqual(manifest["artifacts"]["metadata"]["sha256"], stamped_digest)
        self.assertEqual(manifest["promotion"]["status"], "completed")

    def test_stamp_run_id_mismatch_is_blocked(self):
        with _Box() as box:
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            payload["governance"]["run_id"] = "20260101-000000-forged"
            box.paths["metadata"].write_text(json.dumps(payload), encoding="utf-8")
            _rebind(box)
            _assert_blocked(self, box)

    def test_missing_run_receipt_is_blocked(self):
        with _Box() as box:
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            (box.root / "outputs" / "runs" / payload["run_id"] / "manifest.json").unlink()
            _assert_blocked(self, box)

    def test_digest_drift_in_the_run_receipt_is_blocked(self):
        with _Box() as box:
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            manifest_path = (box.root / "outputs" / "runs" /
                             payload["run_id"] / "manifest.json")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"]["metadata"]["sha256"] = "a" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            _assert_blocked(self, box)

    def test_incomplete_run_is_never_receipt_valid(self):
        with _Box() as box:
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            manifest_path = (box.root / "outputs" / "runs" /
                             payload["run_id"] / "manifest.json")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "in_progress"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            _assert_blocked(self, box)

    def test_entry_purpose_mismatch_is_blocked(self):
        with _Box(mutate_metadata=lambda m: m.update(
                {"governance": {"entry": "longform", "publishable": True}})) as box:
            _assert_blocked(self, box)

    def test_malformed_governance_is_normalized_to_blocked_governance(self):
        with _Box(mutate_metadata=lambda m: m.update({"governance": "direct"})) as box:
            _assert_blocked(self, box)


class DraftStampTests(unittest.TestCase):
    """Dry-run and standard-legacy producers can never be publishable."""

    def test_dry_run_stamp_is_draft_only(self):
        with _Box(mutate_metadata=lambda m: m.update(
                {"governance": {"entry": "dry_run", "publishable": False}})) as box:
            _assert_blocked(self, box)

    def test_standard_legacy_stamp_is_draft_only(self):
        with _Box(mutate_metadata=lambda m: m.update(
                {"governance": {"entry": "standard-legacy", "publishable": False}})) as box:
            _assert_blocked(self, box)

    def test_draft_helper_never_claimed_publishable(self):
        from pipelines import short as ps

        for entry in ("dry_run", "standard-legacy"):
            with self.subTest(entry=entry):
                stamp = ps._draft_governance(entry)
                self.assertFalse(stamp["publishable"])
                self.assertEqual(stamp["entry"], entry)
                self.assertTrue(stamp["reason"])

    def test_longform_stamp_authorizes_longform(self):
        with _Box(purpose="longform") as box:
            decision = _assert_authorized(box, purpose="longform",
                                          platform="youtube_longform")
        self.assertEqual(decision["status"], "authorized")


class LongformAuthorizationTests(unittest.TestCase):
    """P0 regressions: scheduling flag alone must never authorize publication.

    The ``--scheduled-approved`` flag is a window restriction (20:00 IST), not
    an authorization bypass.  Owner-release (``PUBLISH_MODE=publish`` +
    ``AUTO_PUBLISH_APPROVED=true``) is required independently for every publish
    attempt.
    """

    def test_owner_release_only_authorizes(self):
        """PUBLISH_MODE=publish + AUTO_PUBLISH_APPROVED=true authorizes even without --scheduled-approved."""
        with _Box(purpose="longform") as box:
            with patch.dict(
                os.environ,
                {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"},
                clear=True,
            ):
                decision = _assert_authorized(box, purpose="longform",
                                              platform="youtube_longform")
        self.assertEqual(decision["status"], "authorized")

    def test_fully_authorized_with_window_open(self):
        """PUBLISH_MODE=publish + AUTO_PUBLISH_APPROVED=true + --scheduled-approved authorizes when window is open."""
        with _Box(purpose="longform") as box:
            with patch(
                "app.publish.authorization.upload_window_open",
                return_value=True,
            ):
                with patch.dict(
                    os.environ,
                    {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"},
                    clear=True,
                ):
                    # The adapter gate now always requires the env; with publish+approved
                    # and window open, authorization flows to authorize_publish.
                    from unittest.mock import patch as _patch
                    with _patch.dict(
                        os.environ,
                        {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"},
                        clear=True,
                    ):
                        rc = publish_authorization.authorize_publish(
                            platform="youtube_longform", purpose="longform", data_root=box.root,
                            require_window=True)
        self.assertEqual(rc["status"], "authorized")


    def test_fully_authorized_outside_window_is_blocked(self):
        with _Box(purpose="longform") as box:
            with patch("app.publish.authorization.upload_window_open", return_value=False):
                with patch.dict(os.environ,
                                {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"},
                                clear=True):
                    with self.assertRaises(PublishNotAuthorized) as caught:
                        publish_authorization.authorize_publish(
                            platform="youtube_longform", purpose="longform",
                            data_root=box.root, require_window=True)
        self.assertEqual(caught.exception.code, "blocked_schedule")


class LegacyBackfillReceiptTests(unittest.TestCase):
    """External hash-chained journal: trust enters only through the owner."""

    def _point_journal(self, box) -> Path:
        journal = box.root / "data" / "governance_backfill.jsonl"
        patcher = patch.object(backfill_governance, "JOURNAL_PATH", journal)
        patcher.start()
        self.addCleanup(patcher.stop)
        return journal

    def test_valid_backfill_and_reapproval_authorizes(self):
        with _Box(stamp_governance=False) as box:
            journal = self._point_journal(box)
            result = backfill_governance.apply_backfill(
                box.root, "short", "owner re-approved legacy artifact")
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            self.assertEqual(payload["governance"]["entry"], "legacy-backfill")
            self.assertEqual(payload["governance"]["receipt_ref"], result["receipt_ref"])
            _rebind(box)  # owner re-approval binds the stamped bytes
            decision = _assert_authorized(box)
            journal_text = journal.read_text(encoding="utf-8")
        self.assertEqual(decision["status"], "authorized")
        self.assertEqual(len(journal_text.strip().splitlines()), 2)

    def test_tampered_journal_line_fails_the_chain(self):
        with _Box(stamp_governance=False) as box:
            journal = self._point_journal(box)
            backfill_governance.apply_backfill(box.root, "short", "note")
            lines = journal.read_text(encoding="utf-8").splitlines()
            forged = json.loads(lines[0])
            forged["owner_note"] = "rewritten history"
            lines[0] = json.dumps(forged)
            journal.write_text("\n".join(lines) + "\n", encoding="utf-8")
            _rebind(box)
            _assert_blocked(self, box)

    def test_spliced_journal_line_fails_the_chain(self):
        with _Box(stamp_governance=False) as box:
            journal = self._point_journal(box)
            backfill_governance.apply_backfill(box.root, "short", "note")
            lines = journal.read_text(encoding="utf-8").splitlines()
            journal.write_text("\n".join(lines + [lines[0]]) + "\n", encoding="utf-8")
            _rebind(box)
            _assert_blocked(self, box)

    def test_foreign_receipt_ref_is_blocked(self):
        with _Box(stamp_governance=False) as box:
            self._point_journal(box)
            backfill_governance.apply_backfill(box.root, "short", "note")
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            payload["governance"]["receipt_ref"] = "b" * 64
            box.paths["metadata"].write_text(json.dumps(payload), encoding="utf-8")
            _rebind(box)
            _assert_blocked(self, box)

    def test_backfill_refuses_when_not_currently_approved(self):
        with _Box(stamp_governance=False) as box:
            self._point_journal(box)
            box.paths["video"].write_bytes(b"changed-after-approval" + LARGE_VIDEO)
            with self.assertRaises(SystemExit):
                backfill_governance.apply_backfill(box.root, "short", "note")
            payload = json.loads(box.paths["metadata"].read_text(encoding="utf-8"))
            self.assertNotIn("governance", payload)

    def test_backfill_refuses_an_already_stamped_artifact(self):
        with _Box(stamp_governance=False) as box:
            self._point_journal(box)
            backfill_governance.apply_backfill(box.root, "short", "note")
            with self.assertRaises(SystemExit):
                backfill_governance.apply_backfill(box.root, "short", "note")


class ProducerStampOrderTests(unittest.TestCase):
    """Pin: pipelines/short.py stamps -> writes -> the run records THAT digest."""

    def test_strong_main_stamps_before_the_run_records_the_metadata(self):
        import pipelines.short as ps

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def fake_strong(topic, work_dir, metadata_file, **_kwargs):
                (work_dir / "output_short.mp4").write_bytes(LARGE_VIDEO)
                return {"title": "Stamp Order", "topic": "stamp order",
                        "voice_text": "text", "video_path": "output_short.mp4"}

            with patch.object(ps, "SCRIPT_DIR", root), \
                    patch.object(ps, "run_strong_pipeline", side_effect=fake_strong), \
                    patch.object(ps, "archive_video", return_value=root / "archived.mp4"), \
                    patch.object(ps, "record_topic"), \
                    patch.object(ps, "_record_failure") as failure, \
                    patch.dict(os.environ, {"DRY_RUN": ""}, clear=False), \
                    patch("sys.argv", [str(root / "pipelines" / "short.py"),
                                       "--topic", "stamp order"]):
                ps.main()

            runs = sorted((root / "outputs" / "runs").iterdir())
            self.assertEqual(len(runs), 1)
            manifest = json.loads((runs[0] / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "ok")
            failure.assert_not_called()
            metadata_stage = next(
                item for item in manifest["stages"]
                if item["name"] == "metadata_persistence"
            )
            self.assertEqual(metadata_stage["status"], "ok")
            self.assertEqual(manifest["artifacts"]["metadata"]["stage"], "metadata_persistence")
            stamped = json.loads((runs[0] / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(stamped["governance"]["entry"], "orchestrated")
            self.assertEqual(stamped["governance"]["run_id"], manifest["run_id"])
            # the recorded receipt IS the digest of the stamped bytes
            self.assertEqual(manifest["artifacts"]["metadata"]["sha256"],
                             _sha256(runs[0] / "metadata.json"))
            promoted = json.loads((root / "data" / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(promoted["governance"]["publishable"], True)
            self.assertEqual(_sha256(root / "data" / "metadata.json"),
                             _sha256(runs[0] / "metadata.json"))


if __name__ == "__main__":
    unittest.main()