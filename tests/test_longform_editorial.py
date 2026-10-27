import unittest
from pathlib import Path
from unittest.mock import patch

from app.script import longform as longform_script
from pipelines import longform as create_longform


class Response:
    def __init__(self, text, status_code=200, url="https://example.com/paper"):
        self.text = text
        self.status_code = status_code
        self.url = url


def selection_result(selected_id="T1", score=4):
    return {
        "selected_id": selected_id,
        "scores": {
            "viewer_relevance": score,
            "current_interest": score,
            "evidence_quality": score,
            "originality": score,
            "visual_potential": score,
        },
        "reason": "A recent primary source gives a concrete result.",
        "audience": "technology-curious viewers",
        "story_angle": "Explain the result and its limits.",
        "hook_premise": "A specific surprising result from the source.",
    }


class LongformEditorialTests(unittest.TestCase):
    def setUp(self):
        self.research = [
            {
                "title": "AI research on computing",
                "summary": "A primary source describing a measurable AI computing result.",
                "source": "arXiv",
                "url": "https://arxiv.org/abs/1234.5678",
                "published": "2026-10-22T00:00:00Z",
                "rank": 28,
            },
            {
                "title": "Robots in warehouses",
                "summary": "A report on robots and industrial automation.",
                "source": "Hacker News",
                "url": "https://example.com/robots",
                "published": "2026-10-21T00:00:00Z",
                "rank": 20,
            },
        ]

    def test_topic_selection_uses_editorial_scorecard_and_records_it_as_estimate(self):
        with patch.object(longform_script, "recent_topics", return_value="None"), patch(
            "app.script.longform.multi_model_ai.generate_json", return_value=selection_result("T2", 4)
        ) as generate:
            selected, scorecard = longform_script._select_topic(self.research)

        self.assertEqual(selected["url"], "https://example.com/robots")
        self.assertEqual(scorecard["editorial_score"], 80)
        self.assertIn("not measured", scorecard["score_type"])
        prompt = generate.call_args.args[0]
        self.assertIn("Do not invent audience analytics", prompt)
        self.assertIn("AI research on computing", prompt)

    def test_topic_selection_rejects_weak_candidates(self):
        with patch.object(longform_script, "recent_topics", return_value="None"), patch(
            "app.script.longform.multi_model_ai.generate_json", return_value=selection_result(score=2)
        ), self.assertRaisesRegex(RuntimeError, "did not meet|met the editorial bar"):
            longform_script._select_topic(self.research)

    def test_requested_topic_must_be_supported_by_selected_candidate(self):
        with patch.object(longform_script, "recent_topics", return_value="None"), patch(
            "app.script.longform.multi_model_ai.generate_json", return_value=selection_result("T2", 4)
        ), self.assertRaisesRegex(RuntimeError, "does not substantiate"):
            longform_script._select_topic(self.research, "quantum biology")

    def test_primary_source_fetch_prefers_arxiv_full_text_and_excludes_script_content(self):
        source_text = "Detailed paper section and methodology. " * 50
        html = f"<html><script>ignore this text</script><main><h1>Paper</h1><p>{source_text}</p></main></html>"
        with patch(
            "app.script.longform.requests.get",
            return_value=Response(html, url="https://ar5iv.labs.arxiv.org/html/1234.5678"),
        ) as get:
            extracted = longform_script._fetch_primary_source_text("https://arxiv.org/abs/1234.5678")

        self.assertIn("Detailed paper section", extracted)
        self.assertNotIn("ignore this text", extracted)
        self.assertTrue(get.call_args.args[0].endswith("/html/1234.5678"))

    def test_primary_source_fetch_fails_closed_when_page_has_no_readable_content(self):
        with patch(
            "app.script.longform.requests.get", return_value=Response("<html><script>empty</script></html>")
        ), self.assertRaisesRegex(RuntimeError, "refusing an abstract-only script"):
            longform_script._fetch_primary_source_text("https://example.com/paper")

    def test_research_packet_requires_a_relevant_independently_hosted_secondary_source(self):
        selected = {
            "title": "AI consensus research",
            "source": "arXiv",
            "url": "https://arxiv.org/abs/1234.5678",
        }
        secondary = {
            "title": "AI consensus research result explained",
            "summary": "A report on the consensus study.",
            "publisher": "Independent Tech News",
            "url": "https://news.google.com/rss/articles/example",
        }
        with patch("app.script.longform.search_related_news", return_value=[secondary]), patch(
            "app.script.longform._fetch_source_document",
            return_value=("Independent report text " * 100, "https://independent.example.com/story"),
        ):
            documents = longform_script._collect_research_documents(selected, "Primary source text")

        self.assertEqual([doc["kind"] for doc in documents], ["primary", "independent_secondary"])
        self.assertNotEqual(
            documents[0]["url"].split("/")[2],
            documents[1]["url"].split("/")[2],
        )

    def test_script_validation_rejects_mismatched_hook_and_unsupported_quotes(self):
        selected = self.research[0]
        secondary_url = "https://independent.example.com/coverage"
        source_documents = [
            {
                "url": selected["url"],
                "source_text": "The paper measured results across six deployments and reduced latency.",
            },
            {
                "url": secondary_url,
                "source_text": "An independent report describes the measured latency outcome.",
            },
        ]
        parsed = {
            "hook": "A surprising result changed the numbers.",
            "source_urls": [selected["url"], secondary_url],
            "evidence_notes": [
                {
                    "claim": f"Claim {index}",
                    "supporting_quote": (
                        "The paper measured results across six deployments."
                        if index < 2 else "An independent report describes the measured latency outcome."
                    ),
                    "source_url": selected["url"] if index < 2 else secondary_url,
                }
                for index in range(3)
            ],
        }
        with self.assertRaisesRegex(RuntimeError, "first spoken line"):
            longform_script._validate_script(parsed, "The script starts differently.", selected, [selected])

        parsed["hook"] = "A surprising result changed the numbers."
        parsed["evidence_notes"][0]["supporting_quote"] = "An invented result."
        with self.assertRaisesRegex(RuntimeError, "unsupported"):
            longform_script._validate_script(
                parsed,
                parsed["hook"] + " Then the script continues.",
                selected,
                source_documents,
            )

    def test_generate_script_keeps_one_story_and_returns_two_source_evidence_record(self):
        selected = {
            **self.research[0],
            "source_text": (
                "The team tested six deployments with five or nine replicas. "
                "The system reduced mean latency for write-heavy requests. "
                "The authors report an improvement over the fastest baseline."
            ),
        }
        selection = {
            "audience": "technology-curious viewers",
            "story_angle": "Explain the measured result and its limits.",
            "hook_premise": "A clear factual tension.",
            "editorial_score": 80,
            "scores": {},
        }
        hook = "What if computer networks could agree faster?"
        voice_text = hook + " " + " ".join(["The paper reports a measured result and explains the limits."] * 32)
        generated = {
            "title": "Can AI Speed Up Computer Consensus?",
            "hook": hook,
            "voice_text": voice_text,
            "evidence_notes": [
                {
                    "claim": "The evaluation included six deployments.",
                    "supporting_quote": "The team tested six deployments with five or nine replicas.",
                    "source_url": selected["url"],
                },
                {
                    "claim": "The reported measure was latency.",
                    "supporting_quote": "The system reduced mean latency for write-heavy requests.",
                    "source_url": "https://independent.example.com/coverage",
                },
                {
                    "claim": "The authors compared with a baseline.",
                    "supporting_quote": "The authors report an improvement over the fastest baseline.",
                    "source_url": selected["url"],
                },
            ],
            "evidence_gap": "The abstract does not establish results beyond these test conditions.",
            "chapters": [
                {
                    "title": f"Section {index}",
                    "start_seconds": index * 30,
                    "broll_query": f"server room scene {index}",
                    "visual_type": ("network", "process", "comparison", "evidence")[index],
                }
                for index in range(4)
            ],
            "broll_query": "computer network server room",
            "tags": ["AI", "computing"],
            "source_urls": [selected["url"], "https://independent.example.com/coverage"],
            "description": "A source-led explanation.",
            "thumbnail_text": "AI Consensus",
        }
        with patch.object(longform_script, "PROFILE", longform_script.PROFILES["long_2m"]), patch.object(
            longform_script, "PROFILE_NAME", "long_2m"
        ), patch.object(longform_script, "ROOT", Path(".")), patch(
            "app.script.longform.discover_topics", return_value=[*self.research, {
                "title": "Unrelated language model paper",
                "summary": "A separate paper about video models.",
                "source": "arXiv",
                "url": "https://arxiv.org/abs/9999.9999",
                "rank": 99,
            }]
        ), patch("app.script.longform.multi_model_ai.is_configured", return_value=True), patch(
            "app.script.longform._select_topic", return_value=(selected, selection)
        ), patch("app.script.longform._fetch_primary_source_text", return_value=selected["source_text"]), patch(
            "app.script.longform._collect_research_documents",
            return_value=[
                {"kind": "primary", "title": selected["title"], "publisher": "arXiv", "url": selected["url"], "source_text": selected["source_text"]},
                {"kind": "independent_secondary", "title": "Independent coverage", "publisher": "Example", "url": "https://independent.example.com/coverage", "source_text": "The system reduced mean latency for write-heavy requests."},
            ],
        ), patch(
            "app.script.longform.multi_model_ai.generate_json", return_value=generated
        ) as generate:
            result = longform_script.generate_script()

        self.assertEqual(
            result["source_urls"],
            [selected["url"], "https://independent.example.com/coverage"],
        )
        self.assertEqual(len(result["evidence_notes"]), 3)
        self.assertEqual(result["editorial_selection"], selection)
        self.assertEqual(result["research_scope"].startswith("Primary and independent secondary"), True)
        self.assertEqual([chapter["visual_type"] for chapter in result["chapters"]], ["network", "process", "comparison", "evidence"])
        prompt = generate.call_args.args[0]
        self.assertNotIn("Unrelated language model paper", prompt)
        self.assertIn("Retrieved source text", prompt)

    def test_procedural_diagram_layouts_differ_by_story_visual_type(self):
        network_shapes, network_labels = create_longform._motion_diagram_parts("network", "0x37D6E8", 0, 0)
        timeline_shapes, timeline_labels = create_longform._motion_diagram_parts("timeline", "0x37D6E8", 0, 0)
        self.assertNotEqual(network_shapes, timeline_shapes)
        self.assertTrue(any("NODE A" in label for label in network_labels))
        self.assertTrue(any("PAST" in label for label in timeline_labels))


if __name__ == "__main__":
    unittest.main()
