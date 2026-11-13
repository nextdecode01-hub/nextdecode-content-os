# Review package

This package owns review artifact construction and human approval CLIs for Shorts and long-form outputs.

## Modules

- `review_bundle.py`: builds a Shorts review package tied to the current metadata/video hashes and optional run provenance.
- `approve_review.py`: records explicit human checklist approval for a Shorts review package.
- `review_longform.py`: creates the long-form human review package.
- `approve_longform.py`: records explicit human checklist approval for a long-form package.

## Boundaries

- Review approval is a human review record; it is not a publishing authorization by itself.
- Publishing remains guarded by the shared root `publish_authorization.py` boundary and platform-specific checks.
- Hash binding, run provenance, promotion-journal checks, checklist requirements, expiry semantics and runtime paths are preserved.
- Telegram notifications remain outbound-only and cannot approve or mutate review state.
- Root-level scripts remain backward-compatible CLI/import facades until external callers are migrated.

## Runtime storage

Review packages and approval records remain under repository-root `data/`; rendered artifacts remain under `outputs/`. The package does not own or relocate runtime data.
