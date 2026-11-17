import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.render import ffmpeg_tools
from app.render.subtitles import align_script_to_asr, make_kinetic_ass
from app.visuals import chain

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
HAS_FFMPEG = bool(FFMPEG and FFPROBE)


def _ffmpeg(cmd):
    subprocess.run([FFMPEG, "-y", *cmd], check=True, capture_output=True, text=True, timeout=120)


def _make_video(path: Path, *, duration: float = 1.2, audio: str | None = "tone",
                size: str = "360x640") -> Path:
    cmd = ["-f", "lavfi", "-i", f"color=c=0x203040:s={size}:r=30:d={duration}"]
    if audio == "tone":
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}"]
    elif audio == "silent":
        cmd += ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}"]
    cmd += ["-t", str(duration), "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-c:a", "aac", "-shortest"]
    cmd += [str(path)]
    _ffmpeg(cmd)
    return path


def _write_ass(path: Path, *, end: float = 1.0) -> Path:
    path.write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 360\nPlayResY: 640\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
        "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Kinetic,DejaVu Sans Bold,32,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        "-1,0,0,0,100,100,0,0,1,2,1,2,20,20,40,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        f"Dialogue: 0,0:00:00.00,0:00:0{end:.2f},Kinetic,,20,20,40,,hello world\n",
        encoding="utf-8",
    )
    return path


def _shots(count: int, duration: float) -> list[dict]:
    shots = []
    for index in range(count):
        shots.append({
            "index": index,
            "start": round(index * duration, 3),
            "end": round((index + 1) * duration, 3),
            "duration": duration,
            "visual": "rows of servers humming",
            "claim": "Rows of servers humming in a dark hall",
            "asset_query": "servers",
            "caption": "servers humming",
            "zoom_from": 1.0,
            "zoom_to": 1.14,
            "pan": {"x": 0.0, "y": 0.0},
            "transition": "cut",
            "sfx": "none",
            "music_gain_db": -15.0,
        })
    return shots


class ShortClipDurationTests(unittest.TestCase):
    def test_ffmpeg_failure_preserves_bounded_stderr_diagnostic(self):
        completed = subprocess.CompletedProcess(
            args=["ffmpeg"], returncode=1, stdout="", stderr="Invalid data found when processing input"
        )
        with patch("app.render.ffmpeg_tools.subprocess.run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "ffmpeg exited with code 1") as caught:
                ffmpeg_tools._run(["ffmpeg", "-i", "private/path.mp4"])
        self.assertIn("Invalid data found", str(caught.exception))
        self.assertNotIn("private/path.mp4", str(caught.exception))

    @unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required")
    def test_human_reviewed_semantic_flag_does_not_fail_strict_visual_qa(self):
        with tempfile.TemporaryDirectory() as td:
            video = _make_video(Path(td) / "reviewed.mp4", duration=1.2)
            result = ffmpeg_tools.qa_video(
                video, width=360, height=640, min_duration=1.0, max_duration=2.0,
                expected_fps=30, silence_db=None, assets=[{
                    "asset_id": "pixabay:reviewed", "relevance_confidence": "medium",
                    "semantic_review": True, "human_reviewed": True,
                }], strict_visuals=True,
            )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["assets"]["semantic_review"], 0)

    @unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required")
    def test_short_video_is_looped_to_fill_the_shot(self):
        from app.render.shots import render_shot

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            source = _make_video(work / "short.mp4", duration=1.0)
            shot = {
                "index": 0, "duration": 2.5, "start": 0.0, "end": 2.5,
                "motion": {"mode": "native", "zoom_from": 1.0, "zoom_to": 1.0},
            }
            out = render_shot(shot, source, work)
            duration = float(ffmpeg_tools._probe_duration(out))
        self.assertGreaterEqual(duration, 2.4)
        self.assertLessEqual(duration, 2.7)


