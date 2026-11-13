NEXTDECODE CONTENT OS

# P0 Batch 04
Source Verification & Contract Freeze Preparation

Owner-review working pack • 01 November 2026

Purpose: turn the existing reconciled architecture and decision work into a controlled, evidence-led source verification process and a clear contract-freeze gate. This pack prepares the work; it does not declare the contract frozen or authorize implementation.

## 1. Executive status

Batch 04 is a source-control and readiness pack. It deliberately separates what is already accepted, what is reconciled as a candidate, what is historically reported, and what still requires authoritative source evidence.

| Area | Current position | What this means |
| --- | --- | --- |
| Architecture direction | Accepted at decision level | Use the established ADR-001–ADR-010 and accepted CF decisions as governing direction. |
| CF decision coverage | CF-01–CF-24 decision outcomes recorded | Do not reopen accepted owner decisions. Exact source wording is still required for the identified CF gaps. |
| Exact source reconciliation | Incomplete | CF-03–CF-12, CF-15–CF-19 and CF-23 exact original wording has not been fully imported/verified in the current working set. |
| Source inventory | Partial | The prior batch found 6 of 13 indexed working artifacts available in its working folder. This is not proof that the remaining files do not exist elsewhere. |
| WP-1 readiness | Preparation only | Schema and migration review can proceed as a review exercise; implementation authorization remains separate. |
| P0 implementation | Not authorized by this document | No repository edits, migrations, agents, tests, deployment, paid services or publishing are authorized here. |

Status rule: a missing source is NOT VERIFIED, not FAILED and not evidence that the source never existed. Do not reconstruct exact wording from memory or summaries.

## 2. Source authority and evidence rules

| Priority | Source class | Use and precedence |
| --- | --- | --- |
| 1 | Explicit owner decisions and accepted ADR/CF decisions | Governing decision authority. A later explicit owner decision may supersede an earlier one. |
| 2 | Governing standards, canonical data dictionary, API/event contracts and lifecycle contracts | Authoritative detailed semantics where consistent with owner decisions. |
| 3 | Approved WP specifications and acceptance contracts | Implementation scope and testable requirements, subordinate to higher-level authority. |
| 4 | Appendices, indexes and supporting registers | Navigation and supporting evidence; not a substitute for governing wording. |
| 5 | Reconciliation notes and generated working documents | Useful analysis and gap tracking; cannot silently override source authority. |
| 6 | Chat summaries, inferred context and agent summaries | Discovery aids only. Never use as proof of exact source wording. |

Every extracted requirement should carry: source filename/title, source version/date if available, page/section/line locator, exact quotation or faithful transcription, extraction date, reviewer, and a stable requirement ID.

- Keep verbatim source text separate from normalized interpretation.

- Record conflicts explicitly; do not silently choose a convenient version.

- When an authoritative source is unavailable, preserve the gap and request the source rather than inventing a replacement.

- A reconciliation document may explain a decision but cannot create an owner decision.

## 3. Source inventory and verification matrix

Use this matrix as the single intake ledger. Replace placeholders only after locating and inspecting the actual authoritative file. 'Not available in current working set' must not be rewritten as 'does not exist'.

| Source / artifact | Expected role | Current evidence status | Required verification action | Closure evidence |
| --- | --- | --- | --- | --- |
| Artifact 08 — authoritative CF source pack/register | Exact original CF-01–CF-24 wording and provenance | NOT VERIFIED in current working set | Locate the original file/version; inspect all CF rows and their notes | File identity + version + exact row locators + extraction review |
| Original ODR master register | Original decision/requirement grouping and ODR provenance | PARTIAL / NOT VERIFIED | Locate master register; compare ODR-22 and linked source rows | Exact ODR row(s), source locators and conflict note |
| Canonical data dictionary | Entity fields, enums, ownership and identity semantics | NOT VERIFIED as a complete source set | Locate approved version; map each WP-1 field and enum | Versioned field/enum mapping |
| API and event contract | Request/response/event envelopes and compatibility rules | RECONCILIATION EXISTS; source completeness NOT VERIFIED | Compare proposed contracts to governing original contract | Endpoint/event-by-event source traceability |
| Lifecycle/state transition contract | Legal transitions and state ownership | RECONCILIATION EXISTS; source completeness NOT VERIFIED | Verify each state/transition against governing source | Transition matrix with exact source locators |
| WP-1 specification | Persistence/domain foundation scope | Review checklist exists; authoritative source status NOT VERIFIED | Locate approved WP-1 specification and acceptance criteria | Requirement-to-schema-to-test traceability |
| WP-2 to WP-6 specifications | Execution, workers, artifacts, governance, integration | Reconciliations exist; source completeness NOT VERIFIED | Locate approved originals and compare batch summaries | WP requirement traceability and unresolved conflicts |
| Existing repository baseline | Preservation and integration constraints | HISTORICAL snapshot only | Use existing recorded snapshot; refresh only if implementation is later authorized and necessary | Timestamped read-only baseline evidence at authorized execution time |

