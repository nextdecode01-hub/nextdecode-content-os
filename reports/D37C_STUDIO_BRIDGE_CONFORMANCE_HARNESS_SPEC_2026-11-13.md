# D37-C — Studio Bridge Contract-Conformance Harness Specification

**Date:** 2026-11-13  
**Status:** SPECIFICATION ONLY — OWNER/QA REVIEW REQUIRED  
**Execution authorization:** NOT GRANTED  
**Environment approval:** NOT GRANTED

## 1. Purpose and authority

Define the smallest safe contract-conformance harness that can be implemented only after required contract freezes and explicit authorization. It validates boundaries before any live canonical Studio adapter is connected.

Authority order:
1. Artifact 07 v1.0 §7.2 remains authoritative for P0-A acceptance IDs, expected results and severity.
2. Owner-approved/frozen WP1–WP5 contracts define the contracts the harness will validate. Current WP2–WP5 v0.1 packages remain design candidates.
3. WP6 defines proposed vertical slice, environment gates, failure injection and evidence requirements; it is not implementation or test execution authorization.
4. Artifact 07 ↔ WP6 crosswalk and test-case manifest are working traceability aids, not replacements for Artifact 07.
5. D37-A and D37-B define the Studio-specific local-to-canonical boundary; they do not create canonical fields or IDs.

No fixture or assertion may invent a canonical field, state, endpoint, identifier, lease parameter, retry parameter or authorization shape.

## 2. Harness boundary

### In scope after authorization
- Pure contract validation against exact owner-frozen schema/version artifacts.
- Synthetic fixtures with deterministic, non-user content and deterministic byte outputs.
- Adapter request/response conformance without live production engine or external provider.
- Local-to-canonical identity separation assertions.
- Artifact-version reference and integrity assertions using an approved test double.
- Governance denial assertions using test-only policy fixtures.
- Duplicate delivery, stale attempt, partial failure and recovery using deterministic fakes.
- Immutable test evidence records traceable to Artifact 07 IDs.

### Explicitly out of scope
- Live canonical database writes or migrations.
- Live WP2 queue, WP3 worker registry, WP4 storage or WP5 policy integration.
- Real worker/provider/channel-account credentials.
- Public-web research, model calls, paid services, cloud storage or external network calls.
- Production rendering, uploads, publishing, distribution or deployment.
- Real user media or production data.
- Changing existing autonomy runtime semantics to fit the harness.
- Replacing/refactoring the Shorts Studio engine.
- Treating local autonomy tests as WP6 acceptance evidence.

## 3. Logical harness components

| Component | Responsibility | Must not do |
|---|---|---|
| Contract fixture loader | Load exact approved contract/schema versions and synthetic fixtures | Generate missing schema or silently accept unknown versions |
| Request validator | Validate adapter input against approved contract | Fill missing canonical IDs or coerce unknown fields |
| Identity boundary checker | Keep canonical references and local provenance identifiers distinct | Derive canonical IDs from local IDs |
| Specialist test double | Return deterministic research/script/Studio-like outputs | Call external models, research providers or production rendering |
| Artifact registry test double | Model approved WP4 request/response semantics with immutable synthetic versions | Claim local paths/hashes are canonical records |
| Policy test double | Return explicit allow/deny outcomes for test-only protected-action scenarios | Become an alternative authorization authority |
| Failure injector | Simulate duplicate, stale, interruption and unavailable dependencies | Change real queues, credentials, leases or provider state |
| Evidence collector | Retain test ID, contract version, fixture digest, result and reviewer trace | Store secrets or label unexecuted cases PASS |

Technology and test framework remain unspecified until approved contracts and repository scope exist.

## 4. Synthetic fixture catalogue

Fixture names are descriptive labels, not canonical IDs or schema fields.

