#!/usr/bin/env python3
"""Tests for the strong editorial pipeline and its supporting modules."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.providers import model_health as model_health
from app.visuals import motion_director as motion_director
from app.script import studio as script_studio
from app.visuals import stock_fetcher as stock_fetcher
from app.script import pipeline as strong_pipeline


class TestAssetQueryBuilding(unittest.TestCase):
    def test_script_punctuation_corruption_is_repaired_before_speech(self):
        result = strong_pipeline._normalize_script_punctuation({
            "voice_text": "Can agents research?or not? DeepMind?s system works; today?s test.",
            "word_count": 99,
        })
        self.assertEqual(
            result["voice_text"],
            "Can agents research? or not? DeepMind's system works; today's test.",
        )
        self.assertEqual(result["word_count"], len(result["voice_text"].split()))

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


class TestScriptFailureSafety(unittest.TestCase):
    def test_automatic_script_mode_fails_closed_when_writer_is_unavailable(self):
        research = {
            "topic": "AI research agents",
            "verdict": "sufficient",
            "claims": [{"claim": "A verified research claim.", "quote": "A verified research claim.",
                        "source_url": "https://example.com/report"}],
        }
        with patch.dict("os.environ", {"NEXTDECODE_SCRIPT_MODE": "auto"}, clear=False), \
             patch.object(strong_pipeline.script_studio, "write_script",
                          side_effect=RuntimeError("provider unavailable")):
            with self.assertRaisesRegex(RuntimeError, "automatic deterministic fallback is disabled"):
                strong_pipeline._draft_script("AI research agents", research, 45)

    def test_evidence_reconciliation_does_not_keep_an_unreviewed_script(self):
        import tempfile
        ledger = {
            "claims": [],
            "script_mapping": {
                "flags": [{
                    "flag": "unqualified_partially_supported",
                    "sentence": "A single-source claim was stated as fact.",
                }]
            },
        }
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(strong_pipeline.claims_ledger, "build_ledger", return_value=ledger), \
             patch.object(strong_pipeline.script_studio, "write_script",
                          side_effect=RuntimeError("rewrite unavailable")):
            with self.assertRaisesRegex(RuntimeError, "refusing to continue with unresolved claims"):
                strong_pipeline._build_evidence_checked_script(
                    "AI research agents", {"claims": []}, {"claims": []},
                    {"voice_text": "A single-source claim was stated as fact."},
                    45, Path(tmp),
                )


class TestEditorialScriptReview(unittest.TestCase):
    def test_qualified_editorial_review_accepts_complete_high_score(self):
        from app.script import studio
        review = {
            "pass": True,
            "score": 88,
            "dimensions": {
                "hook": 4, "clarity": 4, "specificity": 4,
                "narrative_progression": 4, "insight": 4,
                "retention": 4, "evidence_alignment": 4,
            },
            "issues": [],
            "rewrite_instructions": [],
        }
        with patch.object(studio.multi_model_ai, "generate_for_task_json", return_value=review) as judge:
            result = studio._review_script_editorial_quality(
                "AI research agents",
                {"title": "How research agents check claims", "voice_text": "A specific hook. A clear mechanism."},
                {"claims": []},
                45,
            )
        self.assertTrue(result["pass"])
        self.assertEqual(result["score"], 88)
        judge.assert_called_once()
        self.assertEqual(judge.call_args.args[0], "script_review")

    def test_editorial_review_rejects_a_low_dimension_even_when_model_says_pass(self):
        from app.script import studio
        review = {
            "pass": True,
            "score": 91,
            "dimensions": {
                "hook": 4, "clarity": 4, "specificity": 2,
                "narrative_progression": 4, "insight": 4,
                "retention": 4, "evidence_alignment": 4,
            },
            "issues": ["The script is too generic."],
            "rewrite_instructions": ["Add a concrete example."],
        }
        with patch.object(studio.multi_model_ai, "generate_for_task_json", return_value=review):
            result = studio._review_script_editorial_quality(
                "AI research agents", {"title": "Generic", "voice_text": "Generic script."},
                {"claims": []}, 45,
            )
        self.assertFalse(result["pass"])
        self.assertTrue(result["rewrite_instructions"])

    def test_editorial_review_rejects_incomplete_dimension_scores(self):
        from app.script import studio
        with patch.object(studio.multi_model_ai, "generate_for_task_json", return_value={
            "pass": True, "score": 90, "dimensions": {"hook": 5}, "issues": [],
        }):
            with self.assertRaisesRegex(RuntimeError, "omitted its dimension scores|invalid clarity score"):
                studio._review_script_editorial_quality(
                    "AI research agents", {"title": "Test", "voice_text": "Test."},
                    {"claims": []}, 45,
                )


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


class TestProviderQuotaFreshness(unittest.TestCase):
    def test_stale_quota_snapshot_is_unknown_not_available(self):
        import json
        import tempfile
        from datetime import datetime, timedelta, timezone
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "quota.json"
            stale = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
            path.write_text(json.dumps({"checked_at": stale, "providers": {
                "groq": {"models": {"m1": {"checked_at": stale, "headers": {
                    "x-ratelimit-remaining-tokens": "7000",
                    "x-ratelimit-limit-tokens": "8000",
                }}}}
            }}))
            self.assertEqual(model_health.quota_status("groq", model="m1", path=path), "unknown")

    def test_fresh_provider_reported_quota_can_be_available_or_low(self):
        import json
        import tempfile
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "quota.json"
            checked = datetime.now(timezone.utc).isoformat()
            path.write_text(json.dumps({"checked_at": checked, "providers": {
                "groq": {"models": {
                    "available-model": {"checked_at": checked, "headers": {
                        "x-ratelimit-remaining-tokens": "7000",
                        "x-ratelimit-limit-tokens": "8000",
                    }},
                    "low-model": {"checked_at": checked, "headers": {
                        "x-ratelimit-remaining-tokens": "500",
                        "x-ratelimit-limit-tokens": "8000",
                    }},
                }}
            }}))
            self.assertEqual(model_health.quota_status("groq", model="available-model", path=path), "available")
            self.assertEqual(model_health.quota_status("groq", model="low-model", path=path), "low")


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


class TestMoETopicNormalization(unittest.TestCase):
    def test_hyphenated_mixture_of_experts_topic_gets_primary_sources(self):
        urls = strong_pipeline._candidate_urls(
            {"topic": "How mixture-of-experts models route tokens"}, []
        )
        self.assertIn("https://mistral.ai/news/mixtral-of-experts/", urls)
        self.assertIn("https://huggingface.co/blog/mixtral", urls)
        self.assertIn("https://arxiv.org/abs/2401.04088", urls)

    def test_hyphenated_mixture_of_experts_topic_gets_exact_primary_claim(self):
        topic = "How mixture-of-experts models route tokens"
        url = "https://mistral.ai/news/mixtral-of-experts/"
        excerpt = (
            'At every layer, for every token, a router network chooses two of these groups '
            '(the "experts") to process the token and combine their output additively.'
        )
        research = {"topic": topic, "sources": [{"url": url, "text": excerpt}], "claims": []}
        result = strong_pipeline._augment_primary_moe_claims(topic, research)
        self.assertEqual(len(result["claims"]), 1)
        self.assertEqual(result["claims"][0]["source_url"], url)
        self.assertIn("two experts", result["claims"][0]["claim"])


class TestPinnedResearchSources(unittest.TestCase):
    def test_explicit_research_urls_are_added_without_replacing_topic_sources(self):
        urls = (
            "https://arxiv.org/abs/2607.27191;"
            "https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/"
        )
        with patch.dict("os.environ", {"NEXTDECODE_RESEARCH_SOURCE_URLS": urls}):
            result = strong_pipeline._candidate_urls(
                {"topic": "Can AI agents conduct open-ended AI research?"},
                [{"url": "https://www.natureasia.com/en/info/press-releases/detail/9330"}],
            )
        self.assertEqual(result[0], "https://arxiv.org/abs/2607.27191")
        self.assertIn("https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/", result)
        self.assertIn("https://www.natureasia.com/en/info/press-releases/detail/9330", result)

class TestTopicScopedResearchEvidenceBundle(unittest.TestCase):
    def test_non_moe_topic_can_use_fetched_verbatim_qualified_claims(self):
        topic = "Does AI accelerate AI research?"
        url = "https://deepmind.google/discover/blog/ai-research/"
        source_text = "AI tools can assist researchers with selected workflows and tasks."
        supported = {
            "claim_id": "clm_supported", "narration": "AI tools assist selected research tasks.",
            "quote": "AI tools can assist researchers with selected workflows and tasks.",
            "source_url": url, "verification": {"status": "supported"},
            "decision": "include", "excerpt_offset": 0,
        }
        qualified = {
            "claim_id": "clm_qualified", "narration": "The report describes a limited pilot.",
            "quote": "AI tools can assist researchers with selected workflows and tasks.",
            "source_url": url, "verification": {"status": "partially_supported"},
            "decision": "qualify", "excerpt_offset": 0,
        }
        unverified = {
            "claim_id": "clm_unverified", "narration": "AI replaces every researcher.",
            "quote": "not in source", "source_url": url,
            "verification": {"status": "unverified"}, "decision": "exclude",
            "excerpt_offset": None,
        }
        ledger = {"claims": [supported, qualified, unverified]}
        research = {"topic": topic, "sources": [{"url": url, "text": source_text}],
                    "claims": [{"claim": supported["narration"], "quote": supported["quote"], "source_url": url}]}
        with patch.object(strong_pipeline.claims_ledger, "build_ledger", return_value=ledger):
            result = strong_pipeline._script_research_bundle(research)
        self.assertEqual({item["claim_id"] for item in result["claims"]}, {"clm_supported", "clm_qualified"})
        self.assertEqual([item["claim_id"] for item in result["qualified_claims"]], ["clm_qualified"])
        self.assertEqual(result["source_urls"], [url])

    def test_non_moe_topic_does_not_admit_unfetched_or_nonverbatim_qualified_claims(self):
        topic = "AI research tools"
        fetched_url = "https://example.org/research"
        other_url = "https://other.example/research"
        claim = {
            "claim_id": "clm_bad", "narration": "A claim without a located excerpt.",
            "quote": "not found", "source_url": other_url,
            "verification": {"status": "partially_supported"}, "decision": "qualify",
            "excerpt_offset": None,
        }
        with patch.object(strong_pipeline.claims_ledger, "build_ledger", return_value={"claims": [claim]}):
            with self.assertRaisesRegex(RuntimeError, "No supported research claims"):
                strong_pipeline._script_research_bundle({"topic": topic,
                    "sources": [{"url": fetched_url, "text": "A source with unrelated content."}],
                    "claims": []})


if __name__ == "__main__":
    unittest.main()
