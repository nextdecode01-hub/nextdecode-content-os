import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.voice import provider, text_prep


class SpeechTextTests(unittest.TestCase):
    def test_normalizes_numbers_acronyms_and_abbreviations(self):
        result = text_prep.normalize_for_speech(
            "AI catches 84% of N+1 queries, e.g. SQL loops & API misuse."
        )
        self.assertIn("84 percent", result)
        self.assertIn("N plus one", result)
        self.assertIn("for example", result)
        self.assertIn("S Q L", result)
        self.assertIn("A P I", result)
        self.assertIn(" and ", result)
        self.assertNotIn("84%", result)
        self.assertNotIn("N+1", result)

    def test_long_sentence_splits_without_dropping_words(self):
        sentence = (
            "AI review is useful because it catches common mistakes, but it still "
            "misses the system context that explains why the code exists and why "
            "the database query runs inside a loop for every request."
        )
        split = text_prep.split_long_sentences(sentence, max_words=24)
        self.assertGreaterEqual(split.count("."), 2)
        self.assertIn("but it still misses", split.lower())
        original_words = [word.lower().strip(",.") for word in sentence.split()]
        split_words = [word.lower().strip(",.") for word in split.split()]
        self.assertEqual(original_words, split_words)

    def test_short_sentences_are_left_alone(self):
        sentence = "AI review catches style issues in seconds."
        self.assertEqual(text_prep.split_long_sentences(sentence), sentence)

    def test_paragraph_breaks_survive_preparation(self):
        text = "First paragraph with 84% accuracy.\n\nSecond paragraph, e.g. SQL checks."
        prepared = text_prep.prepare_narration(text)
        self.assertIn("\n\n", prepared)
        self.assertIn("84 percent", prepared)
        self.assertIn("for example", prepared)
        self.assertEqual(prepared, text_prep.prepare_narration(prepared))

    def test_script_hash_is_stable(self):
        self.assertEqual(
            text_prep.script_sha256("same script"), text_prep.script_sha256("same script")
        )
        self.assertNotEqual(
            text_prep.script_sha256("one"), text_prep.script_sha256("two")
        )


class EdgeProsodyTests(unittest.TestCase):
    def test_default_prosody_is_neutral(self):
        with patch.dict(os.environ, {"TTS_RATE": "", "TTS_PITCH": "", "TTS_VOLUME": ""}):
            prosody = provider._edge_prosody()
        self.assertEqual(prosody, {"rate": "+0%", "pitch": "+0Hz", "volume": "+0%"})

    def test_environment_values_are_used(self):
        with patch.dict(
            os.environ,
            {"TTS_RATE": "-4%", "TTS_PITCH": "+0Hz", "TTS_VOLUME": "+0%"},
        ):
            prosody = provider._edge_prosody()
        self.assertEqual(prosody["rate"], "-4%")

    def test_invalid_values_fall_back_to_neutral(self):
        with patch.dict(os.environ, {"TTS_RATE": "fast", "TTS_PITCH": "low"}):
            prosody = provider._edge_prosody()
        self.assertEqual(prosody["rate"], "+0%")
        self.assertEqual(prosody["pitch"], "+0Hz")

    def test_edge_command_carries_voice_and_prosody(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "sample.mp3"
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                Path(command[command.index("--write-media") + 1]).write_bytes(b"x" * 256)
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch.object(provider, "_find_edge_tts", return_value="/usr/bin/edge-tts"), patch.object(
                provider.subprocess, "run", side_effect=fake_run
            ):
                provider._synthesize_edge_tts(
                    "hello", out,
                    voice="en-US-AndrewMultilingualNeural",
                    rate="-4%", pitch="+0Hz", volume="+0%",
                )

        command = calls[0]
        self.assertIn("en-US-AndrewMultilingualNeural", command)
        self.assertEqual(command[command.index("--rate") + 1], "-4%")
        self.assertEqual(command[command.index("--pitch") + 1], "+0Hz")
        self.assertEqual(command[command.index("--volume") + 1], "+0%")

    def test_synthesize_with_fallback_does_not_send_edge_voice_to_paid_provider(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "sample.mp3"
            calls = []

            def fake_synthesize(text, target, **kwargs):
                calls.append(kwargs)
                if kwargs.get("provider") == "edge_tts":
                    return {"path": None, "provider": "edge_tts", "error": "offline"}
                return {"path": str(target), "provider": kwargs.get("provider"), "error": None}

            with patch.object(provider, "synthesize", side_effect=fake_synthesize):
                provider.synthesize_with_fallback(
                    "hello", out, preferred="edge_tts",
                    voice="en-US-AndrewMultilingualNeural", rate="-4%",
                )

        paid = [call for call in calls if call.get("provider") != "edge_tts"]
        self.assertTrue(paid)
        for call in paid:
            self.assertNotIn("voice", call)
            self.assertNotIn("rate", call)


class VoicePipelinePrepTests(unittest.TestCase):
    def test_generate_voice_applies_opt_in_text_prep(self):
        from app.script import pipeline

        captured = {}

        def fake_synthesize(text, path, **kwargs):
            captured["text"] = text
            captured["voice"] = kwargs.get("voice")
            return {"path": str(path), "provider": "edge_tts", "duration_hint": 1.0}

        with patch.dict(os.environ, {"TTS_TEXT_PREP": "on", "TTS_VOICE": "en-US-AndrewMultilingualNeural"}), patch.object(
            pipeline.voice_provider, "synthesize_with_fallback", side_effect=fake_synthesize
        ):
            pipeline.generate_voice(
                "AI catches 84% of N+1 queries.", Path("/tmp/voice_prep_test.mp3")
            )

        self.assertIn("84 percent", captured["text"])
        self.assertIn("N plus one", captured["text"])
        self.assertEqual(captured["voice"], "en-US-AndrewMultilingualNeural")

    def test_text_prep_is_off_by_default(self):
        from app.script import pipeline

        captured = {}

        def fake_synthesize(text, path, **kwargs):
            captured["text"] = text
            return {"path": str(path), "provider": "edge_tts", "duration_hint": 1.0}

        with patch.dict(os.environ, {"TTS_TEXT_PREP": "", "TTS_VOICE": ""}), patch.object(
            pipeline.voice_provider, "synthesize_with_fallback", side_effect=fake_synthesize
        ):
            pipeline.generate_voice("AI catches 84% of N+1 queries.", Path("/tmp/voice_prep_off.mp3"))

        self.assertEqual(captured["text"], "AI catches 84% of N+1 queries.")


if __name__ == "__main__":
    unittest.main()
