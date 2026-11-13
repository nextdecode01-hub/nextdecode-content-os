# WP1 — DOMAIN AND PERSISTENCE

Read first: workspace 00_MASTER_INDEX, 01_DOCUMENT_REGISTER, 02_AGENT_OPERATING_PROTOCOL and 04_OPEN_GAPS_AND_CONFLICTS.

## Source sequence
1. Accepted P0 ADR baseline (ADR-001/002 and relevant CF decisions).
2. Canonical Data Dictionary and Entity Ownership Registry.
3. Module-to-Contract Traceability Matrix.
4. WP1 candidate package: boundary 0.1, design resolution 0.2, schema candidate 0.3.
5. Batch05 WP1 design candidate and Batch19 database/ERD specification; reconcile rather than assume either is frozen.
6. Relevant Architecture Pipeline Part 3 and API/Event standard.

## Deliverable
Produce a source-traceable WP1 reconciliation: canonical entity ownership, identity/version distinction, persistence boundary, relational constraints, migration compatibility and synthetic acceptance cases.

## Boundary
Do not implement WP2 queue/job execution, WP3 worker registry, WP4 binary storage, WP5 authorization or WP6 full integration inside WP1. Do not invent workflow/job identity semantics while X-01 is unresolved. Preserve existing Shorts Studio data and local SQLite use where contracts permit; PostgreSQL-compatible shared state remains governed by ADR-002.

## Stop conditions
Conflicting owner decisions, unresolved entity ownership, unsafe migration assumptions, or any need for owner-reserved decisions. No code/repo changes or tests without separate authorization.