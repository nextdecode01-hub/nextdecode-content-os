import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from pipelines import longform as create_longform


class FakeResponse:
    def __init__(self, payload=None, chunks=()):
        self.payload = payload or {}
        self.chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload

    def iter_content(self, chunk_size):
        return iter(self.chunks)


class LongformVisualTests(unittest.TestCase):
    def test_voiceover_resolves_edge_tts_beside_python_when_not_on_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            python = Path(temporary) / "venv" / "bin" / "python"
            executable = python.with_name("edge-tts")
            executable.parent.mkdir(parents=True)
            executable.touch()
            with patch.object(create_longform.shutil, "which", return_value=None), patch.object(
                create_longform.sys, "executable", str(python)
            ), patch.object(create_longform.subprocess, "run") as run:
                create_longform.voiceover("Hello world.", Path(temporary) / "voice.mp3")

        self.assertEqual(run.call_args.args[0][0], str(executable))

    def test_pexels_search_download_records_creator_and_license_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "scene.mp4"
            search = FakeResponse({
                "videos": [{
                    "id": 42,
                    "url": "https://www.pexels.com/video/example-42/",
                    "user": {"name": "Example Creator"},
                    "video_files": [{
                        "width": 1920,
                        "height": 1080,
                        "link": "https://videos.pexels.com/example.mp4",
                    }],
                }]
            })
            download = FakeResponse(chunks=[b"x" * 120_000])
            with patch.object(create_longform, "PEXELS_API_KEY", "test-key"), patch(
                "pipelines.longform.requests.get",
                side_effect=[search, download],
            ) as get:
                result = create_longform._find_pexels_clip("research technology", destination, set())

            self.assertEqual(get.call_count, 2)
            self.assertEqual(result["creator"], "Example Creator")
            self.assertEqual(result["license"], "Pexels License")
            self.assertEqual(result["video_id"], 42)
            self.assertTrue(destination.is_file())

    def test_stock_sequence_aligns_available_clips_to_their_chapters(self):
        chapters = [
            {"title": f"Chapter {index}", "start_seconds": index * 60, "broll_query": f"scene {index}"}
            for index in range(5)
        ]
        clips = [
            {"asset_path": f"scene_{index}_{take}.mp4", "chapter_index": index}
            for index in (0, 1, 3, 4)
            for take in (1, 2)
        ]
        with patch("pipelines.longform.subprocess.run") as run:
            create_longform._render_stock_sequence(clips, chapters, Path("background.mp4"), 300)

        command = run.call_args.args[0]
        filter_complex = command[command.index("-filter_complex") + 1]
        self.assertIn("concat=n=8", filter_complex)
        self.assertIn("trim=duration=60.000", filter_complex)
        self.assertEqual(command.count("-stream_loop"), 8)

    def test_pixabay_search_results_are_cached_for_24_hours_without_saving_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            hits = [{"id": 42, "videos": {}}]
            with patch.object(create_longform, "ROOT", Path(temporary)), patch.object(
                create_longform, "PIXABAY_API_KEY", "private-test-key"
            ), patch(
                "pipelines.longform.requests.get",
                return_value=FakeResponse({"hits": hits}),
            ) as get:
                first = create_longform._pixabay_search_results("research technology")
                second = create_longform._pixabay_search_results("research technology")

            self.assertEqual(first, hits)
            self.assertEqual(second, hits)
            get.assert_called_once()
            self.assertEqual(get.call_args.args[0], "https://pixabay.com/api/videos/")
            cache_files = list((Path(temporary) / "outputs" / "videos" / "pixabay_search_cache").glob("*.json"))
            self.assertEqual(len(cache_files), 1)
            self.assertNotIn("private-test-key", cache_files[0].read_text(encoding="utf-8"))
            self.assertEqual(json.loads(cache_files[0].read_text(encoding="utf-8"))["hits"], hits)

    def test_pixabay_clip_uses_landscape_variant_and_records_attribution(self):
        hit = {
            "id": 42,
            "pageURL": "https://pixabay.com/videos/example-video-42/",
            "user": "ExampleCreator",
            "user_id": 99,
            "videos": {
                "medium": {
                    "url": "https://cdn.pixabay.com/video/medium.mp4",
                    "width": 1280,
                    "height": 720,
                    "size": 2_000_000,
                },
            },
        }
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            create_longform, "_pixabay_search_results", return_value=[hit]
        ), patch.object(create_longform, "_download_stock_clip") as download:
            result = create_longform._find_pixabay_clip(
                "research technology",
                Path(temporary) / "scene.mp4",
                set(),
            )

        download.assert_called_once_with(
            "https://cdn.pixabay.com/video/medium.mp4",
            Path(temporary) / "scene.mp4",
        )
        self.assertEqual(result["creator"], "ExampleCreator")
        self.assertEqual(result["license"], "Pixabay Content License")
        self.assertEqual(result["page_url"], hit["pageURL"])

    def test_pixabay_can_generate_a_review_eligible_stock_cut(self):
        chapters = [
            {"title": f"Chapter {index}", "start_seconds": index * 60, "broll_query": f"technology scene {index}"}
            for index in range(4)
        ]
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            create_longform, "ROOT", Path(temporary)
        ), patch.object(create_longform, "PEXELS_API_KEY", ""), patch.object(
            create_longform, "PIXABAY_API_KEY", "private-test-key"
        ), patch(
            "pipelines.longform._find_pixabay_clip",
            side_effect=[
                {
                    "video_id": index,
                    "provider": "pixabay",
                    "creator": "Creator",
                    "page_url": "https://pixabay.com/videos/example/",
                    "asset_path": f"scene_{index}.mp4",
                }
                for index in range(8)
            ],
        ), patch("pipelines.longform._render_stock_sequence") as render:
            result = create_longform.landscape_background(
                "technology research",
                Path(temporary) / "background.mp4",
                240,
                chapters,
            )

        render.assert_called_once()
        self.assertEqual(result["mode"], "pixabay_stock")
        self.assertEqual(result["asset_count"], 8)

    def test_procedural_fallback_creates_motion_graphics_but_stays_draft_only(self):
        chapters = [
            {"title": f"Chapter {index}", "start_seconds": index * 30, "broll_query": f"research scene {index}"}
            for index in range(4)
        ]
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            create_longform, "ROOT", Path(temporary)
        ), patch.object(create_longform, "DEMO_VIDEO_PATH", ""), patch.object(
            create_longform, "PEXELS_API_KEY", ""
        ), patch.object(create_longform, "PIXABAY_API_KEY", ""), patch.object(
            create_longform, "_render_motion_graphics", return_value=8
        ) as render:
            result = create_longform.landscape_background(
                "research technology",
                Path(temporary) / "background.mp4",
                120,
                chapters,
            )

        self.assertEqual(result["mode"], "procedural_fallback")
        self.assertEqual(result["scene_count"], 8)
        self.assertTrue(result["motion_graphics"])
        self.assertIn("not licensed footage", result["description"])
        render.assert_called_once()

    def test_render_uses_compatible_audio_and_rejects_silence(self):
        probe = json.dumps({
            "format": {"duration": "170.2"},
            "streams": [
                {"codec_type": "video", "width": 1920, "height": 1080},
                {"codec_type": "audio", "sample_rate": "48000", "channels": 2, "duration": "170.2"},
            ],
        })
        with patch(
            "pipelines.longform.subprocess.run",
            side_effect=[
                None,
                type("Result", (), {"stdout": probe})(),
                type("Result", (), {"stderr": "max_volume: -5.0 dB"})(),
            ],
        ) as run:
            create_longform.render(Path("background.mp4"), Path("voice.mp3"), Path("captions.ass"), Path("out.mp4"))

        render_command = run.call_args_list[0].args[0]
        self.assertIn("48000", render_command)
        self.assertIn("loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000", render_command)

        with patch(
            "pipelines.longform.subprocess.run",
            side_effect=[
                None,
                type("Result", (), {"stdout": probe})(),
                type("Result", (), {"stderr": "max_volume: -inf dB"})(),
            ],
        ), self.assertRaisesRegex(RuntimeError, "silent or too quiet"):
            create_longform.render(Path("background.mp4"), Path("silent.mp3"), Path("captions.ass"), Path("out.mp4"))


if __name__ == "__main__":
    unittest.main()
