"""Per-task public-web egress broker for network-enabled specialists."""
from __future__ import annotations

import base64
import ipaddress
import json
import shutil
import socket
import socketserver
import tempfile
import threading
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
import urllib3.connection
import urllib3.connectionpool
from urllib3.util.connection import create_connection
from urllib3.exceptions import NewConnectionError

MAX_REQUEST_BYTES = 1_048_576
MAX_RESPONSE_BYTES = 4_000_000
MAX_REDIRECTS = 5
BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".test", ".invalid")


class _ValidatedHost(str):
    """String-compatible validated hostname carrying the exact checked IP."""
    def __new__(cls, hostname: str, pinned_ip: str):
        value = super().__new__(cls, hostname)
        value.pinned_ip = pinned_ip
        return value


def validate_public_url(url: str) -> str:
    if not isinstance(url, str) or len(url) > 4096:
        raise ValueError("invalid_url")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("unsupported_url")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("url_credentials_or_fragment_forbidden")
    if parsed.port is not None and parsed.port not in {80, 443}:
        raise ValueError("non_standard_port_forbidden")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "metadata.google.internal"} or host.endswith(BLOCKED_SUFFIXES):
        raise ValueError("non_public_host_forbidden")
    try:
        address = ipaddress.ip_address(host)
        addresses = [str(address)]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80),
                                         type=socket.SOCK_STREAM)
        except OSError:
            raise ValueError("host_resolution_failed") from None
        addresses = list(dict.fromkeys(item[4][0].split("%", 1)[0] for item in records))
    if not addresses or any(not ipaddress.ip_address(item).is_global for item in addresses):
        raise ValueError("non_public_address_forbidden")
    # Carry the exact checked address to the socket layer. The original
    # hostname remains in the pool for Host header, TLS SNI and cert checks.
    return _ValidatedHost(host, addresses[0])


def _pinned_session(session: requests.Session, pinned_ip: str) -> None:
    """Mount connection pools that cannot perform a second DNS lookup."""
    class PinnedHTTPConnection(urllib3.connection.HTTPConnection):
        _nd_pinned_ip = pinned_ip

        def _new_conn(self):
            try:
                return create_connection((self._nd_pinned_ip, self.port), self.timeout,
                                         source_address=self.source_address,
                                         socket_options=self.socket_options)
            except OSError as exc:
                raise NewConnectionError(self, f"Pinned connection failed: {exc}") from exc

    class PinnedHTTPSConnection(urllib3.connection.HTTPSConnection):
        _nd_pinned_ip = pinned_ip

        def _new_conn(self):
            try:
                return create_connection((self._nd_pinned_ip, self.port), self.timeout,
                                         source_address=self.source_address,
                                         socket_options=self.socket_options)
            except OSError as exc:
                raise NewConnectionError(self, f"Pinned connection failed: {exc}") from exc

    class PinnedHTTPPool(urllib3.connectionpool.HTTPConnectionPool):
        ConnectionCls = PinnedHTTPConnection

    class PinnedHTTPSPool(urllib3.connectionpool.HTTPSConnectionPool):
        ConnectionCls = PinnedHTTPSConnection

    # Test doubles used by the unit suite do not expose Requests adapters.
    if not hasattr(session, "mount") or not hasattr(session, "get_adapter"):
        return
    old_http = session.get_adapter("http://")
    old_https = session.get_adapter("https://")
    old_http.close()
    if old_https is not old_http:
        old_https.close()
    session.mount("http://", requests.adapters.HTTPAdapter())
    session.mount("https://", requests.adapters.HTTPAdapter())
    for adapter in (session.get_adapter("http://"), session.get_adapter("https://")):
        adapter.poolmanager.pool_classes_by_scheme = {
            "http": PinnedHTTPPool, "https": PinnedHTTPSPool,
        }


