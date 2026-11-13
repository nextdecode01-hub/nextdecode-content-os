# Tracking package

This package owns run identity and artifact tracking for generation runs.

## Module

- `run_tracker.py` — run IDs, run directories, manifest lifecycle, artifact hashes, append-only run index, failure records, promotion journal and consistency checks.

## Compatibility and storage

The root-level `run_tracker.py` remains an import alias for existing pipeline, publishing-authorization and test consumers. New code should import from `app.tracking`.

Default paths remain:
- `outputs/runs/` — per-run manifests and artifacts.
- `data/runs/index.jsonl` — append-only run index.
- Promotion journal paths remain within the existing data/runs layout.

## State invariants

- Run manifest schema and lifecycle semantics are unchanged by the package move.
- Terminal states remain immutable.
- Artifact paths, sizes and SHA-256 values remain recorded.
- Promotion must complete and be journaled before a run can be marked successful.
- Interrupted/unknown runs are not automatically recovered or deleted.
- No existing run, manifest, index or promotion journal was rewritten during the package move.
