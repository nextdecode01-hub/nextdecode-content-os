#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$ROOT"
PYTHON="${SHORTS_STUDIO_PYTHON:-$ROOT/venv/bin/python}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python environment not found: $PYTHON" >&2
    exit 1
fi

exec 9>"$ROOT/.scheduled_generation.lock"
if ! flock -n 9; then
    "$PYTHON" "$ROOT/notify_status.py" "Nextdecode Studio: a scheduled generation is already running; this duplicate run was skipped." || true
    exit 1
fi

if PUBLISH_MODE=review bash "$ROOT/run_pipeline.sh"; then
    :
else
    status=$?
    "$PYTHON" "$ROOT/notify_status.py" "Nextdecode Studio: scheduled Short generation or review packaging failed; no upload was started." || true
    exit "$status"
fi

weekday="$(TZ=Asia/Kolkata date +%u)"
if [[ "$weekday" == "3" || "$weekday" == "6" ]]; then
    if bash "$ROOT/run_longform_pipeline.sh"; then
        :
    else
        status=$?
        "$PYTHON" "$ROOT/notify_status.py" "Nextdecode Studio: scheduled long-form generation failed; the Short remains queued for review." || true
        exit "$status"
    fi
fi
