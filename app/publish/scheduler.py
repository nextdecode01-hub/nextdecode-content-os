#!/usr/bin/env python3
"""Run the 20:00 IST publishing checks for only today's owner-approved content."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.security.approval_integrity import upload_window_open
from app.notifications.notify_status import send_status
ROOT = Path(__file__).resolve().parents[2]
IST = ZoneInfo("Asia/Kolkata")


def main() -> int:
    now = datetime.now(IST)
    if not upload_window_open(now):
        message = "Scheduled publishing was skipped because this check ran outside the 20:00 IST hour."
        print(json.dumps({"status": "skipped_outside_window", "local_time": now.isoformat(), "reason": message}))
        send_status("Nextdecode Studio: " + message + " No upload was started.")
        return 2

    commands = [
        ([sys.executable, "-m", "app.publish.orchestration", "--scheduled-approved"], None),
    ]
    if now.weekday() in {2, 5}:
        # ND-ENG-006-R7 (P0): the scheduling flag is a window restriction, not an
        # authorization. The adapter now requires the owner-release env gate on
        # every attempt; the scheduler — which already verified the 20:00 IST
        # window above and holds the scheduled owner release — grants that env to
        # the long-form child explicitly.
        longform_env = dict(os.environ)
        longform_env["PUBLISH_MODE"] = "publish"
        longform_env["AUTO_PUBLISH_APPROVED"] = "true"
        commands.append((
            [sys.executable, "-m", "app.publish.youtube_longform_upload", "--scheduled-approved"],
            longform_env,
        ))

    results = []
    failed = False
    ambiguous = False
    blocked = False
    # Exit-code contract (ND-ENG-002B): 0 = completed, 2 = policy blocked,
    # 3 = ambiguous external outcome; every other code is a plain failure.
    outcome_by_code = {0: "completed", 2: "blocked_policy", 3: "ambiguous"}
    for command, child_env in commands:
        result = subprocess.run(command, cwd=ROOT, check=False, env=child_env)
        outcome = outcome_by_code.get(result.returncode, "failed")
        if outcome == "ambiguous":
            ambiguous = True
        if outcome == "blocked_policy":
            blocked = True
        results.append({"command": command[-1].rsplit(".", 1)[-1], "exit_code": result.returncode,
                        "outcome": outcome})
        if outcome not in {"completed", "blocked_policy"}:
            failed = True

    # Top-level status mirrors the aggregate exit ladder (ND-ENG-002B-R4):
    # blocked > ambiguous > failed > completed.
    if blocked:
        top_status = "blocked"
    elif ambiguous:
        top_status = "ambiguous"
    elif failed:
        top_status = "failed"
    else:
        top_status = "completed"

    print(json.dumps({"status": top_status,
                      "ambiguous": ambiguous, "local_time": now.isoformat(), "results": results}))
    # Aggregate exit precedence mirrors publish_all (ND-ENG-002B): a policy
    # stop must not be retried by automation, ambiguity requires manual
    # reconciliation, and an ordinary failure ranks below both.
    if blocked:
        return 2
    if ambiguous:
        return 3
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
