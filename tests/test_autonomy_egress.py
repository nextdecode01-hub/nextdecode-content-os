from __future__ import annotations

import base64
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from app.autonomy.egress_proxy import (
    EgressProxy, SANDBOX_SITECUSTOMIZE, _fetch, validate_public_url,
)
from app.autonomy.sandbox import SandboxUnavailable, build_bwrap_command


def test_public_url_guard_rejects_loopback_private_and_metadata_ranges():
    for url in (
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://localhost/",
    ):
        with pytest.raises(ValueError):
            validate_public_url(url)


def test_public_url_guard_rejects_non_http_schemes_and_nonstandard_ports():
    with pytest.raises(ValueError, match="unsupported_url"):
        validate_public_url("file:///etc/passwd")
    with pytest.raises(ValueError, match="non_public_address_forbidden"):
        validate_public_url("http://192.0.2.1/")
    with pytest.raises(ValueError, match="non_standard_port_forbidden"):
        validate_public_url("https://8.8.8.8:8443/")


def test_broker_rejects_methods_other_than_get_and_head():
    assert _fetch({"method": "POST", "url": "https://example.com"}) == {
        "error": "method_not_allowed"
    }


def test_broker_filters_credentials_and_returns_bounded_response(monkeypatch):
    import app.autonomy.egress_proxy as proxy

    monkeypatch.setattr(
        proxy, "validate_public_url",
        lambda _url: proxy._ValidatedHost("example.com", "8.8.8.8"),
    )

    class FakeResponse:
        status_code = 200
        url = "https://example.com/"
        headers = {"Content-Type": "text/plain", "Set-Cookie": "secret=hidden"}

        def iter_content(self, chunk_size):
            yield b"hello"

        def close(self):
            pass

    class FakeSession:
        trust_env = True

        def request(self, method, url, **kwargs):
            assert method == "GET"
            assert "Authorization" not in kwargs["headers"]
            assert "Cookie" not in kwargs["headers"]
            return FakeResponse()

        def close(self):
            pass

    monkeypatch.setattr(proxy.requests, "Session", FakeSession)
    result = proxy._fetch({
        "method": "GET", "url": "https://example.com/",
        "headers": {"Authorization": "Bearer secret", "Cookie": "secret=1",
                    "User-Agent": "NEXTDECODE test"},
    })
    assert result["status_code"] == 200
    assert base64.b64decode(result["body"]) == b"hello"
    assert "Set-Cookie" not in result["headers"]


def test_bwrap_network_access_requires_broker_and_always_unshares_ip_network():
    with pytest.raises(SandboxUnavailable, match="restricted egress broker"):
        build_bwrap_command("app.autonomy.specialist_cli", ["--help"], network_access=True)

    with EgressProxy() as broker:
        command = build_bwrap_command(
            "app.autonomy.specialist_cli", ["--help"],
            network_access=True, egress_dir=broker.directory,
        )
        assert "--unshare-net" in command
        assert ["--ro-bind", str(broker.directory), "/run/nextdecode-egress"] == command[
            command.index("--ro-bind", command.index("--bind") + 3):
            command.index("--ro-bind", command.index("--bind") + 3) + 3
        ]
        assert "/run/nextdecode-egress/broker.sock" in command
        assert "/run/nextdecode-egress:/workspace" in command


def test_sitecustomize_routes_requests_through_unix_socket(tmp_path):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            request = json.loads(self.rfile.readline())
            assert request["method"] == "GET"
            assert request["url"] == "https://example.com/test"
            response = {
                "status_code": 200, "url": request["url"],
                "headers": {"Content-Type": "text/plain; charset=utf-8"},
                "body": base64.b64encode(b"brokered").decode("ascii"),
            }
            self.wfile.write((json.dumps(response) + "\n").encode())

    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True

    socket_path = str(tmp_path / "egress.sock")
    server = Server(socket_path, Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        (tmp_path / "sitecustomize.py").write_text(SANDBOX_SITECUSTOMIZE, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path)
        env["NEXTDECODE_EGRESS_SOCKET"] = socket_path
        result = subprocess.run(
            [sys.executable, "-c",
             "import requests; r=requests.get('https://example.com/test'); "
             "print(r.status_code, r.text)"],
            env=env, capture_output=True, text=True, timeout=10, check=True,
        )
        assert result.stdout.strip() == "200 brokered"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)



