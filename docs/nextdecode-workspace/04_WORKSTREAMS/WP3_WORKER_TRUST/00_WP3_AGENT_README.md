# WP3 — WORKER REGISTRY, IDENTITY AND TRUST

Read workspace master index, document register, agent protocol and open-gap register first.

## Source sequence
1. Accepted P0 ADR-005 and relevant CF decisions.
2. Shared Intelligence Contract 10 and Data Dictionary.
3. Worker Trust Credential Contract Reconciliation.
4. WP3 Worker Registry Contract Boundary.
5. Architecture Pipeline Parts 4–5; Batch07 and Batch20.

## Deliverable
Worker identity and registration lifecycle, trust/verification states, capability declaration vs verification vs availability vs authorization, credential scope/expiry/revocation, assignment handshake, heartbeat and active-task fencing. Provide threat scenarios and acceptance cases.

## Boundary
Do not create provider credentials, provision workers, change secrets or deploy infrastructure. Worker capability never grants permission by itself; central authorization remains authoritative.

## Stop conditions
Unresolved identity ownership, revocation semantics or in-flight task policy. No implementation or credential changes without explicit authorization.