| Fixture | Purpose | Constraints |
|---|---|---|
| valid_research_request | Valid synthetic research specialist request | No network research; deterministic local response |
| valid_script_request | Script request referencing synthetic research evidence | Research and script identities remain distinct |
| unknown_contract_version | Unsupported version rejection | No fallback or guessed interpretation |
| missing_canonical_reference | Missing required canonical reference | Fail closed; no local-ID substitution |
| local_identity_collision | Local strings resemble canonical IDs | Keep typed identities separate |
| valid_artifact_bytes | Deterministic bytes with known digest and size | Synthetic, versioned fixture |
| artifact_hash_mismatch | Integrity mismatch | Block/quarantine per frozen WP4 contract |
| artifact_version_replacement | Attempt to mutate existing version | Existing version remains unchanged |
| duplicate_delivery | Repeated same logical event/request | One logical effect under approved idempotency contract |
| stale_attempt_result | Result from superseded attempt/lease | Reject at authoritative WP2/WP3 boundary |
| worker_scope_mismatch | Worker lacks required capability or scope | Deny at authoritative assignment/trust boundary |
| missing_authorization | Protected action has no authorization | Deny; no side effect |
| authorization_mismatch | Wrong artifact version/hash or destination | Deny |
| blocked_quality | Hard-blocked QA outcome | Ordinary approval cannot clear hard blocker |
| unknown_rights | Rights state unknown/pending | Protected use denied per approved policy |
| partial_artifact_transfer | Transfer interruption | Partial bytes never become available immutable artifact |
| dry_run_to_live_escalation | Attempt to change dry-run to live side effect | Deny without separately authorized path |

Fixture contents, digests, schemas and canonical reference values must be generated only from approved contracts and recorded in a versioned fixture manifest. No values are specified here.

## 5. Conformance scenario groups

| Group | Scenario | Expected oracle | Artifact 07 trace |
|---|---|---|---|
| C-01 Contract version | Submit supported and unsupported versions | Supported validates; unsupported explicitly rejects without fallback | API-02; exact mapping follows manifest |
| C-02 Identity separation | Supply canonical references and local provenance, including collision-looking values | Never synthesize canonical IDs from local IDs | ID-01..06; manifest gaps remain open |
| C-03 Specialist handoff | Research output feeds script request through explicit exact-version dependency | Preserve dependency; missing/invalid reference blocks handoff | Exact Artifact 07 mapping needs owner/QA approval |
| C-04 Artifact registration | Submit deterministic bytes and metadata to WP4 test double | Retain returned canonical version reference; verify digest/size | AR-01 |
| C-05 Artifact immutability | Attempt to replace existing version bytes/metadata | Existing version unchanged; new version distinct under frozen contract | AR-05 |
| C-06 Duplicate delivery | Deliver same idempotent request/event more than once | One logical effect; dedup evidence retained | Q-05; API-03 |
| C-07 Stale result | Submit result from superseded attempt/lease | Reject; current attempt state unchanged | ST-03; Q-04; WK-05 as applicable |
| C-08 Worker scope | Unknown, revoked, expired or insufficient worker | Deny without claim or protected artifact access | WK-01..08; F-08..10 |
| C-09 Governance denial | Missing, expired, revoked or mismatched authorization | Deny with reason; no outbound side effect | GV-01..05 |
| C-10 Hard blockers | Ordinary approval for BLOCKED QA or UNKNOWN/PENDING rights | Hard QA blocker and rights restriction remain enforced | GV-06..07 |
| C-11 Partial transfer | Interrupt synthetic artifact transfer | No durable-available artifact until complete and verified | AR-06 |
| C-12 Failure/recovery | Simulate worker loss, duplicate callback and process interruption | Follow frozen WP2/WP3 semantics; no duplicate logical effect | F-01..05; numeric values remain approved test-only |
| C-13 Dry-run boundary | Attempt dry-run-to-live escalation | Deny; no provider/upload/publish invocation | GV-10/GV-12; F-17 |
| C-14 Direct bypass | Invoke adapter without required governance boundary | Deny and audit; no side effect | GV-09; F-18; API-06 |
| C-15 Evidence reconstruction | Reconstruct synthetic scenario from retained evidence | Ordered attributable trace with exact contract/fixture versions | OP-01/02/04; mapping gaps remain explicit |

C-01..C-15 are harness group labels, not replacements for Artifact 07 or WP6 IDs.

## 6. Mandatory negative assertions

Every relevant scenario must prove absence of the prohibited effect, not merely observe an error response:

- No canonical ID is generated from a local ID, filename, path, UUID or hash.
- No local plan/task/run/artifact state is written as canonical WP2/WP3/WP4 state.
- No unsupported contract version is silently interpreted.
- No stale worker/attempt commits after authoritative supersession.
- No duplicate delivery produces duplicate logical transition or artifact registration.
- No partial or checksum-invalid artifact becomes available.
- No artifact version is overwritten.
- No review flag, QA completion or ordinary approval is treated as protected-action authorization.
- No missing, expired, revoked, mismatched or unknown authorization permits a protected action.
- No hard QA blocker or unresolved rights state is bypassed.
- No direct pipeline/adapter route bypasses centralized governance.
- No dry-run path reaches live rendering, provider, upload, publish or distribution.
- No secrets appear in logs, fixture output or evidence.

