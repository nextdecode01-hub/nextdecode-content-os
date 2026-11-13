"""Enforce the clean repository-root policy: no forwarding/compatibility Python files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_PYTHON = {"setup_check.py"}

def test_root_contains_only_operational_python_entrypoints() -> None:
    actual = {path.name for path in ROOT.glob("*.py")}
    assert actual == ALLOWED_ROOT_PYTHON

def test_all_retired_wrapper_targets_exist_in_canonical_packages() -> None:
    targets = (
        "app/operations/analytics_collect.py", "app/operations/meta_preflight.py",
        "app/operations/monetization_tracker.py", "app/operations/review_ledger.py",
        "app/operations/video_archive.py", "app/operations/workspace_sync.py",
        "app/notifications/notify_status.py", "app/notifications/notify_review.py",
        "app/providers/multi_model_ai.py", "app/providers/model_health.py",
        "app/providers/omniroute_client.py", "app/tracking/run_tracker.py",
        "app/publish/social_orchestrator.py", "app/publish/facebook_reels_upload.py",
        "app/publish/instagram_reels_upload.py", "app/publish/youtube_upload.py",
        "app/publish/youtube_longform_upload.py", "app/publish/scheduler.py",
        "app/publish/orchestration.py", "app/publish/authorization.py",
        "app/review/review_bundle.py", "app/review/approve_review.py",
        "app/review/approve_longform.py", "app/review/review_longform.py",
        "app/security/approval_integrity.py", "app/render/legacy_api.py", "app/visuals/motion_director.py",
        "app/visuals/visual_assets.py", "app/visuals/visual_quality.py",
        "app/visuals/stock_fetcher.py", "tools/maintenance/backfill_governance.py",
    )
    for relative in targets:
        assert (ROOT / relative).is_file(), relative
