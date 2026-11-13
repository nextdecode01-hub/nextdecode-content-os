# Operations package

This package contains operational utilities that support Shorts Studio without belonging to the core research, script, voice, visuals, render or publishing-adapter domains.

## Modules

- `analytics_collect.py` — analytics source discovery, collection and local history.
- `meta_preflight.py` — read-only Meta Page/Instagram configuration preflight.
- `monetization_tracker.py` — local monetization progress snapshot.
- `review_ledger.py` — manual content-quality and feedback ledger.
- `video_archive.py` — copies approved/generated video artifacts into the configured archive location.
- `workspace_sync.py` — legacy SQLite prototype and optional external workspace mirrors. It is not the canonical NEXTDECODE shared-data model.

## Compatibility

The root-level modules with the same names are compatibility aliases. They preserve legacy imports and delegate CLI execution to the package implementation. New Python code should import from `app.operations`.

`setup_check.py` remains a self-contained root entrypoint because its tests and local usage execute a copied script without the repository package tree.

## Boundaries

- These utilities do not establish canonical P0 contracts, owner decisions or workflow authority.
- `workspace_sync.py` remains a local prototype; do not treat its SQLite schema as the canonical NEXTDECODE domain model.
- Analytics, preflight and tracker tools do not authorize publication.
- Keep API/provider calls behind existing explicit configuration; tests must use mocks or offline fixtures.
