# WP6 — VERTICAL SLICE INTEGRATION, RECOVERY AND ACCEPTANCE

Read workspace master index, document register, agent protocol and open-gap register first.

## Source sequence
1. Accepted P0 baseline and WP-0 closure record.
2. WP1–WP5 reconciled/frozen contracts and their acceptance cases.
3. WP6 Acceptance Contract/Test Oracle Reconciliation.
4. WP6 Vertical Slice Integration, Recovery and Validation.
5. Artifact07 acceptance framework; Batch10 and Batch14.

## Deliverable
Integration map for the explicitly bounded P0-A vertical slice; contract compatibility checks; end-to-end lineage; failure injection and recovery matrix; acceptance evidence package and release recommendation.

## Boundary
WP6 consumes accepted WP1–WP5 contracts; it does not redesign them. P0-A is not a full Control Center. A release recommendation is not deployment authorization. No production publishing or paid infrastructure.

## Stop conditions
Any upstream contract is still ambiguous/frozen status unknown, missing rollback evidence, unverified production claims or unsafe external side effects. QA must remain independent.