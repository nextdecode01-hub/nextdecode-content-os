"""Phase 9 regression tests: export quality, voice-first mixing, clipping safety.

The measurements these tests encode:
- Edge TTS renders 24 kHz / 48 kbps mono mp3; that is the source ceiling.
- Reusing the voice pad for the ducking sidechain cost ~6 dB of narration level
  in every bed mix, so the mix now uses ``asplit``.
- ``alimiter`` defaults to automatic level detection, which *raises* the summed
  mix to 0.0 dBTP; ``level=false`` holds the ceiling instead.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.render import ffmpeg_tools
from app.voice import provider

ROOT = Path(__file__).resolve().parents[1]
HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def _loudnorm_filter(**kwargs):
    """Patch the measurement pass so filter-graph tests stay fast."""
    return patch.object(ffmpeg_tools, "_measure_loudnorm", return_value="loudnorm=I=-16:TP=-1.5:LRA=11")


class VoiceSelectionTests(unittest.TestCase):
    def test_approved_voice_is_the_default(self):
        self.assertEqual(provider.DEFAULT_VOICE, "en-US-AndrewMultilingualNeural")

    def test_environment_still_overrides_the_voice(self):
        with tempfile.TemporaryDirectory() as td:
            captured = {}

            def fake_run(cmd, *args, **kwargs):
                captured["cmd"] = cmd
                Path(cmd[cmd.index("--write-media") + 1]).write_bytes(b"x")
                return subprocess.CompletedProcess(cmd, 0, "", "")

            env = {"TTS_VOICE": "en-US-GuyNeural", "TTS_RATE": "", "TTS_PITCH": "", "TTS_VOLUME": ""}
            with patch.dict(os.environ, env), \
                    patch.object(provider, "_find_edge_tts", return_value="edge-tts"), \
                    patch.object(provider.subprocess, "run", side_effect=fake_run):
                provider._synthesize_edge_tts("hello", Path(td) / "out.mp3")
            self.assertEqual(captured["cmd"][captured["cmd"].index("--voice") + 1],
                             "en-US-GuyNeural")

    def test_default_voice_is_used_when_env_is_blank(self):
        with tempfile.TemporaryDirectory() as td:
            captured = {}

            def fake_run(cmd, *args, **kwargs):
                captured["cmd"] = cmd
                Path(cmd[cmd.index("--write-media") + 1]).write_bytes(b"x")
                return subprocess.CompletedProcess(cmd, 0, "", "")

            env = {"TTS_VOICE": "", "TTS_RATE": "", "TTS_PITCH": "", "TTS_VOLUME": ""}
            with patch.dict(os.environ, env), \
                    patch.object(provider, "_find_edge_tts", return_value="edge-tts"), \
                    patch.object(provider.subprocess, "run", side_effect=fake_run):
                provider._synthesize_edge_tts("hello", Path(td) / "out.mp3")
            self.assertEqual(captured["cmd"][captured["cmd"].index("--voice") + 1],
                             provider.DEFAULT_VOICE)


class SourceFormatTests(unittest.TestCase):
    def test_edge_tts_output_format_is_recorded(self):
        info = provider.probe_audio_format(ROOT / "outputs" / "phase8_demos" / "demo 1_raw.mp3")
        if not HAS_FFMPEG or not info:
            self.skipTest("ffmpeg or the Phase 8 demo is unavailable")
        # Documents the ceiling: 24 kHz mono, 48 kbps.
        self.assertEqual(info["codec"], "mp3")
        self.assertEqual(str(info["sample_rate"]), "24000")
        self.assertEqual(str(info["channels"]), "1")

    def test_probe_of_missing_file_is_empty(self):
        self.assertEqual(provider.probe_audio_format("nope.mp3"), {})


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required")
class MasterChainTests(unittest.TestCase):
    def _voice(self, work: Path) -> Path:
        src = ROOT / "outputs" / "phase8_demos" / "demo 1_raw.mp3"
        if not src.is_file():
            self.skipTest("Phase 8 demo sample is missing")
        return src

    def test_wav_master_is_lossless_and_consistent(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            master = provider.to_wav_master(self._voice(work), work / "voice.wav")
            self.assertIsNotNone(master)
            info = provider.probe_audio_format(master)
            self.assertEqual(info["codec"], "pcm_s24le")
            self.assertEqual(str(info["sample_rate"]), str(44100))
            self.assertEqual(str(info["channels"]), "1")

    def test_master_mp3_is_constant_320k(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            master = provider.to_wav_master(self._voice(work), work / "voice.wav")
            out = provider.export_master_mp3(master, work / "voice_320k.mp3")
            self.assertIsNotNone(out)
            info = provider.probe_audio_format(out)
            self.assertEqual(info["codec"], "mp3")
            self.assertEqual(int(info["bit_rate"]), 320000)

    def test_export_can_carry_a_loudness_filter(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            master = provider.to_wav_master(self._voice(work), work / "voice.wav")
            plain = provider.export_master_mp3(master, work / "plain.mp3")
            loud = provider.export_master_mp3(master, work / "loud.mp3", audio_filter="volume=6dB")

            def mean(path):
                text = subprocess.run(
                    ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
                     "-af", "volumedetect", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
                return float(re.search(r"mean_volume:\s*(-?[\d.]+) dB", text).group(1))

            self.assertAlmostEqual(mean(loud) - mean(plain), 6.0, delta=0.6)
            self.assertEqual(int(provider.probe_audio_format(loud)["bit_rate"]), 320000)

    def test_missing_input_returns_none_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(provider.to_wav_master(Path(td) / "absent.mp3"))
            self.assertIsNone(provider.export_master_mp3(Path(td) / "absent.wav", Path(td) / "x.mp3"))


class DeliverySettingsTests(unittest.TestCase):
    def test_default_delivery_bitrate_is_320k(self):
        with patch.dict(os.environ, {"AUDIO_BITRATE": ""}):
            self.assertEqual(ffmpeg_tools.audio_bitrate(), "320k")

    def test_bitrate_override_and_garbage_fallback(self):
        with patch.dict(os.environ, {"AUDIO_BITRATE": "128k"}):
            self.assertEqual(ffmpeg_tools.audio_bitrate(), "128k")
        with patch.dict(os.environ, {"AUDIO_BITRATE": "loudnorm"}):
            self.assertEqual(ffmpeg_tools.audio_bitrate(), ffmpeg_tools.DEFAULT_AUDIO_BITRATE)

    def test_music_bed_is_off_by_default(self):
        with patch.dict(os.environ, {"MUSIC_BED": "", "MUSIC_BED_FILE": ""}):
            self.assertFalse(ffmpeg_tools.music_bed_requested())

    def test_music_bed_opt_in_and_file_implies_on(self):
        with patch.dict(os.environ, {"MUSIC_BED": "on", "MUSIC_BED_FILE": ""}):
            self.assertTrue(ffmpeg_tools.music_bed_requested())
        with patch.dict(os.environ, {"MUSIC_BED": "", "MUSIC_BED_FILE": "anything.mp3"}):
            self.assertTrue(ffmpeg_tools.music_bed_requested())

    def test_music_bed_source_requires_a_real_file(self):
        with patch.dict(os.environ, {"MUSIC_BED_FILE": "no/such/track.mp3"}):
            self.assertIsNone(ffmpeg_tools.music_bed_source())


class MixGraphTests(unittest.TestCase):
    def _graph(self, music: Path | None, sfx=()) -> list[str]:
        with tempfile.TemporaryDirectory() as td:
            captured = {}
            with _loudnorm_filter(), patch.object(ffmpeg_tools, "_run",
                                                  side_effect=lambda cmd, **k: captured.update(cmd=cmd)):
                ffmpeg_tools._mix_audio([], Path("voice.wav"), Path(td), -15.0, music, list(sfx))
            return captured["cmd"]

    def test_voice_pad_is_split_when_a_bed_is_present(self):
        cmd = self._graph(Path("music.wav"))
        graph = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("asplit=2", graph)
        self.assertIn("[vsc]", graph)
        self.assertNotIn("afifo", graph)

    def test_voice_only_graph_skips_the_extra_branch(self):
        graph_cmd = self._graph(None)
        graph = graph_cmd[graph_cmd.index("-filter_complex") + 1]
        self.assertNotIn("asplit", graph)
        self.assertNotIn("sidechaincompress", graph)

    def test_ducking_is_conservative(self):
        cmd = self._graph(Path("music.wav"))
        graph = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("ratio=3", graph)
        self.assertIn("makeup=1", graph)
        self.assertNotIn("ratio=12", graph)
        self.assertNotIn("makeup=2", graph)

    def test_limiter_cannot_auto_raise_the_master(self):
        cmd = self._graph(Path("music.wav"))
        graph = cmd[cmd.index("-filter_complex") + 1]
        match = re.search(r"alimiter=([^;\]]+)", graph)
        self.assertIsNotNone(match)
        self.assertIn("level=false", match.group(1))
        self.assertIn("normalize=0", graph)

    def test_mix_is_written_as_lossless_24_bit(self):
        cmd = self._graph(None)
        self.assertIn("pcm_s24le", cmd)
        self.assertEqual(cmd[cmd.index("-ar") + 1], str(ffmpeg_tools.AUDIO_RATE))


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required")
class MixLevelTests(unittest.TestCase):
    """The regressions that matter are audible: level and noise floor."""

    def _voice(self, work: Path) -> Path:
        src = ROOT / "outputs" / "phase8_demos" / "demo 1_raw.mp3"
        if not src.is_file():
            self.skipTest("Phase 8 demo sample is missing")
        return src

    def _lufs(self, path: Path) -> tuple[float, float]:
        text = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
             "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
            capture_output=True, text=True).stderr
        found = dict(re.findall(r'"(input_i|input_tp)" : "(-?[\d.]+)"', text))
        return float(found["input_i"]), float(found["input_tp"])

    def test_narration_level_survives_the_bed(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            voice = self._voice(work)
            bed = ffmpeg_tools.synthesize_music_bed(work / "bed", 14.0)
            only_dir, bed_dir = work / "only", work / "with"
            only_dir.mkdir(); bed_dir.mkdir()
            only = ffmpeg_tools._mix_audio([], voice, only_dir, -15.0, None, [])
            with_bed = ffmpeg_tools._mix_audio([], voice, bed_dir, -15.0, bed, [])
            a_i, a_tp = self._lufs(only)
            b_i, b_tp = self._lufs(with_bed)
        self.assertAlmostEqual(a_i, -16.0, delta=1.0)
        # The old graph lost about 6 dB here; the bed may only add a little.
        self.assertGreaterEqual(b_i, a_i - 1.5)
        self.assertLess(b_i, a_i + 2.0)
        self.assertLessEqual(b_tp, -1.0)

    def test_bed_has_no_broadband_hiss(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            bed = ffmpeg_tools.synthesize_music_bed(work, 6.0)
            text = subprocess.run(
                ["ffmpeg", "-hide_banner", "-nostats", "-i", str(bed), "-af",
                 "highpass=f=6000,volumedetect", "-f", "null", "-"],
                capture_output=True, text=True).stderr
            match = re.search(r"mean_volume:\s*(-?[\d.]+) dB", text)
        self.assertIsNotNone(match)
        # A pink-noise bed measured around -35 dB here; a tonal bed is far below.
        self.assertLessEqual(float(match.group(1)), -60.0)


if __name__ == "__main__":
    unittest.main()
