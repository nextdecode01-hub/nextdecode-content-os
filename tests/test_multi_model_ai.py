import os
import unittest
from unittest.mock import patch

import multi_model_ai
import create_longform
import create_short


class GenerateJsonTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "OMNIROUTE_API_KEY": "test-key",
                "GEMINI_API_KEY": "test-key",
                "GROQ_API_KEY": "test-key",
                "OLLAMA_BASE_URL": "http://localhost:11434",
            },
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def _longform_generation_responses(self, source_url):
        source_text = (
            "A research team tested six deployments with five replicas. "
            "The system reduced mean latency in write-heavy requests. "
            "The authors compared results with the fastest baseline."
        )
        secondary_url = "https://independent.example.com/coverage"
        secondary_text = (
            "An independent technology publication reviewed the consensus result. "
            "Its report describes lower latency in the tested deployments. "
            "It cautions that further evaluation is needed."
        )
        selection = {
            "selected_id": "T1",
            "scores": {
                "viewer_relevance": 4,
                "current_interest": 4,
                "evidence_quality": 4,
                "originality": 4,
                "visual_potential": 4,
            },
            "reason": "The primary source reports a concrete evaluation.",
            "audience": "technology-curious viewers",
            "story_angle": "Explain what was measured and what remains unknown.",
            "hook_premise": "A precise source-backed result.",
        }
        sentence = "A careful long form explanation uses evidence and discusses the limits of this research."
        voice_text = " ".join([sentence] * 72)
        script = {
            "title": "A Careful Long-Form Research Explainer",
            "hook": sentence,
            "voice_text": voice_text,
            "evidence_notes": [
                {
                    "claim": "The evaluation used six deployments.",
                    "supporting_quote": "A research team tested six deployments with five replicas.",
                    "source_url": source_url,
                },
                {
                    "claim": "The reported outcome concerned latency.",
                    "supporting_quote": "An independent technology publication reviewed the consensus result.",
                    "source_url": secondary_url,
                },
                {
                    "claim": "Results were compared to a baseline.",
                    "supporting_quote": "The authors compared results with the fastest baseline.",
                    "source_url": source_url,
                },
            ],
            "evidence_gap": "The source summary does not establish generalization beyond its test conditions.",
            "chapters": [
                {
                    "title": f"Chapter {number}",
                    "start_seconds": number * 60,
                    "broll_query": f"research scene {number}",
                    "visual_type": ("network", "process", "comparison", "evidence")[number],
                }
                for number in range(4)
            ],
            "broll_query": "research technology",
            "tags": ["AI", "research"],
            "source_urls": [source_url, secondary_url],
            "description": "An evidence-based overview.",
            "thumbnail_text": "RESEARCH EXPLAINED",
        }
        return source_text, selection, script, secondary_text

    def test_uses_omniroute_first(self):
        expected = {"title": "OmniRoute"}
        with (
            patch.object(multi_model_ai.omniroute_client, "is_configured", return_value=True),
            patch.object(multi_model_ai.omniroute_client, "generate_json", return_value=expected) as omniroute,
            patch.object(multi_model_ai, "call_gemini") as gemini,
            patch.object(multi_model_ai, "call_groq") as groq,
            patch.object(multi_model_ai, "call_ollama") as ollama,
        ):
            result = multi_model_ai.generate_json("prompt", temperature=0.4, timeout=30)

        self.assertEqual(result, expected)
        omniroute.assert_called_once_with("prompt", 0.4, 30)
        gemini.assert_not_called()
        groq.assert_not_called()
        ollama.assert_not_called()

    def test_selected_ollama_provider_does_not_try_remote_providers(self):
        expected = {"title": "Local model"}
        with (
            patch.dict(os.environ, {"AI_GENERATION_PROVIDER": "ollama"}),
            patch.object(multi_model_ai.omniroute_client, "is_configured", return_value=True),
            patch.object(multi_model_ai.omniroute_client, "generate_json") as omniroute,
            patch.object(multi_model_ai, "call_gemini") as gemini,
            patch.object(multi_model_ai, "call_groq") as groq,
            patch.object(multi_model_ai, "call_ollama", return_value=expected) as ollama,
        ):
            result = multi_model_ai.generate_json("prompt", temperature=0.4, timeout=30)

        self.assertEqual(result, expected)
        ollama.assert_called_once()
        omniroute.assert_not_called()
        gemini.assert_not_called()
        groq.assert_not_called()

    def test_falls_back_to_gemini_after_omniroute_failure(self):
        with (
            patch.object(multi_model_ai.omniroute_client, "is_configured", return_value=True),
            patch.object(multi_model_ai.omniroute_client, "generate_json", side_effect=TimeoutError),
            patch.object(multi_model_ai, "call_gemini", return_value='{"title":"Gemini"}') as gemini,
            patch.object(multi_model_ai, "call_groq") as groq,
        ):
            result = multi_model_ai.generate_json("prompt", temperature=0.4, timeout=30)

        self.assertEqual(result, {"title": "Gemini"})
        gemini.assert_called_once()
        groq.assert_not_called()

    def test_invalid_provider_json_falls_through_to_groq(self):
        with (
            patch.object(multi_model_ai.omniroute_client, "is_configured", return_value=False),
            patch.object(multi_model_ai, "call_gemini", return_value="not json"),
            patch.object(multi_model_ai, "call_groq", return_value='{"title":"Groq"}') as groq,
        ):
            result = multi_model_ai.generate_json("prompt", temperature=0.4, timeout=30)

        self.assertEqual(result, {"title": "Groq"})
        groq.assert_called_once()

    def test_reports_provider_failures_when_all_fallbacks_fail(self):
        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "g", "GROQ_API_KEY": "q"}, clear=True),
            patch.object(multi_model_ai.omniroute_client, "is_configured", return_value=False),
            patch.object(multi_model_ai, "call_gemini", side_effect=TimeoutError),
            patch.object(multi_model_ai, "call_groq", side_effect=RuntimeError),
            patch.object(multi_model_ai, "call_pollinations_text", side_effect=RuntimeError("pollinations down")),
            patch.object(multi_model_ai, "call_ollama", side_effect=ConnectionError),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Gemini TimeoutError, Groq RuntimeError, PollinationsText RuntimeError, Ollama ConnectionError",
            ):
                multi_model_ai.generate_json("prompt", temperature=0.4, timeout=30)

    def test_short_generator_uses_shared_provider_layer(self):
        source_url = "https://example.com/research"
        research = [{"title": "Example AI research", "url": source_url, "summary": "A verified source."}]
        sentence = "Researchers tested a small tool that turns sketches into simple animations, while the experiment still has limits for real world use."
        voice_text = " ".join([sentence] * 4)
        parsed = {
            "content_pillar": "How It Works",
            "hook": sentence,
            "title": "A New Way to Animate Sketches",
            "voice_text": voice_text,
            "broll_query": "animation sketches",
            "youtube_tags": ["AI", "technology"],
            "instagram_hashtags": ["#AI", "#Tech"],
            "source_urls": [source_url],
            "platform_copy": {
                "youtube_description": "A short explanation of a research prototype.",
                "instagram_caption": "A new research prototype explores sketch animation.",
                "facebook_title": "Sketch Animation Research",
                "facebook_description": "What could this enable?",
            },
        }
        with (
            patch.object(create_short, "discover_topics", return_value=research),
            patch.object(create_short.multi_model_ai, "is_configured", return_value=True),
            patch.object(create_short.multi_model_ai, "generate_json", return_value=parsed) as generate_json,
        ):
            result = create_short.generate_script("Example AI research")

        self.assertEqual(result["title"], parsed["title"])
        generate_json.assert_called_once()
        self.assertEqual(generate_json.call_args.kwargs["temperature"], 0.65)

    def test_longform_generator_uses_shared_provider_layer(self):
        source_url = "https://example.com/longform-research"
        research = [{
            "title": "Long-form research topic",
            "url": source_url,
            "summary": "A verified source.",
            "source": "Hacker News",
        }]
        source_text, selection, script, secondary_text = self._longform_generation_responses(source_url)
        with (
            patch.object(create_longform, "discover_topics", return_value=research),
            patch.object(create_longform.multi_model_ai, "is_configured", return_value=True),
            patch.object(create_longform, "_fetch_primary_source_text", return_value=source_text),
            patch.object(create_longform, "_collect_research_documents", return_value=[
                {"kind": "primary", "title": "Long-form research topic", "publisher": "Hacker News", "url": source_url, "source_text": source_text},
                {"kind": "independent_secondary", "title": "Independent coverage", "publisher": "Example", "url": "https://independent.example.com/coverage", "source_text": secondary_text},
            ]),
            patch.object(create_longform.multi_model_ai, "generate_json", side_effect=[selection, script]) as generate_json,
        ):
            result = create_longform.generate_script("Long-form research topic")

        self.assertEqual(result["title"], script["title"])
        self.assertEqual(result["editorial_selection"]["editorial_score"], 80)
        self.assertEqual(generate_json.call_count, 2)
        self.assertEqual(generate_json.call_args.kwargs["temperature"], 0.35)

    def test_longform_local_provider_gets_extended_generation_timeout(self):
        source_url = "https://example.com/longform-research"
        research = [{
            "title": "Long-form research topic",
            "url": source_url,
            "summary": "A verified source.",
            "source": "Hacker News",
        }]
        source_text, selection, script, secondary_text = self._longform_generation_responses(source_url)
        with (
            patch.dict(os.environ, {"AI_GENERATION_PROVIDER": "ollama"}),
            patch.object(create_longform, "discover_topics", return_value=research),
            patch.object(create_longform.multi_model_ai, "is_configured", return_value=True),
            patch.object(create_longform, "_fetch_primary_source_text", return_value=source_text),
            patch.object(create_longform, "_collect_research_documents", return_value=[
                {"kind": "primary", "title": "Long-form research topic", "publisher": "Hacker News", "url": source_url, "source_text": source_text},
                {"kind": "independent_secondary", "title": "Independent coverage", "publisher": "Example", "url": "https://independent.example.com/coverage", "source_text": secondary_text},
            ]),
            patch.object(create_longform.multi_model_ai, "generate_json", side_effect=[selection, script]) as generate_json,
        ):
            create_longform.generate_script("Long-form research topic")

        self.assertEqual(generate_json.call_args_list[-1].kwargs["timeout"], 600)

    def test_longform_profiles_cover_two_to_ten_minutes(self):
        self.assertEqual(
            {name for name, profile in create_longform.PROFILES.items() if 2 <= profile["minutes"] <= 10},
            {"long_2m", "long_4m", "long_6m", "long_8m", "long_10m"},
        )
        self.assertEqual(create_longform.PROFILES["long_8m"]["minutes"], 8)

    def test_longform_chapters_require_distinct_searchable_visuals(self):
        chapters = [
            {"title": f"Chapter {number}", "start_seconds": number * 60, "broll_query": f"technology scene {number}"}
            for number in range(4)
        ]
        self.assertEqual(len(create_longform._chapter_visuals(chapters)), 4)
        chapters[2]["start_seconds"] = chapters[1]["start_seconds"]
        with self.assertRaisesRegex(RuntimeError, "strictly increasing"):
            create_longform._chapter_visuals(chapters)


if __name__ == "__main__":
    unittest.main()
