"""Regression tests for visual scene classification in app.visuals.chain.

Covers:
- Normal b-roll classification (ambient shots without numbers, claims, or lists)
- Normal motion-graphic classification (percentages, multipliers, spelled quantities, claim hints, list markers)
- Boundary and ambiguous cases (model names, dates/years, partial hints vs substring matches)
- Missing or malformed inputs (empty dict, None values, non-string, missing keys)
- Consistency of classification with downstream consumers (build_scene_brief, plan_scenes)
"""
import unittest

from app.visuals import chain


class VisualClassificationRegressionTests(unittest.TestCase):
    """Exhaustive test suite for classify_scene, _scene_type, and downstream consistency."""

    def test_normal_broll_ambient_descriptions(self):
        """Ambient visual descriptions without numbers, claims, or lists must classify as broll."""
        samples = [
            ("A team walking through an open office at night", "footage"),
            ("Neon city skyline reflecting across the river", "footage"),
            ("Cinematic landscape of misty mountains at sunrise", "footage"),
            ("Close-up of keyboard typing with shallow depth of field", "footage"),
            ("A quiet hallway with soft morning lighting", "footage"),
        ]
        for text, expected_type in samples:
            with self.subTest(text=text):
                res = chain.classify_scene({"caption": text})
                self.assertEqual(res["visual_type"], "broll")
                self.assertFalse(res["has_number"])
                self.assertEqual(res["scene_type"], expected_type)

    def test_normal_motion_graphic_explicit_numbers(self):
        """Explicit numbers (percentages, multipliers, spelled quantities) trigger motion_graphic."""
        samples = [
            ("Accuracy increased by 45.2% on the benchmark", "45.2%"),
            ("Throughput jumped 10 fold after optimization", "10×"),
            ("Latency dropped 5 times faster", "5×"),
            ("The cluster used over fifty gigawatt-hours", "50 GWh"),
            ("Cost fell to zero point one percent of total", "0.1%"),
            ("Throughput reached nearly 120 gigawatts", "120 GW"),
        ]
        for text, expected_num in samples:
            with self.subTest(text=text):
                res = chain.classify_scene({"claim": text})
                self.assertEqual(res["visual_type"], "motion_graphic")
                self.assertTrue(res["has_number"])
                self.assertIn(res["scene_type"], {"chart", "typography"})
                if expected_num:
                    self.assertEqual(chain._first_number(text), expected_num)

    def test_normal_motion_graphic_claim_hints(self):
        """Text containing GRAPHIC_HINTS keywords triggers motion_graphic even without digits."""
        hints_to_test = [
            ("A recent study reveals a major shift in compiler design", "study"),
            ("Industry report confirms ongoing infrastructure migration", "report"),
            ("A national survey highlighted engineer burnout", "survey"),
            ("According to senior leadership the strategy changed", "according"),
            ("Market analysis predicts significant disruption ahead", "analysis"),
            ("Rapid growth across enterprise deployments", "growth"),
            ("Unexpected decrease in memory consumption", "decrease"),
            ("Finally we arrive at the core architectural lesson", "finally"),
        ]
        for text, hint in hints_to_test:
            with self.subTest(hint=hint):
                res = chain.classify_scene({"visual": text})
                self.assertEqual(res["visual_type"], "motion_graphic")
                self.assertIn(res["scene_type"], {"chart", "typography"})

    def test_normal_motion_graphic_list_markers(self):
        """Numbered list items (1., 2), first, second, third) trigger motion_graphic."""
        list_samples = [
            "1. Isolate the failing network socket",
            "2) Inspect the heap profile immediately",
            "3. Deploy the patched binary to canary nodes",
            "first identify the bottleneck before refactoring",
            "second verify the thread safety of the pool",
            "third execute the integration test suite",
        ]
        for text in list_samples:
            with self.subTest(text=text):
                res = chain.classify_scene({"caption": text})
                self.assertEqual(res["visual_type"], "motion_graphic")

    def test_boundary_model_names_and_hardware_codes(self):
        """Model names and hardware terms without standalone digits or graphic hints classify as broll."""
        # Note: GPT-4 and H100 are explicitly handled by chain._first_number
        samples = [
            ("GPT-4 is a large model", "broll"),
            ("H100 chips run hot", "broll"),
        ]
        for text, expected in samples:
            with self.subTest(text=text):
                self.assertEqual(chain._first_number(text), "")
                res = chain.classify_scene({"caption": text})
                self.assertEqual(res["visual_type"], expected)
                self.assertFalse(res["has_number"])

    def test_boundary_years_dates_and_n_plus_one(self):
        """Standalone years and expressions like 'N+1' are explicitly excluded from statistics."""
        cases = [
            "A 2024 paper explored transformer attention",
            "In 2026 teams adopted automated governance",
            "The project started in late 1999",
            "Your pull request might introduce an N+1 query vulnerability",
            "Solving the N plus 1 query performance bug",
        ]
        for text in cases:
            with self.subTest(text=text):
                num = chain._first_number(text)
                self.assertEqual(num, "", f"Expected no extracted stat number for: {text}")
                res = chain.classify_scene({"caption": text})
                self.assertEqual(res["visual_type"], "broll")

    def test_scene_type_specializations_for_broll(self):
        """broll visual_type routes scene_type based on UI, DIAGRAM, MAP, and PRODUCT hints."""
        spec_cases = [
            ("Live terminal interface running continuous monitoring", "ui_demo"),
            ("A complex pipeline architecture flowchart", "motion_graphic"),  # 'chart' in GRAPHIC_HINTS promotes to motion_graphic
            ("Worldwide global grid map of latency distributions", "map"),
            ("Close up of a semiconductor chip and hardware sensor", "product"),
            ("A team of researchers discussing in a glass conference room", "footage"),
        ]
        for text, expected_type in spec_cases:
            with self.subTest(expected=expected_type):
                res = chain.classify_scene({"caption": text})
                if expected_type == "motion_graphic":
                    self.assertEqual(res["visual_type"], "motion_graphic")
                else:
                    self.assertEqual(res["visual_type"], "broll")
                    self.assertEqual(res["scene_type"], expected_type)

    def test_scene_type_specializations_for_motion_graphic(self):
        """motion_graphic visual_type routes scene_type to 'chart' or 'typography'."""
        # Repeated units or CHART_HINTS -> chart
        chart_cases = [
            "Revenue was 10 million compared with 25 million last quarter",
            "Data shows percentage of errors dropped significantly",
            "Statistics survey comparing model A versus model B",
        ]
        for text in chart_cases:
            with self.subTest(text=text):
                res = chain.classify_scene({"claim": text})
                self.assertEqual(res["visual_type"], "motion_graphic")
                self.assertEqual(res["scene_type"], "chart")

        # Single figure without chart hints -> typography
        res_typo = chain.classify_scene({"claim": "The throughput reached 50 gigawatt-hours"})
        self.assertEqual(res_typo["visual_type"], "motion_graphic")
        self.assertEqual(res_typo["scene_type"], "typography")

    def test_input_precedence_claim_caption_visual(self):
        """classify_scene uses the first non-empty text among claim, caption, visual."""
        # claim (broll) takes precedence over caption (motion_graphic hint)
        res1 = chain.classify_scene({
            "claim": "Quiet server room with glowing lights",
            "caption": "A 50% increase in network capacity",
        })
        self.assertEqual(res1["visual_type"], "broll")

        # caption takes precedence over visual if claim is empty
        res2 = chain.classify_scene({
            "claim": "",
            "caption": "Accuracy reached 99.8%",
            "visual": "Quiet server room with glowing lights",
        })
        self.assertEqual(res2["visual_type"], "motion_graphic")

        # visual is used if claim and caption are empty
        res3 = chain.classify_scene({
            "visual": "A 10 fold speedup in compiling time",
        })
        self.assertEqual(res3["visual_type"], "motion_graphic")

    def test_missing_or_malformed_inputs(self):
        """Handles empty dicts, missing keys, None values, and non-string types safely."""
        # Empty dict -> broll footage, no number, default keyword 'technology'
        empty_res = chain.classify_scene({})
        self.assertEqual(empty_res["visual_type"], "broll")
        self.assertEqual(empty_res["scene_type"], "footage")
        self.assertFalse(empty_res["has_number"])
        self.assertEqual(empty_res["keyword"], "technology")

        # None values across all fields
        none_res = chain.classify_scene({"claim": None, "caption": None, "visual": None})
        self.assertEqual(none_res["visual_type"], "broll")
        self.assertEqual(none_res["scene_type"], "footage")
        self.assertFalse(none_res["has_number"])
        self.assertEqual(none_res["keyword"], "technology")

        # Non-string data in fields without numeric conversion
        dummy_res = chain.classify_scene({"caption": []})
        self.assertEqual(dummy_res["visual_type"], "broll")
        self.assertEqual(dummy_res["scene_type"], "footage")
        self.assertEqual(dummy_res["keyword"], "technology")

    def test_consistency_build_scene_brief_and_classify_scene(self):
        """build_scene_brief must inherit classification attributes consistently."""
        shot = {
            "index": 2,
            "claim": "Processing speed doubled by 200%",
            "caption": "server rack",
            "duration": 3.5,
        }
        classified = chain.classify_scene(shot)
        brief = chain.build_scene_brief(shot, index=2)

        self.assertEqual(brief["visual_type"], classified["visual_type"])
        self.assertEqual(brief["scene_type"], classified["scene_type"])
        self.assertEqual(brief["validation"]["has_number"], classified["has_number"])
        self.assertEqual(brief["fallback_chain"], chain.GRAPHIC_FALLBACK_CHAIN)
        self.assertEqual(brief["visual_purpose"], chain._visual_purpose(classified["scene_type"]))

    def test_consistency_plan_scenes_budget_and_fallbacks(self):
        """Downstream plan_scenes must respect classification and correctly downgrade when budget is exceeded."""
        # 4 consecutive graphic candidates
        shots = [
            {"index": i, "claim": f"Benchmark result {i} improved by {i + 10}%"}
            for i in range(4)
        ]
        planner = chain.plan_scenes(shots)

        # First 2 should be motion_graphic, subsequent must be capped/downgraded to broll footage
        self.assertEqual(planner["scenes"][0]["visual_type"], "motion_graphic")
        self.assertEqual(planner["scenes"][1]["visual_type"], "motion_graphic")
        self.assertEqual(planner["scenes"][2]["visual_type"], "broll")
        self.assertEqual(planner["scenes"][2]["scene_type"], "footage")
        self.assertEqual(planner["scenes"][2]["fallback_chain"], chain.BROLL_FALLBACK_CHAIN)
        self.assertIn("b-roll breaks up repeated full-screen cards", planner["scenes"][2]["variety_note"])

    def test_broll_semantic_relevance_and_topic_fallback(self):
        """ND-PROD-005 Improvement 1: Regression tests for b-roll semantic relevance and fallback."""
        # 1. Previously mismatched Scene 8: 'currently being' / 'framework currently being'
        s8 = {
            "caption": "The framework is currently being revised under the White House AI Action Plan.",
            "asset_query": "currently being",
            "topic": "AI Risk Governance",
        }
        kw8 = chain.extract_keyword(s8)
        self.assertNotIn("currently", kw8)
        self.assertNotIn("being", kw8)
        cands8 = chain._query_candidates(s8, kw8)
        self.assertNotIn("currently being", cands8)
        self.assertTrue(any("governance" in c or "boardroom" in c or "corporate" in c or "risk" in c for c in cands8))

        # 2. Previously mismatched Scene 9: 'being revised'
        s9 = {
            "caption": "The framework is currently being revised under the White House AI Action Plan.",
            "asset_query": "being revised",
            "topic": "AI Policy",
        }
        kw9 = chain.extract_keyword(s9)
        self.assertNotIn("being", kw9)
        self.assertNotIn("revised", kw9)
        self.assertEqual(kw9, "government policy")
        cands9 = chain._query_candidates(s9, kw9)
        self.assertNotIn("being revised", cands9)
        self.assertIn("government policy", cands9)

        # 3. Previously mismatched Scene 11: 'full framework'
        s11 = {
            "caption": "You can review the full framework on the official NIST website to evaluate your own AI deployment risks.",
            "asset_query": "full framework",
            "topic": "NIST AI Framework",
        }
        kw11 = chain.extract_keyword(s11)
        self.assertNotIn("full", kw11)
        self.assertNotIn("framework", kw11)
        self.assertIn("nist", kw11)
        cands11 = chain._query_candidates(s11, kw11)
        self.assertNotIn("full framework", cands11)

        # 4. Pure verb phrase & passive voice fallbacks
        s_passive = {"asset_query": "being implemented", "topic": "chip manufacturing"}
        kw_passive = chain.extract_keyword(s_passive)
        self.assertNotIn("implemented", kw_passive)
        self.assertNotIn("being", kw_passive)
        self.assertIn(kw_passive, ("semiconductor", "chip"))

        # 5. Concrete valid query passes through unchanged
        s_concrete = {"asset_query": "gpu semiconductor chip"}
        self.assertEqual(chain.extract_keyword(s_concrete), "gpu semiconductor chip")


if __name__ == "__main__":
    unittest.main()
