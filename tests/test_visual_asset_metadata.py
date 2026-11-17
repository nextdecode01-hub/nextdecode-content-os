from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.visuals import chain, stock_fetcher


class AssetMetadataRelevanceTests(unittest.TestCase):
    def test_query_candidates_include_explicit_visual_intent(self):
        shot = {
            "narration": "Cooling systems protect dense compute racks.",
            "visual_intent": "close-up of liquid-cooled GPU server racks",
            "asset_query": "artificial intelligence",
        }
        candidates = chain._query_candidates(shot, "artificial intelligence")
        self.assertEqual(candidates[0], "close-up of liquid-cooled GPU server racks")

    def test_pixabay_ranking_uses_visual_intent_and_narration_metadata(self):
        hits = [
            {
                "id": 1, "duration": 10, "width": 1080, "height": 1920,
                "tags": "server racks data center",
            },
            {
                "id": 2, "duration": 10, "width": 1080, "height": 1920,
                "title": "Liquid cooled GPU server racks",
                "description": "Cold plate cooling for high density compute",
                "tags": "server racks data center GPU liquid cooling cold plates",
            },
        ]
        scene = {
            "narration": "Cold plates cool GPU servers.",
            "visual_intent": "show liquid cooled GPU server racks",
        }
        chosen = chain._pick_hit(hits, "server racks", scene=scene)
        self.assertEqual(chosen["id"], 2)

    def test_asset_relevance_score_uses_visual_intent_description_and_tags(self):
        result = chain.validate_asset_relevance(
            {
                "narration": "Cold plates remove heat from GPU servers.",
                "visual_intent": "show liquid cooled GPU server racks",
                "visual_purpose": "show the hardware discussed",
                "search_query": "server racks",
                "keyword": "server racks",
            },
            {
                "provider": "pixabay",
                "query": "server racks",
                "title": "GPU server racks",
                "description": "Liquid cooling with cold plates",
                "tags": "server data center gpu cold plates liquid cooling",
            },
        )
        self.assertGreater(result["relevance_score"], 0.35)
        self.assertGreater(result["intent_overlap"], 0.0)
        self.assertIn("gpu", result["matched_terms"])

    def test_wikimedia_query_match_can_use_description_metadata(self):
        item = {
            "title": "File:Technical photograph 001.jpg",
            "object_name": "",
            "description": "Liquid cooled GPU server rack in a data center",
        }
        self.assertTrue(stock_fetcher._query_match(item, "GPU server rack"))

    def test_pixabay_cache_key_normalizes_whitespace_and_versioned_identity(self):
        self.assertEqual(chain._cache_path("GPU   server racks"), chain._cache_path("gpu server racks"))
        self.assertTrue(chain._cache_path("gpu server racks").name.endswith(".json"))


    def test_wikimedia_search_results_are_cached_by_normalized_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = [{"title": "File:Data center.jpg", "description": "data center"}]
            with patch.object(stock_fetcher, "CACHE_DIR", Path(tmp)), patch.object(
                stock_fetcher, "_search_pages", return_value=results,
            ) as search:
                first = stock_fetcher._cached_search_pages("Data   Center", limit=6)
                second = stock_fetcher._cached_search_pages("data center", limit=6)
            self.assertEqual(first, results)
            self.assertEqual(second, results)
            search.assert_called_once()


if __name__ == "__main__":
    unittest.main()
