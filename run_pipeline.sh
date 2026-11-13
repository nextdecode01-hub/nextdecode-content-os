#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"
if [[ -n "${SHORTS_STUDIO_PYTHON:-}" ]]; then
    PYTHON="$SHORTS_STUDIO_PYTHON"
else
    source "$DIR/venv/bin/activate"
    PYTHON="$DIR/venv/bin/python"
fi
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python environment not found: $PYTHON" >&2
    exit 1
fi

if "$PYTHON" "$DIR/pipelines/short.py" "$@"; then
    :
else
    status=$?
    "$PYTHON" -m app.notifications.notify_status "Nextdecode Shorts Studio: video generation failed before publishing. Check the execution for details." || true
    exit "$status"
fi

"$PYTHON" -m app.review.review_bundle

if [[ "${PUBLISH_MODE:-review}" != "publish" ]]; then
    "$PYTHON" -m app.notifications.notify_review short
    exit 0
fi

"$PYTHON" -m app.publish.orchestration
