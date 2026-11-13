# Maintenance utilities

This package contains explicit operator-run maintenance commands. It is not imported by normal application workflows.

## Governance backfill

Canonical implementation: `backfill_governance.py`.

The compatibility command remains available at the repository root:

```bash
./venv/bin/python backfill_governance.py --purpose short --owner-note "..."
```

The command is plan-only unless BOTH `--execute` and `BACKFILL_CONFIRM=YES` are supplied. A real backfill changes approval-governance metadata and appends the external journal; it is an owner-controlled operation, not a routine maintenance step. Never invoke the execute path during tests or automated pipelines.

The root module remains a compatibility shim for imports and CLI callers. Runtime paths resolve from the repository root, not this package directory.