## 4. Exact CF wording capture worksheet

The following rows are intentionally left as capture slots. Fill them only from Artifact 08 or another verified governing source. The accepted decision outcome remains recorded; this worksheet is about source fidelity, not reopening the decision.

| CF ID | Known decision status | Verbatim source wording | Source locator | Review |
| --- | --- | --- | --- | --- |
| CF-03 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-04 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-05 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-06 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-07 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-08 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-09 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-10 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-11 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-12 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-15 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-16 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-17 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-18 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-19 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |
| CF-23 | Accepted outcome recorded in decision register; exact original wording not yet verified here | [PASTE VERBATIM SOURCE TEXT] | [FILE / VERSION / PAGE / SECTION / ROW] | PENDING |

Review procedure for each row:

1. Confirm that the source is the governing original or an explicitly approved revision.

1. Capture the entire row, including conditions, options, rationale, owner notes and dependencies.

1. Compare the verbatim text with the accepted decision record; flag any mismatch without silently rewriting either.

1. Record whether the difference is wording-only, a substantive conflict, or missing provenance.

1. Escalate only a genuinely substantive unresolved owner decision. Do not ask the owner to reapprove decisions already accepted.

## 5. Conflict and provenance register

| ID | Issue | Current treatment | Closure test | Owner / disposition |
| --- | --- | --- | --- | --- |
| SRC-01 | Exact wording gaps for CF-03–CF-12, CF-15–CF-19 and CF-23 | Keep as NOT VERIFIED; do not reconstruct | All exact rows captured and independently checked against Artifact 08 | Source custodian / pending |
| SRC-02 | Only 6 of 13 indexed artifacts were available in prior working folder | Treat as partial folder visibility, not global absence | Inventory reconciled against authoritative source location | Source custodian / pending |
| SRC-03 | ODR-22 grouping may combine independent topics | Keep ODR-22 provisional; underlying L-08/L-09/L-13 constraints remain source-backed | Inspect complete original ODR master register and determine whether a combined row exists | Architecture reviewer / pending |
| SRC-04 | Status vocabulary source precedence | Use four separate dimensions; owner review still pending for source precedence | Confirm the vocabulary and precedence against governing register and owner-approved policy | Owner review / pending |
| SRC-05 | Historical implementation reports lack fresh runtime evidence | Do not infer current implementation or production readiness | Only close with scoped, timestamped execution evidence and independent QA | Engineering + QA / pending |

Do not collapse the following dimensions into one status field:

| Dimension | Values / labels | Interpretation |
| --- | --- | --- |
| Decision authority | OWNER-ACCEPTED, PROPOSED, OPEN, DEFERRED | Who has decided and whether a decision is authoritative. CARRIED_FORWARD / SOURCE-DEFINED are provenance labels; OWNER-RESERVED means owner-only. |
| Design maturity | DRAFT, RECONCILED, CANDIDATE, FROZEN | How mature the design/contract is. |
| Implementation | NOT_IMPLEMENTED, IN_PROGRESS, IMPLEMENTED, PARTIALLY_IMPLEMENTED, RETIRED | What exists in a specific implementation. |
| Evidence | NOT_RUN, NOT_VERIFIED, VERIFIED, FAILED, NOT_APPLICABLE, INCONCLUSIVE | What has actually been tested or inspected, with scope and evidence. |
| QA outcome | PASS, PASS_WITH_WARNINGS, NEEDS_REVIEW, BLOCKED | Independent or designated quality disposition; hard blockers remain blocking. |
| Execution outcome | Includes UNKNOWN_OUTCOME where applicable | Execution uncertainty is not the same as QA or evidence status. |

## 6. Contract freeze gate

A contract freeze is a controlled approval event, not a document formatting milestone. The freeze decision should be made only when all required evidence is assembled and the owner can review a concise exception list.

