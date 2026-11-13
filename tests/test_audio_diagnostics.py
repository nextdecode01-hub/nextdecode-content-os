import math
import random
import subprocess
import tempfile
import unittest
import wave
from array import array
from pathlib import Path

from app.render import audio_diagnostics, ffmpeg_tools

SAMPLE_RATE = 44100


def _write_tone(path: Path, seconds: float = 4.0,
                burst: tuple[float, float] | None = None) -> Path:
    """220 Hz tone, optionally with a white-noise whoosh in a time window."""
    rng = random.Random(7)
    samples = array("h")
    for index in range(int(seconds * SAMPLE_RATE)):
        t = index / SAMPLE_RATE
        value = 0.15 * math.sin(2 * math.pi * 220 * t)
        if burst and burst[0] <= t < burst[1]:
            value += 0.20 * rng.uniform(-1.0, 1.0)
        samples.append(int(max(-1.0, min(1.0, value)) * 32767))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(samples.tobytes())
    return path


class BoundaryDiagnosticTests(unittest.TestCase):
    def test_clean_tone_has_no_flagged_cut(self):
        with tempfile.TemporaryDirectory() as td:
            path = _write_tone(Path(td) / "clean.wav")
            result = audio_diagnostics.analyze_boundaries(path, [2.0])
        self.assertTrue(result["checked"])
        self.assertEqual(result["boundary_count"], 1)
        self.assertEqual(result["flagged"], 0)
        self.assertEqual(result["status"], "pass")

    def test_noise_whoosh_after_cut_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            path = _write_tone(Path(td) / "whoosh.wav", burst=(2.0, 2.7))
            result = audio_diagnostics.analyze_boundaries(path, [2.0])
        self.assertTrue(result["checked"])
        self.assertEqual(result["flagged"], 1)
        boundary = result["boundaries"][0]
        self.assertTrue(boundary["burst_like"])
        self.assertGreater(boundary["hf_excess_db"], audio_diagnostics.HF_EXCESS_DB)
        self.assertEqual(result["status"], "warning")

    def test_abrupt_speech_like_onset_is_not_a_click(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "speech_onset.wav"
            samples = array("h")
            for index in range(int(4.0 * SAMPLE_RATE)):
                t = index / SAMPLE_RATE
                value = 0.0
                if t >= 2.0:
                    value = 0.30 * math.sin(2 * math.pi * 180 * t)
                samples.append(int(value * 32767))
            with wave.open(str(path), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(SAMPLE_RATE)
                handle.writeframes(samples.tobytes())
            result = audio_diagnostics.analyze_boundaries(path, [2.0])
        self.assertEqual(result["flagged"], 0)
        self.assertGreater(result["boundaries"][0]["onset_ratio"], 6.0)

    def test_mix_without_sfx_is_clean_and_sfx_regresses(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            voice = _write_tone(work / "voice.wav")
            clean = ffmpeg_tools._mix_audio([], voice, work, -15.0, None, [])
            clean_result = audio_diagnostics.analyze_boundaries(clean, [2.0])
            self.assertEqual(clean_result["flagged"], 0)

            # The detector must still catch a hard transient on a cut.  The old
            # white-noise whoosh is written out here as the known-bad reference;
            # Phase 9 replaced that recipe with a band-limited pink whoosh.
            harsh = work / "sfx_harsh.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                 "-i", "anoisesrc=duration=0.7:color=white",
                 "-af", "highpass=f=900", "-ar", str(SAMPLE_RATE), str(harsh)],
                check=True,
            )
            noisy = ffmpeg_tools._mix_audio(
                [], voice, work, -15.0, None, [(2.0, harsh)]
            )
            noisy_result = audio_diagnostics.analyze_boundaries(noisy, [2.0])
            self.assertEqual(noisy_result["flagged"], 1)
            self.assertTrue(noisy_result["boundaries"][0]["burst_like"])

    def test_phase9_sfx_are_band_limited_and_not_flagged(self):
        """The softened SFX must not read as a click at a cut."""
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            voice = _write_tone(work / "voice.wav")
            for kind in ("whoosh", "impact", "riser"):
                path = ffmpeg_tools.synthesize_sfx(kind, work)
                self.assertIsNotNone(path, f"{kind} failed to render")
                mixed = ffmpeg_tools._mix_audio(
                    [], voice, work, -15.0, None, [(2.0, path)]
                )
                result = audio_diagnostics.analyze_boundaries(mixed, [2.0])
                self.assertEqual(result["flagged"], 0, f"{kind} still clicks at the cut")


if __name__ == "__main__":
    unittest.main()
