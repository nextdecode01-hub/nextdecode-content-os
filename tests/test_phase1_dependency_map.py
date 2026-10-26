"""Phase 1 smoke test: dependency map matches the live n8n workflow contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "dependency_map.md"
WORKFLOW = ROOT / "workflow_n8n_approved_schedule.json"


def test_map_exists_and_covers_n8n_endpoints() -> None:
    text = DOC.read_text(encoding="utf-8")
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))

    http_urls = {
        node.get("parameters", {}).get("url")
        for node in workflow.get("nodes", [])
        if node.get("type") == "n8n-nodes-base.httpRequest"
    }
    assert http_urls, "workflow has no HTTP request nodes"
    for url in http_urls:
        assert url in text, f"dependency map is missing n8n endpoint: {url}"


def test_map_lists_runner_and_legacy_servers() -> None:
    text = DOC.read_text(encoding="utf-8")
    for required in (
        "/healthz",
        "/run/generate",
        "/run/publish",
        "n8n_runner.py",
        "server_3000.py",
        "server_5678.py",
        "auth_server.py",
        "instagram_reels_upload.py",
    ):
        assert required in text, f"dependency map is missing {required}"


def test_map_lists_canonical_entrypoints() -> None:
    text = DOC.read_text(encoding="utf-8")
    for required in (
        "run_scheduled_generation.sh",
        "run_pipeline.sh",
        "run_longform_pipeline.sh",
        "scheduled_publish.py",
        "create_short.py",
        "create_longform.py",
        "publish_all.py",
    ):
        assert required in text, f"dependency map is missing {required}"
