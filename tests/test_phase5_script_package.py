"""Phase 5 smoke test: script modules live in app/script/ and imports resolve."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import create_longform
from app.script import longform, studio, voice_guide

ROOT = Path(__file__).resolve().parents[1]

SCRIPT_MODULES = {
    "app/script/studio.py": "studio",
    "app/script/voice_guide.py": "voice_guide",
    "app/script/longform.py": "longform",
}

OLD_ROOT_MODULES = ("script_studio", "voice_guide")


def test_script_package_files_and_init_exist() -> None:
    assert (ROOT / "app" / "script" / "__init__.py").is_file()
    for relative in SCRIPT_MODULES:
        assert (ROOT / relative).is_file(), f"{relative} is missing"


def test_old_root_modules_were_moved_not_copied() -> None:
    for name in OLD_ROOT_MODULES:
        assert not (ROOT / f"{name}.py").exists(), f"{name}.py still exists in the repo root"


def test_public_api_is_importable() -> None:
    assert callable(studio.write_script)
    assert callable(studio.build_beat_sheet)
    assert callable(voice_guide.find_slop)
    assert callable(longform.generate_script)
    assert callable(longform._select_topic)


def test_longform_script_logic_is_not_duplicated_in_root_pipeline() -> None:
    assert create_longform.generate_script is longform.generate_script
    for moved in ("recent_topics", "_select_topic", "_validate_script", "_chapter_visuals"):
        assert not hasattr(create_longform, moved), f"{moved} was copied instead of moved"
    assert hasattr(create_longform, "_motion_diagram_parts")


def test_longform_paths_and_profiles_resolve() -> None:
    assert longform.ROOT == ROOT
    assert longform.PROFILE_NAME in longform.PROFILES
    assert longform.PROFILE is longform.PROFILES[longform.PROFILE_NAME]
    assert {"long_2m", "long_4m", "long_6m", "long_8m", "long_10m"} <= set(longform.PROFILES)


def test_no_active_code_imports_old_script_names() -> None:
    pattern = re.compile(
        r"^\s*(?:from|import)\s+(" + "|".join(re.escape(name) for name in OLD_ROOT_MODULES) + r")\b",
        re.MULTILINE,
    )
    offenders: list[str] = []
    for path in sorted(ROOT.glob("*.py")) + sorted(ROOT.glob("app/**/*.py")):
        source = path.read_text(encoding="utf-8-sig")
        for match in pattern.finditer(source):
            offenders.append(f"{path.relative_to(ROOT)}: {match.group(0).strip()}")
    assert not offenders, "old script imports remain: " + ", ".join(offenders)


def test_script_modules_run_as_package_clis() -> None:
    for module in ("app.script.studio", "app.script.voice_guide"):
        result = subprocess.run(
            [sys.executable, "-m", module, "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, f"{module} --help failed: {result.stderr[-800:]}"


def test_setup_check_reports_new_module_paths() -> None:
    source = (ROOT / "setup_check.py").read_text(encoding="utf-8")
    for module in ("app.script.studio", "app.script.voice_guide"):
        assert f'"{module}"' in source, f"setup_check.py is not checking {module}"
