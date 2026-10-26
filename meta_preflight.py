#!/usr/bin/env python3
"""Validate Meta Page/Instagram settings without creating or publishing media."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)


def env(name: str) -> str:
    return os.getenv(name, "").strip()


def check_graph(version: str, object_id: str, token: str, fields: str) -> tuple[bool, str]:
    try:
        response = requests.get(
            f"https://graph.facebook.com/{version}/{object_id}",
            params={"fields": fields, "access_token": token},
            timeout=30,
        )
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        return False, type(exc).__name__
    if not response.ok or "error" in payload:
        error = payload.get("error", {})
        message = error.get("message", "Meta returned an error") if isinstance(error, dict) else str(error)
        return False, message
    return True, json.dumps({key: payload.get(key) for key in ("id", "name", "username", "account_type") if key in payload}, ensure_ascii=False)


def main() -> int:
    required = ("META_GRAPH_API_VERSION", "FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN", "INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN")
    missing = [name for name in required if not env(name)]
    if missing:
        print(json.dumps({"status": "needs_setup", "missing": missing}, ensure_ascii=False))
        return 2

    version = env("META_GRAPH_API_VERSION")
    checks = {}
    checks["facebook_page"] = check_graph(version, env("FACEBOOK_PAGE_ID"), env("FACEBOOK_PAGE_ACCESS_TOKEN"), "id,name")
    checks["instagram_account"] = check_graph(version, env("INSTAGRAM_USER_ID"), env("INSTAGRAM_ACCESS_TOKEN"), "id,username,account_type")
    result = {"status": "ready" if all(item[0] for item in checks.values()) else "failed", "checks": {key: {"ok": ok, "detail": detail} for key, (ok, detail) in checks.items()}}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
