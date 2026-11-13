"""Publishing-governance regression tests - ND-ENG-002.

Everything here is hermetic: sandbox roots, mocked platform services, no network, no
live publishing, no writes to the repository's live ``data/`` or ``outputs/`` slots.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.publish import orchestration as publish_all
from app.publish import authorization as publish_authorization
from app.publish.authorization import PublishNotAuthorized, authorize_publish
from app.publish import facebook_reels_upload as fb
from app.publish import instagram_reels_upload as ig
from app.publish import youtube_longform_upload as longform
from app.publish import youtube_upload as yt
from governance_fixtures import build_sandbox, permitted_cutout, publishable_metadata

# The publisher adapters refuse videos under 150 KB, so governance fixtures use a
# realistically sized stand-in payload.
LARGE_VIDEO = b"rendered-short-payload" * 10_000
META_ENV = {
    "META_GRAPH_API_VERSION": "v19.0",
    "INSTAGRAM_USER_ID": "ig-user",
    "INSTAGRAM_ACCESS_TOKEN": "ig-token",
    "FACEBOOK_PAGE_ID": "page-id",
    "FACEBOOK_PAGE_ACCESS_TOKEN": "page-token",
}


class _Sandbox:
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


class DirectPublisherApprovalTests(unittest.TestCase):
    """1-4: every direct publisher path enforces current approval."""

    def test_youtube_direct_upload_rejects_missing_approval(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(publish_authorization, "ROOT", Path(tmp)), \
                patch.object(yt, "get_authenticated_service") as service:
            with self.assertRaises(PublishNotAuthorized) as caught:
                yt.upload_video("clip.mp4", "T", "D", ["ai"], data_root=Path(tmp))
        self.assertEqual(caught.exception.code, "blocked_approval")
        service.assert_not_called()

    def test_instagram_direct_publish_rejects_missing_approval(self):
        with tempfile.TemporaryDirectory() as tmp, \
                _Sandbox() as box, \
                patch.object(publish_authorization, "ROOT", Path(tmp)), \
                patch.object(ig, "METADATA", box.paths["metadata"]), \
                patch.object(ig, "VIDEO", box.paths["video"]), \
                patch.dict(os.environ, META_ENV), \
                patch.object(ig.requests, "post") as post:
            with self.assertRaises(PublishNotAuthorized):
                ig.publish()
        post.assert_not_called()

    def test_facebook_direct_publish_rejects_missing_approval(self):
        with tempfile.TemporaryDirectory() as tmp, \
                _Sandbox() as box, \
                patch.object(publish_authorization, "ROOT", Path(tmp)), \
                patch.object(fb, "METADATA", box.paths["metadata"]), \
                patch.object(fb, "VIDEO", box.paths["video"]), \
                patch.dict(os.environ, META_ENV), \
                patch.object(fb.requests, "post") as post:
            with self.assertRaises(PublishNotAuthorized):
                fb.publish()
        post.assert_not_called()

    def test_expired_approval_blocks_every_direct_publisher(self):
        expired = "2026-01-01T09:00:00+05:30"
        with _Sandbox(approved_at=expired) as box:
            with self.assertRaises(PublishNotAuthorized) as youtube:
                yt.upload_video(str(box.paths["video"]), "T", "D", [], data_root=box.root)
            self.assertEqual(youtube.exception.code, "blocked_approval")
            with patch.object(ig, "METADATA", box.paths["metadata"]), \
                    patch.object(ig, "VIDEO", box.paths["video"]), \
                    patch.dict(os.environ, META_ENV):
                with self.assertRaises(PublishNotAuthorized):
                    ig.publish()
            with patch.object(fb, "METADATA", box.paths["metadata"]), \
                    patch.object(fb, "VIDEO", box.paths["video"]), \
                    patch.dict(os.environ, META_ENV):
                with self.assertRaises(PublishNotAuthorized):
                    fb.publish()

    def test_hash_mismatch_blocks_every_direct_publisher(self):
        with _Sandbox() as box:
            # Keep the payload above the adapters' 150 KB render guard so the test
            # reaches authorization instead of failing the artifact sanity check.
            box.paths["video"].write_bytes(b"different-render-after-approval" + LARGE_VIDEO)
            with self.assertRaises(PublishNotAuthorized) as caught:
                yt.upload_video(str(box.paths["video"]), "T", "D", [], data_root=box.root)
            self.assertIn("does not match", caught.exception.reason)
            with patch.object(ig, "METADATA", box.paths["metadata"]), \
                    patch.object(ig, "VIDEO", box.paths["video"]), \
                    patch.dict(os.environ, META_ENV):
                with self.assertRaises(PublishNotAuthorized):
                    ig.publish()
            with patch.object(fb, "METADATA", box.paths["metadata"]), \
                    patch.object(fb, "VIDEO", box.paths["video"]), \
                    patch.dict(os.environ, META_ENV):
                with self.assertRaises(PublishNotAuthorized):
                    fb.publish()


class RightsAndEvidenceTests(unittest.TestCase):
    """6-8 plus approved decisions 3, 5: rights and evidence fail closed."""

    def test_unknown_rights_block_publishing(self):
        for status in ("unknown", "incompatible"):
            with _Sandbox(mutate_metadata=lambda m, s=status: m["evidence"].update(
                    {"cutouts": [permitted_cutout(status=s)]})) as box:
                with self.assertRaises(PublishNotAuthorized) as caught:
                    authorize_publish(platform="youtube", data_root=box.root)
                self.assertEqual(caught.exception.code, "blocked_rights")

    def test_unrecognized_or_malformed_rights_metadata_fails_closed(self):
        cases = [
            {"reuse_rights": None},
            {"reuse_rights": {}},
            {"reuse_rights": {"status": ""}},
            {"reuse_rights": "permitted"},
            {"reuse_rights": {"status": "maybe"}},
            {"reuse_rights": {"basis": "no status field"}},
        ]
        for payload in cases:
            record = {"claim_id": "clm_0001", "scene_index": 0}
            record.update(payload)
            with _Sandbox(mutate_metadata=lambda m, r=record: m["evidence"].update(
                    {"cutouts": [r]})) as box:
                with self.assertRaises(PublishNotAuthorized) as caught:
                    authorize_publish(platform="youtube", data_root=box.root)
                self.assertEqual(caught.exception.code, "blocked_rights", str(payload))

    def test_legitimate_no_cutout_content_still_publishes(self):
        # A Short with no on-screen claim cutouts has no rights exposure; the absence of
        # cutouts must not be confused with missing rights metadata.
        with _Sandbox() as box:
            decision = authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(decision["status"], "authorized")
        self.assertEqual(decision["destination"], "private")

    def test_missing_rights_on_a_real_cutout_is_blocked_not_inferred(self):
        with _Sandbox(mutate_metadata=lambda m: m["evidence"].update(
                {"cutouts": [{"claim_id": "clm_0001", "scene_index": 0}]})) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertIn("reuse_rights", caught.exception.reason)

    def test_renderer_serialized_permitted_rights_reach_real_publish_authorizer(self):
        """Exercise renderer serialization through the actual authorization boundary."""
        from app.render import assembly

        card = {
            "claim_id": "clm_0001",
            "path": "cutouts/source-card.png",
            "publish_ready": True,
            "reuse_rights": {
                "status": "permitted",
                "basis": "public_domain",
                "source_url": "https://example.gov/source",
            },
            "attribution_lines": ["Example publisher", "2025", "https://example.gov/source"],
        }
        persisted = assembly._serialize_cutout_evidence({0: card})
        with _Sandbox(mutate_metadata=lambda m: m["evidence"].update(
                {"cutouts": persisted})) as box:
            decision = authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(decision["status"], "authorized")

    def test_renderer_serialized_unknown_rights_are_blocked_by_real_publish_authorizer(self):
        """Unknown rights must remain blocking after renderer metadata serialization."""
        from app.render import assembly

        card = {
            "claim_id": "clm_0001",
            "path": "cutouts/source-card.png",
            "publish_ready": False,
            "reuse_rights": {
                "status": "unknown",
                "basis": "no licence evidence",
                "source_url": "https://example.invalid/source",
            },
            "attribution_lines": [],
        }
        persisted = assembly._serialize_cutout_evidence({0: card})
        with _Sandbox(mutate_metadata=lambda m: m["evidence"].update(
                {"cutouts": persisted})) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_rights")

    def _assert_evidence_blocked(self, mutate):
        with _Sandbox(mutate_metadata=mutate) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_evidence")

    def test_unsupported_claims_block_publishing(self):
        self._assert_evidence_blocked(
            lambda m: m["evidence"]["summary"].update({"by_status": {"supported": 1, "unsupported": 1}}))

    def test_outdated_claims_block_publishing(self):
        self._assert_evidence_blocked(
            lambda m: m["evidence"]["summary"].update({"by_status": {"supported": 1, "outdated": 2}}))

    def test_unverified_claims_block_publishing(self):
        self._assert_evidence_blocked(
            lambda m: m["evidence"]["summary"].update({"by_status": {"unverified": 1}}))

    def test_conflicting_claims_block_publishing(self):
        self._assert_evidence_blocked(
            lambda m: m["evidence"]["summary"].update({"by_status": {"conflicting": 1}}))

    def test_missing_evidence_blocks_publishing(self):
        self._assert_evidence_blocked(lambda m: m.pop("evidence"))

    def test_evidence_needs_review_flag_is_unverified_and_blocks(self):
        self._assert_evidence_blocked(lambda m: m["evidence"]["flags"].append(
            {"flag": "evidence_needs_review", "claim_id": "clm_0001", "sentence": "x"}))

    def test_shot_level_evidence_flags_block(self):
        self._assert_evidence_blocked(
            lambda m: m["shots"][0].update({"evidence_flags": ["evidence_missing"]}))

    def test_factual_sentence_without_a_claim_record_blocks(self):
        self._assert_evidence_blocked(
            lambda m: m["evidence"].update({"unmapped_factual": ["NIST said a thing."]}))

    def test_missing_claim_status_summary_fails_closed(self):
        self._assert_evidence_blocked(lambda m: m["evidence"].update({"summary": {}}))

    def test_tampered_claim_ledger_blocks(self):
        with _Sandbox() as box:
            box.paths["ledger"].write_text(json.dumps({"claims": []}), encoding="utf-8")
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_evidence")

    def test_unbound_claim_ledger_blocks(self):
        with _Sandbox(mutate_metadata=lambda m: m["evidence"].update({"ledger_sha256": ""})) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_evidence")

    def test_non_strong_artifacts_can_never_publish(self):
        for quality in ("standard", "dry_run", ""):
            with _Sandbox(mutate_metadata=lambda m, q=quality: m.update({"quality": q})) as box:
                with self.assertRaises(PublishNotAuthorized) as caught:
                    authorize_publish(platform="youtube", data_root=box.root)
            self.assertEqual(caught.exception.code, "blocked_quality", quality)


class StoryboardGovernanceTests(unittest.TestCase):
    """9: review is mandatory by default, and promotion cannot bypass it."""

    def test_needs_review_artifact_cannot_authorize(self):
        with _Sandbox(mutate_metadata=lambda m: m["storyboard"].update(
                {"review_status": "needs_review", "approved": False})) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_review")

    def test_disabled_storyboard_record_cannot_authorize(self):
        with _Sandbox(mutate_metadata=lambda m: m["storyboard"].update(
                {"review_status": "disabled", "approved": False})) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_review")

    def test_human_approved_storyboard_authorizes(self):
        with _Sandbox(mutate_metadata=lambda m: m["storyboard"].update(
                {"review_status": "needs_review", "human_approved": True})) as box:
            decision = authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(decision["status"], "authorized")

    def test_default_gate_is_require_without_environment(self):
        from app.visuals import storyboard

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "storyboard review required"):
                storyboard.enforce_review_gate({"review_status": "needs_review",
                                                "review_reasons": ["unverified visual"]})

    def test_unknown_gate_mode_fails_closed(self):
        from app.visuals import storyboard

        with patch.dict(os.environ, {"STORYBOARD_GATE": "sometimes"}):
            with self.assertRaisesRegex(RuntimeError, "not a recognised mode"):
                storyboard.enforce_review_gate({"review_status": "needs_review"})

    def test_explicit_warn_mode_is_opt_in_only(self):
        from app.visuals import storyboard

        with patch.dict(os.environ, {"STORYBOARD_GATE": "warn"}):
            storyboard.enforce_review_gate({"review_status": "needs_review",
                                            "review_reasons": ["x"]})


class ShortRenderQualityAuthorizationTests(unittest.TestCase):
    def test_short_upload_requires_passing_render_qa(self):
        with _Sandbox(mutate_metadata=lambda m: m.update({"qa": {"status": "fail"}})) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_quality")

    def test_short_upload_requires_burned_captions(self):
        with _Sandbox(mutate_metadata=lambda m: m.update({"captions_burned": False})) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_quality")

    def test_short_upload_requires_45_to_60_seconds(self):
        with _Sandbox(mutate_metadata=lambda m: m.update({
            "qa": {"status": "pass", "duration": 35.0, "width": 1080,
                   "height": 1920, "fps": 30.0}
        })) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(caught.exception.code, "blocked_quality")


class DirectEntryGovernanceTests(unittest.TestCase):
    """10: the direct pipeline entry point produces draft-only artifacts."""

    def test_direct_cli_run_is_marked_non_publishable_and_blocked(self):
        from app.script import pipeline

        fake = publishable_metadata()
        fake.update({
            "video_path": "outputs/output_short.mp4",
            "duration_seconds": 42.0,
            "word_count": 110,
            "research": {"claims": [{"claim_id": "clm_0001"}]},
        })
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "metadata.json"
            with patch.object(pipeline, "ROOT", root), \
                    patch.object(pipeline, "run", return_value=dict(fake)):
                code = pipeline.main(["--topic", "AI grids", "--out", str(out)])
            self.assertEqual(code, 0)
            written = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(written["governance"], {
                "entry": "direct", "publishable": False,
                "reason": "the direct pipeline entry point does not run the approved orchestration"})

            ledger = root / "research" / "claim_ledger.json"
            ledger.parent.mkdir(parents=True, exist_ok=True)
            sandbox = build_sandbox(root, metadata=written, video_bytes=LARGE_VIDEO)
            with patch.object(publish_authorization, "ROOT", root):
                with self.assertRaises(PublishNotAuthorized) as caught:
                    authorize_publish(platform="youtube", data_root=root)
        self.assertEqual(caught.exception.code, "blocked_governance")
        self.assertEqual(sandbox["root"], root)

    def test_malformed_governance_block_fails_closed(self):
        with _Sandbox(mutate_metadata=lambda m: m.update({"governance": "direct"})) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root)
        # ND-ENG-006: malformed governance is now normalized to blocked_governance
        # (fail-closed intent preserved; no silent acceptance path remains).
        self.assertEqual(caught.exception.code, "blocked_governance")


class PublishAllBoundaryTests(unittest.TestCase):
    """6-7 at the orchestrator boundary, plus destination re-authorization."""

    def _run_publisher(self, box, *, mutate=None):
        with patch.object(publish_all, "ROOT", box.root), \
                patch.object(publish_all, "validate_content", return_value=""), \
                patch.object(publish_all, "platform_configured", return_value=(True, "")), \
                patch.object(publish_all, "send_status", return_value=True), \
                patch.dict(os.environ, {"PUBLISH_MODE": "publish",
                                        "AUTO_PUBLISH_APPROVED": "true"}), \
                patch.object(publish_all.subprocess, "run") as runner:
            if mutate:
                mutate()
            code = publish_all.run(scheduled_approved=False)
        return code, runner

    def test_publish_all_blocks_unknown_rights_before_any_upload(self):
        with _Sandbox(mutate_metadata=lambda m: m["evidence"].update(
                {"cutouts": [permitted_cutout(status="unknown")]})) as box:
            code, runner = self._run_publisher(box)
        self.assertEqual(code, 2)
        runner.assert_not_called()

    def test_publish_all_blocks_unsupported_claims_before_any_upload(self):
        with _Sandbox(mutate_metadata=lambda m: m["evidence"]["summary"].update(
                {"by_status": {"supported": 1, "unsupported": 3}})) as box:
            code, runner = self._run_publisher(box)
        self.assertEqual(code, 2)
        runner.assert_not_called()

    def test_publish_all_authorizes_each_destination(self):
        with _Sandbox() as box:
            with patch.object(publish_all, "ROOT", box.root), \
                    patch.object(publish_all, "validate_content", return_value=""), \
                    patch.object(publish_all, "platform_configured", return_value=(True, "")), \
                    patch.object(publish_all, "send_status", return_value=True), \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish",
                                            "AUTO_PUBLISH_APPROVED": "true"}), \
                    patch.object(publish_all, "authorize_publish",
                                 wraps=publish_authorization.authorize_publish) as spy, \
                    patch.object(publish_all.subprocess, "run",
                                 return_value=MagicMock(returncode=0, stdout="", stderr="")) as runner:
                code = publish_all.run(scheduled_approved=False)
        # YouTube private staging is authorized; the first inherently public
        # social destination is denied before its adapter can be invoked.
        self.assertEqual(code, 2)
        self.assertEqual(spy.call_count, 3)
        self.assertEqual(runner.call_count, 1)

    def test_drift_after_preflight_stops_remaining_destinations(self):
        with _Sandbox() as box:
            good = authorize_publish(platform="youtube", data_root=box.root)
            drifted = dict(good, metadata_sha256="f" * 64)
            calls = []

            def fake_run(*args, **kwargs):
                calls.append(args[0])
                return MagicMock(returncode=0, stdout="", stderr="")

            with patch.object(publish_all, "ROOT", box.root), \
                    patch.object(publish_all, "validate_content", return_value=""), \
                    patch.object(publish_all, "platform_configured", return_value=(True, "")), \
                    patch.object(publish_all, "send_status", return_value=True), \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish",
                                            "AUTO_PUBLISH_APPROVED": "true"}), \
                    patch.object(publish_all, "authorize_publish",
                                 side_effect=[good, good, drifted, good]), \
                    patch.object(publish_all.subprocess, "run", side_effect=fake_run):
                code = publish_all.run(scheduled_approved=False)
            self.assertEqual(code, 2)
            # preflight + youtube authorized and uploaded; facebook drifted and stopped the run
            self.assertEqual(len(calls), 1)

    def test_ambiguous_destination_result_is_reported_not_retried(self):
        with _Sandbox() as box:
            with patch.object(publish_all, "ROOT", box.root), \
                    patch.object(publish_all, "validate_content", return_value=""), \
                    patch.object(publish_all, "platform_configured", return_value=(True, "")), \
                    patch.object(publish_all, "send_status", return_value=True) as notify, \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish",
                                            "AUTO_PUBLISH_APPROVED": "true"}), \
                    patch.object(publish_all.subprocess, "run",
                                 return_value=MagicMock(returncode=3, stdout="", stderr="")) as runner, \
                    patch.object(publish_all, "authorize_publish",
                                 wraps=publish_authorization.authorize_publish) as auth_spy:
                code = publish_all.run(scheduled_approved=False)
            self.assertEqual(code, 3)
            self.assertEqual(runner.call_count, 1)
            self.assertEqual(auth_spy.call_count, 2)
            message = " ".join(call.args[0] for call in notify.call_args_list)
            self.assertIn("ambiguous", message)
            self.assertIn("not atomic", message)


class LongformDestinationTests(unittest.TestCase):
    """Long-form remains private; non-private destinations are policy-blocked."""

    def _upload(self, box, argv):
        service = MagicMock()
        service.videos.return_value.insert.return_value.next_chunk.return_value = (None, {"id": "lf1"})
        with patch.object(longform, "ROOT", box.root), \
                patch.object(longform, "get_authenticated_service", return_value=service), \
                patch.object(longform, "MediaFileUpload", return_value="media"), \
                patch.object(longform, "send_status", return_value=True), \
                patch.dict(os.environ, {"PUBLISH_MODE": "publish",
                                        "AUTO_PUBLISH_APPROVED": "true"}):
            code = longform.main(argv)
        return code, service

    def test_longform_defaults_to_private(self):
        with _Sandbox(purpose="longform") as box:
            code, service = self._upload(box, [])
        self.assertEqual(code, 0)
        body = service.videos.return_value.insert.call_args.kwargs["body"]
        self.assertEqual(body["status"]["privacyStatus"], "private")

    def test_longform_public_without_owner_release_is_blocked(self):
        with _Sandbox(purpose="longform") as box:
            code, service = self._upload(box, ["--destination", "public"])
        self.assertEqual(code, 2)
        service.videos.return_value.insert.assert_not_called()

    def test_longform_public_with_owner_release_remains_blocked(self):
        with _Sandbox(purpose="longform", public_release=True) as box:
            code, service = self._upload(box, ["--destination", "public"])
        self.assertEqual(code, 2)
        service.videos.return_value.insert.assert_not_called()

    def test_longform_stale_owner_release_is_blocked(self):
        with _Sandbox(purpose="longform", public_release=True) as box:
            record = json.loads(box.paths["public_release"].read_text(encoding="utf-8"))
            record["approved_at"] = "2026-01-01T09:00:00+05:30"
            box.paths["public_release"].write_text(json.dumps(record), encoding="utf-8")
            code, service = self._upload(box, ["--destination", "public"])
        self.assertEqual(code, 2)
        service.videos.return_value.insert.assert_not_called()

    def test_longform_scheduling_flag_alone_is_not_authorization(self):
        """--scheduled-approved alone without owner release must not authorize."""
        service = MagicMock()
        service.videos.return_value.insert.return_value.next_chunk.return_value = (None, {"id": "lf1"})
        with _Sandbox(purpose="longform") as box:
            # No PUBLISH_MODE=publish or AUTO_PUBLISH_APPROVED=true
            with patch.object(longform, "ROOT", box.root), \
                    patch.object(longform, "get_authenticated_service", return_value=service), \
                    patch.object(longform, "MediaFileUpload", return_value="media"), \
                    patch.object(longform, "send_status", return_value=True):
                code = longform.main(["--scheduled-approved"])
        self.assertEqual(code, 2)
        service.videos.return_value.insert.assert_not_called()

    def test_longform_owner_release_without_scheduled_flag_authorizes_private(self):
        """Owner release alone (no --scheduled-approved) authorizes private staging."""
        service = MagicMock()
        service.videos.return_value.insert.return_value.next_chunk.return_value = (None, {"id": "lf1"})
        with _Sandbox(purpose="longform") as box:
            with patch.object(longform, "ROOT", box.root), \
                    patch.object(longform, "get_authenticated_service", return_value=service), \
                    patch.object(longform, "MediaFileUpload", return_value="media"), \
                    patch.object(longform, "send_status", return_value=True), \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                code = longform.main([])
        self.assertEqual(code, 0)
        body = service.videos.return_value.insert.call_args.kwargs["body"]
        self.assertEqual(body["status"]["privacyStatus"], "private")

    def test_longform_owner_release_missing_false_expired_hash_mismatch_blocked(self):
        """Missing, false, expired, or hash-mismatched owner release blocks."""
        service = MagicMock()
        service.videos.return_value.insert.return_value.next_chunk.return_value = (None, {"id": "lf1"})
        with _Sandbox(purpose="longform", public_release=True) as box:
            # Case 1: Missing owner release file
            box.paths["public_release"].unlink(missing_ok=True)
            with patch.object(longform, "ROOT", box.root), \
                    patch.object(longform, "get_authenticated_service", return_value=service), \
                    patch.object(longform, "MediaFileUpload", return_value="media"), \
                    patch.object(longform, "send_status", return_value=True), \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                code = longform.main(["--destination", "public"])
            self.assertEqual(code, 2)
            service.videos.return_value.insert.assert_not_called()

        # Case 2: False owner release status
        with _Sandbox(purpose="longform", public_release=True) as box:
            record = json.loads(box.paths["public_release"].read_text(encoding="utf-8"))
            record["status"] = "rejected"
            box.paths["public_release"].write_text(json.dumps(record), encoding="utf-8")
            with patch.object(longform, "ROOT", box.root), \
                    patch.object(longform, "get_authenticated_service", return_value=service), \
                    patch.object(longform, "MediaFileUpload", return_value="media"), \
                    patch.object(longform, "send_status", return_value=True), \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                code = longform.main(["--destination", "public"])
            self.assertEqual(code, 2)
            service.videos.return_value.insert.assert_not_called()

        # Case 3: Expired owner release
        with _Sandbox(purpose="longform", public_release=True) as box:
            record = json.loads(box.paths["public_release"].read_text(encoding="utf-8"))
            record["approved_at"] = "2026-01-01T09:00:00+05:30"
            box.paths["public_release"].write_text(json.dumps(record), encoding="utf-8")
            with patch.object(longform, "ROOT", box.root), \
                    patch.object(longform, "get_authenticated_service", return_value=service), \
                    patch.object(longform, "MediaFileUpload", return_value="media"), \
                    patch.object(longform, "send_status", return_value=True), \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                code = longform.main(["--destination", "public"])
            self.assertEqual(code, 2)
            service.videos.return_value.insert.assert_not_called()

        # Case 4: Hash-mismatched owner release
        with _Sandbox(purpose="longform", public_release=True) as box:
            record = json.loads(box.paths["public_release"].read_text(encoding="utf-8"))
            record["metadata_sha256"] = "f" * 64
            box.paths["public_release"].write_text(json.dumps(record), encoding="utf-8")
            with patch.object(longform, "ROOT", box.root), \
                    patch.object(longform, "get_authenticated_service", return_value=service), \
                    patch.object(longform, "MediaFileUpload", return_value="media"), \
                    patch.object(longform, "send_status", return_value=True), \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish", "AUTO_PUBLISH_APPROVED": "true"}):
                code = longform.main(["--destination", "public"])
            self.assertEqual(code, 2)
            service.videos.return_value.insert.assert_not_called()


class DryRunSideEffectTests(unittest.TestCase):
    """13: a dry run validates governance but touches nothing external."""

    def test_youtube_cli_dry_run_uploads_nothing_and_writes_no_ledger(self):
        with _Sandbox() as box:
            ledger_file = box.root / "data" / "uploaded_content.json"
            service = MagicMock()
            with patch.object(yt, "SCRIPT_DIR", box.root), \
                    patch.object(yt, "get_authenticated_service", return_value=service), \
                    patch.object(yt, "MediaFileUpload") as media:
                code = yt.main(["--dry-run"])
            self.assertEqual(code, 0)
            media.assert_not_called()
            service.videos.return_value.insert.assert_not_called()
            self.assertFalse(ledger_file.exists())

    def test_youtube_cli_dry_run_still_requires_approval(self):
        with _Sandbox() as box:
            box.paths["approval"].unlink()
            with patch.object(yt, "SCRIPT_DIR", box.root), \
                    patch.object(yt, "get_authenticated_service") as service, \
                    patch.object(yt, "MediaFileUpload"):
                code = yt.main(["--dry-run"])
            self.assertEqual(code, 2)
            service.assert_not_called()


class ApiAuthenticationTests(unittest.TestCase):
    """11-12: protected routes fail closed, and malformed payloads are rejected."""

    def setUp(self):
        from fastapi.testclient import TestClient

        from api import main as api_main

        self.api = api_main
        self.client = TestClient(api_main.app)
        self.headers = {"Authorization": "Bearer test-key"}

    def test_unconfigured_server_key_closes_the_api(self):
        with patch.dict(os.environ, {"SHORTS_STUDIO_API_KEY": ""}, clear=False):
            for response in (self.client.get("/jobs"),
                             self.client.get("/status/abc"),
                             self.client.post("/start", json={})):
                self.assertEqual(response.status_code, 503)

    def test_missing_or_invalid_bearer_header_is_rejected(self):
        with patch.dict(os.environ, {"SHORTS_STUDIO_API_KEY": "test-key"}, clear=False):
            self.assertEqual(self.client.get("/jobs").status_code, 401)
            self.assertEqual(self.client.get("/jobs", headers={"Authorization": "test-key"}).status_code, 401)
            self.assertEqual(self.client.get("/jobs", headers={"Authorization": "Bearer "}).status_code, 401)
            self.assertEqual(self.client.get(
                "/jobs", headers={"Authorization": "Bearer wrong-key"}).status_code, 401)
            self.assertEqual(self.client.get("/status/abc", headers={"Authorization": "Bearer wrong"}).status_code, 401)

    def test_authenticated_requests_are_served(self):
        with patch.dict(os.environ, {"SHORTS_STUDIO_API_KEY": "test-key"}, clear=False):
            self.assertEqual(self.client.get("/jobs", headers=self.headers).status_code, 200)
            self.assertEqual(self.client.get("/status/nope", headers=self.headers).status_code, 200)

    def test_health_stays_open_for_probes(self):
        with patch.dict(os.environ, {"SHORTS_STUDIO_API_KEY": ""}, clear=False):
            self.assertEqual(self.client.get("/health").status_code, 200)

    def test_malformed_start_payloads_are_rejected(self):
        bad_payloads = [
            ([], "JSON object", (400, 422)),
            ({"dry_run": "yes"}, "boolean", (400,)),
            ({"topic": 12}, "string", (400,)),
            ({"quality": ["strong"]}, "string", (400,)),
            ({"publish_now": True}, "unknown", (400,)),
            ({"topic": "x" * 400}, "characters", (400,)),
        ]
        with patch.dict(os.environ, {"SHORTS_STUDIO_API_KEY": "test-key"}, clear=False), \
                patch.object(self.api, "run_job", lambda *args, **kwargs: None), \
                patch.object(self.api.threading, "Thread") as thread:
            for payload, needle, codes in bad_payloads:
                response = self.client.post("/start", json=payload, headers=self.headers)
                self.assertIn(response.status_code, codes, payload)
                if codes == (400,):
                    self.assertIn(needle, response.json()["detail"])
            thread.start.assert_not_called()

    def test_start_still_refuses_non_strong_quality(self):
        with patch.dict(os.environ, {"SHORTS_STUDIO_API_KEY": "test-key"}, clear=False), \
                patch.object(self.api, "run_job", lambda *args, **kwargs: None), \
                patch.object(self.api.threading, "Thread"):
            response = self.client.post("/start", json={"quality": "standard"},
                                        headers=self.headers)
        self.assertEqual(response.status_code, 400)

    def test_valid_dry_run_start_is_accepted(self):
        with patch.dict(os.environ, {"SHORTS_STUDIO_API_KEY": "test-key"}, clear=False), \
                patch.object(self.api, "run_job", lambda *args, **kwargs: None), \
                patch.object(self.api.threading, "Thread") as thread, \
                patch.object(self.api, "jobs", {}):
            response = self.client.post("/start", json={"dry_run": True, "topic": "AI grids"},
                                        headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("job_id", response.json())


class AuthorizationProbeTests(unittest.TestCase):
    """The narrow approval-binding probe stays separate from full governance."""

    def test_probe_reports_only_approval_binding_state(self):
        with _Sandbox() as box:
            with patch.object(publish_authorization, "ROOT", box.root):
                self.assertEqual(publish_authorization.verify_approval_binding(data_root=box.root), "")
                box.paths["video"].write_bytes(b"changed-after-approval")
                reason = publish_authorization.verify_approval_binding(data_root=box.root)
        self.assertIn("does not match", reason)

    def test_probe_does_not_apply_evidence_or_rights_policy(self):
        metadata = publishable_metadata()
        metadata["evidence"]["summary"]["by_status"] = {"supported": 1, "unsupported": 4}
        with _Sandbox(metadata=metadata) as box:
            self.assertEqual(publish_authorization.verify_approval_binding(data_root=box.root), "")
            with self.assertRaises(PublishNotAuthorized):
                authorize_publish(platform="youtube", data_root=box.root)

    def test_publish_all_probe_delegates_to_the_shared_binding(self):
        with _Sandbox() as box:
            with patch.object(publish_all, "ROOT", box.root):
                self.assertEqual(publish_all.approval_matches_current_content(), "")
                box.paths["video"].write_bytes(b"changed-after-approval")
                self.assertIn("does not match", publish_all.approval_matches_current_content())


if __name__ == "__main__":
    unittest.main()


class DirectEntryDownstreamRegressionTests(unittest.TestCase):
    def test_direct_pipeline_artifact_is_blocked_by_publish_all(self):
        from app.script import pipeline

        fake = publishable_metadata()
        fake.update({
            "video_path": "outputs/output_short.mp4",
            "duration_seconds": 42.0,
            "word_count": 110,
            "research": {"claims": [{"claim_id": "clm_0001"}]},
        })
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "direct_metadata.json"
            with patch.object(pipeline, "ROOT", root), \
                    patch.object(pipeline, "run", return_value=dict(fake)):
                code = pipeline.main(["--topic", "AI grids", "--out", str(output)])
            self.assertEqual(code, 0)
            direct_metadata = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(direct_metadata["governance"]["publishable"])

            build_sandbox(root, metadata=direct_metadata, video_bytes=LARGE_VIDEO)
            with patch.object(publish_all, "ROOT", root), \
                    patch.object(publish_all, "validate_content", return_value=""), \
                    patch.object(publish_all, "platform_configured", return_value=(True, "")), \
                    patch.object(publish_all, "send_status", return_value=True), \
                    patch.dict(os.environ, {"PUBLISH_MODE": "publish",
                                            "AUTO_PUBLISH_APPROVED": "true"}), \
                    patch.object(publish_all.subprocess, "run") as runner:
                result = publish_all.run(scheduled_approved=False)

            self.assertEqual(result, 2)
            runner.assert_not_called()


class PublicPublishingPolicyBoundaryTests(unittest.TestCase):
    """Public distribution remains denied until a separate owner policy exists."""

    def test_fabricated_owner_release_cannot_enable_youtube_public(self):
        with _Sandbox(purpose="longform", public_release=True) as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube_longform", purpose="longform",
                                  data_root=box.root, destination="public")
        self.assertEqual(caught.exception.code, "blocked_public_policy")

    def test_youtube_unlisted_destination_is_blocked(self):
        with _Sandbox() as box:
            with self.assertRaises(PublishNotAuthorized) as caught:
                authorize_publish(platform="youtube", data_root=box.root,
                                  destination="unlisted")
        self.assertEqual(caught.exception.code, "blocked_public_policy")

    def test_inherently_public_and_unknown_platforms_are_blocked(self):
        for platform in ("facebook", "instagram", "tiktok", "threads", "unknown-platform"):
            with self.subTest(platform=platform), _Sandbox() as box:
                with self.assertRaises(PublishNotAuthorized) as caught:
                    authorize_publish(platform=platform, data_root=box.root)
                self.assertEqual(caught.exception.code, "blocked_public_policy")

    def test_private_youtube_staging_remains_authorized(self):
        with _Sandbox() as box:
            decision = authorize_publish(platform="youtube", data_root=box.root)
        self.assertEqual(decision["status"], "authorized")
        self.assertEqual(decision["destination"], "private")
        self.assertIsNone(decision["public_release"])

    def test_instagram_and_facebook_direct_adapters_block_before_network(self):
        with _Sandbox() as box:
            with patch.object(ig, "ROOT", box.root), \
                    patch.object(ig, "METADATA", box.paths["metadata"]), \
                    patch.object(ig, "VIDEO", box.paths["video"]), \
                    patch.dict(os.environ, META_ENV), \
                    patch.object(ig.requests, "post") as ig_post:
                with self.assertRaises(PublishNotAuthorized) as instagram:
                    ig.publish()
            self.assertEqual(instagram.exception.code, "blocked_public_policy")
            ig_post.assert_not_called()

            with patch.object(fb, "ROOT", box.root), \
                    patch.object(fb, "METADATA", box.paths["metadata"]), \
                    patch.object(fb, "VIDEO", box.paths["video"]), \
                    patch.dict(os.environ, META_ENV), \
                    patch.object(fb.requests, "post") as fb_post:
                with self.assertRaises(PublishNotAuthorized) as facebook:
                    fb.publish()
            self.assertEqual(facebook.exception.code, "blocked_public_policy")
            fb_post.assert_not_called()
