# WP4 — ARTIFACT REGISTRY, STORAGE AND LIFECYCLE

Read workspace master index, document register, agent protocol and open-gap register first.

## Source sequence
1. Accepted P0 ADR-006 and relevant CF decisions.
2. Data Dictionary and Architecture Pipeline Part 7.
3. Artifact Contract Reconciliation.
4. Artifact Lifecycle, Retention, Deletion and Legal Hold Reconciliation.
5. WP4 Artifact Registration, Storage and Transfer boundary.
6. Batch08 and relevant Batch26 privacy/retention material.

## Deliverable
Reconcile Asset vs Artifact vs ArtifactVersion; immutable version/hash rules; manifest exact-version references; metadata/binary storage boundary; provenance, quarantine, transfer, integrity and lifecycle dependency model.

## Boundary
Retention periods, legal hold, irreversible purge authority and backup deletion propagation are owner-reserved. Do not delete/purge, select a paid storage provider or create storage infrastructure.

## Stop conditions
Any unresolved deletion/retention authority, unclear manifest immutability or unsafe dependency/cascade semantics. Read-only until separately authorized.