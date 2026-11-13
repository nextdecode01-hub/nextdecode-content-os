# NEXTDECODE P0 — X-12 Unified Status Vocabulary, Source Precedence & Evidence Classification

**Version:** 0.1  
**Status:** Reconciliation candidate — not owner-approved; not a contract freeze  
**Scope:** P0 design registers, specifications, implementation tracking and verification evidence

## 1. Purpose

Prevent status words from being used interchangeably across decisions, design maturity, implementation and verification. A record may be accepted as a decision while its design is not frozen, its code is not implemented, and its behavior is not verified.

## 2. Four independent status dimensions

### 2.1 Decision authority / disposition

| Value | Meaning | Does not mean |
|---|---|---|
| `OWNER-ACCEPTED` | Explicitly accepted by the owner with traceable evidence | Implemented or tested |
| `PROPOSED` | Recommendation awaiting authority | Approved default |
| `OPEN` | Decision unresolved | Permission to choose silently |
| `DEFERRED` | Deliberately postponed, ideally with reason and re-entry condition | Accepted or permanently out of scope |

`CARRIED_FORWARD` is a traceability/register disposition, not an owner decision. `SOURCE-DEFINED` records that a term or rule appears in a source; it does not establish owner acceptance. `OWNER-RESERVED` means only the owner may decide.

### 2.2 Design maturity

| Value | Meaning |
|---|---|
| `DRAFT` | Initial proposal or incomplete definition |
| `RECONCILED` | Known source conflicts/gaps have been analyzed and recorded |
| `CANDIDATE` | Internally coherent candidate ready for owner review |
| `FROZEN` | Exact baseline formally approved by the owner, versioned and traceable |

Only explicit owner approval of the identified detailed contract baseline can produce `FROZEN`. A set of accepted ADRs/CFs does not automatically freeze every detailed schema, transition, numeric parameter or API contract.

### 2.3 Implementation state

| Value | Meaning |
|---|---|
| `NOT_IMPLEMENTED` | No implementation evidence identified |
| `IN_PROGRESS` | Work has started; completion not established |
| `IMPLEMENTED` | Implementation exists in a specified code/build baseline |
| `PARTIALLY_IMPLEMENTED` | Some required behavior exists; known requirements remain missing |
| `RETIRED` | Previously implemented behavior has been deliberately withdrawn/replaced |

Code presence alone does not prove correctness, runtime operation, security enforcement or acceptance.

### 2.4 Evidence / verification state

| Value | Meaning |
|---|---|
| `NOT_RUN` | Defined verification has not been executed |
| `NOT_VERIFIED` | No sufficient evidence is available to support the claim |
| `VERIFIED` | Required oracle passed against a named build, environment and scope with retained evidence |
| `FAILED` | Verification ran and the defined oracle failed |
| `NOT_APPLICABLE` | Explicitly outside the stated scope, with rationale |
| `INCONCLUSIVE` | Verification ran but cannot support pass/fail due to ambiguity, environment, missing evidence or nondeterminism |

Absence of evidence is not a test failure. A failed test is not automatically proof that the whole feature is absent.

## 3. Other status vocabularies must remain in their own domains

- QA outcomes: `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_REVIEW`, `BLOCKED`. These are review outcomes, not decision authority or implementation status.
- WP-6 evidence ledger may additionally use `NOT_RUN`, `NOT_APPLICABLE`, `INCONCLUSIVE`; these describe test execution/evidence.
- Execution state `UNKNOWN_OUTCOME` describes an execution or external-side-effect ambiguity. It is not a verification result or owner decision.
- Rights states remain the accepted CF-20 vocabulary: `UNKNOWN`, `PENDING_REVIEW`, `CLEARED`, `RESTRICTED`, `EXPIRED`, `REVOKED`, `DENIED`.
- Approval decisions remain the accepted CF-21 vocabulary: `APPROVED`, `REJECTED`, `CHANGES_REQUESTED`, `EXPIRED`, `REVOKED`.
- Workflow/job/attempt/lease state vocabularies remain separate state machines. Do not reuse them as register statuses.

## 4. Source precedence

Apply this precedence while respecting scope and authority:

1. Explicit owner decision record and accepted ADR/CF, for the exact decision and scope.
2. Governing standards, canonical data dictionary, API/event and lifecycle contracts, provided they do not override an explicit owner decision.
3. WP-1 through WP-6 specifications.
4. Consolidated appendices, traceability matrices and derivative indexes.
5. Reconciliation documents, which are subordinate proposals unless explicitly accepted.
6. Chat summaries, generated summaries and informal notes, which cannot override authoritative source records.

If two sources conflict:
- Preserve both source statements and their versions.
- Record the exact conflicting clauses and affected scope.
- Mark the issue `OPEN` or `NEEDS_REVIEW` in the relevant dimension.
- Do not silently choose the newer-looking, more detailed or more convenient text.
- A later source supersedes an earlier one only when it has explicit authority, scope, date/version and a traceable supersession relationship.

## 5. Minimum traceability record

Every material decision, contract rule, implementation claim and verification claim should record:

- Stable record ID.
- Record type and status dimension.
- Exact value and concise rationale.
- Source ID, source filename, version and hash when available.
- Authority/owner and scope.
- Decision/effective date, if known.
- References and `supersedes` relationship.
- Approval evidence pointer, if applicable.
- Review owner and recheck/expiry condition.
- For implementation: repository, path/module, commit/build identifier and implementation scope.
- For verification: test/fixture ID, environment, worker/runtime identity where relevant, run date, oracle, result and evidence pointer.
- Unknown fields must be explicitly `UNKNOWN`/not supplied; never fabricate hashes, commit IDs, build IDs or dates.

## 6. Update and transition rules

- Status changes are append-only events; preserve prior values and who/what changed them.
- A decision change does not silently change design maturity, implementation or evidence.
- A design revision does not silently change owner authority.
- Implementation completion does not imply verification.
- Verification applies only to the exact named build, environment, configuration, fixture and scope.
- A new build or changed policy may require re-verification.
- `DEFERRED` requires a reason and, where practical, a revisit trigger.
- `FROZEN` requires exact baseline identity and explicit owner approval.
- `VERIFIED` requires a defined oracle and retained evidence; a narrative assertion is insufficient.

## 7. NEXTDECODE examples

| Example | Decision authority | Design maturity | Implementation | Evidence |
|---|---|---|---|---|
| CF-24: no paid services; provider choice remains deferred | No-paid-services: `OWNER-ACCEPTED`; provider choice: `DEFERRED` | Detailed provider design not frozen | Not implied | Not implied |
| ADR-007 centralized authorization | `OWNER-ACCEPTED` | Detailed implementation contract may remain candidate/open | Not established by ADR | `NOT_VERIFIED` absent current evidence |
| WP-6 vertical-slice test cases | Acceptance target is source-defined; test execution not authorized by this document | `CANDIDATE` | Not implied | `NOT_RUN` until actually run |
| ODR-22 grouping | `PROVISIONAL GROUPING`; not owner-accepted | Reconciliation note | Not applicable | Source provenance partly reconciled; original register provenance incomplete |
| X-09 lifecycle reconciliation | Underlying constraints source-backed; legal hold/purge authority owner-reserved | `CANDIDATE` | Not implied | `NOT_RUN` |
| Historical Phase 10 report: 535 passed | Historical claim only | Not a current design status | Historical implementation claim | Not current verification; current state `NOT_VERIFIED` until reproduced against a named baseline |

## 8. Register consistency checks

A register validator should flag:
1. `FROZEN` without explicit owner approval and baseline identity.
2. `VERIFIED` without build, environment, scope, oracle and evidence.
3. `FAILED` when no verification run exists.
4. `IMPLEMENTED` inferred solely from a design document.
5. `OWNER-ACCEPTED` without an authoritative decision source.
6. `CARRIED_FORWARD` treated as owner approval.
7. `SOURCE-DEFINED` treated as owner approval.
8. `DEFERRED` without reason or revisit condition where one is required.
9. `UNKNOWN_OUTCOME` used as a QA or decision status.
10. QA outcomes used as implementation states.
11. Superseded sources silently deleted from traceability.
12. Contradictory source claims without a conflict record.
13. Verification evidence applied to a different commit/build.
14. A status change that overwrites history.
15. A rights/approval status reused outside its own state machine.
16. A provider selection inferred from a general free-first preference.
17. A test marked `FAILED` merely because it has not been run.
18. `NOT_APPLICABLE` without scope and rationale.

## 9. Proposed test oracles (not executed)

- ST-01: reject `FROZEN` with no owner approval evidence.
- ST-02: reject `VERIFIED` with no build identifier.
- ST-03: reject `VERIFIED` with no test oracle.
- ST-04: allow `NOT_RUN` with no run evidence.
- ST-05: reject `FAILED` without a completed run record.
- ST-06: keep `CARRIED_FORWARD` distinct from `OWNER-ACCEPTED`.
- ST-07: keep `SOURCE-DEFINED` distinct from `OWNER-ACCEPTED`.
- ST-08: keep `UNKNOWN_OUTCOME` in execution-state domain only.
- ST-09: reject implicit status propagation between dimensions.
- ST-10: preserve old status values in append-only history.
- ST-11: require explicit scope for `NOT_APPLICABLE`.
- ST-12: flag contradictory authoritative sources.
- ST-13: require explicit supersession metadata for source replacement.
- ST-14: ensure verification evidence is bound to exact build/environment/scope.
- ST-15: ensure QA outcomes cannot be parsed as implementation states.
- ST-16: ensure rights and approval vocabularies remain separate.
- ST-17: ensure deferred decisions have revisit metadata.
- ST-18: ensure historical test reports cannot satisfy current verification.

**Execution status:** All proposed oracles are `NOT_RUN`. This document does not execute tests or authorize repository changes.

## 10. Open items and limits

- Confirm exact canonical source filenames/versions/hashes when the master register is assembled.
- Confirm whether any additional status vocabulary has already been formally frozen in a source not available in the reconciliation set.
- Owner approval is required before this status model becomes normative.
- X-12 is substantially specified as a candidate, not a formal contract freeze.

## 11. Next step

Integrate X-12 into the consolidated master decision/evidence register and cross-document traceability package. Then submit the complete detailed contract baseline for owner review. Implementation remains a separate, explicitly authorized stage.