| Gate | Required condition | Evidence required | Current assessment |
| --- | --- | --- | --- |
| F1 — Authority | Decision register and governing source hierarchy are identified | Source inventory and provenance map | PARTIAL |
| F2 — Exact wording | All governing CF wording imported and reconciled | Artifact 08 extraction sheet with locators | NOT READY |
| F3 — Semantics | Entities, states, transitions, events, errors, permissions and invariants agree | Cross-contract consistency matrix | NOT VERIFIED |
| F4 — Traceability | Every P0 requirement maps to contract element, WP owner and acceptance test | Requirement-to-contract-to-test matrix | PARTIAL |
| F5 — Exceptions | No unresolved critical conflict; all deferrals explicit and bounded | Conflict register and owner-reserved list | OPEN |
| F6 — Owner approval | Owner explicitly approves the consolidated freeze candidate | Recorded owner approval tied to exact version/hash | NOT REQUESTED |
| F7 — Change control | Versioning, amendment and supersession rules are stated | Contract change-control section | DRAFT / REVIEW |

Freeze outcome options:

- FREEZE — all mandatory gates pass; exact version and scope are recorded.

- FREEZE WITH EXPLICIT DEFERRED ITEMS — only if each deferral is non-blocking, bounded, assigned and explicitly accepted by the owner.

- DO NOT FREEZE — any mandatory source, semantic, traceability or owner-approval gate remains unresolved.

Current recommendation: DO NOT FREEZE YET. The exact original CF wording and full authoritative source inventory are still incomplete.

## 7. WP-1 schema review: required checks before implementation

This is a design-review checklist only. It does not authorize migrations or repository modifications.

| Review area | Questions the WP-1 contract must answer | Required evidence / output |
| --- | --- | --- |
| Canonical identity | Are canonical IDs immutable UUIDv7? Are identity and version separate? Are retries prevented from creating duplicate canonical entities? | Entity/ID policy and uniqueness constraints |
| Ownership | Does each canonical entity have one authoritative owner? Are cross-domain references typed and non-owning? | Ownership matrix and foreign-key/reference rules |
| Content model | Are ContentItem and ContentVariant distinct? Which fields are shared versus variant-specific? | Entity definitions and examples |
| State separation | Are content, workflow, execution, review, approval, authorization and distribution states independent? | State ownership and transition tables |
| Authorization | Is centralized authorization the only authority? Are approval, authorization and execution distinct? | Policy decision interface and negative tests |
| Rights and evidence | Do unknown/missing/ambiguous rights fail closed for protected actions? Is evidence use-specific and attributable? | Rights schema, evidence references and enforcement cases |
| Auditability | Can every material change, approval, denial and state transition be attributed and correlated? | Audit event schema and correlation identifiers |
| Idempotency | Are idempotency keys and uniqueness scopes defined for commands and job creation? | Idempotency contract and duplicate-request tests |
| Versioning | Are records and artifacts versioned? How are stale reviews and approvals invalidated? | Version binding and supersession rules |
| Deletion / retention | Are retention, legal hold, deletion request and tombstone semantics explicit? | Lifecycle policy and authorization constraints |
| Migration safety | Are migrations additive where possible, reversible where safe, and backed by a tested recovery plan? | Migration plan, backup/restore evidence and rollback boundaries |
| Compatibility | How are schema/API/event versions evolved without breaking active workers or stored records? | Compatibility matrix and deprecation policy |

WP-1 review exit criteria:

- Every persisted field has a named owner, type, nullability, validation rule and lifecycle rule.

- Every enum has an authoritative definition and an explicit unknown/invalid handling policy.

- Every relationship has declared cardinality, ownership semantics and deletion behavior.

- Every protected transition has a centralized authorization check and auditable decision.

- Every critical invariant has at least one positive and one negative acceptance test.

- No migration is run until a separate implementation authorization is recorded.

## 8. P0 cross-package freeze consistency checks

| Invariant | WP-1 | WP-2 | WP-3 | WP-4 | WP-5 | WP-6 |
| --- | --- | --- | --- | --- | --- | --- |
| Canonical identity and version | Persist | Propagate | Bind worker job | Bind artifact | Bind review/approval | Verify end-to-end |
| At-least-once execution + idempotency | Store keys | Enforce | Report attempts | Deduplicate transfer | Audit exceptions | Replay/recovery test |
| Central authorization | Reference policy | Check before dispatch | Scoped credentials | Scoped artifact access | Enforce gates | Negative-path validation |
| Rights / evidence fail-closed | Store evidence | Block unsafe jobs | No capability override | Preserve provenance | Enforce policy | Test blocked path |
| Artifact integrity/versioning | Metadata model | Track outputs | Transfer safely | Hash/version/repair | Bind approvals | Verify recovery |
| Human approval before publishing | Persist approval refs | Require gate | No bypass | Exact artifact version | Authorize action | Prove no publish without approval |
| Existing Shorts Studio preservation | Reference integration boundary | Adapter job contract | Worker boundary | Artifact boundary | Policy boundary | Vertical-slice proof |

