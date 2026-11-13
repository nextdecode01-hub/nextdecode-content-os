#!/usr/bin/env python3
"""Publish the current MP4 as an Instagram Reel via Meta Graph API.

Meta fetches video_url from the public Internet. If INSTAGRAM_VIDEO_URL is not
provided, this script can expose only this MP4 through a temporary Cloudflare
Quick Tunnel (development/initial integration only; no uptime SLA).
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

from app.publish.authorization import PublishNotAuthorized, authorize_publish, authorization_error, verify_protected_action_decision
from app.publish.artifact_snapshot import ArtifactIntegrityError, upload_snapshot

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)
VIDEO = ROOT / "outputs" / "output_short.mp4"
METADATA = ROOT / "data" / "metadata.json"
LEDGER = ROOT / "data" / "meta_uploads.json"
GRAPH = "https://graph.facebook.com"


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name} in .env; Instagram upload skipped.")
    return value


def api_json(response: requests.Response) -> dict:
    try:
        result = response.json()
    except ValueError:
        response.raise_for_status()
        raise RuntimeError("Meta returned a non-JSON response.")
    if not response.ok or "error" in result:
        error = result.get("error", {})
        message = error.get("message", "Meta Graph API request failed") if isinstance(error, dict) else str(error)
        raise RuntimeError(f"Meta Graph API error: {message}")
    return result


def fingerprint(account_id: str, metadata: dict) -> str:
    content = "\n".join((str(metadata.get("title", "")), str(metadata.get("voice_text", ""))))
    return account_id + ":" + hashlib.sha256(content.strip().lower().encode("utf-8")).hexdigest()


def ledger_read() -> dict:
    if not LEDGER.exists():
        return {"facebook": {}, "instagram": {}}
    value = json.loads(LEDGER.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Meta upload ledger is invalid; refusing a possible duplicate.")
    for platform in ("facebook", "instagram"):
        if platform in value and not isinstance(value[platform], dict):
            raise RuntimeError("Meta upload ledger is invalid; refusing a possible duplicate.")
        value.setdefault(platform, {})
    return value


def ledger_write(value: dict) -> None:
    temp = LEDGER.with_suffix(".json.tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    os.replace(temp, LEDGER)


def wait_until_reachable(url: str, timeout: int = 90) -> bool:
    """Wait until the tunnel hostname resolves and serves the file (DNS propagation)."""
    host = url.split("/")[2]
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        except socket.gaierror:
            time.sleep(5)
            continue
        try:
            response = requests.head(url, timeout=30, allow_redirects=True)
            if response.ok:
                return True
        except requests.RequestException:
            pass
        time.sleep(5)
    return False


def public_video_url(*, serve_path: Path) -> tuple[str, callable]:
    """Expose one MP4 to Meta through a temporary local tunnel.

    The caller must supply the process-local descriptor path returned by
    upload_snapshot(); mutable workspace paths are never valid serving sources.
    """
    served = Path(serve_path)
    if (served.parent not in {Path("/proc/self/fd"), Path("/dev/fd")}
            or not served.name.isdecimal() or not served.is_file()):
        raise ArtifactIntegrityError(
            "Instagram tunnel requires a live descriptor-pinned upload snapshot; "
            "refusing a mutable workspace pathname")
    configured = os.getenv("INSTAGRAM_VIDEO_URL", "").strip()
    if configured:
        raise ArtifactIntegrityError(
            "INSTAGRAM_VIDEO_URL is an external source whose bytes cannot be bound "
            "to the authorized digest; unset it and use the publisher-owned tunnel")

    binary = shutil.which("cloudflared")
    if not binary:
        raise RuntimeError(
            "Instagram needs its publisher-owned temporary tunnel; install cloudflared "
            "and enable INSTAGRAM_TUNNEL_FALLBACK=true")

    route = "/reel/" + secrets.token_urlsafe(24) + ".mp4"
    file_size = served.stat().st_size

    class VideoHandler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            if self.path != route:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def do_GET(self):
            if self.path != route:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with served.open("rb") as stream:
                shutil.copyfileobj(stream, self.wfile, length=1024 * 256)

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), VideoHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    process = subprocess.Popen(
        [binary, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    lines: queue.Queue[str] = queue.Queue()

    def collect():
        if process.stdout:
            for line in process.stdout:
                lines.put(line.rstrip())

    threading.Thread(target=collect, daemon=True).start()
    tunnel_url = None
    deadline = time.time() + 40
    while time.time() < deadline and process.poll() is None:
        try:
            line = lines.get(timeout=1)
        except queue.Empty:
            continue
        match = re.search(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", line)
        if match:
            tunnel_url = match.group(0)
            break
    if not tunnel_url:
        if process.poll() is None:
            process.terminate()
        server.shutdown()
        server.server_close()
        raise RuntimeError("Could not start the temporary Cloudflare tunnel; Instagram upload skipped.")

    video_url = tunnel_url + route
    if not wait_until_reachable(video_url):
        if process.poll() is None:
            process.terminate()
        server.shutdown()
        server.server_close()
        raise RuntimeError("The temporary Cloudflare tunnel was not reachable yet; Instagram upload skipped.")

    def cleanup():
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        server.shutdown()
        server.server_close()
    return video_url, cleanup


def publish(*, dry_run: bool = False) -> dict:
    version = required("META_GRAPH_API_VERSION")
    ig_user_id = required("INSTAGRAM_USER_ID")
    token = required("INSTAGRAM_ACCESS_TOKEN")
    if not METADATA.exists() or not VIDEO.exists() or VIDEO.stat().st_size < 150_000:
        raise RuntimeError("A valid generated MP4 and metadata.json are required; Instagram upload skipped.")

    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    platform_copy = metadata.get("platform_copy", {})
    if not isinstance(platform_copy, dict):
        platform_copy = {}
    title = str(metadata.get("title", "")).strip()
    tags = metadata.get("tags", [])
    if not title or not isinstance(tags, list):
        raise RuntimeError("Instagram caption metadata is invalid; upload skipped.")
    caption = str(platform_copy.get("instagram_caption", "")).strip()
    if not caption:
        caption = title
    sources = metadata.get("source_urls", [])
    if isinstance(sources, list) and sources:
        caption += "\n\nSource: " + str(sources[0])
    hashtags = metadata.get("instagram_hashtags", tags)
    if isinstance(hashtags, list) and hashtags:
        caption += "\n\n" + " ".join(str(tag) for tag in hashtags[:5])
    caption = caption[:2200]

    decision = authorize_publish(platform="instagram", purpose="short", data_root=ROOT,
                                 metadata_file=METADATA, video_file=VIDEO)

    # ND-M3-R1-FIX: caller-supplied URLs and environment markers are never
    # authorization. Reject this configuration before *any* early return
    # (including dry-run and duplicate-ledger outcomes), so every invocation
    # reports the same unsafe external-source configuration consistently.
    if os.getenv("INSTAGRAM_VIDEO_URL", "").strip():
        raise ArtifactIntegrityError(
            "INSTAGRAM_VIDEO_URL is an unverified external source; refusing to publish "
            "bytes that cannot be bound to the authorized video digest")

    if dry_run:
        print(json.dumps({"status": "dry_run", "uploaded": False, "platform": "instagram",
                          "title": title}))
        return {"status": "dry_run"}

    key = fingerprint(ig_user_id, metadata)
    ledger = ledger_read()
    if key in ledger["instagram"]:
        previous = ledger["instagram"][key]
        print(json.dumps({"status": "skipped_duplicate", "media_id": previous.get("media_id", "")}))
        return {"status": "skipped_duplicate"}
    verify_protected_action_decision(decision, platform="instagram", purpose="short")
    with upload_snapshot(VIDEO, decision["video_sha256"], root=ROOT) as snapshot:
        video_url, cleanup = public_video_url(serve_path=snapshot.path)  # type: ignore[arg-type]
        base = f"{GRAPH}/{version}"
        try:
            created = api_json(requests.post(
                f"{base}/{ig_user_id}/media",
                data={"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=45,
            ))
            container_id = created.get("id")
            if not container_id:
                raise RuntimeError("Meta did not return an Instagram media container.")

            deadline = time.time() + 12 * 60
            status_code = "IN_PROGRESS"
            while time.time() < deadline:
                status = api_json(requests.get(
                    f"{base}/{container_id}",
                    params={"fields": "status_code,status"},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30,
                ))
                status_code = status.get("status_code", "")
                if status_code == "FINISHED":
                    break
                if status_code in {"ERROR", "EXPIRED"}:
                    raise RuntimeError(f"Instagram media processing ended with {status_code}.")
                time.sleep(10)
            if status_code != "FINISHED":
                raise RuntimeError("Instagram media processing timed out; upload not published.")

            published = api_json(requests.post(
                f"{base}/{ig_user_id}/media_publish",
                data={"creation_id": container_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=45,
            ))
            media_id = published.get("id")
            if not media_id:
                raise RuntimeError("Meta did not return a published Instagram media ID.")
            ledger["instagram"][key] = {
                "media_id": media_id,
                "title": title,
                "content_pillar": metadata.get("content_pillar", ""),
                "hook": metadata.get("hook", ""),
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                ledger_write(ledger)
            except OSError as exc:
                # The Reel is already live; retrying the publish would duplicate it.
                print(json.dumps({"status": "ambiguous", "uploaded": True, "media_id": media_id,
                                  "reason": "Instagram published but the local duplicate ledger could not "
                                            "be written; reconcile before retrying",
                                  "error": type(exc).__name__}, ensure_ascii=False))
                return {"status": "ambiguous", "media_id": media_id}
            print(json.dumps({"status": "published", "media_id": media_id, "title": title}))
            return {"status": "published", "media_id": media_id}
        finally:
            cleanup()


if __name__ == "__main__":
    try:
        outcome = publish(dry_run="--dry-run" in sys.argv)
    except PublishNotAuthorized as exc:
        code, reason = authorization_error(exc)
        print(json.dumps({"status": code, "reason": reason}, ensure_ascii=False))
        raise SystemExit(2)
    except ArtifactIntegrityError as exc:
        # ND-M3-F1: digests diverged after authorization; Meta fetched nothing.
        print(json.dumps({"status": "blocked_artifact_integrity", "uploaded": False,
                          "reason": str(exc)}, ensure_ascii=False))
        raise SystemExit(2)
    except Exception as exc:
        print(f"Instagram Reel publish failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if outcome.get("status") == "ambiguous":
        raise SystemExit(3)


