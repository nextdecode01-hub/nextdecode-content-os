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

    @patch('app.script.studio.multi_model_ai.generate_json')
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

    @patch('app.script.studio.multi_model_ai.generate_json')
    @patch('app.script.studio.multi_model_ai.generate')
    def test_critic_loop_stops_after_max_rewrites(self, mock_generate, mock_generate_json):
        mock_generate.return_value = "AI has one key benefit for developers today."
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

    @patch('app.script.studio.multi_model_ai.generate_json')
    @patch('app.script.studio.multi_model_ai.generate')
    def test_report_renders_without_crashing(self, mock_generate, mock_generate_json):
        mock_generate.return_value = "AI changes how we process data today."
        mock_generate_json.return_value = {
            "content_pillar": "How It Works",
            "hook": "AI changes how we process data today.",
            "title": "AI Data Processing",
            "voice_text": CLEAN_VOICE_TEXT,
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
