"""Keep application code on canonical package imports after root-shim migration."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_MODULES = {
    "analytics_collect",
    "meta_preflight",
    "monetization_tracker",
    "review_ledger",
    "video_archive",
    "workspace_sync",
    "notify_status",
    "notify_review",
    "multi_model_ai",
    "model_health",
    "omniroute_client",
    "run_tracker",
    "approval_integrity",
    "publish_authorization",
}
SCAN_ROOTS = (ROOT / "app", ROOT / "pipelines")
ROOT_ORCHESTRATORS = (ROOT / "app" / "publish" / "orchestration.py", ROOT / "app" / "publish" / "scheduler.py", ROOT / "app" / "publish" / "social_orchestrator.py")


def _legacy_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                alias.name
                for alias in node.names
                if alias.name in LEGACY_MODULES
            )
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module in LEGACY_MODULES:
                found.append(node.module)
    return found


def test_application_and_pipeline_code_use_canonical_packages() -> None:
    offenders = []
    for base in SCAN_ROOTS:
        for path in base.rglob("*.py"):
            imports = _legacy_imports(path)
            if imports:
                offenders.append(f"{path.relative_to(ROOT)}: {sorted(set(imports))}")
    assert not offenders, "legacy root imports remain in app/pipelines: " + "; ".join(offenders)


def test_root_orchestrators_use_canonical_notification_package() -> None:
    offenders = []
    for path in ROOT_ORCHESTRATORS:
        imports = _legacy_imports(path)
        if imports:
            offenders.append(f"{path.name}: {sorted(set(imports))}")
    assert not offenders, "root orchestrators still import compatibility shims: " + "; ".join(offenders)
