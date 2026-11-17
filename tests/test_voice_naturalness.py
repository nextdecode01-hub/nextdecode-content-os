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

    def test_silent_provider_is_not_an_automatic_fallback(self):
        with patch.object(provider, "_env", side_effect=lambda key: {
            "TTS_PROVIDER": "edge_tts",
            "TTS_ALLOW_SILENT_FALLBACK": "",
        }.get(key, "")):
            chain = provider._provider_chain("edge_tts")
        self.assertEqual(chain[0], "edge_tts")
        self.assertNotIn("silent", chain)

    def test_silent_provider_requires_explicit_opt_in(self):
        with patch.object(provider, "_env", side_effect=lambda key: {
            "TTS_PROVIDER": "edge_tts",
            "TTS_ALLOW_SILENT_FALLBACK": "true",
        }.get(key, "")):
            chain = provider._provider_chain("edge_tts")
        self.assertEqual(chain[-1], "silent")

    def test_silent_can_be_explicitly_selected_for_diagnostics(self):
        with patch.object(provider, "_env", side_effect=lambda key: {
            "TTS_PROVIDER": "edge_tts",
            "TTS_ALLOW_SILENT_FALLBACK": "true",
        }.get(key, "")):
            chain = provider._provider_chain("silent")
        self.assertEqual(chain[0], "silent")

    def test_synthesize_rejects_near_silent_provider_output(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "silent.mp3"
            def fake_synth(text, target, **kwargs):
                target.write_bytes(b"valid-looking-container")
            with patch.dict(provider._SYNTHESIZERS, {"edge_tts": fake_synth}), \
                 patch.object(provider, "_audio_peak_db", return_value=-91.0):
                result = provider.synthesize("hello", out, provider="edge_tts")
        self.assertIsNone(result["path"])
        self.assertTrue(result["degraded"])
        self.assertIn("near-silent", result["error"])

    def test_synthesize_accepts_audible_provider_output(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "audible.mp3"
            def fake_synth(text, target, **kwargs):
                target.write_bytes(b"valid-looking-container")
            with patch.dict(provider._SYNTHESIZERS, {"edge_tts": fake_synth}), \
                 patch.object(provider, "_audio_peak_db", return_value=-12.0):
                result = provider.synthesize("hello", out, provider="edge_tts")
        self.assertEqual(result["path"], str(out.resolve()))
        self.assertEqual(result["audio_peak_db"], -12.0)

    def test_synthesize_with_fallback_rejects_degraded_provider_output(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "voice.mp3"
            calls = []

            def fake_synthesize(text, target, **kwargs):
                name = kwargs.get("provider")
                calls.append(name)
                if name == "silent":
                    return {"path": str(target), "provider": name,
                            "error": None, "degraded": True}
                return {"path": str(target), "provider": name,
                        "error": None, "degraded": False}

            with patch.object(provider, "_provider_chain", return_value=["silent", "edge_tts"]), \
                 patch.object(provider, "synthesize", side_effect=fake_synthesize):
                result = provider.synthesize_with_fallback("hello", out)

        self.assertEqual(calls, ["silent", "edge_tts"])
        self.assertEqual(result["provider"], "edge_tts")
        self.assertFalse(result["degraded"])

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


class KokoroFallbackTests(unittest.TestCase):
    def test_kokoro_is_the_first_fallback_after_edge_tts(self):
        with patch.object(provider, "_env", side_effect=lambda key, default="": {
            "TTS_ALLOW_SILENT_FALLBACK": "",
            "TTS_ALLOW_LOCAL_MODELS": "true",
        }.get(key, default)):
            chain = provider._provider_chain("edge_tts")
        self.assertEqual(chain[:2], ["edge_tts", "kokoro_local"])
        self.assertNotIn("silent", chain)

    def test_kokoro_fallback_is_used_before_hosted_providers(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "voice.mp3"
            calls = []

            def fake_synthesize(text, target, **kwargs):
                name = kwargs.get("provider")
                calls.append(name)
                if name == "edge_tts":
                    return {"path": None, "provider": name, "error": "network unavailable", "degraded": True}
                return {"path": str(target), "provider": name, "error": None, "degraded": False}

            with (
                patch.object(provider, "synthesize", side_effect=fake_synthesize),
                patch.dict(os.environ, {"TTS_ALLOW_LOCAL_MODELS": "true"}),
            ):
                result = provider.synthesize_with_fallback("hello", out, preferred="edge_tts")

        self.assertEqual(calls, ["edge_tts", "kokoro_local"])
        self.assertEqual(result["provider"], "kokoro_local")
        self.assertFalse(result["degraded"])

    def test_provider_status_exposes_local_kokoro_readiness(self):
        ready = {
            "configured": True,
            "detail": "local Kokoro runtime ready",
        }
        with patch.object(provider, "_kokoro_runtime_status", return_value=ready):
            status = provider.provider_status()
        self.assertTrue(status["kokoro_local"]["configured"])
        self.assertEqual(status["kokoro_local"]["detail"], "local Kokoro runtime ready")


class KokoroChunkingTests(unittest.TestCase):
    def test_local_kokoro_is_disabled_when_local_models_are_not_allowed(self):
        with patch.dict(os.environ, {"TTS_PROVIDER": "edge_tts", "TTS_ALLOW_LOCAL_MODELS": "false"}):
            self.assertNotIn("kokoro_local", provider._provider_chain())
            result = provider.synthesize("Local inference must be blocked.", "unused.mp3", provider="kokoro_local")
        self.assertIsNone(result.get("path"))
        self.assertIn("disabled", result.get("error", "").lower())

    def test_kokoro_default_speed_matches_short_duration_contract(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            script_path = root / "app" / "voice" / "kokoro_local.mjs"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("// test fixture", encoding="utf-8")
            (root / "data" / "cache").mkdir(parents=True)
            out = root / "voice.mp3"
            calls = []
            status = {
                "configured": True,
                "detail": "ready",
                "node": "/usr/bin/node",
                "voice": "af_heart",
                "model_id": "local-kokoro-fixture",
            }

            def fake_run(command, **kwargs):
                if "input" in kwargs:
                    payload = json.loads(kwargs["input"])
                    calls.append(payload["speed"])
                    for chunk_path in Path(payload["output_dir"]).glob("chunk_*.wav"):
                        chunk_path.write_bytes(b"wav")
                    for index in range(len(payload["chunks"])):
                        (Path(payload["output_dir"]) / f"chunk_{index:03d}.wav").write_bytes(b"wav")
                else:
                    Path(command[-1]).write_bytes(b"encoded-audio")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with (
                patch.object(provider, "ROOT", root),
                patch.object(provider, "_kokoro_runtime_status", return_value=status),
                patch.object(provider, "_find_ffmpeg", return_value="/usr/bin/ffmpeg"),
                patch.object(provider.subprocess, "run", side_effect=fake_run),
                patch.object(provider, "_env", side_effect=lambda key, default="": (
                    default if key == "KOKORO_SPEED" else os.getenv(key, default)
                )),
            ):
                provider._synthesize_kokoro_local("A short test narration.", out)

            self.assertEqual(calls, [1.45])
            self.assertTrue(out.is_file())

    def test_local_kokoro_chunks_short_form_script_before_inference(self):
        text = " ".join(
            f"Sentence {index} explains why specialist experts process only selected tokens."
            for index in range(1, 9)
        )
        chunks = provider.chunk_text(text, provider.KOKORO_CHUNK_SIZE)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= provider.KOKORO_CHUNK_SIZE for chunk in chunks))
        self.assertEqual(" ".join(chunks), text)


class FreeNetworkTTSFallbackTests(unittest.TestCase):
    def test_gtts_is_available_after_edge_and_optional_local_kokoro(self):
        with patch.object(provider, "_env", side_effect=lambda key, default="": {
            "TTS_ALLOW_SILENT_FALLBACK": "",
            "TTS_ALLOW_LOCAL_MODELS": "false",
        }.get(key, default)):
            chain = provider._provider_chain("edge_tts")
        self.assertEqual(chain[:2], ["edge_tts", "gtts"])
        self.assertNotIn("silent", chain)

    def test_gtts_is_registered_as_a_real_provider(self):
        self.assertIn("gtts", provider.PROVIDERS)
        self.assertIn("gtts", provider._SYNTHESIZERS)
