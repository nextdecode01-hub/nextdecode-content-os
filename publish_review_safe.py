#!/usr/bin/env python3
"""Run publishing without turning an intentional review block into an n8n failure."""
from __future__ import annotations

import json
import os

from publish_all import run


def main() -> int:
    status = run()
    review_only = os.getenv("PUBLISH_MODE", "review").strip().lower() != "publish" or os.getenv("AUTO_PUBLISH_APPROVED", "false").strip().lower() != "true"
    if status == 2 and review_only:
        print(json.dumps({"status": "review_ready", "message": "Publishing is intentionally waiting for human approval."}))
        return 0
    return status


if __name__ == "__main__":
    raise SystemExit(main())
