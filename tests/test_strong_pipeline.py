#!/usr/bin/env python3
"""Tests for the strong editorial pipeline and its supporting modules."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import model_health
import motion_director
import script_studio
import stock_fetcher
import strong_pipeline


class TestAssetQueryBuilding(unittest.TestCase):
    def test_concept_query_for_a_known_subject(self):
        query = script_studio.build_asset_query("robot arm factory automation", "hook")
        self.assertIn("robot", query.lower())

    def test_query_is_never_a_generic_template(self):
        for topic in ["Using LLM for confidence scoring is a bad idea", "quantum error correction", "the ocean plastic crisis"]:
            query = script_studio.build_asset_query(topic, "mechanism")
            self.assertNotIn("relevant technology", query.lower())
            self.assertNotIn("close-up of relevant", query.lower())
            self.assertGreaterEqual(len(query.split()), 1)

    def test_concepts_vary_per_shot(self):
        variants = script_studio.concepts_for("ai model training on a gpu cluster with data")
        self.assertGreaterEqual(len(variants), 2)
        first = script_studio.build_asset_query("ai model training on a gpu cluster with data", "hook", variant=0)
        second = script_studio.build_asset_query("ai model training on a gpu cluster with data", "hook", variant=1)
        self.assertNotEqual(first, second)

    def test_beat_sheet_uses_topic_in_shot_hints(self):
        beats = script_studio.build_beat_sheet(
            "Robots now pick up objects in factories. The arms use force sensors. "
            "That changes how lines are staffed. Safety checks still need a person. "
            "Teams see steadier output.",
            duration=30.0,
            topic="robot arm factory automation",
        )
        self.assertTrue(beats)
        self.assertTrue(any("robot" in beat["shot_hint"].lower() for beat in beats))


class TestShotPlanning(unittest.TestCase):
    def test_motion_director_uses_query_variants(self):
        script = {
            "title": "robot arms",
            "shots": [
                {"text": "robots pick things up", "asset_query": "robotics laboratory",
                 "asset_query_variants": ["robotics laboratory", "server room"], "duration": 3.0},
            ],
        }
        shots = motion_director.plan_shots(script, audio_duration=26.0)
        queries = [shot["asset_query"] for shot in shots]
        self.assertGreater(len(set(queries)), 1)
        self.assertTrue(all(q for q in queries))

    def test_shots_are_tighter_than_before(self):
        script = {"title": "test", "shots": [{"text": "a", "asset_query": "laboratory", "duration": 2.0}] * 6}
        shots = motion_director.plan_shots(script, audio_duration=36.0)
        self.assertGreaterEqual(len(shots), 8)
        self.assertLessEqual(max(shot["duration"] for shot in shots), 3.0)


class TestStockFetcher(unittest.TestCase):
    def test_search_is_offline_safe(self):
        self.assertIsInstance(stock_fetcher.search_images(""), list)
        self.assertIsInstance(stock_fetcher.search_images("a"), list)

    def test_credit_lines_include_licence_and_page(self):
        assets = [{
            "title": "File:Example.jpg",
            "author": "A Photographer",
            "license": "CC BY 2.0",
            "page_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
        }]
        lines = stock_fetcher.credit_lines(assets)
        self.assertEqual(len(lines), 1)
        self.assertIn("CC BY 2.0", lines[0])
        self.assertIn("commons.wikimedia.org", lines[0])

    def test_credit_lines_ignore_malformed_entries(self):
        self.assertEqual(stock_fetcher.credit_lines([None, {}, {"title": ""}]), [])

    def test_wikimedia_result_must_match_the_full_subject(self):
        old_book = {"title": "File:A world in perplexity (1918).jpg"}
        census = {"title": "File:New York enumeration district census.jpg"}
        product_screenshot = {"title": "File:Ansicht einer Perplexity Page.png"}

        self.assertFalse(stock_fetcher._query_match(old_book, "perplexity pages"))
        self.assertFalse(stock_fetcher._query_match(census, "switzerland block"))
        self.assertTrue(stock_fetcher._query_match(product_screenshot, "perplexity pages"))


class TestModelHealth(unittest.TestCase):
    def test_unconfigured_provider_is_marked_not_configured(self):
        with patch.dict("os.environ", {}, clear=False):
            record = model_health.probe_provider("ollama", timeout=1)
        self.assertFalse(record["configured"])
        self.assertFalse(record["ok"])

    def test_probe_writes_and_reloads(self, ):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "health.json"
            model_health.save_health({"updated_at": "x", "providers": {}}, path)
            loaded = model_health.load_health(path)
            self.assertEqual(loaded["providers"], {})

    def test_should_skip_respects_ignore_flag(self):
        with patch.dict("os.environ", {"AI_IGNORE_HEALTH": "1"}, clear=False):
            self.assertFalse(model_health.should_skip("groq"))

    def test_unhealthy_provider_is_skipped_after_a_fresh_failure(self):
        import tempfile
        from datetime import datetime, timezone

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "health.json"
            record = {
                "provider": "groq",
                "configured": True,
                "ok": False,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "latency_ms": 100,
            }
            model_health.save_health({"updated_at": "", "providers": {"groq": record}}, path)
            self.assertTrue(model_health.should_skip("groq", path=path))
            self.assertEqual(model_health.unhealthy_providers(path=path), ["groq"])


class TestStrongPipelineWiring(unittest.TestCase):
    def test_visual_description_is_honest_about_stock(self):
        assets = [
            {"provider": "wikimedia", "path": "/tmp/a.jpg", "title": "File:A.jpg", "license": "CC BY 2.0"},
            {"provider": "wikimedia", "path": "/tmp/b.jpg", "title": "File:B.jpg", "license": "CC0"},
        ]
        visuals = strong_pipeline._describe_visuals(assets, [{"index": 0}, {"index": 1}])
        self.assertEqual(visuals["mode"], "multi_shot_stock")
        self.assertEqual(visuals["asset_count"], 2)
        self.assertEqual(visuals["providers"], {"wikimedia": 2})

    def test_visual_description_flags_ai_and_procedural(self):
        ai = strong_pipeline._describe_visuals([{"provider": "gemini", "path": "/tmp/a.png"}], [{}])
        self.assertEqual(ai["mode"], "multi_shot_ai")
        procedural = strong_pipeline._describe_visuals([{"provider": "procedural"}], [{}])
        self.assertEqual(procedural["mode"], "multi_shot_procedural")
        empty = strong_pipeline._describe_visuals([], [{"index": 0}])
        self.assertEqual(empty["mode"], "multi_shot_procedural")

    def test_missing_shot_assets_make_stock_video_ineligible(self):
        assets = [{"provider": "wikimedia", "path": "/tmp/a.jpg"}]
        visuals = strong_pipeline._describe_visuals(assets, [{"index": 0}, {"index": 1}])
        self.assertEqual(visuals["mode"], "multi_shot_mixed")
        self.assertEqual(visuals["procedural_shot_count"], 1)

    def test_estimated_words_cover_the_whole_duration(self):
        words = strong_pipeline.estimated_words("one two three four", 4.0)
        self.assertEqual(len(words), 4)
        self.assertAlmostEqual(words[-1]["end"], 4.0, places=3)


if __name__ == "__main__":
    unittest.main()
