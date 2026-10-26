import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import motion_director
import motion_render

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
HAS_FFMPEG = bool(FFMPEG and FFPROBE)


def _ffprobe_json(path: Path) -> dict:
    cmd = [
        FFPROBE, "-v", "error", "-print_format", "json",
        "-show_entries", "format=duration:stream=codec_type,width,height",
        str(path),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if completed.returncode != 0:
        return {}
    try:
        return json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return {}


class PlanShotsTests(unittest.TestCase):
    def test_plan_shots_from_beat_sheet_invariants(self):
        script = {
            "topic": "test topic",
            "beat_sheet": [
                {"text": f"Beat number {i} has something interesting to say", "visual": f"visual {i}"}
                for i in range(12)
            ],
        }
        shots = motion_director.plan_shots(script, audio_duration=30.0)

        self.assertGreaterEqual(len(shots), 8)
        self.assertEqual(shots[0]["start"], 0.0)
        self.assertAlmostEqual(shots[-1]["end"], 30.0, delta=0.3)

        prev_end = 0.0
        prev_zoom = None
        for shot in shots:
            self.assertGreaterEqual(shot["duration"], 1.2)
            self.assertLessEqual(shot["duration"], 3.4)
            self.assertAlmostEqual(shot["start"], prev_end, places=6)
            prev_end = shot["end"]
            self.assertIn(shot["source"], motion_director.SOURCES)
            self.assertIn(shot["sfx"], ("whoosh", "impact", "riser", "none"))
            self.assertTrue(-18.0 <= shot["music_gain_db"] <= -13.0)
            self.assertLessEqual(len(shot["caption"]), 42)
            zoom = (shot["zoom_from"], shot["zoom_to"])
            if prev_zoom is not None:
                self.assertNotEqual(zoom, prev_zoom, "adjacent shots must differ in zoom")
            prev_zoom = zoom
        self.assertEqual(shots[0]["transition"], "fade")
        self.assertEqual(shots[-1]["transition"], "fade")

    def test_explicit_shots_are_used(self):
        script = {
            "shots": [
                {"caption": f"explicit shot {i}", "visual": f"v{i}", "source": "procedural"}
                for i in range(10)
            ],
        }
        shots = motion_director.plan_shots(script, audio_duration=24.0)
        self.assertGreaterEqual(len(shots), 8)
        self.assertAlmostEqual(shots[-1]["end"], 24.0, delta=0.3)

    def test_never_crashes_on_empty_input(self):
        shots = motion_director.plan_shots({}, audio_duration=5.0)
        self.assertTrue(isinstance(shots, list))
        self.assertTrue(len(shots) >= 1)

    def test_default_duration_when_missing(self):
        shots = motion_director.plan_shots(
            {"beat_sheet": [{"text": "one"}, {"text": "two"}]},
        )
        self.assertGreaterEqual(len(shots), 8)


class KenBurnsFilterTests(unittest.TestCase):
    def test_filter_is_non_empty_and_contains_zoompan(self):
        shot = {"index": 0, "start": 0.0, "end": 3.0, "duration": 3.0,
                "zoom_from": 1.0, "zoom_to": 1.14, "pan": {"x": 0.0, "y": 0.0}}
        f = motion_render.build_ken_burns_filter(shot)
        self.assertIsInstance(f, str)
        self.assertTrue(len(f) > 0)
        self.assertIn("zoompan", f)
        self.assertIn("d=90", f)

    def test_filter_passes_ffmpeg_validation(self):
        if not HAS_FFMPEG:
            self.skipTest("ffmpeg not available")
        shot = {"index": 1, "start": 3.0, "end": 6.3, "duration": 3.3,
                "zoom_from": 1.02, "zoom_to": 1.18, "pan": {"x": 6.0, "y": 0.0}}
        f = motion_render.build_ken_burns_filter(shot)
        cmd = [
            FFMPEG, "-y", "-f", "lavfi", "-i", "color=c=red:s=1080x1920:r=30:d=3.3",
            "-vf", f"{f},format=yuv420p",
            "-frames:v", "100", "-f", "null", "-",
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        self.assertEqual(completed.returncode, 0, completed.stderr[-500:])


class RenderPlanTests(unittest.TestCase):
    def test_estimate_render_plan_shape(self):
        shots = motion_director.plan_shots(
            {"beat_sheet": [{"text": f"b{i}"} for i in range(10)]},
            audio_duration=30.0,
        )
        plan = motion_director.estimate_render_plan(shots)
        self.assertIn("total_duration", plan)
        self.assertIn("shot_count", plan)
        self.assertIn("avg_shot", plan)
        self.assertIn("cut_rate_per_min", plan)
        self.assertIn("asset_counts", plan)
        self.assertGreaterEqual(plan["shot_count"], 8)
        self.assertAlmostEqual(plan["total_duration"], 30.0, delta=0.3)


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required")
class IntegrationRenderTests(unittest.TestCase):
    def test_render_3_shot_synthetic_video(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            shots = [
                {"index": 0, "start": 0.0, "end": 3.4, "duration": 3.4, "visual": "one",
                 "asset_query": "one", "source": "procedural", "caption": "shot one",
                 "zoom_from": 1.0, "zoom_to": 1.14, "pan": {"x": 0.0, "y": 0.0},
                 "transition": "fade", "sfx": "impact", "music_gain_db": -15.0},
                {"index": 1, "start": 3.4, "end": 6.7, "duration": 3.3, "visual": "two",
                 "asset_query": "two", "source": "procedural", "caption": "shot two",
                 "zoom_from": 1.02, "zoom_to": 1.18, "pan": {"x": -6.0, "y": 3.0},
                 "transition": "cut", "sfx": "whoosh", "music_gain_db": -15.5},
                {"index": 2, "start": 6.7, "end": 10.0, "duration": 3.3, "visual": "three",
                 "asset_query": "three", "source": "procedural", "caption": "shot three",
                 "zoom_from": 1.0, "zoom_to": 1.16, "pan": {"x": 8.0, "y": -2.0},
                 "transition": "fade", "sfx": "none", "music_gain_db": -16.0},
            ]
            audio = td / "silent.wav"
            subprocess.run([FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                            "-t", "10", "-c:a", "pcm_s16le", str(audio)],
                           check=True, capture_output=True)
            out = td / "out.mp4"
            result = motion_render.render_video(shots, audio, out, work_dir=td, ass_path=None)

            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 20_000)
            data = _ffprobe_json(out)
            video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
            self.assertIsNotNone(video)
            self.assertEqual(int(video.get("width") or 0), 1080)
            self.assertEqual(int(video.get("height") or 0), 1920)
            has_audio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
            self.assertTrue(has_audio)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["width"], 1080)
            self.assertEqual(result["height"], 1920)


if __name__ == "__main__":
    unittest.main()
