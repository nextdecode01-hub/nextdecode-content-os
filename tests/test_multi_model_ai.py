import os
import unittest
from unittest.mock import patch

from app.providers import multi_model_ai as multi_model_ai
from app.script import longform as longform_script
from app.script import short as create_short


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

    def test_retired_providers_are_not_in_active_order(self):
        with patch.dict(os.environ, {"AI_PROVIDER_CHAIN": "omniroute,ollama,gemini,groq"}, clear=True):
            order = multi_model_ai._provider_order()
        self.assertNotIn("omniroute", order)
        self.assertNotIn("ollama", order)
        self.assertIn("gemini", order)
        self.assertIn("groq", order)

    def test_autonomy_mode_fails_closed_without_retired_local_runtime(self):
        with patch.dict(os.environ, {"NEXTDECODE_AUTONOMY_MODE": "true", "AI_HEALTH_GATE": "false"}, clear=True):
            self.assertEqual(multi_model_ai._provider_order(), [])
            with self.assertRaisesRegex(RuntimeError, "no providers are configured"):
                multi_model_ai.generate_json("prompt", temperature=0.4, timeout=5)

    def test_explicit_ollama_selection_uses_only_local_json_provider(self):
        with (
            patch.dict(os.environ, {
                "AI_GENERATION_PROVIDER": "ollama",
                "OLLAMA_MODEL": "qwen2.5-coder:3b",
                "AI_HEALTH_GATE": "false",
            }, clear=True),
            patch.object(multi_model_ai, "call_ollama", return_value='{"title":"Local draft"}') as local,
            patch.object(multi_model_ai, "call_groq") as groq,
            patch.object(multi_model_ai, "call_gemini") as gemini,
        ):
            result = multi_model_ai.generate_json("prompt", temperature=0.25, timeout=120)
        self.assertEqual(result, {"title": "Local draft"})
        local.assert_called_once_with(
            "prompt", model="qwen2.5-coder:3b", temperature=0.25, timeout=120, json_mode=True
        )
        groq.assert_not_called()
        gemini.assert_not_called()

    def test_explicit_ollama_selection_routes_task_json_locally(self):
        with (
            patch.dict(os.environ, {
                "AI_GENERATION_PROVIDER": "ollama",
                "OLLAMA_MODEL": "qwen2.5-coder:3b",
                "AI_HEALTH_GATE": "false",
            }, clear=True),
            patch.object(multi_model_ai, "call_ollama", return_value='{"voice_text":"local"}') as local,
            patch("app.providers.model_router.generate_for_task") as hosted,
        ):
            result = multi_model_ai.generate_for_task_json("script_drafting", "prompt", temperature=0.3, timeout=180)
        self.assertEqual(result["voice_text"], "local")
        self.assertEqual(result["_nextdecode_model_route"]["provider"], "ollama")
        self.assertEqual(result["_nextdecode_model_route"]["execution"], "local")
        local.assert_called_once()
        hosted.assert_not_called()

    def test_explicit_ollama_selection_routes_plain_text_locally(self):
        with (
            patch.dict(os.environ, {"AI_GENERATION_PROVIDER": "ollama", "OLLAMA_MODEL": "qwen2.5-coder:3b"}, clear=True),
            patch.object(multi_model_ai, "call_ollama", return_value="local text") as local,
            patch.object(multi_model_ai, "_auto_text_chain") as hosted,
        ):
            result = multi_model_ai.generate("prompt", timeout=180, temperature=0.2)
        self.assertEqual(result, "local text")
        local.assert_called_once()
        hosted.assert_not_called()

    def test_ollama_is_not_added_to_hosted_auto_fallback(self):
        with patch.dict(os.environ, {"AI_PROVIDER_CHAIN": "ollama,groq"}, clear=True):
            self.assertNotIn("ollama", multi_model_ai._provider_order())

    def test_invalid_provider_json_falls_through_to_groq(self):
        with (
            patch.dict(os.environ, {"AI_PROVIDER_CHAIN": "gemini,groq", "AI_HEALTH_GATE": "false", "GEMINI_API_KEY": "g", "GROQ_API_KEY": "q"}, clear=True),
            patch.object(multi_model_ai, "call_gemini", return_value="not json"),
            patch.object(multi_model_ai, "call_groq", return_value='{"title":"Groq"}') as groq,
        ):
            result = multi_model_ai.generate_json("prompt", temperature=0.4, timeout=30)
        self.assertEqual(result, {"title": "Groq"})
        groq.assert_called_once()

    def test_reports_provider_failures_without_retired_adapters(self):
        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "g", "GROQ_API_KEY": "q", "AI_PROVIDER_CHAIN": "omniroute,ollama,gemini,groq,pollinations_text", "AI_HEALTH_GATE": "false"}, clear=True),
            patch.object(multi_model_ai, "call_gemini", side_effect=TimeoutError),
            patch.object(multi_model_ai, "call_groq", side_effect=RuntimeError),
            patch.object(multi_model_ai, "call_pollinations_text", side_effect=ConnectionError),
        ):
            with self.assertRaisesRegex(RuntimeError, "Gemini TimeoutError, Groq RuntimeError, PollinationsText ConnectionError"):
                multi_model_ai.generate_json("prompt", temperature=0.4, timeout=30)

    def test_short_generator_uses_shared_provider_layer(self):
        source_url = "https://example.com/research"
        research = [{"title": "Example AI research", "url": source_url, "summary": "A verified source."}]
        sentence = "Researchers tested a small tool that turns sketches into simple animations, while the experiment still has limits for real world use."
        voice_text = " ".join([sentence] * 5)
        parsed = {
            "content_pillar": "science_explainer",
            "editorial_angle": "A concrete research prototype shows how sketches can become animations, with current limitations.",
            "viewer_question": "Can a sketch become an animation automatically?",
            "viewer_payoff": "The viewer understands the capability and its current limits.",
            "hook": sentence,
            "title": "A New Way to Animate Sketches",
            "voice_text": voice_text,
            "production_storyboard": [
                {"phase": "hook", "start_seconds": 0, "end_seconds": 15, "narration": sentence,
                 "viewer_purpose": "Show the surprising research capability.",
                 "visual_type": "custom_animation", "visual_action": "A hand-drawn sketch transforms into a simple moving scene.",
                 "asset_search": "research sketch to animation demo", "on_screen_text": "FROM SKETCH TO MOTION",
                 "audio_direction": "Natural narration with a subtle pencil sound.", "edit_direction": "Open on the sketch and match-cut into the animation.",
                 "rights_notes": "Use only an authorized demonstration or create an original illustrative sketch.",
                 "fallback": "Create a clearly labelled original demonstration."},
                {"phase": "evidence", "start_seconds": 15, "end_seconds": 30, "narration": sentence,
                 "viewer_purpose": "Ground the explanation in the research.",
                 "visual_type": "primary_document", "visual_action": "Show the research page and highlight the described method.",
                 "asset_search": "original research paper", "on_screen_text": "WHAT THE RESEARCH SHOWS",
                 "audio_direction": "Narration with music lowered under evidence.", "edit_direction": "Slow document push-in and readable highlight.",
                 "rights_notes": "Link and attribute the original paper; use a limited relevant excerpt.",
                 "fallback": "Use a source-linked citation card."},
                {"phase": "payoff", "start_seconds": 30, "end_seconds": 45, "narration": sentence,
                 "viewer_purpose": "Clarify practical limits and takeaway.",
                 "visual_type": "motion_graphic", "visual_action": "Compare a simple successful output with a labelled limitation card.",
                 "asset_search": "original sketch animation comparison graphic", "on_screen_text": "PROMISING, NOT LIMITLESS",
                 "audio_direction": "Narration resolves with a clean music ending.", "edit_direction": "Split-screen comparison, then decisive cut to end card.",
                 "rights_notes": "Use original graphics and only cleared example assets.",
                 "fallback": "Use a text-led comparison with the limitation stated."}
            ],
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
            patch.object(create_short.multi_model_ai, "generate_for_task_json", return_value=parsed) as generate_json,
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
            patch.object(longform_script, "discover_topics", return_value=research),
            patch.object(longform_script.multi_model_ai, "is_configured", return_value=True),
            patch.object(longform_script, "_fetch_primary_source_text", return_value=source_text),
            patch.object(longform_script, "_collect_research_documents", return_value=[
                {"kind": "primary", "title": "Long-form research topic", "publisher": "Hacker News", "url": source_url, "source_text": source_text},
                {"kind": "independent_secondary", "title": "Independent coverage", "publisher": "Example", "url": "https://independent.example.com/coverage", "source_text": secondary_text},
            ]),
            patch.object(longform_script.multi_model_ai, "generate_json", side_effect=[selection, script]) as generate_json,
        ):
            result = longform_script.generate_script("Long-form research topic")

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
            patch.object(longform_script, "discover_topics", return_value=research),
            patch.object(longform_script.multi_model_ai, "is_configured", return_value=True),
            patch.object(longform_script, "_fetch_primary_source_text", return_value=source_text),
            patch.object(longform_script, "_collect_research_documents", return_value=[
                {"kind": "primary", "title": "Long-form research topic", "publisher": "Hacker News", "url": source_url, "source_text": source_text},
                {"kind": "independent_secondary", "title": "Independent coverage", "publisher": "Example", "url": "https://independent.example.com/coverage", "source_text": secondary_text},
            ]),
            patch.object(longform_script.multi_model_ai, "generate_json", side_effect=[selection, script]) as generate_json,
        ):
            longform_script.generate_script("Long-form research topic")

        self.assertEqual(generate_json.call_args_list[-1].kwargs["timeout"], 600)

    def test_longform_profiles_cover_two_to_ten_minutes(self):
        self.assertEqual(
            {name for name, profile in longform_script.PROFILES.items() if 2 <= profile["minutes"] <= 10},
            {"long_2m", "long_4m", "long_6m", "long_8m", "long_10m"},
        )
        self.assertEqual(longform_script.PROFILES["long_8m"]["minutes"], 8)

    def test_longform_chapters_require_distinct_searchable_visuals(self):
        chapters = [
            {"title": f"Chapter {number}", "start_seconds": number * 60, "broll_query": f"technology scene {number}"}
            for number in range(4)
        ]
        self.assertEqual(len(longform_script._chapter_visuals(chapters)), 4)
        chapters[2]["start_seconds"] = chapters[1]["start_seconds"]
        with self.assertRaisesRegex(RuntimeError, "strictly increasing"):
            longform_script._chapter_visuals(chapters)


