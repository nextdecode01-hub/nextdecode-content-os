# WP2 — WORKFLOW AND DURABLE EXECUTION

Read workspace master index, document register, agent protocol and open-gap register first.

## Source sequence
1. Accepted P0 ADR baseline, especially durable queue/outbox/inbox and separate lifecycle decisions.
2. Data Dictionary and Module-to-Contract Matrix.
3. API/Event Contract Standard and lifecycle/state transition source.
4. WP2 Durable Job Workflow Execution candidate.
5. Workflow/Job Contract Reconciliation and State Transition Matrix Reconciliation.
6. Architecture Pipeline Parts 4–5; Batch06 and Batch17–18.

## Deliverable
Reconciled definitions and ownership for WorkflowDefinition, WorkflowRun, WorkflowTask, Job and JobAttempt; state transitions; retries, leases, idempotency, cancellation, recovery and event contracts. Explicitly identify which details require owner decision.

## Boundary
X-01 is unresolved in the inherited P0 record. Do not silently settle identity ownership. Do not design worker trust (WP3), artifact persistence (WP4), authorization policy (WP5) or full integration (WP6).

## Stop conditions
Any ambiguity in canonical identity, lifecycle authority, duplicate side-effect handling or event compatibility. Read-only unless separately authorized.