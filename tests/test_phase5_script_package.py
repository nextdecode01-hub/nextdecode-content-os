"""Phase 5 smoke test: script logic and stage entrypoints follow the target tree."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from app.script import longform, pipeline, short, studio, voice_guide
from pipelines import longform as longform_pipeline
from pipelines import short as short_pipeline

ROOT = Path(__file__).resolve().parents[1]

SCRIPT_MODULES = {
    "app/script/short.py": "short",
    "app/script/longform.py": "longform",
    "app/script/studio.py": "studio",
    "app/script/voice_guide.py": "voice_guide",
    "app/script/pipeline.py": "pipeline",
    "pipelines/short.py": "short_pipeline",
    "pipelines/longform.py": "longform_pipeline",
}

OLD_ROOT_MODULES = (
    "create_short",
    "create_longform",
    "strong_pipeline",
    "script_studio",
    "voice_guide",
)


def test_script_and_pipeline_files_exist() -> None:
    assert (ROOT / "app" / "script" / "__init__.py").is_file()
    assert (ROOT / "pipelines" / "__init__.py").is_file()
    for relative in SCRIPT_MODULES:
        assert (ROOT / relative).is_file(), f"{relative} is missing"


def test_old_root_modules_were_moved_not_copied() -> None:
    for name in OLD_ROOT_MODULES:
        assert not (ROOT / f"{name}.py").exists(), f"{name}.py still exists in the repo root"


def test_public_api_is_importable() -> None:
    assert callable(short.generate_script)
    assert callable(longform.generate_script)
    assert callable(studio.write_script)
    assert callable(voice_guide.find_slop)
    assert callable(pipeline.run)
    assert callable(short_pipeline.main)
    assert callable(longform_pipeline.main)


def test_pipeline_entrypoints_reuse_script_packages() -> None:
    assert longform_pipeline.generate_script is longform.generate_script
    assert short_pipeline.generate_script is short.generate_script
    assert short_pipeline.strong_pipeline is pipeline
    for moved in ("recent_topics", "_select_topic", "_validate_script"):
        assert not hasattr(longform_pipeline, moved), f"{moved} was copied instead of moved"


def test_project_paths_resolve_to_repo_root() -> None:
    assert short.PROJECT_ROOT == ROOT
    assert longform.ROOT == ROOT
    assert pipeline.ROOT == ROOT
    assert short_pipeline.ROOT == ROOT
    assert longform_pipeline.ROOT == ROOT
    assert longform.PROFILE_NAME in longform.PROFILES


def test_no_active_code_imports_old_module_names() -> None:
    pattern = re.compile(
        r"^\s*(?:from|import)\s+(" + "|".join(re.escape(name) for name in OLD_ROOT_MODULES) + r")\b",
        re.MULTILINE,
    )
    offenders: list[str] = []
    for path in sorted(ROOT.glob("*.py")) + sorted(ROOT.glob("app/**/*.py")) + sorted(ROOT.glob("pipelines/*.py")):
        source = path.read_text(encoding="utf-8-sig")
        for match in pattern.finditer(source):
            offenders.append(f"{path.relative_to(ROOT)}: {match.group(0).strip()}")
    assert not offenders, "old module imports remain: " + ", ".join(offenders)


def test_entrypoints_run_from_repo_root() -> None:
    for command in (
        [sys.executable, "pipelines/short.py", "--help"],
        [sys.executable, "pipelines/longform.py", "--help"],
        [sys.executable, "-m", "app.script.pipeline", "--help"],
    ):
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)
        assert result.returncode == 0, f"{' '.join(command)} failed: {result.stderr[-800:]}"


def test_shell_scripts_call_new_entrypoints() -> None:
    assert "pipelines/short.py" in (ROOT / "run_pipeline.sh").read_text(encoding="utf-8")
    assert "pipelines/longform.py" in (ROOT / "run_longform_pipeline.sh").read_text(encoding="utf-8")
    assert "app.script.pipeline" in (ROOT / "run_gen.sh").read_text(encoding="utf-8")


def test_dry_run_uses_local_voice_and_writes_separate_metadata(tmp_path) -> None:
    audio = tmp_path / "voice.mp3"
    audio.write_bytes(b"local-test-audio")
    with (
        patch(
            "app.voice.provider.synthesize",
            return_value={"path": str(audio), "provider": "silent", "duration_hint": 30.0},
        ) as synthesize,
        patch("app.voice.provider.probe_duration", return_value=30.0),
        patch.object(short_pipeline, "_dry_run_background"),
        patch.object(short_pipeline, "render_final_short"),
        patch("motion_render.make_kinetic_ass"),
    ):
        metadata = short_pipeline.run_dry_run(tmp_path / "work", tmp_path / "metadata_dry_run.json")

    synthesize.assert_called_once()
    assert synthesize.call_args.kwargs["provider"] == "silent"
    assert metadata["dry_run"] is True
    assert metadata["human_review_status"] == "not_for_publish"
    assert (tmp_path / "metadata_dry_run.json").is_file()


def test_setup_check_reports_new_module_paths() -> None:
    source = (ROOT / "setup_check.py").read_text(encoding="utf-8")
    for module in ("app.script.short", "app.script.longform", "app.script.studio", "app.script.voice_guide", "app.script.pipeline"):
        assert f'"{module}"' in source, f"setup_check.py is not checking {module}"
