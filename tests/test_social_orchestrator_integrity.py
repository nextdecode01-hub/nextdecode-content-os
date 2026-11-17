from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from app.publish import artifact_snapshot, social_orchestrator as social


def _authorized_receipt(platform, video_sha256, purpose="short"):
    """Full-shape WP5 protected-action receipt mirroring authorize_publish.

    verify_protected_action_decision enforces the receipt's scope keys, the
    canonical binding fields and the derived authorization_id, so the fake
    must satisfy the same contract a real receipt does.
    """
    from app.publish import authorization as authorization_module
    decision = {
        "policy_version": authorization_module.POLICY_VERSION,
        "status": "authorized",
        "action_type": "publish",
        "platform": str(platform),
        "purpose": purpose,
        "destination": "private",
        "public_release": None,
        "approved_at": "2026-11-06T00:00:00+00:00",
        "reviewer": "test-reviewer",
        "metadata_sha256": "c" * 64,
        "video_sha256": video_sha256,
    }
    binding_fields = (
        "policy_version", "action_type", "platform", "purpose", "destination",
        "approved_at", "reviewer", "metadata_sha256", "video_sha256",
    )
    decision["authorization_id"] = hashlib.sha256(
        json.dumps({key: decision[key] for key in binding_fields},
                   sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return decision


class SocialOrchestratorIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = self.root / "source.mp4"
        self.video.write_bytes(b"authorized-video-bytes" * 2048)
        self.digest = hashlib.sha256(self.video.read_bytes()).hexdigest()
        self.ledger = self.root / "data" / "ledger.json"
        self.lock = self.ledger.with_suffix(".json.lock")
        self.stack = patch.multiple(
            social,
            LEDGER=self.ledger,
            LEDGER_LOCK=self.lock,
        )
        self.stack.start()
        self.snapshot_root = patch.object(artifact_snapshot, "ROOT", self.root)
        self.snapshot_root.start()
        self.auth = patch(
            "app.publish.authorization.authorize_publish",
            side_effect=lambda *, platform, **_kwargs: _authorized_receipt(platform, self.digest),
        )
        self.auth.start()
        self.addCleanup(self.auth.stop)
        self.addCleanup(self.snapshot_root.stop)
        self.addCleanup(self.stack.stop)
        self.addCleanup(self.temp.cleanup)

    def test_malformed_ledger_fails_closed(self):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "publishing is blocked"):
            social._ledger()

    def test_non_object_ledger_fails_closed(self):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "top-level shape"):
            social._ledger()

    def test_nested_ledger_records_fail_closed(self):
        fingerprint = "a" * 64
        malformed_records = [
            None,
            "posted",
            [],
            {"post_id": "p1"},
            {"post_id": "p1", "url": None, "ts": "not-a-timestamp"},
        ]
        for record in malformed_records:
            with self.subTest(record=record):
                self.ledger.parent.mkdir(parents=True, exist_ok=True)
                self.ledger.write_text(
                    json.dumps({fingerprint: {"mastodon": record}}),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(RuntimeError, "platform record|timestamp"):
                    social._ledger()

    def test_unknown_platform_and_malformed_fingerprint_fail_closed(self):
        valid_record = {"post_id": "p1", "url": None, "ts": "2026-11-06T00:00:00+00:00"}
        for payload in (
            {"not-a-digest": {"mastodon": valid_record}},
            {"a" * 64: {"unknown-platform": valid_record}},
        ):
            with self.subTest(payload=payload):
                self.ledger.parent.mkdir(parents=True, exist_ok=True)
                self.ledger.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "invalid entry|invalid platform"):
                    social._ledger()

    def test_ledger_save_is_atomic_and_readable(self):
        expected = {"a" * 64: {"mastodon": {
            "post_id": "p1", "url": None, "ts": "2026-11-06T00:00:00+00:00"
        }}}
        social._ledger_save(expected)
        self.assertEqual(social._ledger(), expected)
        self.assertEqual(list(self.ledger.parent.glob("ledger.json.*.tmp")), [])

    def test_fingerprint_requires_verified_bytes(self):
        with self.assertRaisesRegex(ValueError, "digest is required"):
            social._fingerprint("mastodon", "caption", self.video, "")
        with self.assertRaisesRegex(ValueError, "do not match"):
            social._fingerprint("mastodon", "caption", self.video, "0" * 64)

    def test_file_adapter_receives_pinned_snapshot_and_ledger_prevents_duplicate(self):
        seen = []
        def adapter(**kwargs):
            seen.append(Path(kwargs["video_path"]).read_bytes())
            return {"platform": "mastodon", "ok": True, "post_id": "post-1", "url": None, "error": None}

        with patch.dict(social.PLATFORMS, {"mastodon": {
            "name": "mastodon", "requires": [], "capabilities": ["video"],
            "configured": lambda: True, "publish": adapter,
        }}):
            first = social.publish("mastodon", self.video, "A caption")
            second = social.publish("mastodon", self.video, "A caption")

        self.assertTrue(first["ok"])
        self.assertFalse(second["ok"])
        self.assertIn("duplicate", second["error"])
        self.assertEqual(seen, [self.video.read_bytes()])
        self.assertTrue(self.ledger.is_file())
        self.assertEqual(len(json.loads(self.ledger.read_text(encoding="utf-8"))), 1)


    def test_concurrent_posts_are_serialized_and_only_one_adapter_runs(self):
        calls = []
        def adapter(**kwargs):
            calls.append(Path(kwargs["video_path"]).read_bytes())
            return {"platform": "mastodon", "ok": True, "post_id": "post-1", "url": None, "error": None}

        with patch.dict(social.PLATFORMS, {"mastodon": {
            "name": "mastodon", "requires": [], "capabilities": ["video"],
            "configured": lambda: True, "publish": adapter,
        }}):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(
                    lambda _: social.publish("mastodon", self.video, "same caption"),
                    range(2),
                ))
        self.assertEqual(sum(bool(item["ok"]) for item in results), 1)
        self.assertEqual(len(calls), 1)

    def test_provider_success_with_ledger_failure_is_reported_ambiguous(self):
        adapter = unittest.mock.Mock(return_value={
            "platform": "mastodon", "ok": True, "post_id": "post-1", "url": None, "error": None
        })
        with (
            patch.dict(social.PLATFORMS, {"mastodon": {
                "name": "mastodon", "requires": [], "capabilities": ["video"],
                "configured": lambda: True, "publish": adapter,
            }}),
            patch.object(social, "_ledger_save", side_effect=OSError("disk full")),
        ):
            result = social.publish("mastodon", self.video, "caption")
        self.assertFalse(result["ok"])
        self.assertIn("ambiguous", result["error"])
        adapter.assert_called_once()

    def test_url_adapter_fails_closed_without_snapshot_transport(self):
        adapter = unittest.mock.Mock(return_value={"ok": True})
        with patch.dict(social.PLATFORMS, {"instagram": {
            "name": "instagram", "requires": [], "capabilities": ["video"],
            "configured": lambda: True, "publish": adapter,
        }}):
            result = social.publish("instagram", self.video, "caption")
        self.assertFalse(result["ok"])
        self.assertIn("URL adapter cannot prove", result["error"])
        adapter.assert_not_called()

    def test_corrupt_ledger_blocks_before_adapter(self):
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.write_text("not-json", encoding="utf-8")
        adapter = unittest.mock.Mock(return_value={"ok": True})
        with patch.dict(social.PLATFORMS, {"mastodon": {
            "name": "mastodon", "requires": [], "capabilities": ["video"],
            "configured": lambda: True, "publish": adapter,
        }}):
            result = social.publish("mastodon", self.video, "caption")
        self.assertFalse(result["ok"])
        self.assertIn("publishing is blocked", result["error"])
        adapter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
