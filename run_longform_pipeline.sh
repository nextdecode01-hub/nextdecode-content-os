#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$ROOT"
if [[ -n "${SHORTS_STUDIO_PYTHON:-}" ]]; then
    PYTHON="$SHORTS_STUDIO_PYTHON"
elif [[ -x "$ROOT/venv/bin/python" ]]; then
    source "$ROOT/venv/bin/activate"
    PYTHON="$ROOT/venv/bin/python"
else
    PYTHON="python3"
fi
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python environment not found: $PYTHON" >&2
    exit 1
fi
"$PYTHON" "$ROOT/create_longform.py"
"$PYTHON" "$ROOT/review_longform.py"
"$PYTHON" "$ROOT/notify_review.py" longform
echo "Long-form video is queued for human review; no upload was started."
