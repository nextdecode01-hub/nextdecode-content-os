import contextlib
import io
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

from app.visuals import beats, chain, vision_review, storyboard


def shot(index, caption, visual=None, duration=2.8):
    return {
        "index": index,
        "duration": duration,
        "caption": caption,
        "visual": visual or caption,
        "asset_query": caption,
        "asset_query_variants": [],
    }


class ClassificationTests(unittest.TestCase):
    def test_numbers_and_claims_become_motion_graphics(self):
        self.assertEqual(chain.classify_scene(shot(0, "AI data centers used 415 TWh"))["visual_type"], "motion_graphic")
        self.assertEqual(chain.classify_scene(shot(1, "The report says demand doubled"))["visual_type"], "motion_graphic")

    def test_moe_token_arrival_intro_can_use_an_original_diagram(self):
        result = chain.classify_scene({
            "text": "What does a mixture-of-experts model do when a token arrives?",
            "asset_query": "mixture of experts expert modules diagram",
        })
        self.assertEqual(result["scene_type"], "diagram")
        self.assertEqual(result["visual_type"], "motion_graphic")

    def test_token_by_token_moe_beat_can_use_a_diagram(self):
        result = chain.classify_scene({
            "text": "For Mixtral, the choice is made for each token, not once for the whole prompt.",
            "caption": "Token-by-token selection",
            "asset_query": "mixture of experts token routing diagram",
        })
        self.assertEqual(result["scene_type"], "diagram")
        self.assertEqual(result["visual_type"], "motion_graphic")

    def test_scene_brief_uses_narration_text_and_specific_moe_footage_purpose(self):
        brief = chain.build_scene_brief({
            "index": 0,
            "text": "Mixtral is Mistral's sparse mixture-of-experts model, with open weights.",
            "asset_query": "sparse expert network router flowchart",
            "duration": 3.5,
        })
        self.assertEqual(brief["scene_type"], "footage")
        self.assertIn("GPU server hardware", brief["visual_purpose"])
        self.assertEqual(brief["fallback_chain"][0], "wikimedia")

    def test_specialist_network_beat_can_use_an_original_moe_diagram(self):
        result = chain.classify_scene({
            "claim": "Think of the experts as specialist networks inside one model.",
            "caption": "Specialist networks inside one model",
            "asset_query": "mixture of experts expert modules diagram",
            "topic": "How mixture-of-experts models route tokens",
        })
        self.assertEqual(result["scene_type"], "diagram")
        self.assertEqual(result["visual_type"], "motion_graphic")

    def test_moe_topic_query_does_not_turn_non_routing_beats_into_diagrams(self):
        generic_query = "mixture of experts token routing diagram"
        intro = chain.classify_scene({
            "claim": "Mixtral is Mistral's sparse mixture-of-experts model, with open weights.",
            "caption": "Mixtral sparse model",
            "asset_query": generic_query,
            "topic": "How AI Models Activate a Few Experts to Save Compute",
        })
        mechanism = chain.classify_scene({
            "claim": "A router selects two experts for each token at every layer.",
            "caption": "The router chooses",
            "asset_query": generic_query,
            "topic": "How AI Models Activate a Few Experts to Save Compute",
        })
        self.assertEqual(intro["visual_type"], "broll")
        self.assertEqual(intro["scene_type"], "footage")
        self.assertEqual(mechanism["visual_type"], "motion_graphic")
        self.assertEqual(mechanism["scene_type"], "diagram")

    def test_ambient_text_becomes_broll(self):
        self.assertEqual(chain.classify_scene(shot(0, "Rows of servers humming in a dark hall"))["visual_type"], "broll")

    def test_spelled_quantities_count_as_numbers_for_graphics(self):
        self.assertEqual(chain.classify_scene(shot(0, "Training used over fifty gigawatt-hours of power"))["visual_type"], "motion_graphic")
        self.assertEqual(chain.classify_scene(shot(1, "That equals nearly zero point one percent of city use"))["visual_type"], "motion_graphic")
        self.assertEqual(chain._first_number("That equals nearly zero point one percent"), "0.1%")
        self.assertEqual(chain._first_number("That is nearly point one percent"), "0.1%")
        self.assertEqual(chain._first_number("That is nearly point five percent"), "0.5%")
        self.assertEqual(chain._first_number("Training used over fifty gigawatt-hours"), "50 GWh")

    def test_model_names_do_not_supply_the_card_number(self):
        self.assertEqual(chain._first_number("GPT-4 is a large model"), "")
        self.assertEqual(chain._first_number("H100 chips run hot"), "")
        self.assertEqual(chain.classify_scene(shot(0, "GPT-4 is a large model"))["visual_type"], "broll")

    def test_years_and_n_plus_one_are_not_statistics(self):
        self.assertEqual(
            chain._first_number("your pull request might miss an N+1 query"), ""
        )
        self.assertEqual(
            chain._first_number("an N plus 1 query performance problem"), ""
        )
        self.assertEqual(chain._first_number("A 2010 study found complacency"), "")
        self.assertEqual(chain._first_number("a June 2026 guide on productivity"), "")
        self.assertEqual(
            chain._first_number("In 2026, 40% of teams changed review"), "40%"
        )

    def test_claim_field_drives_classification_over_shot_hint(self):
        scene = chain.classify_scene({
            "index": 0,
            "claim": "Global data centers used 415 TWh in 2024",
            "caption": "data visualization chart illustrating...",
            "asset_query": "data centers",
        })
        self.assertEqual(scene["visual_type"], "motion_graphic")
        self.assertEqual(scene["keyword"], "data centers")

    def test_keyword_is_short_english_without_filler(self):
        scene = chain.classify_scene({
            "index": 0,
            "caption": "servers humming",
            "visual": "data center server room illustrating the point of this line - alternate angle",
            "asset_query": "data center server room illustrating the point of this line - alternate angle",
        })
        self.assertEqual(scene["keyword"], "data center server")

    def test_stock_cap_is_below_half_of_the_video(self):
        shots = [shot(i, f"ambient shot {chr(97 + i)}") for i in range(6)]
        planner = chain.plan_scenes(shots)
        self.assertEqual(planner["total"], 6)
        self.assertEqual(planner["stock_cap"], 2)
        self.assertLess(planner["stock_cap"], planner["total"] / 2)


