import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.visuals import motion_director as motion_director
from app.render import legacy_api as motion_render

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

    def test_one_shot_per_beat_avoids_repeated_claims(self):
        beats = [{"text": f"Beat {i} explains a different point"} for i in range(12)]
        shots = motion_director.plan_shots({"beat_sheet": beats}, audio_duration=30.0)
        self.assertEqual(len(shots), 12)
        claims = [shot["claim"] for shot in shots]
        self.assertEqual(len(set(claims)), 12)

    def test_beat_labels_are_carried_to_shots(self):
        beats = [
            {"text": "Hook line", "label": "hook"},
            {"text": "Mechanism line", "label": "mechanism"},
            {"text": "Payoff line", "label": "payoff"},
            {"text": "Close line", "label": "payoff"},
        ]
        shots = motion_director.plan_shots({"beat_sheet": beats}, audio_duration=24.0)
        self.assertEqual(shots[0]["beat_label"], "hook")
        self.assertIn("mechanism", {shot["beat_label"] for shot in shots})


class KenBurnsFilterTests(unittest.TestCase):
    def test_filter_is_non_empty_and_contains_zoompan(self):
        shot = {"index": 0, "start": 0.0, "end": 3.0, "duration": 3.0,
                "zoom_from": 1.0, "zoom_to": 1.14, "pan": {"x": 0.0, "y": 0.0}}
        f = motion_render.build_ken_burns_filter(shot)
        self.assertIsInstance(f, str)
        self.assertTrue(len(f) > 0)
        self.assertIn("zoompan", f)
        self.assertIn("d=1", f)
        self.assertIn("pow(", f)
        self.assertNotIn("d=90", f)

    def test_native_video_uses_fixed_crop_not_zoompan(self):
        shot = {"index": 1, "duration": 3.0,
                "motion": {"mode": "native", "zoom_from": 1.04, "zoom_to": 1.04}}
        f = motion_render.build_ken_burns_filter(shot)
        self.assertIn("scale=", f)
        self.assertIn("crop=1080:1920", f)
        self.assertNotIn("zoompan", f)

    def test_edl_contain_framing_and_edge_fades_are_executable(self):
        shot = {
            "duration": 2.0,
            "framing": {"mode": "contain", "focal_x": 0.7, "focal_y": 0.3},
            "edl_transition": {"in": True, "out": False, "duration_frames": 12},
        }
        f = motion_render.build_ken_burns_filter(shot)
        self.assertIn("force_original_aspect_ratio=decrease", f)
        self.assertIn("pad=1080:1920", f)
        self.assertIn("fade=t=in:st=0", f)

    def test_native_framing_and_edge_fades_pass_ffmpeg_validation(self):
        if not HAS_FFMPEG:
            self.skipTest("ffmpeg not available")
        shot = {
            "duration": 1.0,
            "motion": {"mode": "native", "zoom_from": 1.02},
            "framing": {"mode": "fill", "focal_x": 0.8, "focal_y": 0.25},
            "edl_transition": {"in": True, "out": True, "duration_frames": 6},
        }
        filter_str = motion_render.build_ken_burns_filter(shot, width=360, height=640)
        cmd = [FFMPEG, "-y", "-f", "lavfi", "-i", "color=c=red:s=640x360:r=30:d=1",
               "-vf", filter_str, "-frames:v", "30", "-f", "null", "-"]
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        self.assertEqual(completed.returncode, 0, completed.stderr[-500:])

    def test_native_crop_uses_focal_point(self):
        shot = {
            "duration": 2.0,
            "motion": {"mode": "native", "zoom_from": 1.0},
            "framing": {"mode": "fill", "focal_x": 0.8, "focal_y": 0.25},
        }
        f = motion_render.build_ken_burns_filter(shot)
        self.assertIn("(iw-1080)*0.8", f)
        self.assertIn("(ih-1920)*0.25", f)

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