def test_local_model_proxy_is_capability_scoped_and_model_allowlisted(monkeypatch):
    import app.autonomy.egress_proxy as proxy

    request = {
        "method": "POST", "url": "http://127.0.0.1:11434/api/chat",
        "local_model_access": True,
        "json": {
            "model": "gemma3:4b", "stream": False,
            "messages": [{"role": "user", "content": "Draft a concise outline"}],
        },
    }
    assert proxy._fetch(request, allow_local_model=False)["error"] == "local_model_scope_denied"

    class FakeResponse:
        status_code = 200
        url = request["url"]
        headers = {"Content-Type": "application/json"}

        def iter_content(self, chunk_size):
            yield b'{"message":{"content":"ok"}}'

        def close(self):
            pass

    class FakeSession:
        trust_env = True

        def post(self, url, **kwargs):
            assert url == request["url"]
            assert kwargs["json"]["model"] == "gemma3:4b"
            return FakeResponse()

        def close(self):
            pass

    monkeypatch.setattr(proxy.requests, "Session", FakeSession)
    result = proxy._fetch(request, allow_local_model=True)
    assert result["status_code"] == 200
    assert json.loads(base64.b64decode(result["body"]))["message"]["content"] == "ok"

    unsafe = {**request, "json": {**request["json"], "model": "unapproved-model"}}
    assert proxy._fetch(unsafe, allow_local_model=True)["error"] == "local_model_payload_rejected"



def test_broker_revalidates_redirect_targets_before_following(monkeypatch):
    import app.autonomy.egress_proxy as proxy

    original_guard = proxy.validate_public_url
    checked = []

    def guard(url):
        checked.append(url)
        if url == "https://example.com/start":
            return proxy._ValidatedHost("example.com", "8.8.8.8")
        return original_guard(url)

    class RedirectResponse:
        status_code = 302
        url = "https://example.com/start"
        headers = {"Location": "http://127.0.0.1:11434/api/chat"}

        def close(self):
            pass

    class FakeSession:
        trust_env = True
        calls = 0

        def request(self, method, url, **kwargs):
            self.calls += 1
            return RedirectResponse()

        def close(self):
            pass

    fake = FakeSession()
    monkeypatch.setattr(proxy, "validate_public_url", guard)
    monkeypatch.setattr(proxy.requests, "Session", lambda: fake)
    result = proxy._fetch({"method": "GET", "url": "https://example.com/start"})
    assert result["error"] == "egress_request_rejected_or_failed"
    assert checked == ["https://example.com/start", "http://127.0.0.1:11434/api/chat"]
    assert fake.calls == 1



def test_public_url_guard_rejects_mixed_public_and_private_dns_answers(monkeypatch):
    import socket
    import app.autonomy.egress_proxy as proxy

    monkeypatch.setattr(proxy.socket, "getaddrinfo", lambda *args, **kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.7", 443)),
    ])
    with pytest.raises(ValueError, match="non_public_address_forbidden"):
        proxy.validate_public_url("https://mixed.example/")



def test_validated_dns_address_is_pinned_for_socket_connect_and_hostname_is_preserved(monkeypatch):
    import requests
    import app.autonomy.egress_proxy as proxy

    resolutions = []
    connects = []

    def resolve(host, port, **kwargs):
        resolutions.append((host, port))
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", port))]

    def connect(address, timeout, **kwargs):
        connects.append(address)
        return object()

    monkeypatch.setattr(proxy.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(proxy, "create_connection", connect)
    validated = proxy.validate_public_url("https://rebinding.example/path")
    assert validated == "rebinding.example"
    assert validated.pinned_ip == "8.8.8.8"

    session = requests.Session()
    try:
        proxy._pinned_session(session, validated.pinned_ip)
        adapter = session.get_adapter("https://")
        pool = adapter.poolmanager.connection_from_host(
            "rebinding.example", port=443, scheme="https"
        )
        connection = pool._new_conn()
        connection._new_conn()
        assert connects == [("8.8.8.8", 443)]
        assert resolutions == [("rebinding.example", 443)]
        assert connection.host == "rebinding.example"
    finally:
        session.close()


def test_dns_rebinding_after_validation_cannot_change_pinned_destination(monkeypatch):
    import requests
    import app.autonomy.egress_proxy as proxy

    dns_calls = []
    connect_targets = []

    def changing_dns(host, port, **kwargs):
        dns_calls.append(host)
        address = "8.8.4.4" if len(dns_calls) == 1 else "127.0.0.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    monkeypatch.setattr(proxy.socket, "getaddrinfo", changing_dns)
    monkeypatch.setattr(
        proxy, "create_connection",
        lambda address, timeout, **kwargs: connect_targets.append(address) or object(),
    )
    validated = proxy.validate_public_url("https://rebind.example/")
    assert validated.pinned_ip == "8.8.4.4"

    session = requests.Session()
    try:
        proxy._pinned_session(session, validated.pinned_ip)
        pool = session.get_adapter("https://").poolmanager.connection_from_host(
            "rebind.example", port=443, scheme="https"
        )
        connection = pool._new_conn()
        connection._new_conn()
        assert connection.host == "rebind.example"
    finally:
        session.close()

    assert dns_calls == ["rebind.example"]
    assert connect_targets == [("8.8.4.4", 443)]
