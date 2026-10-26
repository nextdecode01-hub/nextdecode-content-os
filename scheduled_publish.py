#!/usr/bin/env python3
"""Run the 20:00 IST publishing checks for only today's owner-approved content."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from approval_integrity import upload_window_open
from notify_status import send_status

ROOT = Path(__file__).resolve().parent
IST = ZoneInfo("Asia/Kolkata")


def main() -> int:
    now = datetime.now(IST)
    if not upload_window_open(now):
        message = "Scheduled publishing was skipped because this check ran outside the 20:00 IST hour."
        print(json.dumps({"status": "skipped_outside_window", "local_time": now.isoformat(), "reason": message}))
        send_status("Nextdecode Studio: " + message + " No upload was started.")
        return 2

    commands = [
        [sys.executable, str(ROOT / "publish_all.py"), "--scheduled-approved"],
    ]
    if now.weekday() in {2, 5}:
        commands.append([
            sys.executable,
            str(ROOT / "youtube_longform_upload.py"),
            "--scheduled-approved",
        ])

    results = []
    failed = False
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, check=False)
        results.append({"command": Path(command[1]).name, "exit_code": result.returncode})
        if result.returncode not in {0, 2}:
            failed = True

    print(json.dumps({"status": "completed_with_errors" if failed else "completed", "local_time": now.isoformat(), "results": results}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