class SceneMotionPlanTests(unittest.TestCase):
    def _shots(self, count=6, duration=2.5):
        return [
            {"index": i, "start": i * duration, "end": (i + 1) * duration,
             "duration": duration, "zoom_from": 1.0, "zoom_to": 1.14,
             "pan": {"x": 6.0, "y": 0.0}}
            for i in range(count)
        ]

    def test_video_footage_keeps_native_motion_at_cut_scale(self):
        shots = self._shots(3)
        details = [
            {"scene_type": "typography", "path": "/tmp/card.png"},
            {"scene_type": "footage", "path": "/tmp/clip.mp4"},
            {"scene_type": "chart", "path": "/tmp/chart.png"},
        ]
        motions = motion_director.assign_motion(shots, details, width=1080)
        self.assertEqual(motions[1]["mode"], "native")
        self.assertEqual(shots[1]["zoom_from"], shots[1]["zoom_to"])
        self.assertAlmostEqual(shots[1]["zoom_from"], shots[0]["zoom_to"], places=3)
        self.assertAlmostEqual(shots[2]["zoom_from"], shots[1]["zoom_to"], delta=0.01)

    def test_stills_alternate_zoom_direction_within_bounds(self):
        shots = self._shots(6)
        details = [{"scene_type": "photo_footage", "path": f"/tmp/p{i}.jpg"}
                   for i in range(6)]
        motions = motion_director.assign_motion(shots, details, width=1080)
        for motion in motions:
            self.assertGreaterEqual(motion["zoom_from"], 1.0)
            self.assertLessEqual(motion["zoom_to"], 1.08)
            self.assertLessEqual(abs(motion["pan"]["x0"]), 1080 * 0.012 + 0.1)
            self.assertLessEqual(abs(motion["pan"]["x1"]), 1080 * 0.012 + 0.1)
        directions = [
            (motion["zoom_to"] > motion["zoom_from"]) for motion in motions
        ]
        for left, right in zip(directions, directions[1:]):
            self.assertNotEqual(left, right, "zoom direction should alternate")

    def test_text_cards_do_not_pan(self):
        shots = self._shots(2)
        details = [{"scene_type": "typography", "path": f"/tmp/c{i}.png"}
                   for i in range(2)]
        motions = motion_director.assign_motion(shots, details)
        for motion in motions:
            self.assertEqual(motion["pan"]["x0"], 0.0)
            self.assertEqual(motion["pan"]["x1"], 0.0)

    def test_gradient_caption_uses_still_text_profile(self):
        shots = self._shots(1)
        details = [{"scene_type": "footage", "provider": "gradient",
                    "path": "/tmp/gradient.mp4"}]
        motions = motion_director.assign_motion(shots, details)
        self.assertEqual(motions[0]["profile"], "gradient_text_card")
        self.assertEqual(motions[0]["mode"], "kenburns")
        self.assertLessEqual(motions[0]["zoom_to"], 1.04)
        self.assertEqual(motions[0]["pan"]["x0"], 0.0)

    def test_per_cut_sfx_are_off_by_default(self):
        with patch.dict(os.environ, {"SHOT_SFX": ""}):
            shots = motion_director.plan_shots(
                {"beat_sheet": [{"text": f"Beat {i} about AI coding"} for i in range(10)]},
                audio_duration=30.0,
            )
        self.assertEqual({shot["sfx"] for shot in shots}, {"none"})

    def test_per_cut_sfx_can_be_opted_in(self):
        with patch.dict(os.environ, {"SHOT_SFX": "on"}):
            shots = motion_director.plan_shots(
                {"beat_sheet": [{"text": f"Beat {i} about AI coding"} for i in range(10)]},
                audio_duration=30.0,
            )
        self.assertIn("whoosh", {shot["sfx"] for shot in shots})


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
class LegacyAssetResolverTests(unittest.TestCase):
    def test_procedural_source_needs_no_network(self):
        with tempfile.TemporaryDirectory() as td:
            detail = motion_render.resolve_asset_detail(
                {"index": 0, "source": "procedural", "asset_query": "servers"}, Path(td))

        self.assertIsNone(detail["path"])
        self.assertEqual(detail["provider"], "procedural")

    def test_demo_source_uses_owner_recording(self):
        with tempfile.TemporaryDirectory() as td:
            demo = Path(td) / "demo.mp4"
            demo.write_bytes(b"x")
            with patch.dict(os.environ, {"DEMO_VIDEO_PATH": str(demo)}):
                detail = motion_render.resolve_asset_detail({"index": 0, "source": "demo"}, Path(td))

        self.assertEqual(detail["provider"], "demo")
        self.assertEqual(detail["path"], str(demo))

    def test_stock_source_delegates_to_canonical_chain(self):
        with tempfile.TemporaryDirectory() as td:
            asset = {"path": str(Path(td) / "a.jpg"), "title": "t", "license": "CC0"}
            with patch.object(motion_render.visual_chain, "_pixabay_asset", return_value=None), patch.object(
                motion_render.visual_chain, "_wikimedia_asset", return_value=asset
            ):
                detail = motion_render.resolve_asset_detail(
                    {"index": 1, "source": "pixabay", "asset_query": "servers"}, Path(td))

        self.assertEqual(detail["provider"], "pixabay")
        self.assertEqual(detail["path"], asset["path"])


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
            # Test-only gate: this case covers render mechanics (motion, dimensions,
            # audio).  Production keeps STORYBOARD_GATE=require.
            with patch.dict(os.environ, {"DRY_RUN": "1", "STORYBOARD_GATE": "warn"}), \
                    patch("app.visuals.stock_fetcher.fetch_shot_image", return_value=None):
                # This test validates rendering mechanics, not live Wikimedia
                # availability; keep the integration render hermetic.
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
            self.assertTrue((td / "editorial_handoff.otio").is_file())
            self.assertEqual(result["width"], 1080)
            self.assertEqual(result["height"], 1920)


if __name__ == "__main__":
    unittest.main()


