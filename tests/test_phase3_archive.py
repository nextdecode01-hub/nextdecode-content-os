"""Archive rationalization and canonical package layout checks."""
from __future__ import annotations
import re
import subprocess
from pathlib import Path
from importlib import import_module

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive"
ARCHIVED = {"_holding/legacy-oauth/get_code.py", "_holding/legacy-oauth/manual_auth.py"}
REMOVED_AFTER_AUDIT = {
    "archive/legacy-oauth/auth_server.py", "archive/legacy-oauth/exchange_token.py",
    "archive/legacy-oauth/server_3000.py", "archive/legacy-oauth/server_5678.py",
    "archive/unused-infra/logging_config.py", "archive/unused-infra/resilience.py",
    "archive/optional-cli/ollama_chat.py", "archive/optional-cli/publish_review_safe.py",
    "archive/superseded/create_short.py", "archive/abandoned-agent-scripts/replace_feed_fetchers.py",
    "archive/abandoned-agent-scripts/replace_desk_functions.ps1",
    "archive/abandoned-agent-scripts/README.md", "archive/unused-infra",
    "archive/optional-cli", "archive/superseded", "archive/abandoned-agent-scripts",
}
MOVED_AFTER_AUDIT = {"archive/optional-cli/ollama_chat.py": "tools/dev/ollama_chat.py"}
RETIRED_ROOT_WRAPPERS = {
    "analytics_collect.py", "approval_integrity.py", "approve_longform.py", "approve_review.py",
    "backfill_governance.py", "facebook_reels_upload.py", "instagram_reels_upload.py",
    "meta_preflight.py", "model_health.py", "monetization_tracker.py", "motion_director.py",
    "multi_model_ai.py", "notify_review.py", "notify_status.py", "omniroute_client.py",
    "publish_all.py", "publish_authorization.py", "publish_social.py", "review_bundle.py",
    "review_ledger.py", "review_longform.py", "run_tracker.py", "scheduled_publish.py",
    "stock_fetcher.py", "video_archive.py", "visual_assets.py", "visual_quality.py",
    "workspace_sync.py", "youtube_longform_upload.py", "youtube_upload.py",
}

def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)

def test_archive_directory_and_readme_exist() -> None:
    assert (ROOT / "_holding" / "legacy-oauth").is_dir()
    assert (ARCHIVE / "README.md").is_file()

def test_retained_archive_files_exist_and_are_tracked() -> None:
    tracked = {p for p in git("ls-files", "-z").stdout.split("\0") if p}
    for relative in sorted(ARCHIVED):
        assert (ROOT / relative).is_file()
        original = relative.replace("_holding/", "archive/")
        assert relative in tracked or original in tracked

def test_archive_readme_documents_every_retained_file() -> None:
    readme = (ROOT / "_holding" / "README.md").read_text(encoding="utf-8")
    for relative in sorted(ARCHIVED):
        assert Path(relative).name in readme

def test_archived_modules_are_not_in_root() -> None:
    for relative in sorted(ARCHIVED):
        assert not (ROOT / Path(relative).name).exists()

def test_no_active_code_references_retained_archive_modules() -> None:
    names = sorted(Path(relative).stem for relative in ARCHIVED)
    pattern = re.compile(r"\b(" + "|".join(re.escape(name) for name in names) + r")\b")
    files = list(ROOT.glob("*.py")) + list(ROOT.glob("*.sh"))
    offenders = []
    for path in files:
        if path.is_file():
            for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if pattern.search(line):
                    offenders.append(f"{path.name}:{line_no}")
    assert not offenders, "; ".join(offenders)

def test_confirmed_redundant_archive_items_were_removed() -> None:
    for relative in sorted(REMOVED_AFTER_AUDIT):
        assert not (ROOT / relative).exists()

def test_ollama_chat_was_moved_to_developer_tools() -> None:
    for old, new in MOVED_AFTER_AUDIT.items():
        assert not (ROOT / old).exists()
        assert (ROOT / new).is_file()
    assert (ROOT / "tools" / "dev" / "README.md").is_file()

def test_retired_root_wrappers_are_absent_and_canonical_modules_exist() -> None:
    targets = {
        "analytics_collect.py": "app.operations.analytics_collect",
        "approval_integrity.py": "app.security.approval_integrity",
        "approve_longform.py": "app.review.approve_longform",
        "approve_review.py": "app.review.approve_review",
        "backfill_governance.py": "tools.maintenance.backfill_governance",
        "facebook_reels_upload.py": "app.publish.facebook_reels_upload",
        "instagram_reels_upload.py": "app.publish.instagram_reels_upload",
        "meta_preflight.py": "app.operations.meta_preflight",
        "model_health.py": "app.providers.model_health",
        "monetization_tracker.py": "app.operations.monetization_tracker",
        "motion_director.py": "app.visuals.motion_director",
        "multi_model_ai.py": "app.providers.multi_model_ai",
        "notify_review.py": "app.notifications.notify_review",
        "notify_status.py": "app.notifications.notify_status",
        "omniroute_client.py": "app.providers.omniroute_client",
        "publish_all.py": "app.publish.orchestration",
        "publish_authorization.py": "app.publish.authorization",
        "publish_social.py": "app.publish.social_orchestrator",
        "review_bundle.py": "app.review.review_bundle",
        "review_ledger.py": "app.operations.review_ledger",
        "review_longform.py": "app.review.review_longform",
        "run_tracker.py": "app.tracking.run_tracker",
        "scheduled_publish.py": "app.publish.scheduler",
        "stock_fetcher.py": "app.visuals.stock_fetcher",
        "video_archive.py": "app.operations.video_archive",
        "visual_assets.py": "app.visuals.visual_assets",
        "visual_quality.py": "app.visuals.visual_quality",
        "workspace_sync.py": "app.operations.workspace_sync",
        "youtube_longform_upload.py": "app.publish.youtube_longform_upload",
        "youtube_upload.py": "app.publish.youtube_upload",
    }
    assert set(targets) == RETIRED_ROOT_WRAPPERS
    for root_name, module_name in targets.items():
        assert not (ROOT / root_name).exists(), root_name
        assert import_module(module_name).__file__ is not None

def test_root_contains_only_working_python_entrypoints() -> None:
    assert {p.name for p in ROOT.glob("*.py")} == {
        "setup_check.py"
    }