class AbsoluteFrameAllocationTests(unittest.TestCase):
    def test_fractional_shots_sum_to_exact_absolute_timeline_frames(self):
        from app.render.shots import render_shot

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            image = work / "still.jpg"
            image.write_bytes(b"fixture")
            captured = []
            duration = 45.0
            count = 14

            def fake_run(command, *args, **kwargs):
                captured.append(int(command[command.index("-frames:v") + 1]))
                Path(command[-1]).write_bytes(b"x" * 2048)

            with patch("app.render.shots._run", side_effect=fake_run):
                for index in range(count):
                    shot = {
                        "index": index,
                        "start": duration * index / count,
                        "end": duration * (index + 1) / count,
                        "duration": duration / count,
                        "motion": {"mode": "native", "zoom_from": 1.0, "zoom_to": 1.0},
                    }
                    render_shot(shot, image, work, fps=30, width=64, height=64)

        self.assertEqual(len(captured), count)
        self.assertEqual(sum(captured), 1350)

    def test_render_shot_uses_absolute_start_end_frame_allocation(self):
        from app.render.shots import render_shot

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            image = work / "still.jpg"
            image.write_bytes(b"fixture")
            captured = {}

            def fake_run(command, *args, **kwargs):
                captured["command"] = command
                Path(command[-1]).write_bytes(b"x" * 2048)

            shot = {
                "index": 7, "start": 0.001, "end": 0.017,
                "duration": 0.016,
                "motion": {"mode": "native", "zoom_from": 1.0, "zoom_to": 1.0},
            }
            with patch("app.render.shots._run", side_effect=fake_run):
                render_shot(shot, image, work, fps=30)

        command = captured["command"]
        self.assertEqual(command[command.index("-frames:v") + 1], "1")
        self.assertEqual(command[command.index("-t") + 1], str(1 / 30))


class MixFilterTests(unittest.TestCase):
    def test_music_gain_uses_decibel_units_and_keeps_voice_level(self):
        with tempfile.TemporaryDirectory() as td:
            captured = {}

            def fake_run(cmd, *args, **kwargs):
                captured["cmd"] = cmd

            with patch.object(ffmpeg_tools, "_run", side_effect=fake_run):
                ffmpeg_tools._mix_audio(
                    [], Path("voice.wav"), Path(td), -15.0,
                    Path("music.wav"), [],
                )
            filter_arg = captured["cmd"][captured["cmd"].index("-filter_complex") + 1]
            self.assertIn("volume=-15.0dB", filter_arg)
            self.assertIn("normalize=0", filter_arg)
            self.assertIn("alimiter", filter_arg)
            self.assertIn("-ar", captured["cmd"])
            # FFmpeg 8 builds ship without the legacy fifo/afifo filters.
            self.assertNotIn("afifo", filter_arg)


class CaptionSpacingTests(unittest.TestCase):
    def _spoken_text(self, words):
        with tempfile.TemporaryDirectory() as td:
            path = make_kinetic_ass(words, Path(td) / "captions.ass")
            content = path.read_text(encoding="utf-8")
        dialogue = [line for line in content.splitlines() if line.startswith("Dialogue:")]
        return " ".join(re.sub(r"\{[^}]*\}", "", line.split(",", 9)[9]) for line in dialogue)

    def test_words_are_separated_on_screen(self):
        words = [
            {"word": "query", "start": 0.0, "end": 0.4},
            {"word": "consumes", "start": 0.4, "end": 0.9},
            {"word": "roughly", "start": 0.9, "end": 1.3},
        ]
        self.assertEqual(self._spoken_text(words), "query consumes roughly")

    def test_punctuation_and_number_tokens_stay_together(self):
        words = [
            {"word": "nearly", "start": 0.0, "end": 0.3},
            {"word": "0", "start": 0.3, "end": 0.4},
            {"word": ".", "start": 0.4, "end": 0.45},
            {"word": "1", "start": 0.45, "end": 0.55},
            {"word": "%", "start": 0.55, "end": 0.6},
            {"word": "of", "start": 0.6, "end": 0.7},
        ]
        self.assertEqual(self._spoken_text(words), "nearly 0.1% of")


