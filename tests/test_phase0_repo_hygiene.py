"""Phase 0 smoke test: repository safety and secret hygiene.

Checks names only; never reads or asserts secret values.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_IGNORE_PATTERNS = {
    ".env",
    ".env.*",
    "*.mp4",
    "*.mp3",
    "*.wav",
    "*.ass",
    "/data/",
    "/outputs/",
    "/shots/",
    "/.venv/",
    "/venv/",
    "__pycache__/",
}

SECRET_NAMES = {
    ".env",
    ".env.bak-2026-10-26",
    ".n8n-docker.env",
    "youtube_token.json",
    "token.json",
    "token_usage.json",
}

GENERATED_SUFFIXES = {".mp4", ".mp3", ".wav", ".ass", ".srt"}


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_git_has_baseline_and_backup_branch() -> None:
    head = git("rev-parse", "--verify", "HEAD")
    assert head.returncode == 0, "no baseline commit exists"

    backup = git("rev-parse", "--verify", "--quiet", "refs/heads/backup/pre-restructure")
    assert backup.returncode == 0, "backup/pre-restructure branch is missing"


def test_required_ignore_patterns_present() -> None:
    lines = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    missing = REQUIRED_IGNORE_PATTERNS - lines
    assert not missing, f".gitignore missing patterns: {sorted(missing)}"


def test_secret_paths_are_ignored() -> None:
    for name in sorted(SECRET_NAMES):
        result = git("check-ignore", "-q", name)
        assert result.returncode == 0, f"{name} is not git-ignored"


def test_no_secret_or_generated_files_tracked() -> None:
    tracked = git("ls-files", "-z").stdout.split("\0")
    tracked = [path for path in tracked if path]

    for path in tracked:
        assert path not in SECRET_NAMES, f"secret file is tracked: {path}"
        assert Path(path).suffix.lower() not in GENERATED_SUFFIXES, (
            f"generated media is tracked: {path}"
        )


def test_env_example_contains_keys_only() -> None:
    for lineno, raw in enumerate(
        (ROOT / ".env.example").read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        assert "=" in line, f".env.example:{lineno} is not KEY=value"
        key, value = line.split("=", 1)
        assert key.strip(), f".env.example:{lineno} has an empty key"
        value = value.split("#", 1)[0].strip()
        assert not value, f".env.example:{lineno} ({key.strip()}) has a value; keys only"


def test_dockerignore_excludes_secrets_and_state() -> None:
    lines = {
        line.strip()
        for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    for required in (".env", "data/", "outputs/", "shots/", "archive/"):
        assert required in lines, f".dockerignore missing {required}"
