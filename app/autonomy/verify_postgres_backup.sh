#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/demon/shorts_studio"
BACKUP="${1-}"
if [[ -z "$BACKUP" ]]; then
  echo "Usage: $0 /absolute/path/to/autonomy-YYYYMMDDTHHMMSSZ.dump" >&2
  exit 2
fi
if [[ "$BACKUP" != /* ]]; then
  BACKUP="$ROOT/$BACKUP"
fi
if [[ ! -f "$BACKUP" || ! -s "$BACKUP" ]]; then
  echo "Backup file is missing or empty: $BACKUP" >&2
  exit 1
fi

DIR="$(dirname "$BACKUP")"
NAME="$(basename "$BACKUP")"
SIDECAR="$BACKUP.sha256"
if [[ ! -f "$SIDECAR" ]]; then
  echo "Checksum sidecar is missing: $SIDECAR" >&2
  echo "Legacy backup: archive validation only is available; no checksum claim can be made." >&2
  exit 3
fi

(
  cd "$DIR"
  sha256sum --check "$NAME.sha256"
)

/usr/bin/podman exec -i nextdecode-postgres pg_restore --list < "$BACKUP" >/dev/null
printf 'BACKUP_VERIFIED: %s\n' "$BACKUP"
printf 'Checks: SHA-256 match; PostgreSQL custom archive catalog readable.\n'
printf 'Note: this does not perform a restore or prove point-in-time recoverability.\n'