## 7. Artifact 07 traceability and known gaps

The harness must preserve direct/partial/gap classifications from the current crosswalk. It must not claim a scenario covers an entire family unless every mapped oracle is independently demonstrated.

Known manifest gaps remain open:
- ID-02 and ID-04 canonical duplicate identity / multiple production attempts.
- ST-02..ST-04 and ST-06 transition, concurrency and cross-domain mutation details.
- Q-02, Q-06 and Q-07 concurrent lease, retry terminal handling and scheduler restart specifics.
- WK-08 offline/reconnect behavior.
- API-01, API-02, API-05 and API-06 exact boundary/size/command mappings.
- GV-02, GV-03 and GV-11 decision evidence and policy-version detail.
- OP-03 heartbeat/lease telemetry, OP-04 denial evidence detail, OP-06 backup restore.
- Distribution visibility, unknown external outcome and in-flight pause remain outside current pre-distribution P0-A scope unless explicitly re-scoped.

Source: docs/nextdecode-workspace/04_WORKSTREAMS/WP6_INTEGRATION_RECOVERY_ACCEPTANCE/01_SPECIFICATIONS_AND_RECONCILIATION/NEXTDECODE_P0_Artifact07_Test_Case_Level_Acceptance_Manifest_0.1.md.

## 8. Evidence record requirements

For every executed case, retain subject to approved schema:
- Exact Artifact 07 requirement ID and severity.
- Exact approved WP6 trace IDs and mapping qualification.
- Contract/schema version and digest.
- Fixture manifest version and fixture digest.
- Exact source/build/review target identity.
- Approved isolated environment identity and configuration evidence.
- Authorized test command and parameters.
- Input/output references and integrity evidence.
- Test timestamps and correlation/causation evidence where defined by frozen contract.
- Result: PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED, NOT_RUN or NOT_APPLICABLE.
- Failure details, recovery outcome and negative-side-effect proof.
- Independent reviewer disposition and owner acceptance decision.

Never include raw secrets, credentials, user media or unredacted restricted data.

## 9. Environment and execution gates

No harness test may execute until all applicable conditions are explicitly approved:

1. WP1–WP5 detailed contracts are owner-approved/frozen, including WP2/WP3 lease/fencing authority.
2. Artifact 07 ↔ WP6 test-case mappings and mandatory scope are approved.
3. ENV-01..14 prerequisites are evidenced: isolated database/storage/worker, test-only policy, outbound egress denial, sanitized logs, teardown safety, test-only numeric parameters, stable review target, clock semantics and abort mechanism.
4. Synthetic fixtures and deterministic outputs are approved and versioned.
5. Exact test commands, paths, environment and permitted actions are authorized.
6. Independent QA review target and responsibilities are established.
7. Separate implementation authorization names exact repository paths and allowed changes.

Until then all cases remain NOT_RUN. The specification itself is not a test result.

## 10. Stop conditions

Stop and return BLOCKED/NOT_READY if:
- any required contract is missing, ambiguous, unfrozen or version-mismatched;
- canonical identity ownership or WP2/WP3 lease/fencing authority remains unresolved;
- a schema/field must be invented;
- the environment cannot prove isolation or outbound denial;
- real credentials, providers, user media or production data are encountered;
- cleanup could affect non-test resources;
- a scenario can create an external side effect;
- evidence cannot distinguish local prototype IDs from canonical references;
- a critical Artifact 07 oracle has no approved mapping;
- command or numeric parameters are not explicitly authorized.

## 11. Recommended implementation order after authorization

1. Contract loader and strict version validation.
2. Identity separation validators and synthetic fixture manifest.
3. Request/response conformance with specialist test doubles.
4. WP4 artifact test-double conformance and immutability checks.
5. WP5 policy test-double denial conformance.
6. Duplicate/stale/partial-failure injection.
7. Evidence collector and Artifact 07 traceability report.
8. Independent read-only QA.
9. Only after this passes, separately authorized canonical service integration and WP6 vertical slice.

## 12. Final disposition

**D37-C harness specification: COMPLETE — documentation only.**  
**Implementation: NOT AUTHORIZED.**  
**Test execution: NOT AUTHORIZED; all proposed cases remain NOT_RUN.**  
**Next gate:** owner/QA review of contract freeze, Artifact 07 mapping gaps, environment prerequisites and exact implementation authorization.

No source code, schemas, APIs, migrations, tests, runtime tasks, Git state, external services, uploads, publishing or deployments were changed or executed for this specification.