if __name__ == "__main__":
    unittest.main()



class GeminiSdkTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_uses_google_genai_client_and_millisecond_timeout(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from google import genai

        response = SimpleNamespace(
            text='{"ok": true}',
            usage_metadata=SimpleNamespace(total_token_count=12),
        )
        client = MagicMock()
        client.models.generate_content.return_value = response
        with patch.object(genai, "Client", return_value=client) as factory:
            result = multi_model_ai.call_gemini(
                "prompt", model="gemini-test", timeout=17, json_mode=True
            )

        self.assertEqual(result, '{"ok": true}')
        factory.assert_called_once()
        self.assertEqual(factory.call_args.kwargs["api_key"], "test-key")
        self.assertEqual(factory.call_args.kwargs["http_options"].timeout, 17000)
        call = client.models.generate_content.call_args.kwargs
        self.assertEqual(call["model"], "gemini-test")
        self.assertEqual(call["contents"], "prompt")
        self.assertEqual(call["config"].response_mime_type, "application/json")
        client.close.assert_called_once()

    def test_rejects_missing_api_key_without_constructing_client(self):
        from google import genai

        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch.object(genai, "Client") as factory:
            with self.assertRaisesRegex(RuntimeError, "Set GEMINI_API_KEY"):
                multi_model_ai.call_gemini("prompt", model="gemini-test")
        factory.assert_not_called()

    def test_falls_through_models_and_reports_failure_types(self):
        from unittest.mock import MagicMock
        from google import genai

        client = MagicMock()
        client.models.generate_content.side_effect = [TimeoutError(), RuntimeError("private detail")]
        with (
            patch.object(multi_model_ai, "gemini_model_chain", return_value=["gemini-a", "gemini-b"]),
            patch.object(genai, "Client", return_value=client),
        ):
            with self.assertRaisesRegex(RuntimeError, "gemini-a TimeoutError, gemini-b RuntimeError"):
                multi_model_ai.call_gemini("prompt")
        self.assertEqual(client.models.generate_content.call_count, 2)
        client.close.assert_called_once()



def test_ollama_requests_have_a_bounded_generation_token_limit():
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "{\"ok\":true}"}, "eval_count": 12}

    with (
        patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://127.0.0.1:11434", "OLLAMA_MODEL": "gemma3:4b"}),
        patch.object(multi_model_ai, "_check_provider_budget"),
        patch.object(multi_model_ai, "_increment_usage"),
        patch.object(multi_model_ai.requests, "post", return_value=FakeResponse()) as post,
    ):
        result = multi_model_ai.call_ollama("bounded prompt", temperature=0.2, timeout=180, json_mode=True)

    assert result == "{\"ok\":true}"
    payload = post.call_args.kwargs["json"]
    assert payload["options"]["num_predict"] == 512
    assert payload["format"] == "json"
    assert post.call_args.kwargs["timeout"] == 180