class PlanVarietyTests(unittest.TestCase):
    def test_cards_do_not_dominate_the_video(self):
        shots = [shot(i, f"Demand grew {10 + i} percent in 2024") for i in range(8)]
        planner = chain.plan_scenes(shots)
        kinds = [planner["scenes"][i]["visual_type"] for i in range(8)]

        self.assertEqual(kinds[0], "motion_graphic")
        self.assertLessEqual(kinds.count("motion_graphic"), len(shots) // 2)
        self.assertIn("broll", kinds)
        for start in range(len(kinds) - chain.MAX_CONSECUTIVE_GRAPHICS):
            window = kinds[start:start + chain.MAX_CONSECUTIVE_GRAPHICS + 1]
            self.assertNotEqual(set(window), {"motion_graphic"})

    def test_duplicate_card_text_becomes_recap_not_broll(self):
        shots = [
            shot(0, "Stack Overflow reports 52% productivity gains"),
            shot(1, "Developers still report 52% productivity gains"),
            shot(2, "A second survey found 70% faster reviews"),
            shot(3, "Rows of servers humming in a dark hall"),
        ]
        planner = chain.plan_scenes(shots)
        self.assertEqual(planner["scenes"][0]["visual_type"], "motion_graphic")
        recap = planner["scenes"][1]
        self.assertEqual(recap["visual_type"], "motion_graphic")
        self.assertEqual(recap["card_variant"], "recap")
        self.assertIn("narration-derived recap", recap.get("variety_note", ""))
        self.assertEqual(recap["fallback_chain"], chain.GRAPHIC_FALLBACK_CHAIN)
        self.assertEqual(recap["recap_figures"][0]["number"], "52%")
        self.assertNotIn("pixabay_video", recap["fallback_chain"])

    def test_recap_figures_come_only_from_narration(self):
        shots = [
            shot(0, "Review cycles fell 30% after AI suggestions"),
            shot(1, "Review cycles fell 30% after AI suggestions"),
            shot(2, "Security catches rose 54% in the same study"),
            shot(3, "Security catches rose 54% in the same study"),
        ]
        planner = chain.plan_scenes(shots)
        numbers = {
            figure["number"]
            for index in (1, 3)
            for figure in planner["scenes"][index].get("recap_figures", [])
        }
        self.assertTrue(numbers)
        self.assertTrue(numbers <= {"30%", "54%"})

    def test_cards_and_recaps_never_run_three_in_a_row(self):
        texts = []
        for number in (12, 34, 56, 78):
            texts.extend([
                f"Study one reports {number}% faster reviews",
                f"Study two reports {number}% faster reviews",
            ])
        shots = [shot(i, text) for i, text in enumerate(texts)]
        planner = chain.plan_scenes(shots)
        kinds = [planner["scenes"][i]["visual_type"] for i in range(len(shots))]
        for start in range(len(kinds) - 2):
            self.assertNotEqual(
                kinds[start:start + 3], ["motion_graphic"] * 3,
                f"three full-screen graphics in a row at {start}: {kinds}",
            )
        self.assertLessEqual(kinds.count("motion_graphic"), len(shots) // 2)

    def test_downgraded_card_uses_the_broll_chain_and_stock(self):
        shots = [shot(i, f"Demand grew {10 + i} percent in 2024") for i in range(4)]
        planner = chain.plan_scenes(shots)
        downgraded = [
            planner["scenes"][i] for i in range(4)
            if planner["scenes"][i].get("variety_note")
        ]

        self.assertTrue(downgraded)
        for brief in downgraded:
            self.assertEqual(brief["visual_type"], "broll")
            self.assertEqual(brief["scene_type"], "footage")
            self.assertTrue(brief["allow_stock"])
            self.assertIn("pixabay_video", brief["fallback_chain"])


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_generated_video_is_registered_only_with_valid_sidecar_and_hash(self):
        import hashlib
        import json
        import shutil
        import subprocess

        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("ffmpeg/ffprobe unavailable")
        from app.visuals import motion_director
        from app.visuals.shotplan import plan_shot_plan, annotate_shots

        video_dir = self.dir / "clips"
        video_dir.mkdir()
        media = video_dir / "server-room.mp4"
        subprocess.run([
            shutil.which("ffmpeg"), "-v", "error", "-f", "lavfi",
            "-i", "color=c=navy:s=360x640:d=2:r=30", "-an",
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-y", str(media),
        ], check=True, capture_output=True, timeout=30)
        digest = hashlib.sha256(media.read_bytes()).hexdigest()
        from app.providers.video_generation_workflow import _probe_video
        metadata = _probe_video(media)
        record = {
            "schema": "nextdecode.generated-video-asset.v1",
            "run_id": "local-acceptance",
            "provider": "kling", "model": "fixture-model", "task_id": "fixture-task",
            "prompt": "A vertical server room fixture", "local_path": str(media.resolve()),
            "sha256": digest, "status": "qualified", "metadata": metadata,
            "requires_editorial_review": True,
        }
        sidecar = media.with_suffix(media.suffix + ".asset.json")
        sidecar.write_text(json.dumps(record), encoding="utf-8")
        source = {
            "topic": "AI infrastructure",
            "voice_text": "Rows of servers power the model.",
            "shots": [{
                "claim": "Rows of servers power the model.",
                "caption": "Rows of servers power the model.",
                "asset_query": "server room",
                "generated_video_asset": str(sidecar),
            }],
        }
        shots = motion_director.plan_shots(source, audio_duration=5.0)
        plan = plan_shot_plan(source, audio_duration=5.0)
        shots = annotate_shots(shots, plan)
        planner = chain.plan_scenes(shots)
        detail = chain.resolve_scene(shots[0], self.dir, planner, dry_run=True)
        self.assertEqual(detail["provider"], "generated_video")
        self.assertEqual(Path(detail["path"]).resolve(), media.resolve())
        self.assertEqual(detail["generated_provenance"]["sha256"], digest)
        self.assertTrue(detail["generated_provenance"]["requires_editorial_review"])

    def test_tampered_generated_video_is_rejected_and_uses_local_fallback(self):
        import hashlib
        import json
        import shutil
        import subprocess

        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("ffmpeg/ffprobe unavailable")
        media = self.dir / "tampered.mp4"
        subprocess.run([
            shutil.which("ffmpeg"), "-v", "error", "-f", "lavfi",
            "-i", "color=c=navy:s=360x640:d=2:r=30", "-an",
            "-pix_fmt", "yuv420p", "-c:v", "libx264", "-y", str(media),
        ], check=True, capture_output=True, timeout=30)
        from app.providers.video_generation_workflow import _probe_video
        record = {
            "schema": "nextdecode.generated-video-asset.v1", "run_id": "local-acceptance",
            "provider": "kling", "model": "fixture-model", "task_id": "fixture-task",
            "prompt": "fixture", "local_path": str(media.resolve()),
            "sha256": hashlib.sha256(media.read_bytes()).hexdigest(),
            "status": "qualified", "metadata": _probe_video(media),
            "requires_editorial_review": True,
        }
        sidecar = media.with_suffix(media.suffix + ".asset.json")
        sidecar.write_text(json.dumps(record), encoding="utf-8")
        media.write_bytes(media.read_bytes() + b"tampered")
        shot = {
            "index": 0, "duration": 2.0, "claim": "A server room powers the model",
            "caption": "A server room powers the model", "visual": "server room",
            "generated_video_asset": str(sidecar),
        }
        planner = chain.plan_scenes([shot])
        detail = chain.resolve_scene(shot, self.dir, planner, dry_run=True)
        self.assertNotEqual(detail["provider"], "generated_video")
        self.assertNotEqual(detail.get("provider"), "generated_video_rejected")
        self.assertTrue(detail.get("path"))
        self.assertTrue(Path(detail["path"]).is_file())

    def test_motion_graphic_uses_local_card_without_network(self):
        shots = [shot(0, "AI data centers used 415 TWh")]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_pixabay_asset", side_effect=AssertionError("no stock for graphics")), patch.object(
            chain, "_wikimedia_asset", side_effect=AssertionError("no stills for graphics")
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)
        self.assertEqual(detail["provider"], "motion_graphic")
        self.assertTrue(Path(detail["path"]).is_file())

    def test_recap_scene_renders_local_recap_card_without_stock(self):
        shots = [
            shot(0, "AI review cuts cycle time by 52%"),
            shot(1, "A follow-up survey found 70% faster reviews"),
            shot(2, "Rows of servers humming in a dark hall"),
            shot(3, "Teams still report 52% faster review cycles"),
            shot(4, "Developers compare notes before shipping"),
            shot(5, "Managers review the rollout plan"),
            shot(6, "Engineers test one final build"),
        ]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_pixabay_asset", side_effect=AssertionError("no stock for recaps")), patch.object(
            chain, "_wikimedia_asset", side_effect=AssertionError("no stills for recaps")
        ):
            detail = chain.resolve_scene(shots[3], self.dir, planner)
        self.assertEqual(detail["provider"], "motion_graphic")
        self.assertEqual(detail["card_variant"], "recap")
        self.assertIn("recap_003", Path(detail["path"]).name)
        self.assertTrue(Path(detail["path"]).is_file())

    def test_generic_wikimedia_title_is_rejected(self):
        with patch(
            "app.visuals.stock_fetcher.fetch_shot_image",
            return_value={
                "path": str(self.dir / "x.jpg"),
                "title": "Performance Measurement - Grassroots Development Programme",
            },
        ):
            result = chain._wikimedia_asset(
                shot(0, "software development performance"),
                "software development performance",
                self.dir, 0, set(),
            )
        self.assertIsNone(result)

    def test_moe_neural_network_still_passes_exact_phrase_match(self):
        with patch(
            "app.visuals.stock_fetcher.fetch_shot_image",
            return_value={
                "path": str(self.dir / "x.jpg"),
                "title": "File:Message Passing Neural Network.png",
                "query": "neural network",
            },
        ), patch.object(chain, "_visual_quality", return_value=("ok", {})):
            result = chain._wikimedia_asset(
                shot(0, "specialist networks inside a model"),
                "mixture experts expert", self.dir, 0, set(),
                extra_queries=["neural network"],
            )
        self.assertIsNotNone(result)
        self.assertEqual(result["query"], "neural network")

    def test_specific_wikimedia_title_is_kept(self):
        with patch(
            "app.visuals.stock_fetcher.fetch_shot_image",
            return_value={
                "path": str(self.dir / "x.jpg"),
                "title": "File:Cursor AI Coding Agent.png",
            },
        ), patch.object(chain, "_visual_quality", return_value=("ok", {})):
            result = chain._wikimedia_asset(
                shot(0, "coding agents"), "coding agents", self.dir, 0, set(),
            )
        self.assertIsNotNone(result)
        self.assertEqual(result["provider"], "wikimedia")
        self.assertEqual(result["relevance"], "title_query_match")

    def test_low_light_stock_is_skipped_for_the_next_candidate(self):
        shots = [{
            "index": 0, "duration": 3.0,
            "caption": "Rows of servers humming",
            "visual": "rows of servers humming",
            "asset_query": "coding agents",
            "asset_query_variants": ["coding agents", "programmer desk"],
        }] + [shot(i, f"ambient scene {i}") for i in range(1, 4)]
        planner = chain.plan_scenes(shots)
        dark = {"path": str(self.dir / "dark.mp4"), "provider": "pixabay",
                "title": "", "visual_quality": "low_light"}
        good = {"path": str(self.dir / "good.mp4"), "provider": "pixabay",
                "title": "", "visual_quality": "ok"}
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", side_effect=[dark, good]
        ), patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            chain, "_ai_configured", return_value=False
        ), patch.object(vision_review, "enabled", return_value=False), patch.object(
            vision_review, "review_asset", return_value={"checked": False, "status": "disabled", "attempts": 0, "reason": "vision review disabled"}
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)
        self.assertEqual(detail["provider"], "pixabay")
        self.assertEqual(detail["query"], "programmer desk")

    def test_low_light_stock_falls_back_to_a_card_instead_of_dark_footage(self):
        shots = [{
            "index": 0, "duration": 3.0,
            "caption": "Rows of servers humming",
            "visual": "rows of servers humming",
            "asset_query": "coding agents",
            "asset_query_variants": ["coding agents"],
        }] + [shot(i, f"ambient scene {i}") for i in range(1, 4)]
        planner = chain.plan_scenes(shots)
        dark = {"path": str(self.dir / "dark.mp4"), "provider": "pixabay",
                "title": "", "visual_quality": "low_light"}
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=dark
        ), patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            chain, "_ai_configured", return_value=False
        ), patch.object(chain, "_local_component_asset", return_value=None), patch.object(
            chain, "_gradient_caption", return_value=self.dir / "g.mp4"
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)
        self.assertEqual(detail["provider"], "gradient")
        self.assertIn("low-light", detail["fallback_reason"])

    def test_broll_prefers_stock_then_tracks_the_cap(self):
        shots = [shot(i, "rows of servers humming") for i in range(4)]
        planner = chain.plan_scenes(shots)
        self.assertEqual(planner["stock_cap"], 1)
        # lexical-medium stock assets are fine while vision review is disabled
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value={"path": "/tmp/x.mp4", "provider": "pixabay", "title": ""}
        ) as pixabay, patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            vision_review, "enabled", return_value=False
        ), patch.object(
            vision_review, "review_asset", return_value={"checked": False, "status": "disabled", "attempts": 0, "reason": "vision review disabled"}
        ):
            first = chain.resolve_scene(shots[0], self.dir, planner)
            second = chain.resolve_scene(shots[1], self.dir, planner)

        self.assertEqual(first["provider"], "pixabay")
        self.assertEqual(planner["stock_used"], 1)
        # after the cap the stock chain is skipped; the local original graphic wins
        self.assertEqual(second["provider"], "motion_graphic")
        self.assertEqual(pixabay.call_count, 1)

    def test_wikimedia_assets_record_a_stable_id_and_honest_relevance(self):
        asset = {"path": str(self.dir / "photo.jpg"), "title": "File:Data center.jpg", "license": "CC0"}
        with patch("app.visuals.stock_fetcher.fetch_shot_image", return_value=asset):
            detail = chain._wikimedia_asset(
                {"index": 0, "asset_query": "data center"}, "data center", self.dir, 0, set(),
            )

        self.assertEqual(detail["asset_id"], "wikimedia:File:Data center.jpg")
        self.assertEqual(detail["relevance"], "title_query_match")

    def test_dry_run_skips_every_network_provider(self):
        shots = [shot(0, "rows of servers humming")]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_pixabay_asset", side_effect=AssertionError("no network in dry run")), patch.object(
            chain, "_wikimedia_asset", side_effect=AssertionError("no network in dry run")
        ), patch.object(chain, "_ai_asset", side_effect=AssertionError("no network in dry run")):
            detail = chain.resolve_scene(shots[0], self.dir, planner, dry_run=True)
        # the local original vector component is preferred over a caption slide by design
        self.assertEqual(detail["provider"], "motion_graphic")

    def test_successful_lower_tier_provider_keeps_the_attempt_trail(self):
        shots = [shot(i, "rows of servers humming") for i in range(4)]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=None
        ), patch.object(
            chain, "_wikimedia_asset", return_value={"path": "/tmp/still.jpg", "provider": "wikimedia",
                                                     "title": "File:Data center servers rows.jpg",
                                                     "tags": "data center servers"}
        ), patch.object(chain, "_ai_configured", return_value=False), patch.object(
            vision_review, "enabled", return_value=False
        ), patch.object(
            vision_review, "review_asset", return_value={"checked": False, "status": "disabled", "attempts": 0, "reason": "vision review disabled"}
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)

        self.assertEqual(detail["provider"], "wikimedia")
        self.assertIn("no unused stock video matched", detail["attempts"])

    def test_coverr_slot_is_skipped_without_key(self):
        shots = [shot(0, "rows of servers humming")]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=None
        ), patch.object(chain, "_coverr_asset", side_effect=AssertionError("Coverr must be skipped without key")), patch.object(
            chain, "_wikimedia_asset", return_value=None
        ), patch.object(chain, "_ai_configured", return_value=False), patch.object(
            chain, "_gradient_caption", return_value=self.dir / "g.mp4"
        ):
            chain.resolve_scene(shots[0], self.dir, planner)

    def test_ai_image_requires_a_configured_provider(self):
        shots = [shot(0, "rows of servers humming")]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=None
        ), patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            chain, "_ai_asset", side_effect=AssertionError("ai must be gated")
        ), patch.object(chain, "_ai_configured", return_value=False):
            detail = chain.resolve_scene(shots[0], self.dir, planner)
        # stock is exhausted inside the test env, so the engine falls back to its
        # local original vector component rather than a caption gradient by design
        self.assertEqual(detail["provider"], "motion_graphic")

    def test_pixabay_failure_never_logs_the_request_url_or_key(self):
        secret = "SECRET123"
        url = f"https://pixabay.com/api/videos/?key={secret}&q=servers"
        captured = io.StringIO()
        with patch.dict(os.environ, {"PIXABAY_API_KEY": secret}, clear=False), patch.object(
            chain, "_cached_hits", return_value=None
        ), patch.object(
            chain.urllib.request, "urlopen", side_effect=urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
        ), contextlib.redirect_stdout(captured):
            self.assertEqual(chain._pixabay_hits("servers"), [])
        output = captured.getvalue()
        self.assertNotIn(secret, output)
        self.assertNotIn("pixabay.com", output)
        self.assertIn("HTTP 403", output)