class ScriptCaptionAlignmentTests(unittest.TestCase):
    def test_script_spelling_replaces_asr_mishearing(self):
        asr = [
            {"word": "The", "start": 0.0, "end": 0.2},
            {"word": "GrigApps", "start": 0.2, "end": 0.6},
            {"word": "report", "start": 0.6, "end": 1.0},
        ]
        aligned = align_script_to_asr("The GrayGaps report", asr)
        self.assertEqual([item["word"] for item in aligned], ["The", "GrayGaps", "report"])
        self.assertAlmostEqual(aligned[1]["start"], 0.2)
        self.assertAlmostEqual(aligned[1]["end"], 0.6)

    def test_missing_script_words_are_interpolated_in_order(self):
        asr = [
            {"word": "We", "start": 0.0, "end": 0.2},
            {"word": "use", "start": 0.2, "end": 0.4},
            {"word": "tools", "start": 0.4, "end": 0.7},
            {"word": "daily", "start": 0.7, "end": 1.0},
        ]
        aligned = align_script_to_asr("We use AI tools daily", asr)
        self.assertEqual([item["word"] for item in aligned], ["We", "use", "AI", "tools", "daily"])
        for left, right in zip(aligned, aligned[1:]):
            self.assertLessEqual(left["start"], right["start"])
            self.assertLessEqual(left["end"], right["start"] + 0.001)

    def test_empty_inputs_return_empty_alignment(self):
        self.assertEqual(align_script_to_asr("", [{"word": "x", "start": 0, "end": 1}]), [])
        self.assertEqual(align_script_to_asr("hello", []), [])


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required")
class StockClipPrepTests(unittest.TestCase):
    def test_black_lead_in_is_trimmed(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            source = td / "source.mp4"
            subprocess.run([
                FFMPEG, "-y",
                "-f", "lavfi", "-i", "color=c=black:s=360x640:r=30:d=2",
                "-f", "lavfi", "-i", "testsrc2=s=360x640:r=30:d=4",
                "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                str(source),
            ], check=True, capture_output=True, timeout=120)

            prepared = chain._prepare_clip(source, td / "prepared.mp4")

            self.assertIsNotNone(prepared)
            self.assertEqual(ffmpeg_tools._black_intervals(prepared, min_duration=0.5), [])


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required")
class QaVideoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing or too small"):
            ffmpeg_tools.qa_video(self.dir / "missing.mp4", min_duration=0.1, max_duration=10)

    def test_missing_audio_stream_fails(self):
        video = _make_video(self.dir / "mute.mp4", audio=None)
        with self.assertRaisesRegex(RuntimeError, "no audio stream"):
            ffmpeg_tools.qa_video(
                video, width=360, height=640, min_duration=0.5, max_duration=5,
            )

    def test_silent_audio_fails(self):
        video = _make_video(self.dir / "silent.mp4", audio="silent")
        with self.assertRaisesRegex(RuntimeError, "silent or extremely quiet"):
            ffmpeg_tools.qa_video(
                video, width=360, height=640, min_duration=0.5, max_duration=5,
                silence_db=-50.0,
            )

    def test_tone_audio_passes_with_fps_and_assets(self):
        video = _make_video(self.dir / "tone.mp4")
        summary = ffmpeg_tools.qa_video(
            video, width=360, height=640, min_duration=0.5, max_duration=5,
            expected_fps=30, silence_db=-50.0,
            assets=[{"asset_id": "pixabay:1"}, {"asset_id": "pixabay:2"}],
        )
        self.assertEqual(summary["status"], "pass")
        self.assertTrue(summary["checks"]["fps"])
        self.assertTrue(summary["checks"]["audio_level"])
        self.assertTrue(summary["checks"]["unique_assets"])

    def test_caption_timing_and_duplicate_assets_are_reported(self):
        video = _make_video(self.dir / "tone.mp4")
        ass = _write_ass(self.dir / "captions.ass", end=3.0)
        summary = ffmpeg_tools.qa_video(
            video, width=360, height=640, min_duration=0.5, max_duration=5,
            silence_db=None, captions=ass,
            assets=[{"asset_id": "same"}, {"asset_id": "same"}],
        )
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["captions"]["events"], 1)
        self.assertTrue(any("beyond" in warning for warning in summary["warnings"]))
        self.assertTrue(any("consecutive" in warning for warning in summary["warnings"]))
        self.assertFalse(summary["checks"]["unique_assets"])

    def test_low_confidence_assets_are_flagged_for_review(self):
        video = _make_video(self.dir / "tone.mp4")
        summary = ffmpeg_tools.qa_video(
            video, width=360, height=640, min_duration=0.5, max_duration=5,
            silence_db=-50.0,
            assets=[
                {"asset_id": "pixabay:1", "relevance_confidence": "medium", "semantic_review": True},
                {"asset_id": "pixabay:2", "relevance_confidence": "low", "semantic_review": True},
                {"asset_id": "gradient", "relevance_confidence": "none", "semantic_review": True,
                 "visual_quality": "low_light"},
            ],
        )
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["assets"]["low_confidence"], 2)
        self.assertEqual(summary["assets"]["semantic_review"], 3)
        self.assertEqual(summary["assets"]["low_light"], 1)
        self.assertTrue(any("low/no lexical relevance" in warning for warning in summary["warnings"]))
        self.assertTrue(any("need visual review" in warning for warning in summary["warnings"]))
        self.assertTrue(any("too dark/flat" in warning for warning in summary["warnings"]))

    def test_strict_visual_qa_rejects_reused_low_confidence_and_low_light_assets(self):
        video = _make_video(self.dir / "strict-visuals.mp4")
        assets = [
            {"asset_id": "same", "relevance_confidence": "low",
             "semantic_review": True, "visual_quality": "low_light"},
            {"asset_id": "same", "relevance_confidence": "high"},
        ]
        with self.assertRaisesRegex(RuntimeError, "visual asset|low/no lexical|semantic visual|too dark"):
            ffmpeg_tools.qa_video(
                video, width=360, height=640, min_duration=0.5, max_duration=5,
                silence_db=None, assets=assets, strict_visuals=True,
            )

    def test_missing_captions_file_fails(self):
        video = _make_video(self.dir / "tone.mp4")
        with self.assertRaisesRegex(RuntimeError, "captions file is missing"):
            ffmpeg_tools.qa_video(
                video, width=360, height=640, min_duration=0.5, max_duration=5,
                silence_db=None, captions=self.dir / "nope.ass",
            )


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required")
class RenderAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _audio(self, duration: float = 2.4) -> Path:
        audio = self.dir / "voice.wav"
        _ffmpeg(["-f", "lavfi", "-i", f"sine=frequency=220:duration={duration}",
                 "-c:a", "pcm_s16le", str(audio)])
        return audio

    def test_render_burns_captions_and_reports_visual_fallbacks(self):
        from app.render import assembly

        # Test-only gate: this case covers caption/motion mechanics.  Production keeps
        # STORYBOARD_GATE=require (see test_storyboard_require_gate_blocks_before_render).
        with patch.dict(os.environ, {"DRY_RUN": "1", "STORYBOARD_GATE": "warn"}):
            result = assembly.render_video(
                _shots(2, 2.4), self._audio(4.8), self.dir / "out.mp4",
                work_dir=self.dir / "work",
                ass_path=_write_ass(self.dir / "captions.ass", end=4.5),
            )

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["captions_burned"])
        # Phase 9: the bed is opt-in, so a default render is honestly labelled
        # voice-only rather than "mixed" with nothing summed into it.
        self.assertEqual(result["audio_mix_mode"], "voice_only")
        self.assertEqual(result["audio_warning"], "")
        self.assertIsNone(result["music"])
        self.assertEqual(result["audio_settings"]["delivery_bitrate"], "320k")
        self.assertFalse(result["audio_settings"]["music_bed"])
        self.assertEqual(len(result["scene_briefs"]), 2)
        self.assertEqual(result["provider_counts"].get("motion_graphic"), 2)
        self.assertEqual(len(result["fallback_scenes"]), 2)
        self.assertTrue(all(item["fallback_reason"] for item in result["fallback_scenes"]))
        self.assertIn("storyboard", result)
        self.assertEqual(result["storyboard"]["review_status"], "needs_review")
        self.assertTrue(Path(result["storyboard"]["contact_sheet"]).is_file())
        self.assertTrue(Path(result["storyboard"]["json_path"]).is_file())
        summary = ffmpeg_tools.qa_video(
            Path(result["path"]), width=1080, height=1920,
            min_duration=1, max_duration=10, expected_fps=30,
            silence_db=-50.0, assets=result["assets"],
            captions=self.dir / "captions.ass",
        )
        self.assertEqual(summary["status"], "pass")
        self.assertTrue(summary["captions"]["events"])

    def test_missing_caption_artifact_rejects_render(self):
        from app.render import assembly

        with patch.dict(os.environ, {"DRY_RUN": "1", "STORYBOARD_GATE": "warn"}):
            with self.assertRaisesRegex(RuntimeError, "required caption file is missing or empty"):
                assembly.render_video(
                    _shots(1, 2.4), self._audio(2.4), self.dir / "missing_caption.mp4",
                    work_dir=self.dir / "work_missing_caption",
                    ass_path=self.dir / "not-created.ass",
                )

    def test_caption_burn_failure_rejects_render_without_silent_fallback(self):
        from app.render import assembly

        original_run = assembly._run
        def fail_only_caption_burn(command):
            if any("ass=" in str(arg) for arg in command):
                raise RuntimeError("synthetic subtitle filter failure")
            return original_run(command)

        with (
            patch.dict(os.environ, {"DRY_RUN": "1", "STORYBOARD_GATE": "warn"}),
            patch.object(assembly, "_run", side_effect=fail_only_caption_burn),
        ):
            with self.assertRaisesRegex(RuntimeError, "required caption burn-in failed"):
                assembly.render_video(
                    _shots(1, 2.4), self._audio(2.4), self.dir / "caption_failure.mp4",
                    work_dir=self.dir / "work_caption_failure",
                    ass_path=_write_ass(self.dir / "burn-failure.ass", end=2.3),
                )

    def test_production_rejects_nonblocking_storyboard_mode_before_asset_resolution(self):
        from app.render import assembly

        with (
            patch.dict(os.environ, {"DRY_RUN": "0", "STORYBOARD_GATE": "warn"}),
            patch.object(assembly.visual_chain, "plan_scenes") as plan_scenes,
        ):
            with self.assertRaisesRegex(RuntimeError, "production render requires STORYBOARD_GATE=require"):
                assembly.render_video(
                    _shots(1, 2.4), self._audio(2.4), self.dir / "unsafe.mp4",
                    work_dir=self.dir / "work_unsafe",
                )
        plan_scenes.assert_not_called()

    def test_storyboard_require_gate_blocks_before_render(self):
        from app.render import assembly

        out = self.dir / "blocked.mp4"
        with patch.dict(os.environ, {"DRY_RUN": "1", "STORYBOARD_GATE": "require"}):
            with self.assertRaisesRegex(RuntimeError, "storyboard review required"):
                assembly.render_video(
                    _shots(2, 2.4), self._audio(4.8), out,
                    work_dir=self.dir / "work_blocked",
                )
        self.assertFalse(out.exists())

    def test_opt_in_music_bed_produces_a_mixed_stem(self):
        from app.render import assembly

        # Test-only gate; production default stays require.
        with patch.dict(os.environ, {"DRY_RUN": "1", "MUSIC_BED": "on", "STORYBOARD_GATE": "warn"}):
            result = assembly.render_video(
                _shots(2, 2.4), self._audio(4.8), self.dir / "out_bed.mp4",
                work_dir=self.dir / "work_bed",
            )
        self.assertEqual(result["audio_mix_mode"], "mixed")
        self.assertIsNotNone(result["music"])
        self.assertTrue(result["audio_settings"]["music_bed"])
        self.assertIn("ratio=3", result["audio_settings"]["ducking"])

    def test_audio_mix_failure_is_visible_not_silent(self):
        from app.render import assembly

        # Test-only gate; production default stays require.
        with patch.dict(os.environ, {"DRY_RUN": "1", "STORYBOARD_GATE": "warn"}), patch.object(
            assembly, "_mix_audio", side_effect=RuntimeError("filter graph rejected")
        ):
            result = assembly.render_video(
                _shots(1, 2.4), self._audio(2.4), self.dir / "out.mp4",
                work_dir=self.dir / "work2",
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["audio_mix_mode"], "voice_only")
        self.assertIn("audio mix failed", result["audio_warning"])


if __name__ == "__main__":
    unittest.main()
