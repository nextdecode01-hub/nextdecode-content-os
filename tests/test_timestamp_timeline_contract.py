import unittest
from app.script.studio import normalize_timestamp_timeline
from app.research.selector import niche_relevance


class TestTimestampTimelineContract(unittest.TestCase):
    def _timeline(self):
        return [
            {"start": 0, "end": 4, "label": "hook", "narration": "Why does this AI agent matter?", "visual": {"subject": "AI agent interface", "action": "agent completes a task", "type": "screen_recording"}, "visual_brief": "Vertical close-up of a real agent task run", "on_screen_text": "Agent at work", "camera": {"shot_size": "close_up"}, "transition": "cut", "source_claim_ids": ["claim-1"]},
            {"start": 4, "end": 8, "label": "payoff", "narration": "The workflow still needs human review.", "visual": {"subject": "review queue", "action": "person approves output", "type": "real_footage"}, "visual_brief": "Reviewer checks output", "on_screen_text": "Human review", "camera": {"shot_size": "medium"}, "transition": "cut", "source_claim_ids": ["claim-2"]},
        ]

    def test_accepts_contiguous_timestamped_beats(self):
        result = normalize_timestamp_timeline(self._timeline(), duration=8, topic="AI agents")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[-1]["t_end"], 8)
        self.assertEqual(result[0]["visual_family"], "screen_recording")

    def test_rejects_gap_or_overlap(self):
        timeline = self._timeline()
        timeline[1]["start"] = 5
        self.assertEqual(normalize_timestamp_timeline(timeline, duration=8), [])

    def test_rejects_chart_without_numeric_evidence_links(self):
        timeline = self._timeline()
        timeline[0]["visual"]["type"] = "chart"
        timeline[0]["chart"] = {"type": "bar", "title": "Growth", "data": [{"label": "A", "value": 4}]}
        timeline[0]["source_claim_ids"] = []
        self.assertEqual(normalize_timestamp_timeline(timeline, duration=8), [])

    def test_rejects_chart_without_numeric_points(self):
        timeline = self._timeline()
        timeline[0]["visual"]["type"] = "chart"
        timeline[0]["chart"] = {"type": "bar", "title": "Growth", "data": [{"label": "A", "value": "high"}]}
        self.assertEqual(normalize_timestamp_timeline(timeline, duration=8), [])


class TestNicheGate(unittest.TestCase):
    def test_core_ai_topic_is_eligible(self):
        self.assertTrue(niche_relevance({"title": "New AI agents automate developer workflows"})["eligible"])

    def test_tangential_topic_is_not_eligible(self):
        result = niche_relevance({"title": "Handwriting as a Font", "summary": "A new lettering trend"})
        self.assertFalse(result["eligible"])
