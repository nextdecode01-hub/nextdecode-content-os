"""Regression tests for the notification-only Telegram boundary.

Telegram is an outbound notification channel in this milestone. It must not
become an approval or publishing-control channel without a separately approved
contract and implementation.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path: str) -> str:
    if relative_path in {"notify_status.py", "notify_review.py"}:
        relative_path = f"app/notifications/{relative_path}"
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _tree(relative_path: str) -> ast.Module:
    return ast.parse(_source(relative_path), filename=relative_path)


def test_telegram_http_surface_is_outbound_send_message_only():
    source = _source("notify_status.py")
    assert source.count("https://api.telegram.org/bot{token}/sendMessage") == 1
    for forbidden in ("getUpdates", "setWebhook", "answerCallbackQuery", "callback_query"):
        assert forbidden not in source


def test_api_exposes_no_telegram_webhook_or_callback_route():
    tree = _tree("api/main.py")
    route_paths: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not (isinstance(func, ast.Attribute) and func.attr in {"get", "post", "put", "patch", "delete"}):
                continue
            if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                route_paths.append(decorator.args[0].value.lower())
    assert [path for path in route_paths if "telegram" in path or "webhook" in path] == []


def test_review_reminder_uses_manual_local_approval_not_callback_handler():
    source = _source("notify_review.py")
    tree = _tree("notify_review.py")
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    imported_modules = []
    for node in imports:
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif node.module:
            imported_modules.append(node.module)
    assert not any("approve" in module or "publish" in module for module in imported_modules)
    assert "callback_query" not in source
    assert "answerCallbackQuery" not in source
    assert "--interactive" in source


def test_telegram_notifier_does_not_write_approval_or_publish_state():
    tree = _tree("notify_status.py")
    forbidden_names = {
        "approve_review", "approve_longform", "authorize_publish",
        "verify_approval_binding", "publish_all", "AUTO_PUBLISH_APPROVED",
    }
    identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    identifiers.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    identifiers.update(node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module)
    assert identifiers.isdisjoint(forbidden_names)


def test_api_redaction_covers_short_query_tokens_and_cloudflare_id_credentials(monkeypatch):
    from api import main as api_main

    monkeypatch.setenv("CF_ACCOUNT_ID", "acct-id-123456")
    redacted = api_main._redact("https://example.test/?token=abc&account=acct-id-123456")
    assert "token=abc" not in redacted
    assert "acct-id-123456" not in redacted


def test_send_status_performs_one_outbound_post_to_telegram_send_message(monkeypatch):
    import json
    from urllib.parse import urlparse

    from app.notifications import notify_status as notify_status

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-bot-token-123456")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat-123")
    captured = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        captured.append((request, timeout))
        return FakeResponse()

    monkeypatch.setattr(notify_status, "urlopen", fake_urlopen)

    assert notify_status.send_status("pipeline finished") is True
    assert len(captured) == 1
    request, timeout = captured[0]
    parsed = urlparse(request.full_url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "api.telegram.org"
    assert parsed.path.endswith("/sendMessage")
    assert request.get_method() == "POST"
    assert json.loads(request.data.decode("utf-8")) == {
        "chat_id": "test-chat-123",
        "text": "pipeline finished",
        "disable_web_page_preview": True,
    }
    assert timeout == 12


def test_registered_api_routes_have_no_telegram_or_webhook_control_surface():
    from api import main as api_main

    route_paths = [
        str(getattr(route, "path", "")).lower()
        for route in api_main.app.routes
    ]
    assert not [
        path for path in route_paths
        if "telegram" in path or "webhook" in path
    ]


def test_notification_modules_expose_no_inbound_telegram_methods():
    forbidden_markers = (
        "getUpdates",
        "setWebhook",
        "answerCallbackQuery",
        "callback_query",
        "callback_data",
        "editMessageText",
    )
    for filename in ("notify_status.py", "notify_review.py"):
        source = _source(filename)
        for marker in forbidden_markers:
            assert marker not in source, f"{filename} contains inbound Telegram marker {marker!r}"


def test_registered_api_routes_have_no_callback_endpoint():
    from api import main as api_main

    route_paths = [
        str(getattr(route, "path", "")).lower()
        for route in api_main.app.routes
    ]
    assert not [path for path in route_paths if "callback" in path]


def test_notification_modules_have_canonical_package_locations() -> None:
    from app.notifications import notify_status, notify_review

    assert Path(notify_status.__file__).resolve() == ROOT / "app" / "notifications" / "notify_status.py"
    assert Path(notify_review.__file__).resolve() == ROOT / "app" / "notifications" / "notify_review.py"
    assert not (ROOT / "notify_status.py").exists()
    assert not (ROOT / "notify_review.py").exists()


def test_notification_module_cli_entrypoints_work_without_root_shims() -> None:
    import os
    import subprocess
    import sys

    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    review_help = subprocess.run(
        [sys.executable, "-m", "app.notifications.notify_review", "--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert review_help.returncode == 0
    assert "usage:" in review_help.stdout.lower()

    status_no_args = subprocess.run(
        [sys.executable, "-m", "app.notifications.notify_status"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert status_no_args.returncode == 2