A package cannot claim its own invariant is satisfied solely because another package documents it. Each package must provide its own implementation/evidence contribution and WP-6 must verify the integrated behavior.

## 9. Owner-reserved decisions and standing delegation

Accepted decisions must remain accepted; this pack does not reopen them.

- ADR-001–ADR-010 are accepted at decision level.

- CF-01–CF-15 are explicitly accepted; CF-16–CF-21 and CF-23 were accepted under standing delegation; CF-22 is accepted (Option A — centralized authorization); CF-24 is accepted (no paid services, provider/operational choices deferred).

- No paid service, provider activation, cloud deployment, public publishing, production generation, or external side effect is authorized by the accepted architecture decisions.

- Owner-reserved decisions remain owner-only. Agent or assistant recommendations are not approval.

Approval distinctions remain mandatory:

| Term | Meaning | Must not be confused with |
| --- | --- | --- |
| Review | A person examines an item and records findings | Approval or authorization |
| Approval | An authorized reviewer accepts an exact version for a defined purpose | Permission to execute an external action |
| Authorization | Central policy grants a scoped action to a principal | Proof that execution succeeded |
| Execution | A bounded worker attempts the authorized operation | Successful external outcome |
| Confirmed outcome | Evidence verifies what happened externally | A mere API request or local success message |

## 10. Engineering and repository safety boundary

The historical repository snapshot is context, not a fresh inspection. Project path previously reported: /home/demon/shorts_studio. The last supplied snapshot reported 23 tracked modified files and 56 untracked paths; all such work must be preserved.

- Do not reset, revert, stash, clean, delete, overwrite, rename, broadly stage, commit, push, change branches or remotes without explicit approval.

- Do not run migrations, modify code, launch agents, run tests, deploy, activate providers, spend money, generate production content, upload or publish under this pack.

- Do not repeat repository inventory checks merely to advance the document workflow. Refresh a baseline only when implementation is separately authorized and the check is genuinely necessary.

- Preserve the existing Python/FFmpeg Shorts Studio as a bounded specialist engine; do not replace it wholesale.

- Local-first/free-first remains the initial operating constraint. Local work waits safely if its worker is unavailable; no paid fallback is implied.

Agent ownership remains: Qoder — Phase 11 engineering owner; OpenCode — Phase 10 engineering/closure owner; Kilo — independent read-only QA. No agent assignment or execution is authorized here.

## 11. Source intake and closure runbook

1. Locate Artifact 08 and the original ODR master register in the authoritative project/source location.

1. Record filename, version/date, owner/custodian, and source integrity metadata. Do not rename or move source files.

1. Extract the exact CF rows listed in Section 4, preserving notes, options and provenance.

1. Inspect the full ODR register to resolve whether ODR-22 is a real combined row or a provisional grouping.

1. Locate the governing data dictionary, API/event contract, lifecycle contract and approved WP specifications.

1. Populate the source inventory and conflict register with precise locators; keep unavailable items marked NOT VERIFIED.

1. Run a consistency review across the source-derived contracts and the accepted ADR/CF decision outcomes.

1. Prepare a versioned freeze candidate and a short exception report; do not mark it FROZEN.

1. Present only genuinely critical unresolved owner decisions for explicit approval.

1. After owner approval of the exact freeze candidate, issue a separate WP-1 implementation authorization with scope, allowed files/actions, test plan and rollback boundaries.

## 12. Final readiness scorecard

| Readiness dimension | Status | Reason / next evidence |
| --- | --- | --- |
| Architecture direction | ACCEPTED | ADR-001–ADR-010 and accepted decision outcomes recorded. |
| Decision outcome coverage | RECORDED | CF-01–CF-24 outcomes recorded; do not reopen accepted decisions. |
| Exact original CF source wording | NOT VERIFIED | Import and verify the identified rows from Artifact 08. |
| Authoritative source inventory | PARTIAL | Reconcile the full indexed artifact set and original registers. |
| Cross-contract semantic consistency | NOT VERIFIED | Complete source-led entity/state/API/event/WP comparison. |
| Contract freeze | NOT READY | Mandatory source and consistency gates remain open; owner freeze approval not requested. |
| WP-1 schema review | PREPARATION READY | Checklist exists; approved source contract and field-level review still required. |
| WP-1 implementation authorization | NOT AUTHORIZED | Requires separate explicit authorization after freeze/readiness review. |
| Runtime / independent QA | NOT VERIFIED | Historical reports are not fresh runtime evidence; independent QA remains pending. |

END OF BATCH 04


## Source document metadata (preserved from DOCX)

- **Footer:** NEXTDECODE • P0 governance working document • Not an implementation authorization