class SceneBriefTests(unittest.TestCase):
    def test_brief_exposes_the_stage_contract(self):
        brief = chain.build_scene_brief(shot(0, "AI data centers used 415 TWh in 2024"))
        for key in (
            "index", "beat_id", "intent", "narration", "visual_purpose",
            "scene_type", "visual_type", "asset_query", "search_query",
            "queries", "expected_duration", "aspect", "on_screen_text",
            "motion", "fallback_chain", "validation",
        ):
            self.assertIn(key, brief)
        self.assertEqual(brief["aspect"], "9:16")
        self.assertEqual(brief["scene_type"], "typography")
        self.assertTrue(brief["validation"]["query_ok"])
        self.assertIn("local_card", brief["fallback_chain"])

    def test_chart_only_when_numbers_share_a_unit_or_chart_words_appear(self):
        self.assertEqual(
            chain.build_scene_brief(shot(0, "Adoption grew from 10% to 25%"))["scene_type"],
            "chart",
        )
        self.assertEqual(
            chain.build_scene_brief(shot(0, "Data centers used 415 TWh in 2024"))["scene_type"],
            "typography",
        )
        self.assertEqual(
            chain.build_scene_brief(shot(0, "This chart shows why demand climbed"))["scene_type"],
            "chart",
        )

    def test_ui_diagram_map_and_product_are_distinct_scene_types(self):
        cases = {
            "Open the dashboard and export the table": "ui_demo",
            "The architecture routes requests through three service layers": "diagram",
            "Data centers spread across the country": "map",
            "The H100 chip runs hot under load": "product",
            "Rows of servers humming in a dark hall": "product",
            "A calm morning in the city": "footage",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(chain.build_scene_brief(shot(0, text))["scene_type"], expected)

    def test_query_candidates_include_variants_and_synonyms(self):
        brief = chain.build_scene_brief({
            "index": 0,
            "claim": "The power grid is under strain",
            "asset_query": "electricity demand",
            "asset_query_variants": ["data center power"],
        })
        self.assertEqual(brief["queries"][0], "data center power")
        self.assertIn("electricity demand", brief["queries"])
        self.assertTrue(any("power grid" in query for query in brief["queries"]))

    def test_plan_avoids_identical_consecutive_search_queries(self):
        shots = [shot(0, "one"), shot(1, "two")]
        for item in shots:
            item["asset_query"] = "data centers"
            item["asset_query_variants"] = []
        planner = chain.plan_scenes(shots)
        first = planner["scenes"][0]["search_query"]
        second = planner["scenes"][1]["search_query"]
        self.assertNotEqual(first.lower(), second.lower())

    def test_beat_label_sets_intent(self):
        brief = chain.build_scene_brief({
            "index": 3,
            "beat_label": "mechanism",
            "claim": "The model routes each request",
            "asset_query": "server",
        })
        self.assertEqual(brief["intent"], "mechanism")


class RankingTests(unittest.TestCase):
    def _hit(self, hit_id, tags, width, height, duration=10):
        return {
            "id": hit_id, "tags": tags, "width": width, "height": height,
            "duration": duration, "url": f"https://example.test/{hit_id}.mp4",
        }

    def test_pick_hit_prefers_vertical_and_relevant_tags(self):
        hits = [
            self._hit(1, "servers data center", 1920, 1080),
            self._hit(2, "servers data center", 1080, 1920),
            self._hit(3, "sunset beach", 1080, 1920),
        ]
        self.assertEqual(chain._pick_hit(hits, "servers")["id"], 2)

    def test_pick_hit_rejects_geometry_only_matches(self):
        hit = self._hit(3, "elevator shopping center gold", 1080, 1920)
        self.assertIsNone(chain._pick_hit([hit], "data centers"))

    def test_pick_hit_accepts_partial_tag_overlap(self):
        hit = self._hit(4, "data network server router", 1920, 1080)
        self.assertIsNotNone(chain._pick_hit([hit], "data centers"))

    def test_pick_hit_skips_assets_already_used(self):
        hits = [self._hit(7, "servers", 1080, 1920), self._hit(8, "servers", 1080, 1920)]
        chosen = chain._pick_hit(hits, "servers", used_ids={"pixabay:7"})
        self.assertEqual(chosen["id"], 8)
        self.assertIsNone(chain._pick_hit(hits, "servers", used_ids={"pixabay:7", "pixabay:8"}))

    def test_pick_hit_rejects_short_or_invalid_clips(self):
        hits = [self._hit(1, "servers", 0, 0), self._hit(2, "servers", 1080, 1920, duration=1.0)]
        self.assertIsNone(chain._pick_hit(hits, "servers"))


class FallbackDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_gradient_fallback_records_why_it_was_used(self):
        shots = [shot(i, "rows of servers humming") for i in range(4)]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_env", return_value=""), patch.object(
            chain, "_wikimedia_asset", return_value=None
        ), patch.object(chain, "_ai_configured", return_value=False), patch.object(
            chain, "_local_component_asset", return_value=None
        ), patch.object(chain, "_gradient_caption", return_value=self.dir / "g.mp4"):
            detail = chain.resolve_scene(shots[0], self.dir, planner)

        self.assertEqual(detail["provider"], "gradient")
        self.assertIn("no configured stock video provider", detail["fallback_reason"])
        self.assertIn("no unused Wikimedia still matched", detail["fallback_reason"])
        self.assertEqual(detail["relevance"], "none")
        resolved = planner["resolved"][-1]
        self.assertEqual(resolved["provider"], "gradient")
        self.assertTrue(resolved["fallback_reason"])

    def test_stock_success_records_asset_id_and_no_fallback(self):
        shots = [shot(i, "rows of servers humming") for i in range(4)]
        planner = chain.plan_scenes(shots)
        fake = {"path": "/tmp/x.mp4", "provider": "pixabay", "title": "",
                "asset_id": "pixabay:99"}
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=fake
        ), patch.object(vision_review, "enabled", return_value=False), patch.object(
            vision_review, "review_asset", return_value={"checked": False, "status": "disabled", "attempts": 0, "reason": "vision review disabled"}
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)

        self.assertEqual(detail["provider"], "pixabay")
        self.assertEqual(detail["asset_id"], "pixabay:99")
        self.assertEqual(detail["fallback_reason"], "")
        self.assertIn("pixabay:99", planner["used_asset_ids"])


class RelevanceValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _scene(self, index=0):
        return chain.build_scene_brief({
            "index": index,
            "claim": "Rows of servers humming in a dark data center",
            "caption": "servers humming",
            "asset_query": "servers",
            "asset_query_variants": ["data center servers", "server rack data center"],
        }, index=index)

    def test_motion_graphic_is_high_confidence_and_not_reviewed(self):
        scene = self._scene()
        validation = chain.validate_asset_relevance(
            scene, {"provider": "motion_graphic", "fallback_reason": ""}
        )
        self.assertEqual(validation["relevance_confidence"], "high")
        self.assertFalse(validation["semantic_review"])
        self.assertEqual(validation["review_reason"], "")

    def test_pixabay_tag_overlap_is_lexical_and_reviewed(self):
        scene = self._scene()
        validation = chain.validate_asset_relevance(
            scene,
            {
                "provider": "pixabay",
                "query": "data center servers",
                "tags": "server rack data center humming technology",
            },
        )
        self.assertEqual(validation["relevance_confidence"], "medium")
        self.assertTrue(validation["semantic_review"])
        self.assertIn("server", validation["matched_terms"])
        self.assertIn("lexical", validation["relevance_reason"])

    def test_pixabay_unrelated_tags_are_low_confidence(self):
        scene = self._scene()
        validation = chain.validate_asset_relevance(
            scene,
            {"provider": "pixabay", "query": "servers", "tags": "sunset beach ocean"},
        )
        self.assertEqual(validation["relevance_confidence"], "low")
        self.assertTrue(validation["semantic_review"])
        self.assertTrue(validation["review_reason"])

    def test_wikimedia_title_match_is_medium_but_still_reviewed(self):
        scene = self._scene()
        strong = chain.validate_asset_relevance(
            scene, {"provider": "wikimedia", "title": "File:Data center server rack.jpg"}
        )
        weak = chain.validate_asset_relevance(
            scene, {"provider": "wikimedia", "title": "File:Building art.jpg"}
        )
        self.assertEqual(strong["relevance_confidence"], "medium")
        self.assertEqual(weak["relevance_confidence"], "low")
        self.assertTrue(strong["semantic_review"])
        self.assertTrue(weak["semantic_review"])

    def test_dark_or_flat_footage_is_flagged_and_downgraded(self):
        scene = self._scene()
        self.assertTrue(chain._is_low_light({"yavg": 22, "ylow": 10, "yhigh": 20, "ymax": 120}))
        self.assertTrue(chain._is_low_light({"yavg": 44, "ylow": 39.5, "yhigh": 45.9, "ymax": 123.2}))
        self.assertFalse(chain._is_low_light({"yavg": 28.5, "ylow": 20, "yhigh": 23.6, "ymax": 239.6}))
        validation = chain.validate_asset_relevance(
            scene,
            {
                "provider": "pixabay",
                "query": "coding agents",
                "tags": "coding, developer",
                "visual_quality": "low_light",
            },
        )
        self.assertEqual(validation["relevance_confidence"], "low")
        self.assertTrue(validation["semantic_review"])
        self.assertIn("dark or flat", validation["review_reason"])

    def test_visual_quality_flags_low_light_clip(self):
        with patch("app.render.ffmpeg_tools.video_luma_stats", return_value={"yavg": 20, "ylow": 5, "yhigh": 15, "ymax": 90}):
            quality, stats = chain._visual_quality(self.dir / "clip.mp4")
        self.assertEqual(quality, "low_light")
        self.assertEqual(stats["yavg"], 20)

    def test_generated_image_providers_are_reviewed_even_with_vendor_names(self):
        scene = self._scene()
        for provider in ("pollinations", "gemini", "fal", "openai", "cloudflare"):
            with self.subTest(provider=provider):
                validation = chain.validate_asset_relevance(
                    scene, {"provider": provider, "query": "servers"}
                )
                self.assertEqual(validation["relevance_confidence"], "medium")
                self.assertTrue(validation["semantic_review"])

    def test_gradient_fallback_is_low_or_none_reviewed(self):
        scene = self._scene()
        fallback = chain.validate_asset_relevance(
            scene, {"provider": "gradient", "fallback_reason": "no stock provider configured"}
        )
        procedural = chain.validate_asset_relevance(
            scene, {"provider": "procedural", "fallback_reason": ""}
        )
        self.assertEqual(fallback["relevance_confidence"], "none")
        self.assertEqual(procedural["relevance_confidence"], "low")
        self.assertTrue(fallback["semantic_review"])
        self.assertTrue(procedural["semantic_review"])

    def test_resolve_prefers_a_non_low_stock_candidate(self):
        shot_data = {
            "index": 0,
            "duration": 2.8,
            "claim": "Rows of servers humming in a dark data center",
            "caption": "servers humming",
            "asset_query": "servers",
            "asset_query_variants": ["data center servers", "server rack data center"],
        }
        shots = [shot_data] + [shot(i, "rows of servers humming") for i in range(1, 4)]
        planner = chain.plan_scenes(shots)
        low = {"path": "/tmp/low.mp4", "provider": "pixabay", "asset_id": "pixabay:1",
               "tags": "sunset beach ocean"}
        medium = {"path": "/tmp/medium.mp4", "provider": "pixabay", "asset_id": "pixabay:2",
                  "tags": "server rack data center"}
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", side_effect=[low, medium]
        ), patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            chain, "_ai_configured", return_value=False
        ), patch.object(vision_review, "enabled", return_value=False), patch.object(
            vision_review, "review_asset", return_value={"checked": False, "status": "disabled", "attempts": 0, "reason": "vision review disabled"}
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)

        self.assertEqual(detail["provider"], "pixabay")
        self.assertEqual(detail["asset_id"], "pixabay:2")
        self.assertEqual(detail["relevance_confidence"], "medium")
        self.assertTrue(detail["semantic_review"])
        self.assertTrue(any("weak lexical match" in attempt for attempt in detail["attempts"]))
        self.assertEqual(planner["stock_used"], 1)

    def test_resolve_rejects_a_low_stock_candidate_and_uses_a_graphic(self):
        shot_data = {
            "index": 0,
            "duration": 2.8,
            "claim": "Rows of servers humming in a dark data center",
            "caption": "servers",
            "asset_query": "servers",
            "asset_query_variants": [],
        }
        shots = [shot_data] + [shot(i, "rows of servers humming") for i in range(1, 4)]
        planner = chain.plan_scenes(shots)
        low = {"path": "/tmp/low.mp4", "provider": "pixabay", "asset_id": "pixabay:1",
               "tags": "sunset beach ocean"}
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=low
        ), patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            chain, "_ai_configured", return_value=False
        ), patch.object(vision_review, "enabled", return_value=False), patch.object(
            vision_review, "review_asset", return_value={"checked": False, "status": "disabled", "attempts": 0, "reason": "vision review disabled"}
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)

        # stock candidate was rejected; the engine keeps its local original graphic
        self.assertEqual(detail["provider"], "motion_graphic")
        self.assertIn("weak lexical match", "; ".join(detail["attempts"]))
        self.assertEqual(planner["stock_used"], 0)

    def test_resolution_records_confidence_and_review_flags(self):
        shot_data = shot(0, "rows of servers humming")
        planner = chain.plan_scenes([shot_data])
        fake = {"path": "/tmp/x.mp4", "provider": "pixabay", "title": "",
                "asset_id": "pixabay:99", "tags": "server rack"}
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=fake
        ):
            detail = chain.resolve_scene(shot_data, self.dir, planner)

        self.assertIn("relevance_confidence", detail)
        self.assertIn("semantic_review", detail)
        resolved = planner["resolved"][-1]
        self.assertIn("relevance_confidence", resolved)
        self.assertIn("semantic_review", resolved)


class VisionReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_vision_review_is_disabled_by_default(self):
        with patch.dict(os.environ, {"VISION_REVIEW_PROVIDER": ""}, clear=False), patch.object(
            vision_review.requests, "post", side_effect=AssertionError("must not call network")
        ):
            result = vision_review.review_asset({}, {"path": "/tmp/x.mp4"})
        self.assertFalse(result["checked"])
        self.assertIn("disabled", result["reason"])

    def test_groq_vision_review_uses_openai_compatible_image_payload(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"relevance":"high","reason":"A processor board supports the hardware beat."}'
                }
            }]
        }
        with patch.dict(
            os.environ,
            {
                "VISION_REVIEW_PROVIDER": "groq",
                "VISION_REVIEW_MODEL": "qwen/qwen3.8-27b",
                "GROQ_API_KEY": "test-groq-key",
                "GROQ_VISION_MIN_INTERVAL_SECONDS": "0",
            },
            clear=False,
        ), patch.object(vision_review, "_first_frame", return_value=(b"frame", "image/jpeg")), patch.object(
            vision_review.requests, "post", return_value=response
        ) as post_mock:
            result = vision_review.review_asset(
                {"narration": "A processor board supports the hardware beat.", "visual_purpose": "show computing hardware"},
                {"path": "/tmp/frame.mp4", "provider": "pixabay", "query": "processor board"},
            )
        self.assertTrue(result["checked"])
        self.assertEqual(result["provider"], "groq")
        self.assertEqual(result["relevance"], "high")
        self.assertEqual(post_mock.call_args.args[0], "https://api.groq.com/openai/v1/chat/completions")
        body = post_mock.call_args.kwargs["json"]
        self.assertEqual(body["model"], "qwen/qwen3.8-27b")
        self.assertEqual(body["response_format"], {"type": "json_object"})
        image_part = body["messages"][0]["content"][1]["image_url"]["url"]
        self.assertTrue(image_part.startswith("data:image/jpeg;base64,"))

    def test_vision_review_parses_a_verdict(self):
        response = type("R", (), {})()
        response.status_code = 200
        response.json = lambda: {
            "candidates": [{"content": {"parts": [{"text": '{"relevance":"medium","reason":"shows code"}'}]}}]
        }
        with patch.dict(
            os.environ,
            {"VISION_REVIEW_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"},
            clear=False,
        ), patch.object(vision_review, "_first_frame", return_value=(b"img", "image/jpeg")), patch.object(
            vision_review.requests, "post", return_value=response
        ) as post_mock:
            result = vision_review.review_asset(
                {"narration": "coding agents", "visual_purpose": "show code"},
                {"path": "/tmp/x.mp4", "provider": "pixabay"},
            )
        body = post_mock.call_args.kwargs["json"]
        image_part = body["contents"][0]["parts"][1]["inlineData"]
        self.assertEqual(image_part["mimeType"], "image/jpeg")
        self.assertIn("data", image_part)
        self.assertNotIn("inline_data", body["contents"][0]["parts"][1])
        self.assertTrue(result["checked"])
        self.assertEqual(result["relevance"], "medium")
        self.assertIn("code", result["reason"])

    def test_vision_verdict_overrides_lexical_confidence(self):
        shot_data = shot(0, "rows of servers humming")
        planner = chain.plan_scenes([shot_data])
        fake = {"path": "/tmp/x.mp4", "provider": "pixabay", "title": "",
                "asset_id": "pixabay:99", "tags": "sunset beach"}
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=fake
        ), patch.object(
            vision_review, "review_asset",
            return_value={"checked": True, "provider": "gemini", "relevance": "high", "reason": "servers visible"},
        ):
            detail = chain.resolve_scene(shot_data, self.dir, planner)

        self.assertEqual(detail["relevance_confidence"], "high")
        self.assertFalse(detail["semantic_review"])
        self.assertTrue(detail["vision_review"]["checked"])
        self.assertTrue(planner["resolved"][-1]["vision_checked"])


    def test_medium_vision_candidate_is_rejected_before_high_confidence_alternate(self):
        shot_data = shot(0, "rows of servers humming")
        shot_data["asset_query"] = "server rack"
        planner = chain.plan_scenes([shot_data] + [shot(i, "rows of servers humming") for i in range(1, 4)])
        stock = {
            "path": "/tmp/medium.mp4", "provider": "pixabay",
            "asset_id": "pixabay:medium", "tags": "server rack data center",
        }
        alternate = {
            "path": "/tmp/high.mp4", "provider": "coverr",
            "asset_id": "coverr:high", "tags": "server rack data center",
        }
        with patch.object(
            chain, "_env",
            side_effect=lambda name: "key" if name in {"PIXABAY_API_KEY", "COVERR_API_KEY"} else "",
        ), patch.object(chain, "_pixabay_asset", side_effect=[stock, None]), patch.object(
            chain, "_coverr_asset", return_value=alternate,
        ), patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            chain, "_ai_configured", return_value=False,
        ), patch.object(
            vision_review, "review_asset", side_effect=[
                {"checked": True, "provider": "groq", "relevance": "medium", "reason": "generic circuit board"},
                {"checked": True, "provider": "groq", "relevance": "high", "reason": "server racks clearly visible"},
            ],
        ) as review:
            detail = chain.resolve_scene(shot_data, self.dir, planner)

        self.assertEqual(detail["provider"], "coverr")
        self.assertEqual(detail["relevance_confidence"], "high")
        self.assertEqual(review.call_count, 2)

    def test_low_vision_candidate_is_rejected_and_wikimedia_fallback_is_used(self):
        shot_data = shot(0, "rows of servers humming")
        shot_data["asset_query"] = "server rack"
        planner = chain.plan_scenes([shot_data] + [shot(i, "rows of servers humming") for i in range(1, 4)])
        stock = {
            "path": "/tmp/irrelevant.mp4", "provider": "pixabay",
            "asset_id": "pixabay:low", "tags": "servers data center server rack rows humming",
        }
        alternate = {
            "path": "/tmp/alternate.mp4", "provider": "coverr",
            "asset_id": "coverr:server-rack", "tags": "servers data center",
        }
        with patch.object(
            chain, "_env",
            side_effect=lambda name: "key" if name in {"PIXABAY_API_KEY", "COVERR_API_KEY"} else "",
        ), patch.object(chain, "_pixabay_asset", side_effect=[stock, None]), patch.object(
            chain, "_coverr_asset", return_value=alternate,
        ), patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            chain, "_ai_configured", return_value=False,
        ), patch.object(
            vision_review, "review_asset", side_effect=[
                {"checked": True, "provider": "gemini", "relevance": "low", "reason": "shows a beach"},
                {"checked": True, "provider": "gemini", "relevance": "high", "reason": "server racks visible"},
            ],
        ) as review:
            detail = chain.resolve_scene(shot_data, self.dir, planner)

        self.assertEqual(detail["provider"], "coverr")
        self.assertEqual(review.call_count, 2)
        self.assertEqual(planner["stock_used"], 1)
        self.assertEqual(len(planner["resolved"]), 1)
        self.assertEqual(planner["resolved"][0]["provider"], "coverr")
        self.assertTrue(any("rejected by vision review" in item for item in detail["attempts"]))

    def test_medium_vision_candidate_is_rejected_and_fallback_used(self):
        shot_data = shot(0, "rows of servers humming")
        planner = chain.plan_scenes([shot_data] + [shot(i, "rows of servers humming") for i in range(1, 4)])
        stock = {
            "path": "/tmp/uncertain.mp4", "provider": "pixabay",
            "asset_id": "pixabay:medium", "tags": "servers data center server rack rows humming",
        }
        with patch.object(
            chain, "_env",
            side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else "",
        ), patch.object(chain, "_pixabay_asset", return_value=stock), patch.object(
            chain, "_ai_configured", return_value=False
        ), patch.object(
            vision_review, "review_asset",
            return_value={"checked": True, "provider": "gemini", "relevance": "medium", "reason": "uncertain context"},
        ) as review:
            detail = chain.resolve_scene(shot_data, self.dir, planner)

        self.assertEqual(detail["provider"], "motion_graphic")
        self.assertGreaterEqual(review.call_count, 1)
        self.assertIn("medium relevance", "; ".join(detail["attempts"]))
        self.assertEqual(planner["stock_used"], 0)


