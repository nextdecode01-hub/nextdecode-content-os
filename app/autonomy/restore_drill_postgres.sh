#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/demon/shorts_studio"
BACKUP="${1:-}"
if [[ -z "$BACKUP" ]]; then
  echo "Usage: $0 /absolute/path/to/autonomy-YYYYMMDDTHHMMSSZ.dump" >&2
  exit 2
fi
if [[ "$BACKUP" != /* ]]; then
  BACKUP="$ROOT/$BACKUP"
fi
if [[ ! -s "$BACKUP" || ! -f "$BACKUP" ]]; then
  echo "Backup file is missing or empty: $BACKUP" >&2
  exit 1
fi

DIR="$(dirname "$BACKUP")"
NAME="$(basename "$BACKUP")"
(
  cd "$DIR"
  sha256sum --check "$NAME.sha256"
)

CONTAINER="nextdecode-restore-drill-$(date -u +%Y%m%dT%H%M%SZ)-$$"
cleanup() {
  /usr/bin/podman rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# No network, published ports, or persistent volume: this database is disposable.
/usr/bin/podman run -d --rm --name "$CONTAINER" --network none \
  --tmpfs /var/lib/postgresql:rw,size=1g \
  -e POSTGRES_USER=nextdecode \
  -e POSTGRES_PASSWORD=temporary-restore-only \
  -e POSTGRES_DB=nextdecode \
  docker.io/library/postgres:18-alpine >/dev/null

ready=0
for attempt in $(seq 1 40); do
  if /usr/bin/podman exec "$CONTAINER" pg_isready -U nextdecode -d nextdecode >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  echo "RESTORE_DRILL_FAILED: isolated PostgreSQL did not become ready" >&2
  exit 1
fi

/usr/bin/podman exec -i "$CONTAINER" sh -c 'cat > /tmp/restore.dump' < "$BACKUP"
/usr/bin/podman exec "$CONTAINER" pg_restore --exit-on-error --no-owner --no-acl \
  -U nextdecode -d nextdecode /tmp/restore.dump

SQL="SELECT 'plan_idempotency',count(*) FROM plan_idempotency
UNION ALL SELECT 'task_dependencies',count(*) FROM task_dependencies
UNION ALL SELECT 'task_events',count(*) FROM task_events
UNION ALL SELECT 'task_plans',count(*) FROM task_plans
UNION ALL SELECT 'tasks',count(*) FROM tasks
UNION ALL SELECT 'worker_heartbeats',count(*) FROM worker_heartbeats
ORDER BY 1;"

LIVE_COUNTS="$(/usr/bin/podman exec nextdecode-postgres psql -U nextdecode -d nextdecode -Atc "$SQL")"
RESTORED_COUNTS="$(/usr/bin/podman exec "$CONTAINER" psql -U nextdecode -d nextdecode -Atc "$SQL")"

echo "LIVE_COUNTS"
printf '%s\n' "$LIVE_COUNTS"
echo "RESTORED_COUNTS"
printf '%s\n' "$RESTORED_COUNTS"
if [[ "$LIVE_COUNTS" != "$RESTORED_COUNTS" ]]; then
  echo "RESTORE_DRILL_FAILED: restored table counts differ from live database" >&2
  exit 1
fi

echo "RESTORE_DRILL=SUCCESS"
echo "The isolated temporary database will now be removed; the live database is untouched."