class CreativeDirectionTests(unittest.TestCase):
    def test_story_formats_and_visual_styles_change_executable_shot_briefs(self):
        beats = [
            {"text": "A new AI lab opened", "label": "hook", "visual": "research lab"},
            {"text": "The system evaluates hypotheses", "label": "mechanism", "visual": "AI research system"},
            {"text": "The experiment failed", "label": "evidence", "visual": "research paper"},
            {"text": "The lesson is clear", "label": "payoff", "visual": "scientist"},
        ]
        documentary = motion_director.plan_shots(
            {"topic": "AI research", "story_format": "mini_documentary",
             "visual_style": "documentary", "beat_sheet": beats}, audio_duration=12.0)
        cinematic = motion_director.plan_shots(
            {"topic": "AI research", "story_format": "mystery_reveal",
             "visual_style": "cinematic", "beat_sheet": beats}, audio_duration=12.0)
        self.assertEqual(documentary[0]["story_format"], "mini_documentary")
        self.assertEqual(documentary[0]["visual_style"], "documentary")
        self.assertEqual(cinematic[0]["story_format"], "mystery_reveal")
        self.assertNotEqual(documentary[0]["lighting_direction"], cinematic[0]["lighting_direction"])
        self.assertIn(documentary[0]["shot_size"], {"close_up", "wide", "medium", "insert"})
        self.assertTrue(documentary[0]["camera_angle"])
        self.assertTrue(documentary[0]["camera_movement"])
        self.assertTrue(documentary[0]["asset_query_variants"])
        self.assertTrue(all(len(q.split()) <= 7 for q in documentary[0]["asset_query_variants"]))
        self.assertEqual(documentary[0]["transition"], "fade")
        self.assertTrue(documentary[1]["transition_intent"])
        self.assertTrue(documentary[1]["editorial_reason"])


class CreativeFormatSelectionTests(unittest.TestCase):
    def test_auto_story_format_selection_uses_topic_and_narrative_signals(self):
        self.assertEqual(motion_director.creative_director.select_story_format("The history of AI", []), "timeline")
        self.assertEqual(motion_director.creative_director.select_story_format("Is this AI myth actually true?", []), "myth_bust")
        self.assertEqual(motion_director.creative_director.select_story_format("AI research experiment", []), "mini_documentary")
        self.assertEqual(motion_director.creative_director.select_visual_style("AI research", "mini_documentary"), "documentary")

class ExecutableTransitionTests(unittest.TestCase):
    def test_transition_graph_contains_editorial_transitions_and_duration_compensation(self):
        from app.render.ffmpeg_tools import build_editorial_concat_filter
        graph, overlap = build_editorial_concat_filter([
            {"duration": 2.0, "transition_intent": "cut"},
            {"duration": 2.0, "transition_intent": "dissolve"},
            {"duration": 2.0, "transition_intent": "whip_pan"},
        ])
        self.assertIn("xfade=transition=dissolve", graph)
        self.assertIn("xfade=transition=smoothleft", graph)
        self.assertIn("tpad=stop_mode=clone", graph)
        self.assertGreater(overlap, 0.5)

    def test_ffmpeg_executes_dissolve_and_whip_pan_without_shortening_master_timeline(self):
        if not HAS_FFMPEG:
            self.skipTest("ffmpeg not available")
        from app.render.ffmpeg_tools import _concat_videos
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            clips = []
            for index, colour in enumerate(("red", "blue", "green")):
                path = root / f"clip_{index}.mp4"
                subprocess.run([
                    FFMPEG, "-y", "-f", "lavfi", "-i",
                    f"color=c={colour}:s=360x640:r=30:d=2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
                ], check=True, capture_output=True)
                clips.append(path)
            shots = [
                {"duration": 2.0, "transition_intent": "cut"},
                {"duration": 2.0, "transition_intent": "dissolve"},
                {"duration": 2.0, "transition_intent": "whip_pan"},
            ]
            output = _concat_videos(clips, shots, root)
            info = _ffprobe_json(output)
            self.assertAlmostEqual(float(info["format"]["duration"]), 6.0, delta=0.08)


class SemanticCreativeExecutionTests(unittest.TestCase):
    def test_semantic_asset_queries_are_concise_and_topic_relevant(self):
        from app.visuals.creative_director import direct_shots
        result = direct_shots(
            [{"text": "An agent takes on an open-ended research question from an unpublished paper."}],
            topic="Can AI agents conduct open-ended AI research?",
            story_format="mini_documentary", visual_style="documentary",
        )[0]
        self.assertLessEqual(len(result["asset_query"].split()), 6)
        self.assertEqual(result["asset_query_variants"][0], result["asset_query"])
        self.assertIn("research", result["asset_query"])
        self.assertTrue(any(token in result["asset_query"] for token in ("scientists", "agent", "paper")))

    def test_camera_movement_drives_ken_burns_execution(self):
        from app.visuals.motion_director import assign_motion
        push = [{"index": 0, "duration": 2.0, "camera_movement": "slow_push_in"}]
        pull = [{"index": 0, "duration": 2.0, "camera_movement": "slow_pull_back"}]
        push_motion = assign_motion(push, [{"scene_type": "footage", "asset_kind": "image"}])[0]
        pull_motion = assign_motion(pull, [{"scene_type": "footage", "asset_kind": "image"}])[0]
        self.assertGreaterEqual(push_motion["zoom_to"], 1.10)
        self.assertGreaterEqual(pull_motion["zoom_from"], 1.10)
        self.assertEqual(pull_motion["zoom_to"], 1.0)
