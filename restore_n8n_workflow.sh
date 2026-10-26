#!/usr/bin/env bash
#
# restore_n8n_workflow.sh
#
# Idempotently restore the approved n8n schedule workflow
# ("Approved Shorts & Long-Form Studio") into a live n8n instance.
#
# Behaviour:
#   1. Backs up the n8n SQLite database BEFORE touching anything.
#   2. Reads the canonical workflow definition from
#      workflow_n8n_approved_schedule.json (no id -> n8n assigns a fresh one).
#   3. Queries the live n8n API for a workflow with that name.
#        - found and active   -> no-op, exit 0
#        - found but inactive  -> activate it, exit 0
#        - not found           -> POST it, then activate it, exit 0
#   4. Safe to run repeatedly: running it twice changes nothing the second time.
#
# Environment overrides (all optional):
#   N8N_BASE, N8N_API_PATH, N8N_DATA_DIR, BACKUP_DIR, ENV_FILE, WORKFLOW_FILE, PYTHON_BIN
#
set -euo pipefail

ROOT="${ROOT:-/home/demon/shorts_studio}"
WORKFLOW_FILE="${WORKFLOW_FILE:-$ROOT/workflow_n8n_approved_schedule.json}"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
N8N_BASE="${N8N_BASE:-http://localhost:5678}"
N8N_API_PATH="${N8N_API_PATH:-/api/v1}"
N8N_API="$N8N_BASE$N8N_API_PATH"
N8N_DATA_DIR="${N8N_DATA_DIR:-/home/demon/.n8n/.n8n}"
BACKUP_DIR="${BACKUP_DIR:-/home/demon/.n8n/backups}"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$ROOT/venv/bin/python" ]; then
    PYTHON_BIN="$ROOT/venv/bin/python"
  elif [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT/.venv/bin/python"
  else
    PYTHON_BIN="$(command -v python3 || true)"
  fi
fi

log()  { printf '[restore] %s\n' "$*"; }
fail() { printf '[restore] ERROR: %s\n' "$*" >&2; exit 1; }

[ -f "$WORKFLOW_FILE" ] || fail "workflow definition not found: $WORKFLOW_FILE"
[ -f "$ENV_FILE" ]       || fail "env file not found: $ENV_FILE"
[ -n "$PYTHON_BIN" ]     || fail "no python3 interpreter found"
command -v curl >/dev/null 2>&1 || fail "curl is required but not installed"

WORKFLOW_NAME="$("$PYTHON_BIN" -c 'import json,sys;print(json.load(open(sys.argv[1],encoding="utf-8"))["name"])' "$WORKFLOW_FILE")"
log "workflow definition : $WORKFLOW_FILE"
log "workflow name       : $WORKFLOW_NAME"
log "n8n api endpoint    : $N8N_API"

# ---------------------------------------------------------------- step 1: backup
backup_db() {
  mkdir -p "$BACKUP_DIR"
  local ts db
  ts="$(date +%Y%m%d-%H%M%S)"
  db="$N8N_DATA_DIR/database.sqlite"
  if [ -f "$db" ]; then
    cp -a "$db" "$BACKUP_DIR/database.sqlite.$ts.bak"
    log "backup created      : $BACKUP_DIR/database.sqlite.$ts.bak"
  else
    log "backup skipped      : $db not found (nothing to back up)"
  fi
  if [ -f "$WORKFLOW_FILE" ]; then
    cp -a "$WORKFLOW_FILE" "$BACKUP_DIR/$(basename "$WORKFLOW_FILE").$ts.json"
    log "backup created      : $BACKUP_DIR/$(basename "$WORKFLOW_FILE").$ts.json"
  fi
}
backup_db

# ------------------------------------------------------------- read the api key
N8N_API_KEY="$(grep -E '^[[:space:]]*N8N_API_KEY=' "$ENV_FILE" | tail -n 1 | cut -d= -f2- | tr -d '"'"'"'[:space:]')"
[ -n "$N8N_API_KEY" ] || fail "N8N_API_KEY is missing or empty in $ENV_FILE"

api_get() {
  curl -sS --max-time 30 -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_API$1"
}
api_post() {
  curl -sS --max-time 60 -X POST -H "X-N8N-API-KEY: $N8N_API_KEY" \
       -H 'Content-Type: application/json' ${2:+-d "$2"} "$N8N_API$1"
}

# --------------------------------------------------- step 2: look for the workflow
list_json="$(api_get '/workflows?limit=250')" || fail "cannot reach n8n at $N8N_API"
printf '%s' "$list_json" | "$PYTHON_BIN" -c '
import json,sys
raw=sys.stdin.read()
try:
    d=json.loads(raw)
except Exception:
    print("[restore] ERROR: unexpected response from n8n API:", raw[:300]); raise SystemExit(1)
if "data" not in d:
    print("[restore] ERROR: n8n API error:", raw[:300]); raise SystemExit(1)
' || fail "n8n API did not return a workflow list"

existing_id="$("$PYTHON_BIN" -c '
import json,sys
name=sys.argv[1]
d=json.load(sys.stdin)
for w in d.get("data",[]):
    if w.get("name")==name:
        print(w.get("id","")); break
' "$WORKFLOW_NAME" <<<"$list_json")"

if [ -n "$existing_id" ]; then
  existing_active="$("$PYTHON_BIN" -c '
import json,sys
d=json.load(sys.stdin)
for w in d.get("data",[]):
    if w.get("id")==sys.argv[1]:
        print("true" if w.get("active") else "false"); break
' "$existing_id" <<<"$list_json")"
  log "workflow already present: id=$existing_id active=$existing_active"
  if [ "$existing_active" = "true" ]; then
    log "nothing to do - workflow is present and active"
    log "url: $N8N_BASE/workflow/$existing_id"
    exit 0
  fi
  log "workflow is present but inactive -> activating"
  activate_out="$(api_post "/workflows/$existing_id/activate" '')"
  printf '%s' "$activate_out" | "$PYTHON_BIN" -c '
import json,sys
raw=sys.stdin.read()
try: d=json.loads(raw)
except Exception: print("[restore] ERROR: activation returned non-JSON:", raw[:300]); raise SystemExit(1)
if not d.get("active"):
    print("[restore] ERROR: activation did not take effect:", raw[:300]); raise SystemExit(1)
' || fail "activation failed"
  log "activated: $existing_id"
  log "url: $N8N_BASE/workflow/$existing_id"
  exit 0
fi

log "workflow not found in live n8n -> creating it"

# ------------------------------------------- step 3: build a create-safe payload
payload="$("$PYTHON_BIN" - "$WORKFLOW_FILE" <<'PYEOF'
import json, sys
ALLOWED_SETTINGS = {
    "saveExecutionProgress", "saveManualExecutions", "saveDataErrorExecution",
    "saveDataSuccessExecution", "executionTimeout", "errorWorkflow",
    "timezone", "executionOrder",
}
with open(sys.argv[1], encoding="utf-8") as fh:
    doc = json.load(fh)
for key in ("id", "versionId", "active", "owner", "tags", "shared", "pinData"):
    doc.pop(key, None)
settings = doc.get("settings") or {}
doc["settings"] = {k: v for k, v in settings.items() if k in ALLOWED_SETTINGS}
json.dump(doc, sys.stdout)
PYEOF
)"

create_out="$(api_post '/workflows' "$payload")"
new_id="$(printf '%s' "$create_out" | "$PYTHON_BIN" -c '
import json,sys
raw=sys.stdin.read()
try: print(json.loads(raw).get("id",""))
except Exception: print("")
')"
[ -n "$new_id" ] || fail "workflow creation failed: $create_out"
log "created workflow id  : $new_id"

activate_out="$(api_post "/workflows/$new_id/activate" '')"
printf '%s' "$activate_out" | "$PYTHON_BIN" -c '
import json,sys
raw=sys.stdin.read()
try: d=json.loads(raw)
except Exception: print("[restore] ERROR: activation returned non-JSON:", raw[:300]); raise SystemExit(1)
if not d.get("active"):
    print("[restore] ERROR: activation did not take effect:", raw[:300]); raise SystemExit(1)
' || fail "activation failed"

# ------------------------------------------------------------- step 4: verify
api_get "/workflows/$new_id" | "$PYTHON_BIN" -c '
import json,sys
w=json.load(sys.stdin)
print("[restore] verified    : id=%s active=%s nodes=%d" % (
    w.get("id"), w.get("active"), len(w.get("nodes",[]))))
'
log "url: $N8N_BASE/workflow/$new_id"
exit 0