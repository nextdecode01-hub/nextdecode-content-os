"""Phase 3 smoke test: unused modules are archived, not deleted."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive"

ARCHIVED = {
    "archive/legacy-oauth/auth_server.py",
    "archive/legacy-oauth/exchange_token.py",
    "archive/legacy-oauth/get_code.py",
    "archive/legacy-oauth/manual_auth.py",
    "archive/legacy-oauth/server_3000.py",
    "archive/legacy-oauth/server_5678.py",
    "archive/unused-infra/logging_config.py",
    "archive/unused-infra/resilience.py",
    "archive/optional-cli/ollama_chat.py",
    "archive/optional-cli/publish_review_safe.py",
}

KEPT_ROOT_MODULES = {
    "publish_social.py",
    "review_ledger.py",
    "monetization_tracker.py",
    "meta_preflight.py",
    "workspace_sync.py",
    "setup_check.py",
    "notify_status.py",
    "n8n_runner.py",
    "scheduled_publish.py",
}


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_archive_directories_and_readme_exist() -> None:
    for group in ("legacy-oauth", "unused-infra", "optional-cli"):
        assert (ARCHIVE / group).is_dir(), f"archive/{group} is missing"
    assert (ARCHIVE / "README.md").is_file(), "archive/README.md is missing"


def test_archived_files_still_exist_and_are_tracked() -> None:
    tracked = {path for path in git("ls-files", "-z").stdout.split("\0") if path}
    for relative in sorted(ARCHIVED):
        assert (ROOT / relative).is_file(), f"archived file is missing: {relative}"
        assert relative in tracked, f"archived file is not tracked: {relative}"


def test_archive_readme_documents_every_file() -> None:
    readme = (ARCHIVE / "README.md").read_text(encoding="utf-8")
    for relative in sorted(ARCHIVED):
        name = Path(relative).name
        assert f"`{name}`" in readme, f"archive/README.md does not explain {name}"


def test_archived_modules_are_not_in_root() -> None:
    for relative in sorted(ARCHIVED):
        assert not (ROOT / Path(relative).name).exists(), (
            f"{Path(relative).name} still exists in the repo root"
        )


def test_no_active_code_references_archived_modules() -> None:
    names = sorted(Path(relative).stem for relative in ARCHIVED)
    pattern = re.compile(r"\b(" + "|".join(re.escape(name) for name in names) + r")\b")
    active_files = list(ROOT.glob("*.py")) + list(ROOT.glob("*.sh"))
    active_files += [ROOT / "workflow_n8n_approved_schedule.json", ROOT / "compose.yaml"]
    offenders: list[str] = []
    for path in active_files:
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if pattern.search(line):
                offenders.append(f"{path.name}:{lineno}")
    assert not offenders, "active code references archived modules: " + ", ".join(offenders)


def test_documented_manual_tools_remain_in_root() -> None:
    for name in sorted(KEPT_ROOT_MODULES):
        assert (ROOT / name).is_file(), f"{name} should stay in the repo root"
