#!/usr/bin/env bash
set -euo pipefail
exec /home/demon/shorts_studio/venv/bin/python -m app.autonomy.wait_for_postgres
