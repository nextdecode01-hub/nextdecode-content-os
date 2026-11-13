# NEXTDECODE Content OS — Testing & Acceptance Criteria

**Document ID:** ND-P1-QA-001 | **Version:** 0.1.0-draft | **Date:** 2026-11-04  
**Status:** DRAFT — acceptance gates to be finalized with P1 requirements and P0 test oracle.

## 1. Testing principles

- Tests verify contracts and safety boundaries, not merely happy-path generation.
- No test should call real publishing, incur unauthorized cost or trigger uncontrolled external side effects.
- Every state transition has positive and negative tests.
- Retry, duplicate delivery, stale writes and crash recovery are first-class scenarios.
- Historical Phase 10/11 test results are historical evidence, not fresh verification.
- Do not change tests, environment or code without explicit authorization.

## 2. Verification layers

1. Schema/contract validation.
2. Unit tests for domain logic and state machines.
3. Contract tests for producers/consumers.
4. Integration tests across module boundaries.
5. Persistence/restart tests.
6. Workflow and worker recovery tests.
7. Security-negative tests.
8. Governance/rights/approval bypass tests.
9. Staging evaluation and comparative replay.
10. End-to-end acceptance and independent read-only QA.
11. Operational backup/restore drills before production.

## 3. Core test catalogue

| ID | Test | Pass condition |
|---|---|---|
| TST-001 | Canonical ID and version identity | IDs unique; immutable version references preserved |
| TST-002 | Domain ownership and referential integrity | No cross-domain unauthorized mutation or orphan protected record |
| TST-003 | State-machine transition validation | Invalid/stale transitions rejected |
| TST-004 | API/event schema compatibility | Unsupported/broken versions rejected or safely negotiated |
| TST-005 | Duplicate event delivery | One logical side effect; duplicate receipt recorded |
| TST-006 | Retry exhaustion | Bounded retries; terminal/dead-letter state visible |
| TST-007 | Worker lease expiration | Stale worker cannot overwrite newer owner/result |
| TST-008 | Worker revocation | Revoked identity/capability denied |
| TST-009 | Artifact checksum mismatch | Downstream protected operation blocked |
| TST-010 | Artifact immutability | New output creates new version, old version unchanged |
| TST-011 | Approval binding | Changed artifact/version invalidates prior approval per contract |
| TST-012 | Authorization enforcement | Missing/expired/revoked/mismatched authorization denied |
| TST-013 | Rights enforcement | Non-cleared or out-of-scope rights block protected use |
| TST-014 | Hard quality blocker | Ordinary editorial approval cannot bypass blocker |
| TST-015 | Emergency pause | Protected execution stops promptly and audit is recorded |
| TST-016 | Policy snapshot expiry/revocation | Expired dependency blocked; revocation takes precedence |
| TST-017 | Central outage | Only independently safe, pre-authorized low-risk work may continue |
| TST-018 | Agent delegation | Child authority never exceeds parent grant |
| TST-019 | Stage vs production approval | Staging approval alone cannot activate production |
| TST-020 | Batch release integrity | Approved batch immutable; individual decisions independently recorded |
| TST-021 | Creator priority override | Override preserved; protected safety rules remain enforced |
| TST-022 | Rejected recommendation | No repeat without materially new evidence |
| TST-023 | Critical notification | Critical event not silently suppressed by digest/quiet hours |
| TST-024 | Notification deduplication | Source events retained; repeated user-facing alerts grouped |
| TST-025 | Learning evaluation | Current/candidate comparison avoids look-ahead leakage |
| TST-026 | Progressive rollout | Only pre-authorized transitions occur automatically |
| TST-027 | Serious incident recovery | Staging/recovery validation and creator authorization required |
| TST-028 | Failure-domain isolation | Independent safe module remains available where dependencies allow |
| TST-029 | Resume from checkpoint | Only verified inputs/outputs resumed; lineage preserved |
| TST-030 | Export package integrity | Artifact hashes, provenance and required evidence included |
| TST-031 | Shorts adapter boundary | Adapter cannot bypass central governance or replace engine internals |
| TST-032 | Publishing disabled | No public/live action possible in P1 test scope |
| TST-033 | Secret redaction | Credentials absent from logs, traces, prompts and artifacts |
| TST-034 | Restore test | Restored data/artifacts pass integrity and workflow reconciliation |

## 4. Research and content quality acceptance

Recommended evaluation dimensions:
- source authority and directness;
- claim support/contradiction coverage;
- freshness and source independence;
- uncertainty calibration;
- completeness relative to requested depth;
- traceability from claim to source and final artifact;
- distinction between fact, interpretation, hypothesis and forecast;
- brand/content objective alignment;
- rights/usage compliance.

Numeric quality thresholds are Open; they require baseline examples and creator acceptance. Do not invent a single composite score that can override hard safety/rights gates.

## 5. Learning and notification evaluation

- Replay historic events without future leakage.
- Compare candidate/current policy on identical event sets.
- Report latency, volume, missed actionable alerts, duplicates, grouping usefulness, critical compliance and delivery reliability.
- Use controlled simulation for scenarios missing from history.
- Keep staging isolated from real external notifications.
- Require mandatory safety tests to pass before performance trade-offs are considered.
- Preserve the exact configuration and dataset version used in evaluation.

## 6. Acceptance artifacts

Each work package should retain:
- scope and requirement IDs;
- source/contract versions;
- environment and build identity;
- test case IDs and input fixture versions;
- command/execution evidence;
- pass/fail/skip counts;
- sanitized logs;
- failure-injection outcomes;
- limitations and unresolved risks;
- independent reviewer findings;
- explicit owner acceptance record.

## 7. Release gate

A candidate release is not eligible for production activation unless:
- mandatory safety and rights tests pass;
- contract compatibility passes;
- no unresolved critical/high blocker is accepted without explicit risk disposition;
- provenance and audit are intact;
- rollback/recovery is defined;
- staging evidence is reviewed;
- creator explicitly authorizes activation;
- deployment/production permissions exist separately.

No public publishing is authorized by this test plan.
