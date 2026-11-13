#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"
install -m 0644 "$ROOT/deployment/systemd/nextdecode-autonomy-worker.service" "$UNIT_DIR/nextdecode-autonomy-worker.service"
systemctl --user daemon-reload
systemctl --user enable --now nextdecode-autonomy-worker.service
systemctl --user --no-pager --full status nextdecode-autonomy-worker.service
