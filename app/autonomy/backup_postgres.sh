#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/demon/shorts_studio"
BACKUP_DIR="$ROOT/data/autonomy/postgres-backups"
umask 077
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NAME="autonomy-$STAMP.dump"
FINAL="$BACKUP_DIR/$NAME"
TEMP="$FINAL.tmp"
CHECKSUM="$FINAL.sha256"
CHECKSUM_TEMP="$CHECKSUM.tmp"
CONTAINER_TEMP="/tmp/nextdecode-autonomy-$STAMP.dump"

cleanup() {
  rm -f "$TEMP" "$CHECKSUM_TEMP"
  /usr/bin/podman exec nextdecode-postgres rm -f "$CONTAINER_TEMP" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Keep the dump private and on the destination filesystem until every check passes.
/usr/bin/podman exec nextdecode-postgres pg_dump -U nextdecode -d nextdecode -Fc > "$TEMP"
test -s "$TEMP"

/usr/bin/podman exec -i nextdecode-postgres sh -c "cat > '$CONTAINER_TEMP'" < "$TEMP"
/usr/bin/podman exec nextdecode-postgres pg_restore --list "$CONTAINER_TEMP" >/dev/null

HASH="$(sha256sum "$TEMP" | cut -d ' ' -f1)"
printf '%s  %s\n' "$HASH" "$NAME" > "$CHECKSUM_TEMP"
chmod 600 "$TEMP" "$CHECKSUM_TEMP"

# Publish the dump first; the checksum sidecar is the final commit marker.
mv "$TEMP" "$FINAL"
mv "$CHECKSUM_TEMP" "$CHECKSUM"
chmod 600 "$FINAL" "$CHECKSUM"

# Preserve the existing 14-day retention policy and remove each matching sidecar.
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'autonomy-*.dump' -mtime +14 -print0 |
while IFS= read -r -d '' old_dump; do
  rm -f "$old_dump" "$old_dump.sha256"
done

printf '%s\n' "$FINAL"
printf '%s\n' "$CHECKSUM"
