# NEXTDECODE P0 — Owner Review & Implementation Authorization Checklist

**Version:** 0.1  
**Status:** Review aid; no approval is recorded by this document

## 1. Purpose

Keep three separate owner decisions explicit:
1. Approval of the detailed contract baseline.
2. Authorization to implement a named work package.
3. Authorization for external operations such as spending, provider activation, deployment or publishing.

One does not imply another.

## 2. Contract baseline review

Before a detailed contract freeze, confirm:
- [ ] Accepted ADR-001–ADR-010 and CF-01–CF-24 are represented accurately.
- [ ] Source precedence and conflicts are documented.
- [ ] Canonical entities and ownership are complete.
- [ ] Workflow/Task/Job/Attempt/Lease boundaries and transitions are explicit.
- [ ] Worker identity, trust, capability and credential rules are explicit.
- [ ] Artifact/version/manifest/transfer/quarantine lifecycle is explicit.
- [ ] Governance concepts and authorization enforcement are explicit.
- [ ] API/event envelopes, idempotency, compatibility and replay rules are explicit.
- [ ] Retention, legal hold, purge and emergency-pause owner-reserved decisions are resolved or explicitly deferred.
- [ ] Numeric operational parameters are resolved or explicitly deferred with safe behavior.
- [ ] Test oracles and evidence requirements are traceable.
- [ ] Exact document set, versions and hashes (where available) are recorded.

**Freeze record:** exact baseline ID/version, approving owner, date, scope, exclusions and superseded baseline.

## 3. First implementation authorization

For the first engineering authorization, specify:
- Work package: normally WP-1 only.
- Exact approved contract baseline.
- Repository and permitted paths.
- Whether isolated worktree/branch is allowed.
- Existing user modifications/untracked files to preserve.
- Allowed commands and test scope.
- Database/migration constraints.
- Prohibited operations.
- Named engineering owner.
- Required evidence and acceptance reviewer.
- Stop conditions and escalation path.

Recommended first scope: WP-1 canonical domain and persistence foundation only. Do not authorize all WP-1–WP-6 as one broad task unless the owner explicitly chooses that risk.

## 4. External operations authorization — separate

The following each require separate explicit approval:
- Paid service or infrastructure spend.
- Cloud provider/account activation.
- Production deployment.
- Real-data migration.
- External API action with material side effects.
- Public publishing or automated distribution.
- Irreversible deletion/purge.
- Any break-glass governance exception.

## 5. Standing constraints carried forward

- Single-owner Creator Mode initially; one NEXTDECODE brand.
- Local-first/free-first; ₹0 initial spend target.
- Existing Shorts Studio is preserved and integrated through a bounded adapter.
- Human approval before critical publishing actions.
- Automatic public publishing disabled pending separate policy.
- No silent permission from unknown rights/approval/authorization.
- No broad destructive Git operations or user-work replacement.
- Agents cannot self-expand scope or self-approve.

## 6. Current status

This checklist is not filled in and records no new owner decisions. Existing accepted ADR/CF decisions remain accepted as previously recorded; this checklist does not re-open them. Formal detailed contract freeze and implementation authorization remain pending.
