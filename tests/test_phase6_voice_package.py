"""Phase 6 smoke test: TTS provider lives in app/voice/ and imports resolve."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from app.voice import provider
from app.script import pipeline as strong_pipeline

ROOT = Path(__file__).resolve().parents[1]


def test_voice_package_files_and_init_exist() -> None:
    assert (ROOT / "app" / "voice" / "__init__.py").is_file()
    assert (ROOT / "app" / "voice" / "provider.py").is_file()


def test_old_root_module_was_moved_not_copied() -> None:
    assert not (ROOT / "voice_provider.py").exists(), "voice_provider.py still exists in the repo root"


def test_public_api_is_importable() -> None:
    assert callable(provider.synthesize)
    assert callable(provider.synthesize_with_fallback)
    assert callable(provider.synthesize_long)
    assert callable(provider.provider_status)
    assert callable(provider.chunk_text)
    assert strong_pipeline.voice_provider is provider


def test_project_root_and_default_output_resolve() -> None:
    assert provider.ROOT == ROOT
    assert provider._find_edge_tts() is None or Path(provider._find_edge_tts()).is_file()
    default_output = provider.ROOT / "outputs" / "tts_output.mp3"
    assert default_output.parent == ROOT / "outputs"


def test_no_active_code_imports_old_voice_provider_name() -> None:
    pattern = re.compile(r"^\s*(?:from|import)\s+voice_provider\b", re.MULTILINE)
    offenders: list[str] = []
    for path in sorted(ROOT.glob("*.py")) + sorted(ROOT.glob("app/**/*.py")):
        source = path.read_text(encoding="utf-8-sig")
        for match in pattern.finditer(source):
            offenders.append(f"{path.relative_to(ROOT)}: {match.group(0).strip()}")
    assert not offenders, "old voice_provider imports remain: " + ", ".join(offenders)


def test_voice_provider_runs_as_package_cli() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app.voice.provider", "--list"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-800:]


def test_setup_check_reports_new_module_path() -> None:
    source = (ROOT / "setup_check.py").read_text(encoding="utf-8")
    assert '"app.voice.provider"' in source