if __name__ == "__main__":
    unittest.main()


def test_keyless_pollinations_is_available_to_strong_pipeline(monkeypatch):
    for name in ("POLLINATIONS_API_KEY", "GEMINI_API_KEY", "FAL_KEY",
                 "REPLICATE_API_TOKEN", "OPENAI_API_KEY", "CF_ACCOUNT_ID",
                 "CF_API_TOKEN", "VISUAL_PROVIDER", "POLLINATIONS_ENABLED",
                 "AI_IMAGE_FALLBACK"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("POLLINATIONS_ENABLED", "true")
    assert chain._ai_configured() is True


def test_vision_review_retries_rate_limit_and_returns_attempt_count(monkeypatch):
    monkeypatch.setenv("VISION_REVIEW_MAX_RETRIES", "2")
    monkeypatch.setenv("VISION_REVIEW_BACKOFF_SECONDS", "0.1")
    first = Mock(status_code=429, headers={"Retry-After": "0.1"})
    second = Mock(status_code=200, headers={})
    with patch.object(vision_review.requests, "post", side_effect=[first, second]) as post, patch.object(
        vision_review.time, "sleep"
    ):
        response, attempts = vision_review._post_with_backoff(
            "https://example.invalid", headers={}, json_body={}, timeout=1
        )
    assert response is second
    assert attempts == 2
    assert post.call_count == 2


def test_vision_review_exhausted_429_is_explicitly_rate_limited(monkeypatch):
    monkeypatch.setenv("VISION_REVIEW_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("VISION_REVIEW_MAX_RETRIES", "1")
    monkeypatch.setenv("VISION_REVIEW_BACKOFF_SECONDS", "0.1")
    monkeypatch.setenv("GROQ_VISION_MIN_INTERVAL_SECONDS", "0")
    response = Mock(status_code=429, headers={"Retry-After": "0"})
    with patch.object(vision_review, "_first_frame", return_value=(b"frame", "image/jpeg")), patch.object(
        vision_review.requests, "post", return_value=response
    ), patch.object(vision_review.time, "sleep"):
        result = vision_review.review_asset({"narration": "server hardware"}, {"path": "/tmp/x.mp4"})
    assert result["checked"] is False
    assert result["status"] == "rate_limited"
    assert result["attempts"] == 2


def test_unreviewed_external_visual_requires_storyboard_review():
    reasons = storyboard._review_reasons(
        {"narration": "A server rack"},
        {"provider": "pixabay", "relevance_confidence": "high", "vision_review": {"checked": False}},
        Path("/tmp/asset.mp4"),
    )
    assert any("not received a successful visual review" in reason for reason in reasons)


def test_moe_visual_plan_limits_graphics_and_consecutive_cards():
    narration = [
        "A token arrives at the transformer input.",
        "The router scores each expert for this token.",
        "The model sends the token to two specialists.",
        "GPU servers process the selected expert networks.",
        "The experts compute different parts of the response.",
        "Their outputs are combined before the next layer.",
        "Data center hardware supplies the compute.",
        "The final token continues through the model.",
    ]
    plan = chain.plan_scenes([
        {"index": i, "narration": text, "caption": text, "asset_query": text, "duration": 2.5}
        for i, text in enumerate(narration)
    ])
    types = [plan["scenes"][i]["visual_type"] for i in range(len(narration))]
    assert sum(kind == "motion_graphic" for kind in types) <= len(types) // 2
    longest_run = run = 0
    for kind in types:
        run = run + 1 if kind == "motion_graphic" else 0
        longest_run = max(longest_run, run)
    assert longest_run <= 2


def test_passive_token_routing_is_not_flagged_no_action():
    beat = beats.analyse_beat("Tokens are routed to the two most relevant experts.")
    assert beat.action in {"routes", "routed", "is routed", "are routed"}
    assert "no_action" not in beat.flags


def test_high_relevance_but_low_quality_asset_is_rejected():
    shot_data = shot(0, "server rack data center hardware")
    planner = chain.plan_scenes([shot_data, shot(1, "server racks at night"), shot(2, "data center cooling"), shot(3, "GPU compute")])
    planner["stock_cap"] = 2
    planner["scenes"][0]["allow_stock"] = True
    stock = {
        "path": "/tmp/low-quality.mp4", "provider": "pixabay",
        "asset_id": "pixabay:low-quality", "tags": "servers data center server rack",
    }
    with patch.object(
        chain, "_env",
        side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else "",
    ), patch.object(chain, "_pixabay_asset", return_value=stock), patch.object(
        chain, "_wikimedia_asset", return_value=None
    ), patch.object(chain, "_ai_configured", return_value=False), patch.object(
        vision_review, "review_asset",
        return_value={
            "checked": True, "status": "reviewed", "relevance": "high",
            "quality": "low", "reason": "blurry and poorly exposed",
        },
    ):
        detail = chain.resolve_scene(shot_data, Path("/tmp"), planner)
    # the flagged candidate is rejected; the fallback keeps its visual reason
    assert detail["provider"] == "motion_graphic"
    assert "low visual quality" in "; ".join(detail["attempts"])


def test_explicitly_disabled_image_provider_is_not_configured(monkeypatch):
    monkeypatch.setenv("VISUAL_PROVIDER", "off")
    assert chain._ai_configured() is False


def test_ai_image_fallback_can_be_disabled_even_when_a_key_is_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("AI_IMAGE_FALLBACK", "off")
    assert chain._ai_configured() is False


def test_gemini_live_smoke_for_current_benchmark_asset():
    if os.getenv("ND_RUN_GEMINI_LIVE") != "1":
        import pytest
        pytest.skip("set ND_RUN_GEMINI_LIVE=1 to call the configured Gemini vision API")
    asset_path = Path(
        "outputs/runs/20261115-153029-how-mixture-of-experts-models-route-toke/shots/stock_pixabay_002.mp4"
    )
    assert asset_path.is_file()
    result = vision_review.review_asset(
        {
            "narration": "GPU servers power large language models",
            "visual_purpose": "show data center hardware",
            "scene_type": "footage",
        },
        {"path": str(asset_path), "provider": "pixabay", "query": "GPU server racks"},
    )
    print(result)
    assert result.get("checked") is True


class TopicSpecificVisualRelevanceTests(unittest.TestCase):
    def test_generic_panda_match_is_rejected_for_one_giant_query(self):
        result = chain.validate_asset_relevance(
            {"narration": "Instead of one giant network", "search_query": "one giant"},
            {"provider": "pixabay", "query": "one giant", "title": "Giant Panda", "tags": "giant panda animal"},
        )
        self.assertEqual(result["relevance_confidence"], "low")

    def test_generic_machine_learning_match_is_rejected(self):
        result = chain.validate_asset_relevance(
            {"narration": "The model uses specialized experts", "search_query": "machine learning laboratory"},
            {"provider": "pixabay", "query": "machine learning laboratory", "title": "Industrial Landfill", "tags": "machine learning infographic landfill"},
        )
        self.assertEqual(result["relevance_confidence"], "low")

    def test_moe_asset_needs_two_topic_specific_terms(self):
        result = chain.validate_asset_relevance(
            {"narration": "A mixture of experts routes tokens", "search_query": "mixture of experts neural network architecture diagram"},
            {"provider": "pixabay", "query": "mixture of experts neural network architecture diagram", "title": "Mixture of Experts Neural Network", "tags": "mixture experts router"},
        )
        self.assertEqual(result["relevance_confidence"], "medium")
        self.assertIn("expert", result["matched_terms"])

    def test_pixabay_picker_prefers_topic_terms_over_panda_keyword_overlap(self):
        hits = [
            {"id": "panda", "duration": 8, "width": 720, "height": 1280, "tags": "giant panda animal"},
            {"id": "moe", "duration": 8, "width": 720, "height": 1280, "tags": "mixture experts router token routing"},
        ]
        picked = chain._pick_hit(hits, "mixture of experts token routing diagram")
        self.assertEqual(picked["id"], "moe")

    def test_moe_diagram_is_resolved_locally_before_stock_search(self):
        shot_data = {
            "index": 0,
            "duration": 4.0,
            "topic": "How AI Models Activate a Few Experts to Save Compute",
            "beat_label": "mechanism",
            "claim": "A router sends each token to selected experts",
            "caption": "A router sends each token to selected experts",
            "visual": "token routing through specialist experts",
            "asset_query": "mixture of experts token routing diagram",
            "asset_query_variants": [],
        }
        scene = chain.build_scene_brief(shot_data, index=0)
        self.assertEqual(scene["scene_type"], "diagram")
        planner = {"scenes": {0: scene}, "used_asset_ids": set(), "resolved": []}
        with tempfile.TemporaryDirectory() as td:
            with patch.object(chain, "_pixabay_asset", side_effect=AssertionError("stock must not be searched for a local diagram")):
                resolved = chain.resolve_scene(shot_data, Path(td), planner)
        self.assertEqual(resolved["provider"], "motion_graphic")
        self.assertEqual(resolved["card_variant"], "moe_diagram")
        self.assertEqual(resolved["relevance_confidence"], "high")


    def test_explicit_moe_diagram_query_selects_graphic_and_duplicate_becomes_typography(self):
        topic = "How AI Models Activate a Few Experts to Save Compute"
        narration = "In Mixtral's configuration, sparse routing selects a subset for each token."
        base = {
            "duration": 3.5,
            "topic": topic,
            "claim": narration,
            "caption": "Sparse routing selects a subset",
            "visual": "Token routing through specialist experts",
            "asset_query": "mixture of experts token routing diagram",
        }
        classified = chain.classify_scene(base)
        self.assertEqual(classified["visual_type"], "motion_graphic")
        self.assertEqual(classified["scene_type"], "diagram")
        planned = chain.plan_scenes([
            {**base, "index": 0},
            {**base, "index": 1},
        ])
        self.assertEqual(planned["scene_types"].get("diagram"), 1)
        self.assertEqual(planned["scene_types"].get("typography"), 1)
        second = planned["scenes"][1]
        self.assertEqual(second.get("card_variant"), "typography")
        self.assertEqual(second.get("typography_title"), "ONLY SELECTED EXPERTS")
        with tempfile.TemporaryDirectory() as td:
            resolved = chain.resolve_scene(
                {**base, "index": 1}, Path(td),
                {"scenes": {1: second}, "used_asset_ids": set(), "resolved": []},
            )
        self.assertEqual(resolved["provider"], "motion_graphic")
        self.assertEqual(resolved["card_variant"], "typography")
        self.assertEqual(resolved["relevance_confidence"], "high")

    def test_moe_topic_plan_preserves_beat_level_visual_variety(self):
        topic = "How AI Models Activate a Few Experts to Save Compute"
        shots = [
            {
                "index": 0, "duration": 3.5, "topic": topic,
                "claim": "What happens when a token reaches Mixtral?",
                "caption": "A token reaches the model",
                "visual": "Cinematic close-up of a processor",
                "asset_query": "GPU server racks data center",
            },
            {
                "index": 1, "duration": 3.5, "topic": topic,
                "beat_label": "mechanism",
                "claim": "A router selects two experts for each token at every layer.",
                "caption": "Router selects two experts",
                "visual": "Token routing through specialist experts",
                "asset_query": "mixture of experts token routing diagram",
            },
            {
                "index": 2, "duration": 3.5, "topic": topic,
                "claim": "Think of experts as specialist networks inside one model.",
                "caption": "Specialist networks inside one model",
                "visual": "A team collaborating in a modern office",
                "asset_query": "office team collaboration meeting",
            },
            {
                "index": 3, "duration": 3.5, "topic": topic,
                "claim": "The model keeps all of its parameters in memory.",
                "caption": "Model parameters occupy memory",
                "visual": "Close-up of GPU memory modules",
                "asset_query": "GPU memory modules close up",
            },
        ]
        planned = chain.plan_scenes(shots)
        self.assertEqual(planned["scene_types"].get("diagram", 0), 2)
        self.assertGreater(planned["scene_types"].get("footage", 0), 0)
        self.assertEqual(planned["total"], len(shots))
        self.assertEqual(
            sum(1 for scene in planned["scenes"].values()
                if scene.get("scene_type") == "diagram"),
            2,
        )

    def test_generic_moe_capacity_narration_is_not_forced_into_repeated_diagram(self):
        shot_data = {
            "index": 5,
            "duration": 3.6,
            "topic": "How AI Models Activate a Few Experts to Save Compute",
            "claim": "This gives you the knowledge capacity of a huge model with the cost of a smaller one.",
            "caption": "Knowledge capacity with the cost of a smaller model",
            "visual": "capacity and efficiency of the model",
            "asset_query": "knowledge capacity model efficiency",
            "asset_query_variants": [
                "researcher working with neural network visualization",
                "GPU server room cinematic footage",
            ],
        }
        scene = chain.build_scene_brief(shot_data, index=5)
        planner = {"scenes": {5: scene}, "used_asset_ids": set(), "resolved": []}
        with tempfile.TemporaryDirectory() as td:
            with patch.object(
                chain, "_moe_diagram_graphic",
                side_effect=AssertionError("generic supporting narration must not force the MoE diagram"),
            ):
                resolved = chain.resolve_scene(shot_data, Path(td), planner, dry_run=True)
        self.assertNotEqual(resolved.get("card_variant"), "moe_diagram")
        self.assertEqual(resolved["provider"], "motion_graphic")
        self.assertTrue(any("dry run" in attempt for attempt in resolved["attempts"]))

    def test_moe_analogy_and_memory_beats_keep_their_own_visual_treatment(self):
        shots = [
            {
                "index": 3,
                "duration": 3.6,
                "topic": "How AI Models Activate a Few Experts to Save Compute",
                "beat_label": "evidence",
                "claim": "Every employee in a company answering every email is inefficient.",
                "caption": "Every employee answers every email",
                "visual": "company email overload analogy",
                "asset_query": "modern office building",
            },
            {
                "index": 11,
                "duration": 3.6,
                "topic": "How AI Models Activate a Few Experts to Save Compute",
                "beat_label": "implication",
                "claim": "The full model still requires memory to store all parameters.",
                "caption": "Memory footprint remains large",
                "visual": "model memory storage limitation",
                "asset_query": "computer memory modules",
            },
        ]
        for shot_data in shots:
            planner = {"scenes": {shot_data["index"]: chain.build_scene_brief(shot_data, index=shot_data["index"])}, "used_asset_ids": set(), "resolved": []}
            with tempfile.TemporaryDirectory() as td:
                with patch.object(
                    chain, "_moe_diagram_graphic",
                    side_effect=AssertionError("analogy and limitation beats must not be forced into the same diagram"),
                ):
                    resolved = chain.resolve_scene(shot_data, Path(td), planner, dry_run=True)
            self.assertEqual(resolved["provider"], "motion_graphic")
            self.assertNotEqual(resolved.get("card_variant"), "moe_diagram")


class MoEStillQueryTests(unittest.TestCase):
    def test_context_queries_are_specific_and_searchable(self):
        intro = chain._moe_context_still_queries(
            {"narration": "Mixtral is a sparse mixture-of-experts model with open weights."},
            "mixture experts expert",
        )
        token = chain._moe_context_still_queries(
            {"narration": "Each token passes through another transformer layer."},
            "mixture experts expert",
        )
        specialist = chain._moe_context_still_queries(
            {"narration": "Think of the experts as specialist networks inside one model."},
            "mixture experts expert",
        )
        self.assertEqual(intro, ["GPU server", "data center"])
        self.assertEqual(token, ["transformer architecture", "neural network"])
        self.assertEqual(specialist, ["neural network", "artificial neural network"])

    def test_non_moe_scene_does_not_receive_moe_fallback_queries(self):
        self.assertEqual(
            chain._moe_context_still_queries({"narration": "A factory robot sorts packages."}, "factory robot"),
            [],
        )




def test_generated_video_sidecar_is_verified_and_requires_editorial_review(tmp_path, monkeypatch):
    import hashlib
    import json

    media = tmp_path / "generated.mp4"
    media.write_bytes(b"generated clip bytes")
    record = {
        "schema": "nextdecode.generated-video-asset.v1",
        "provider": "kling", "model": "kling-test", "task_id": "task-1",
        "run_id": "run-1", "local_path": str(media.resolve()),
        "sha256": hashlib.sha256(media.read_bytes()).hexdigest(),
        "status": "qualified", "requires_editorial_review": True,
        "prompt": "a relevant data center scene",
        "metadata": {"width": 720, "height": 1280, "size_bytes": media.stat().st_size},
    }
    media.with_suffix(".mp4.asset.json").write_text(json.dumps(record))
    from app.providers import video_generation_workflow
    monkeypatch.setattr(video_generation_workflow, "_probe_video", lambda path: {
        "width": 720, "height": 1280, "size_bytes": media.stat().st_size,
        "duration_seconds": 5.0, "fps": "30/1",
    })
    shot_data = {
        "index": 0, "claim": "A relevant data center scene is shown",
        "caption": "Data center", "visual": "Data center server racks",
        "asset_query": "data center server racks",
        "generated_video_asset": str(media),
    }
    planner = chain.plan_scenes([shot_data])
    detail = chain.resolve_scene(shot_data, tmp_path / "work", planner, dry_run=True)
    assert detail["provider"] == "generated_video"
    assert detail["path"] == str(media.resolve())
    assert detail["generated_provenance"]["sha256"] == record["sha256"]
    assert detail["semantic_review"] is True
    assert detail["relevance_confidence"] == "medium"


def test_generated_video_sidecar_hash_mismatch_falls_back_without_consuming_media(tmp_path):
    import json

    media = tmp_path / "generated.mp4"
    media.write_bytes(b"tampered clip bytes")
    record = {
        "schema": "nextdecode.generated-video-asset.v1",
        "provider": "kling", "model": "kling-test", "task_id": "task-1",
        "local_path": str(media.resolve()), "sha256": "0" * 64,
        "status": "qualified", "requires_editorial_review": True,
        "metadata": {"width": 720, "height": 1280, "size_bytes": media.stat().st_size},
    }
    media.with_suffix(".mp4.asset.json").write_text(json.dumps(record))
    shot_data = {
        "index": 0, "claim": "A data center is shown", "caption": "Data center",
        "visual": "Data center server racks", "asset_query": "data center server racks",
        "generated_video_asset": str(media),
    }
    planner = chain.plan_scenes([shot_data])
    detail = chain.resolve_scene(shot_data, tmp_path / "work", planner, dry_run=True)
    assert detail["provider"] != "generated_video"
    assert detail["path"] != str(media.resolve())


class CreativeDirectionBriefTests(unittest.TestCase):
    def test_explicit_visual_family_and_camera_language_reach_scene_brief(self):
        shot_spec = {
            "index": 2, "text": "A scientist studies the result",
            "visual_family": "real_footage", "shot_size": "close_up",
            "camera_angle": "low_angle", "camera_movement": "slow_push_in",
            "camera_instruction": "close up low angle camera",
            "visual_style": "documentary", "editing_rhythm": "breathing_room",
            "transition_intent": "match_cut", "continuity_group": "research:result",
            "duration": 2.5, "asset_query_variants": ["scientist examining research results close up"],
        }
        brief = chain.build_scene_brief(shot_spec)
        self.assertEqual(brief["scene_type"], "footage")
        self.assertEqual(brief["shot_size"], "close_up")
        self.assertEqual(brief["camera_angle"], "low_angle")
        self.assertEqual(brief["camera_movement"], "slow_push_in")
        self.assertEqual(brief["transition_intent"], "match_cut")
        self.assertEqual(brief["continuity_group"], "research:result")
        self.assertIn("scientist examining research results close up", brief["queries"])

    def test_explicit_diagram_family_overrides_ambient_footage_classifier(self):
        result = chain.classify_scene({"text": "A router selects the best expert", "visual_family": "diagram"})
        self.assertEqual(result["scene_type"], "diagram")
        self.assertEqual(result["visual_type"], "motion_graphic")

def test_local_vector_component_fallback_creates_topic_relevant_map_diagram(tmp_path):
    from app.visuals.chain import _local_component_asset

    shot = {
        "topic": "Protomaps self-hosted map tiles",
        "claim": "Download the PMTiles file and upload it to the CDN.",
        "visual_subject": "vector map tiles and CDN infrastructure",
        "visual_action": "map tile layers loading from a self-hosted CDN server",
    }
    scene = {
        "scene_type": "diagram",
        "visual_subject": shot["visual_subject"],
        "visual_action": shot["visual_action"],
        "narration": shot["claim"],
    }
    result = _local_component_asset(shot, scene, tmp_path, 0)
    assert result is not None
    assert result["generated_locally"] is True
    assert result["external_api_used"] is False
    assert Path(result["path"]).is_file()
    assert result["scene_type"] == "diagram"
