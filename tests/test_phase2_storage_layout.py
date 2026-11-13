"""Phase 2 smoke test: generated state lives under data/ or outputs/."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from app.review import approve_longform as approve_longform
from app.review import approve_review as approve_review
from app.providers import model_health as model_health
from app.providers import multi_model_ai as multi_model_ai
from app.review import review_bundle as review_bundle
from app.operations import workspace_sync as workspace_sync
from app.research import selector as topic_selector
from app.research import trends as trend_research

ROOT = Path(__file__).resolve().parents[1]

DATA_FILES = {
    "analytics_history.json",
    "analytics_latest.json",
    "feedback_ledger.csv",
    "final_script.txt",
    "longform_metadata.json",
    "longform_review_pending.json",
    "longform_script.txt",
    "meta_uploads.json",
    "metadata.json",
    "metadata_strong.json",
    "model_health.json",
    "monetization_progress.json",
    "recent_formats.txt",
    "review_approved.json",
    "review_package.json",
    "review_pending.json",
    "social_upload_ledger.json",
    "token_usage.json",
    "trend_cache.json",
    "trend_history.json",
    "uploaded_content.json",
    "used_topics.txt",
    "workspace.db",
}

OUTPUT_FILES = {
    "output_short.mp4",
    "output_longform.mp4",
    "voice.mp3",
    "subtitles.ass",
    "longform_voice.mp3",
    "longform_subtitles.ass",
    "longform_background.mp4",
    "tts_output.mp3",
}

LEGACY_ROOT_PATTERN = re.compile(
    r'(?:ROOT|SCRIPT_DIR)\s*/\s*"(' + "|".join(
        re.escape(name) for name in sorted(DATA_FILES | OUTPUT_FILES)
    ) + r')"'
)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_storage_directories_exist() -> None:
    assert (ROOT / "data").is_dir(), "data/ directory is missing"
    assert (ROOT / "outputs").is_dir(), "outputs/ directory is missing"


def test_no_generated_files_left_in_repo_root() -> None:
    leftovers = sorted(
        name
        for name in DATA_FILES | OUTPUT_FILES
        if (ROOT / name).exists()
    )
    assert not leftovers, f"generated files still in repo root: {leftovers}"


def test_generated_state_is_not_tracked() -> None:
    tracked = [path for path in git("ls-files", "-z").stdout.split("\0") if path]
    generated = sorted(
        path
        for path in tracked
        if path in DATA_FILES
        or path in OUTPUT_FILES
        or path.startswith(("data/", "outputs/"))
        or Path(path).suffix.lower() in {".mp4", ".mp3", ".wav", ".ass", ".srt", ".db"}
    )
    assert not generated, f"generated state is tracked: {generated}"


def test_module_path_constants_point_to_new_layout() -> None:
    assert review_bundle.METADATA == ROOT / "data" / "metadata.json"
    assert review_bundle.VIDEO == ROOT / "outputs" / "output_short.mp4"
    assert review_bundle.QUEUE == ROOT / "data" / "review_queue"
    assert model_health.HEALTH_PATH == ROOT / "data" / "model_health.json"
    assert workspace_sync.DB_PATH == ROOT / "data" / "workspace.db"
    assert topic_selector.USED_TOPICS_PATH == ROOT / "data" / "used_topics.txt"
    assert trend_research.CACHE_PATH == ROOT / "data" / "trend_cache.json"
    assert multi_model_ai.TOKEN_USAGE_PATH == ROOT / "data" / "token_usage.json"


def test_approval_modules_use_data_and_outputs() -> None:
    approve_review_source = Path(approve_review.__file__).read_text(encoding="utf-8")
    approve_longform_source = Path(approve_longform.__file__).read_text(encoding="utf-8")
    assert 'ROOT / "data" / "review_pending.json"' in approve_review_source
    assert 'ROOT / "outputs" / "output_short.mp4"' in approve_review_source
    assert 'ROOT / "data" / "longform_review_pending.json"' in approve_longform_source
    assert 'ROOT / "outputs" / "output_longform.mp4"' in approve_longform_source
    assert 'TOKEN_FILE = SCRIPT_DIR / "youtube_token.json"' in (
        ROOT / "app" / "publish" / "youtube_upload.py"
    ).read_text(encoding="utf-8")
    assert 'SCRIPT_DIR / "data" / "metadata.json"' in (
        ROOT / "app" / "publish" / "youtube_upload.py"
    ).read_text(encoding="utf-8")


def test_python_modules_have_no_legacy_root_paths() -> None:
    offenders: list[str] = []
    for path in sorted(ROOT.glob("*.py")):
        source = path.read_text(encoding="utf-8-sig")
        for match in LEGACY_ROOT_PATTERN.finditer(source):
            offenders.append(f"{path.name}: {match.group(0)}")
    assert not offenders, "legacy root generated paths remain: " + ", ".join(offenders)
