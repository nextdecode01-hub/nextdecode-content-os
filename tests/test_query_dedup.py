"""I2 — global query de-duplication.

No phrase may serve more than MAX_QUERY_REUSE scenes while a meaningfully
different phrase exists; distinct queries stay distinct; every scene keeps a
usable query; repeats are recorded with their reason and intent.
"""
from __future__ import annotations

import unittest
from collections import Counter

from app.visuals import chain


def _shots(count: int, *, query="programmer workstation", variants=None,
           claims=None, captions=None) -> list[dict]:
    variants = variants or []
    captions = captions or ["The team ships a coding agent"] * count
    shots = []
    for index in range(count):
        shot = {
            "index": index,
            "caption": captions[index % len(captions)],
            "asset_query": query,
            "asset_query_variants": [query] + list(variants),
        }
        if claims:
            shot["claim"] = claims[index % len(claims)]
        shots.append(shot)
    return shots


class GlobalQueryDedupTests(unittest.TestCase):
    def test_no_query_serves_more_than_the_reuse_limit(self):
        variants = ["database query", "software testing", "code review",
                    "query performance", "performance problems"]
        planner = chain.plan_scenes(_shots(12, variants=variants))
        counts = Counter(entry["search_query"] for entry in planner["scenes"].values())
        self.assertLessEqual(max(counts.values()), chain.MAX_QUERY_REUSE, counts)
        self.assertLessEqual(max(planner["query_use"].values()), chain.MAX_QUERY_REUSE)

    def test_distinct_queries_are_preserved(self):
        queries = ["quantum computer", "electric vehicle", "vaccine trial"]
        shots = [{"index": i, "asset_query": q, "caption": q}
                 for i, q in enumerate(queries)]
        planner = chain.plan_scenes(shots)
        self.assertEqual([planner["scenes"][i]["search_query"] for i in range(3)], queries)

    def test_every_scene_keeps_a_usable_query(self):
        planner = chain.plan_scenes(_shots(9, variants=["database query"]))
        for index, scene in planner["scenes"].items():
            self.assertTrue(scene["search_query"], f"scene {index} lost its query")
            self.assertEqual(scene["queries"][0], scene["search_query"])

    def test_switch_is_recorded_and_used_for_the_fetch(self):
        planner = chain.plan_scenes(
            _shots(6, variants=["database query", "software testing"]))
        switched = [scene for scene in planner["scenes"].values()
                    if (scene.get("query_reuse") or {}).get("switched_to")]
        self.assertTrue(switched, "expected at least one rotation")
        self.assertEqual(switched[0]["search_query"],
                         switched[0]["query_reuse"]["switched_to"])
        self.assertEqual(switched[0]["queries"][0], switched[0]["search_query"])
        self.assertTrue(planner["query_switches"])

    def test_single_query_is_kept_and_the_reason_recorded(self):
        shots = [{"index": i, "asset_query": "programmer workstation",
                  "caption": "The team ships a coding agent"} for i in range(5)]
        planner = chain.plan_scenes(shots)
        repeated = [scene for scene in planner["scenes"].values()
                    if (scene.get("query_reuse") or {}).get("switched_to") == ""
                    and scene.get("query_reuse")]
        self.assertTrue(repeated, "repeat without alternatives must be recorded")
        self.assertIn("no distinct query available", repeated[0]["query_reuse"]["reason"])
        self.assertIn("different_intent", repeated[0]["query_reuse"])
        for scene in planner["scenes"].values():
            self.assertTrue(scene["search_query"])

    def test_motion_graphics_do_not_consume_the_query_budget(self):
        shots = []
        for index in range(8):
            if index % 2 == 0:
                shots.append({"index": index, "claim": "The tool reaches 95% accuracy",
                              "caption": "95% accuracy", "asset_query": "programmer workstation"})
            else:
                shots.append({"index": index, "caption": "The team ships a coding agent",
                              "asset_query": "programmer workstation",
                              "asset_query_variants": ["programmer workstation", "database query"]})
        planner = chain.plan_scenes(shots)
        broll = [scene for scene in planner["scenes"].values()
                 if scene["visual_type"] == "broll"]
        self.assertTrue(broll)
        # Only b-roll scenes fetch stock, so only they may consume the budget.
        self.assertEqual(sum(planner["query_use"].values()), len(broll))
        self.assertTrue(all(scene["search_query"] for scene in broll))


if __name__ == "__main__":
    unittest.main()
