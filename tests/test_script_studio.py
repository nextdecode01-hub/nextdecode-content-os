#!/usr/bin/env python3
import json
import unittest
from unittest.mock import patch, MagicMock

from app.script import studio as script_studio
from app.script import voice_guide

CLEAN_VOICE_TEXT = (
    "AI has one key benefit for developers today. Teams can move a slow manual step into a "
    "repeatable automated pass. That reshapes the daily routine more than the headline "
    "suggests. The work still needs a person to check the output before it goes live. Setup "
    "takes time and the awkward edge cases turn up later. Teams that plan for review time, "
    "not only generation time, get a steadier result. The payoff is saved effort on every "
    "run after the first week, and a clearer picture of what the tool cannot do."
)


class TestScriptStudio(unittest.TestCase):
    def setUp(self):
        self.research_good = {
            "verdict": "sufficient",
            "claims": [
                {
                    "text": "A study found improved efficiency",
                    "quote": "The model achieved 40% better efficiency in tests",
                    "source_url": "https://example.com/study1"
                }
            ],
            "source_urls": ["https://example.com/study1"],
            "summary": "Research shows measurable improvements"
        }

    def test_curated_script_override_keeps_research_and_critic_gates(self):
        import tempfile
        from pathlib import Path
        script = {
            "title": "A Curated Evidence-Based Short",
            "hook": "AI research is moving faster, but what can agents actually finish?",
            "voice_text": "AI research is moving faster, but what can agents actually finish? " + " ".join(
                ["The study measured a specific outcome and its limits remain important."] * 25
            ),
            "source_urls": ["https://example.com/study1"],
            "content_pillar": "Hype Check",
            "broll_query": "AI research laboratory",
            "youtube_tags": ["AI research"],
            "instagram_hashtags": ["#AI"],
            "platform_copy": {"instagram_caption": "A research result, with context."},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(script), encoding="utf-8")
            with (
                patch.dict("os.environ", {"NEXTDECODE_SCRIPT_OVERRIDE_PATH": str(path)}),
                patch.object(script_studio, "critique", return_value={"score": 100, "pass": True, "issues": []}) as critic,
                patch.object(script_studio.multi_model_ai, "generate_for_task_json") as model,
            ):
                result = script_studio.write_script(
                    "AI research", self.research_good, seconds=60, strict_research=True
                )
        self.assertEqual(result["model_route"]["provider"], "editorial_override")
        self.assertEqual(result["source_urls"], ["https://example.com/study1"])
        self.assertEqual(result["hook"], "AI research is moving faster, but what can agents actually finish?")
        critic.assert_called_once()
        model.assert_not_called()

    def test_curated_script_override_rejects_sources_outside_research_bundle(self):
        import tempfile
        from pathlib import Path
        script = {
            "title": "A Curated Short",
            "hook": "AI research has a hard problem to solve.",
            "voice_text": "AI research has a hard problem to solve. " + " ".join(["Evidence matters."] * 80),
            "source_urls": ["https://unverified.example/claim"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(script), encoding="utf-8")
            with patch.dict("os.environ", {"NEXTDECODE_SCRIPT_OVERRIDE_PATH": str(path)}):
                with self.assertRaisesRegex(RuntimeError, "absent from the research bundle"):
                    script_studio.write_script("AI research", self.research_good, seconds=60)

    def test_hook_scoring_rejects_banned_generic_phrases(self):
        hooks = [
            "In this video we explore AI",  # generic
            "Game-changer technology emerges",  # banned
            "AI cuts latency by 40 percent in testing",  # good
        ]
        results = script_studio.score_hooks(hooks, topic="AI")
        # Check that bad ones are penalized
        for r in results:
            if "in this video" in r['hook'].lower():
                self.assertTrue(r['is_generic'] or r['score'] < 50)
            if "game-changer" in r['hook'].lower():
                self.assertTrue(r['score'] < 50)

    def test_hook_scoring_penalizes_unanchored_parameter_counts(self):
        with patch.object(script_studio.multi_model_ai, "generate_json", return_value={"best": []}):
            results = script_studio.score_hooks(
                [
                    "How can a 256 billion parameter model use 8 billion per token?",
                    "Why does an AI model activate only a few expert networks?",
                ],
                topic="Mixture of Experts",
            )
        by_hook = {item["hook"]: item for item in results}
        numeric = by_hook["How can a 256 billion parameter model use 8 billion per token?"]
        mechanism = by_hook["Why does an AI model activate only a few expert networks?"]
        self.assertIn("unanchored numeric hook", numeric["reasons"])
        self.assertLess(numeric["score"], mechanism["score"])

    def test_verified_moe_script_uses_primary_source_routing_facts(self):
        research = {
            "source_urls": [
                "https://mistral.ai/news/mixtral-of-experts/",
                "https://huggingface.co/blog/mixtral",
            ],
            "claims": [
                {
                    "claim": "Mixtral is a sparse mixture-of-experts model.",
                    "quote": "Mixtral 8x7B is a high-quality sparse mixture of experts model with open weights.",
                    "source_url": "https://mistral.ai/news/mixtral-of-experts/",
                    "decision": "include",
                    "verification": {"status": "supported"},
                },
                {
                    "claim": "Mixtral routes every token to two experts.",
                    "quote": "At every layer, for every token, a router network chooses two experts to process the token and combine their output additively.",
                    "source_url": "https://mistral.ai/news/mixtral-of-experts/",
                    "decision": "include",
                    "verification": {"status": "supported"},
                },
            ],
        }
        script = script_studio.build_verified_moe_script(
            research, seconds=45, topic="How AI Models Activate a Few Experts to Save Compute"
        )
        self.assertIsNotNone(script)
        self.assertIn("two experts", script["voice_text"].lower())
        self.assertIn("router", script["voice_text"].lower())
        self.assertTrue(script["critic"]["pass"])
        self.assertGreaterEqual(script["word_count"], 80)
        self.assertIn("Mistral's Mixtral design specifies", script["voice_text"])
        self.assertIn("For Mixtral, the model is a sparse mixture-of-experts design", script["voice_text"])

    def test_verified_moe_script_refuses_conflicted_or_outdated_claims(self):
        research = {
            "source_urls": ["https://mistral.ai/news/mixtral-of-experts/"],
            "claims": [
                {
                    "claim": "Mixtral routes every token to two experts.",
                    "quote": "At every layer, for every token, a router network chooses two experts.",
                    "source_url": "https://mistral.ai/news/mixtral-of-experts/",
                    "decision": "research_more",
                    "verification": {"status": "conflicting"},
                },
                {
                    "claim": "Mixtral is a sparse model.",
                    "quote": "Mixtral is a sparse mixture-of-experts model.",
                    "source_url": "https://mistral.ai/news/mixtral-of-experts/",
                    "decision": "research_more",
                    "verification": {"status": "outdated"},
                },
            ],
        }
        self.assertIsNone(script_studio.build_verified_moe_script(
            research, seconds=45, topic="How Mixtral routes experts"
        ))

    def test_critique_rejects_generic_dense_vs_sparse_opening(self):
        script = {
            "title": "How Dense Models Work",
            "voice_text": "Standard models use every parameter for every word. The system processes each token through the network.",
            "hook": "Standard models use every parameter for every word.",
            "source_urls": ["https://example.com/model"],
            "word_count": 18,
            "seconds": 35,
            "slop_score": 0.0,
        }
        result = script_studio.critique(script, research={"claims": []}, topic="Dense models")
        self.assertIn("weak_hook_tension", {item["kind"] for item in result["issues"]})

    def test_critique_rejects_creator_centric_and_vague_mechanism_script(self):
        script = {
            "title": "How Mixture of Experts Works",
            "voice_text": (
                "I read how Mixtral 8x7B works. "
                "A lightweight gating network acts as a manager. "
                "This keeps compute costs low while maintaining a huge knowledge base."
            ),
            "hook": "I read how Mixtral 8x7B works.",
            "source_urls": ["https://example.com/moe"],
            "word_count": 25,
            "seconds": 35,
            "slop_score": 0.0,
        }
        result = script_studio.critique(
            script,
            research={"claims": [{"quote": "A gating network selects experts for each token."}]},
            topic="Mixture of Experts",
        )
        kinds = {item["kind"] for item in result["issues"]}
        self.assertIn("creator_centric_opening", kinds)
        self.assertIn("vague_mechanism_metaphor", kinds)
        self.assertIn("vague_compute_claim", kinds)
        self.assertFalse(result["pass"])

    def test_critique_rejects_source_attribution_and_weak_model_card_cta(self):
        script = {
            "title": "How Mixture of Experts Works",
            "voice_text": (
                "Why do AI models activate only a few experts? "
                "Harsh Agarwal notes that a gating network selects experts for each token. "
                "Check the Mixtral model card to see this in practice."
            ),
            "hook": "Why do AI models activate only a few experts?",
            "source_urls": ["https://example.com/moe"],
            "word_count": 29,
            "seconds": 35,
            "slop_score": 0.0,
        }
        result = script_studio.critique(
            script,
            research={"claims": [{"quote": "A gating network selects experts for each token."}]},
            topic="Mixture of Experts",
        )
        kinds = {item["kind"] for item in result["issues"]}
        self.assertIn("spoken_source_attribution", kinds)
        self.assertIn("weak_model_card_cta", kinds)
        self.assertFalse(result["pass"])

    def test_hook_opening_is_stable_with_abbreviations_decimals_and_punctuation(self):
        cases = [
            ("U.S. AI funding rose 2.5 times. Here is why.", "U.S. AI funding rose 2.5 times."),
            ("AI agents changed the workflow? The evidence is mixed.", "AI agents changed the workflow"),
            ("NIST updated its AI framework. Teams need to adapt.", "NIST updated its AI framework"),
        ]
        for voice_text, hook in cases:
            with self.subTest(voice_text=voice_text):
                self.assertTrue(script_studio._opening_matches_hook(voice_text, hook))
        self.assertFalse(script_studio._opening_matches_hook(
            "The market changed. AI agents are one reason.", "AI agents are one reason"
        ))

    def test_critique_does_not_false_fail_hook_on_decimal_or_abbreviation(self):
        script = {
            "title": "U.S. AI funding",
            "voice_text": "U.S. AI funding rose 2.5 times. The shift is concentrated in applications.",
            "hook": "U.S. AI funding rose 2.5 times.",
            "source_urls": ["https://example.com"],
            "word_count": 14,
            "seconds": 35,
            "slop_score": 0.0,
        }
        result = script_studio.critique(
            script,
            research={"claims": [{"quote": "U.S. AI funding rose 2.5 times"}],
                      "source_urls": ["https://example.com"]},
        )
        self.assertNotIn("hook_position", {item["kind"] for item in result["issues"]})

    def test_beat_sheet_timings_monotonic_and_end_at_duration(self):
        voice_text = "First sentence here. Second sentence follows. Third sentence comes next. Fourth sentence ends it."
        duration = 35.0
        beats = script_studio.build_beat_sheet(voice_text, duration=duration)
        self.assertTrue(len(beats) > 0)
        # Check monotonic
        for i in range(1, len(beats)):
            self.assertGreaterEqual(beats[i]['t_start'], beats[i-1]['t_start'])
            self.assertGreaterEqual(beats[i]['t_end'], beats[i]['t_start'])
        # Ends at duration
        self.assertAlmostEqual(beats[-1]['t_end'], duration, places=1)

    @patch('app.script.studio.multi_model_ai.generate_for_task_json')
    @patch('app.script.studio.multi_model_ai.generate')
    def test_plan_shots_produces_enough_shots_and_sums_correctly(self, mock_generate, mock_generate_json):
        mock_generate_json.return_value = {"best": []}
        mock_generate.return_value = "AI reduces processing time by 40 percent in tests"
        voice_text = "AI reduces processing time by 40 percent in tests. " * 10  # Make it long enough
        beats = script_studio.build_beat_sheet(voice_text, duration=35.0)
        shots = script_studio.plan_shots(beats, duration=35.0, min_shots=8, max_shots=14)
        self.assertGreaterEqual(len(shots), 8)
        total_dur = sum(s['duration'] for s in shots)
        self.assertLessEqual(abs(total_dur - 35.0), 0.35)

    def test_max_shot_merge_preserves_all_narration_claims(self):
        beats = []
        for index in range(16):
            sentence = f"DeepSeek benchmark result number {index} changed the model evaluation."
            beats.append({
                "label": "evidence", "text": sentence,
                "t_start": round(index * 45 / 16, 3),
                "t_end": round((index + 1) * 45 / 16, 3),
                "shot_hint": f"benchmark visual {index}",
            })
        shots = script_studio.plan_shots(
            beats, duration=45.0, min_shots=8, max_shots=14, topic="DeepSeek"
        )
        self.assertEqual(len(shots), 14)
        combined_claims = " ".join(shot.get("claim", "") for shot in shots)
        for beat in beats:
            self.assertIn(beat["text"], combined_claims)

    def test_critique_fails_on_unsupported_number_and_passes_on_clean(self):
        # Unsupported number
        bad_script = {
            'voice_text': 'This gives a ten-fold improvement over baseline.',
            'hook': 'This gives a ten-fold improvement over baseline.',
            'source_urls': ['https://example.com'],
            'word_count': 10,
            'seconds': 35,
            'slop_score': 0.0
        }
        bad_research = {'claims': [{'quote': 'something else entirely', 'source_url': 'https://example.com'}], 'source_urls': ['https://example.com']}
        result_bad = script_studio.critique(bad_script, research=bad_research)
        self.assertFalse(result_bad['pass'])
        self.assertTrue(any(i['kind'] == 'unsupported_number' for i in result_bad['issues']))
        
        # Clean script
        clean_script = {
            'voice_text': 'AI cuts latency by 40 percent in tests. This helps developers save time. The approach works in practice. One limit is that results vary. The payoff is knowing when to use it.',
            'hook': 'AI cuts latency by 40 percent in tests.',
            'source_urls': ['https://example.com'],
            'word_count': 48,
            'seconds': 35,
            'slop_score': 0.0
        }
        clean_research = {'claims': [{'quote': 'The model achieved 40% better efficiency in tests', 'source_url': 'https://example.com'}], 'source_urls': ['https://example.com']}
        result_good = script_studio.critique(clean_script, research=clean_research)
        # May have other issues but not unsupported number
        self.assertFalse(any(i['kind'] == 'unsupported_number' for i in result_good['issues']))

    def test_critique_rejects_script_that_switches_to_another_product(self):
        script = {
            "title": "Kimi K3.1 Pro: 1M Token Context",
            "voice_text": "Kimi K3.1 Pro has a one million token context window.",
            "hook": "Kimi K3.1 Pro has a one million token context window.",
            "source_urls": ["https://example.com/kimi"],
            "word_count": 12,
            "seconds": 35,
            "slop_score": 0.0,
        }
        result = script_studio.critique(
            script,
            research={"claims": [{"quote": "Kimi has one million tokens"}]},
            topic="Using Perplexity Pages to create a shareable research report",
        )
        self.assertIn("off_topic_script", {issue["kind"] for issue in result["issues"]})
        self.assertFalse(result["pass"])

    @patch('app.script.studio.multi_model_ai.generate_for_task_json')
    @patch('app.providers.model_router.generate_for_task')
    @patch('app.script.studio._review_script_editorial_quality')
    def test_critic_loop_stops_after_max_rewrites(self, mock_review, mock_route, mock_generate_json):
        mock_route.return_value = {"text": "AI has one key benefit for developers today."}
        mock_review.return_value = {
            "pass": True, "score": 88,
            "dimensions": {"hook": 4, "clarity": 4, "specificity": 4,
                           "narrative_progression": 4, "insight": 4,
                           "retention": 4, "evidence_alignment": 4},
            "issues": [], "rewrite_instructions": [],
        }
        # First call returns bad script, subsequent calls return better
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "content_pillar": "Hype Check",
                    "hook": "AI has one key benefit for developers today.",
                    "title": "AI Benefit",
                    "voice_text": "AI has one key benefit for developers today. This gives a ten-fold improvement. That changes everything. It cuts processing time by 40 percent according to tests. This helps teams work faster. One limit is setup complexity. The payoff is saved time each day.",  # Has issues
                    "timeline": [{"start": 0, "end": 35, "label": "hook", "narration": "AI has one key benefit for developers today. This gives a ten-fold improvement. That changes everything. It cuts processing time by 40 percent according to tests. This helps teams work faster. One limit is setup complexity. The payoff is saved time each day.", "visual": {"subject": "AI system", "action": "processes a task", "type": "motion_graphic"}, "visual_brief": "A vertical motion graphic showing the AI workflow", "on_screen_text": "AI workflow", "camera": {"shot_size": "medium"}, "transition": "cut", "source_claim_ids": []}],
                    "broll_query": "ai tech",
                    "youtube_tags": ["ai"],
                    "instagram_hashtags": ["#ai"],
                    "platform_copy": {
                        "youtube_description": "AI benefits explained.",
                        "instagram_caption": "A look at AI benefits",
                        "facebook_title": "AI Benefits",
                        "facebook_description": "Understanding AI benefits"
                    },
                    "source_urls": ["https://example.com"]
                }
            else:
                return {
                    "content_pillar": "Hype Check",
                    "hook": "AI has one key benefit for developers today.",
                    "title": "AI Benefit",
                    "voice_text": CLEAN_VOICE_TEXT,
                    "timeline": [{"start": 0, "end": 35, "label": "hook", "narration": CLEAN_VOICE_TEXT, "visual": {"subject": "AI system", "action": "processes a task", "type": "motion_graphic"}, "visual_brief": "A vertical motion graphic showing the AI workflow", "on_screen_text": "AI workflow", "camera": {"shot_size": "medium"}, "transition": "cut", "source_claim_ids": []}],
                    "broll_query": "ai tech",
                    "youtube_tags": ["ai"],
                    "instagram_hashtags": ["#ai"],
                    "platform_copy": {
                        "youtube_description": "AI benefits explained.",
                        "instagram_caption": "A look at AI benefits",
                        "facebook_title": "AI Benefits",
                        "facebook_description": "Understanding AI benefits"
                    },
                    "source_urls": ["https://example.com"]
                }
        mock_generate_json.side_effect = side_effect
        research = {
            "verdict": "sufficient",
            "claims": [{"quote": "The model achieved 40% better efficiency in tests", "source_url": "https://example.com"}],
            "source_urls": ["https://example.com"],
            "summary": "test"
        }
        script = script_studio.write_script("AI benefits", research, seconds=35, max_rewrites=3)
        self.assertIsInstance(script['rewrites'], int)
        self.assertLessEqual(script['rewrites'], 3)

    @patch('app.script.studio.multi_model_ai.generate_for_task_json')
    @patch('app.providers.model_router.generate_for_task')
    @patch('app.script.studio._review_script_editorial_quality')
    def test_report_renders_without_crashing(self, mock_review, mock_route, mock_generate_json):
        mock_route.return_value = {"text": "AI changes how we process data today."}
        mock_review.return_value = {
            "pass": True, "score": 88,
            "dimensions": {"hook": 4, "clarity": 4, "specificity": 4,
                           "narrative_progression": 4, "insight": 4,
                           "retention": 4, "evidence_alignment": 4},
            "issues": [], "rewrite_instructions": [],
        }
        mock_generate_json.return_value = {
            "content_pillar": "How It Works",
            "hook": "AI changes how we process data today.",
            "title": "AI Data Processing",
            "voice_text": CLEAN_VOICE_TEXT,
            "timeline": [{"start": 0, "end": 35, "label": "hook", "narration": CLEAN_VOICE_TEXT, "visual": {"subject": "AI data", "action": "patterns emerge", "type": "motion_graphic"}, "visual_brief": "A vertical data pattern animation", "on_screen_text": "Data patterns", "camera": {"shot_size": "medium"}, "transition": "cut", "source_claim_ids": []}],
            "broll_query": "ai data",
            "youtube_tags": ["ai", "data"],
            "instagram_hashtags": ["#ai"],
            "platform_copy": {
                "youtube_description": "How AI processes data.",
                "instagram_caption": "A look at AI data processing",
                "facebook_title": "AI Data",
                "facebook_description": "Understanding AI data processing"
            },
            "source_urls": ["https://example.com"]
        }
        research = {
            "verdict": "sufficient",
            "claims": [{"quote": "AI uses pattern recognition", "source_url": "https://example.com"}],
            "source_urls": ["https://example.com"],
            "summary": "test"
        }
        script = script_studio.write_script("AI data", research, seconds=35)
        report = script_studio.render_report(script)
        self.assertIsInstance(report, str)
        self.assertTrue(len(report) > 0)


if __name__ == '__main__':
    unittest.main()


def test_moe_beats_generate_topic_specific_visual_queries():
    variants = script_studio.shot_query_variants(
        "How AI Models Activate a Few Experts to Save Compute",
        "A lightweight gating network routes each token to a small set of experts.",
    )
    assert any("mixture of experts" in query for query in variants)
    assert any("router" in query or "token routing" in query for query in variants)