def _fetch(request: dict, *, allow_local_model: bool = False) -> dict:
    method = str(request.get("method", "GET")).upper()
    url = str(request.get("url", ""))
    local_model = url == "http://127.0.0.1:11434/api/chat"
    if local_model:
        payload = request.get("json")
        if (not allow_local_model or request.get("local_model_access") is not True
                or method != "POST" or not isinstance(payload, dict)):
            return {"error": "local_model_scope_denied"}
        messages = payload.get("messages")
        model = payload.get("model")
        if (model != "gemma3:4b" or payload.get("stream") is not False
                or not isinstance(messages, list) or not 1 <= len(messages) <= 16
                or any(not isinstance(item, dict) or item.get("role") not in {"system", "user", "assistant"}
                       or not isinstance(item.get("content"), str) or len(item["content"]) > 20_000
                       for item in messages)
                or len(json.dumps(payload)) > 100_000):
            return {"error": "local_model_payload_rejected"}
    elif method not in {"GET", "HEAD"}:
        return {"error": "method_not_allowed"}
    headers_in = request.get("headers", {})
    if not isinstance(headers_in, dict):
        return {"error": "invalid_headers"}
    safe_headers = {}
    for key, value in headers_in.items():
        if str(key).lower() in {"accept", "accept-language", "user-agent"}:
            safe_headers[str(key)] = str(value)[:500]
    params = request.get("params")
    if params is not None and not isinstance(params, (dict, list, tuple)):
        return {"error": "invalid_params"}
    session = requests.Session()
    session.trust_env = False
    response = None
    try:
        timeout = max(1, min(float(request.get("timeout") or 15), 180 if local_model else 25))
        response = None
        if local_model:
            response = session.post(url, json=payload, timeout=timeout,
                                    allow_redirects=False, stream=True)
        else:
            for redirect in range(MAX_REDIRECTS + 1):
                validated_host = validate_public_url(url)
                pinned_ip = getattr(validated_host, "pinned_ip", None)
                if not pinned_ip:
                    raise ValueError("validated_address_missing")
                _pinned_session(session, pinned_ip)
                response = session.request(method, url, headers=safe_headers,
                    params=params if redirect == 0 else None, timeout=timeout,
                    allow_redirects=False, stream=True)
                params = None
                if response.status_code not in {301, 302, 303, 307, 308}:
                    break
                location = response.headers.get("Location")
                response.close()
                if not location or redirect >= MAX_REDIRECTS:
                    return {"error": "redirect_limit_or_missing_location"}
                url = urljoin(url, location)
        if response is None:
            return {"error": "empty_response"}
        body = b""
        if method != "HEAD":
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    response.close()
                    return {"error": "response_too_large"}
                chunks.append(chunk)
            body = b"".join(chunks)
        return {
            "status_code": response.status_code, "url": response.url,
            "headers": {k: v for k, v in response.headers.items()
                if k.lower() in {"content-type", "content-length", "last-modified",
                                 "etag", "location", "cache-control"}},
            "body": base64.b64encode(body).decode("ascii"),
        }
    except (ValueError, requests.RequestException, OSError, TypeError):
        return {"error": "egress_request_rejected_or_failed"}
    finally:
        if response is not None:
            response.close()
        session.close()


class _Handler(socketserver.StreamRequestHandler):
    allow_local_model = False

    def handle(self):
        raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES or not raw.endswith(b"\n"):
            result = {"error": "request_too_large"}
        else:
            try:
                payload = json.loads(raw)
                result = (_fetch(payload, allow_local_model=self.allow_local_model)
                          if isinstance(payload, dict) else {"error": "invalid_request"})
            except (ValueError, UnicodeDecodeError):
                result = {"error": "invalid_request"}
        self.wfile.write((json.dumps(result, separators=(",", ":")) + "\n").encode())


class _UnixServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    allow_reuse_address = False


class EgressProxy:
    """Short-lived UDS broker; specialists receive no IP network namespace."""
    def __init__(self, *, allow_local_model: bool = False):
        self.directory = Path(tempfile.mkdtemp(prefix="nd-egress-"))
        self.directory.chmod(0o700)
        self.socket_path = self.directory / "broker.sock"
        handler = type("ScopedEgressHandler", (_Handler,), {
            "allow_local_model": bool(allow_local_model)
        })
        self.server = _UnixServer(str(self.socket_path), handler)
        self.socket_path.chmod(0o600)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       name="nextdecode-egress", daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        shutil.rmtree(self.directory, ignore_errors=True)


SANDBOX_SITECUSTOMIZE = r"""
import base64, json, os, socket
import requests
_SOCKET = os.environ.get("NEXTDECODE_EGRESS_SOCKET")
if _SOCKET:
    def _broker_request(method, url, **kwargs):
        data = kwargs.get("data")
        if isinstance(data, bytes):
            data = {"__base64__": base64.b64encode(data).decode("ascii")}
        payload = {"method": str(method).upper(), "url": url, "headers": kwargs.get("headers") or {},
                   "params": kwargs.get("params"), "json": kwargs.get("json"),
                   "local_model_access": os.environ.get("NEXTDECODE_LOCAL_MODEL_ACCESS") == "1",
                   "timeout": kwargs.get("timeout", 15)}
        raw = (json.dumps(payload, separators=(",", ":")) + "\n").encode()
        if len(raw) > 1048576:
            raise requests.RequestException("egress request exceeds size limit")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            broker_timeout = min(190, max(30, float(kwargs.get("timeout") or 15) + 10))
            sock.settimeout(broker_timeout)
            sock.connect(_SOCKET)
            sock.sendall(raw)
            chunks = bytearray()
            while not chunks.endswith(b"\n"):
                part = sock.recv(65536)
                if not part:
                    break
                chunks.extend(part)
                if len(chunks) > 5000000:
                    raise requests.RequestException("egress response exceeds size limit")
        except OSError:
            raise requests.RequestException("restricted egress broker unavailable") from None
        finally:
            sock.close()
        try:
            result = json.loads(bytes(chunks).split(b"\n", 1)[0])
        except Exception:
            raise requests.RequestException("invalid egress broker response") from None
        if result.get("error"):
            raise requests.RequestException(result["error"])
        response = requests.Response()
        response.status_code = int(result["status_code"])
        response.url = result["url"]
        response.headers.update(result.get("headers") or {})
        response._content = base64.b64decode(result.get("body", ""))
        response.encoding = requests.utils.get_encoding_from_headers(response.headers)
        response.request = requests.Request(method=method, url=url).prepare()
        response.history, response.reason, response.elapsed = [], "", 0
        return response
    def _restricted_request(self, method, url, **kwargs):
        if kwargs.get("auth") or kwargs.get("cookies") or kwargs.get("files"):
            raise requests.RequestException("credentials and file uploads are forbidden in specialist egress")
        return _broker_request(method, url, **kwargs)
    requests.Session.request = _restricted_request
"""
