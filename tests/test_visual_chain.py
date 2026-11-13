import contextlib
import io
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from app.visuals import chain, vision_review


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
            chain, "_gradient_caption", return_value=self.dir / "g.mp4"
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
            chain, "_gradient_caption", return_value=self.dir / "g.mp4"
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)
        self.assertEqual(detail["provider"], "gradient")
        self.assertIn("low-light", detail["fallback_reason"])

    def test_broll_prefers_stock_then_tracks_the_cap(self):
        shots = [shot(i, "rows of servers humming") for i in range(4)]
        planner = chain.plan_scenes(shots)
        self.assertEqual(planner["stock_cap"], 1)
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value={"path": "/tmp/x.mp4", "provider": "pixabay", "title": ""}
        ) as pixabay, patch.object(chain, "_wikimedia_asset", return_value=None), patch.object(
            chain, "_gradient_caption", return_value=self.dir / "g.mp4"
        ):
            first = chain.resolve_scene(shots[0], self.dir, planner)
            second = chain.resolve_scene(shots[1], self.dir, planner)

        self.assertEqual(first["provider"], "pixabay")
        self.assertEqual(planner["stock_used"], 1)
        self.assertEqual(second["provider"], "gradient")
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
        self.assertEqual(detail["provider"], "gradient")

    def test_successful_lower_tier_provider_keeps_the_attempt_trail(self):
        shots = [shot(i, "rows of servers humming") for i in range(4)]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=None
        ), patch.object(
            chain, "_wikimedia_asset", return_value={"path": "/tmp/still.jpg", "provider": "wikimedia"}
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)

        self.assertEqual(detail["provider"], "wikimedia")
        self.assertIn("no unused stock video matched", detail["attempts"])

    def test_pexels_slot_is_skipped_without_key(self):
        shots = [shot(0, "rows of servers humming")]
        planner = chain.plan_scenes(shots)
        with patch.object(chain, "_env", side_effect=lambda name: "key" if name == "PIXABAY_API_KEY" else ""), patch.object(
            chain, "_pixabay_asset", return_value=None
        ), patch.object(chain, "_pexels_asset", side_effect=AssertionError("pexels must be skipped")), patch.object(
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
        ), patch.object(chain, "_gradient_caption", return_value=self.dir / "g.mp4"):
            detail = chain.resolve_scene(shots[0], self.dir, planner)
        self.assertEqual(detail["provider"], "gradient")

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
            chain, "_gradient_caption", return_value=self.dir / "g.mp4"
        ):
            detail = chain.resolve_scene(shots[0], self.dir, planner)

        self.assertEqual(detail["provider"], "gradient")
        self.assertIn("no stock video provider configured", detail["fallback_reason"])
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
            "asset_query_variants": ["data center servers", "city skyline"],
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
            "asset_query_variants": ["data center servers", "city skyline"],
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
        ), patch.object(chain, "_gradient_caption", return_value=self.dir / "g.mp4"):
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
        ), patch.object(chain, "_gradient_caption", return_value=self.dir / "g.mp4"):
            detail = chain.resolve_scene(shots[0], self.dir, planner)

        self.assertEqual(detail["provider"], "gradient")
        self.assertIn("weak lexical match", detail["fallback_reason"])
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
        ):
            result = vision_review.review_asset(
                {"narration": "coding agents", "visual_purpose": "show code"},
                {"path": "/tmp/x.mp4", "provider": "pixabay"},
            )
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


if __name__ == "__main__":
    unittest.main()
