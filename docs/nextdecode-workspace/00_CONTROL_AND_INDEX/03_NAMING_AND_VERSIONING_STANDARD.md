# DOCUMENT NAMING AND VERSIONING STANDARD

## File naming
Use: ND-[LAYER]-[DOMAIN]-[DOCUMENT_TYPE]-[NNN]-v[MAJOR.MINOR].md
Examples:
- ND-P0-GOV-DECISION-REGISTER-001-v1.0.md
- ND-P0-WP1-DESIGN-BOUNDARY-001-v0.1.md
- ND-P1-REQ-FUNCTIONAL-001-v0.1.md
- ND-OPS-AGENT-HANDOFF-001-v0.1.md

Use uppercase ASCII, hyphens, stable IDs, and explicit versions. Avoid spaces, ambiguous abbreviations, dates-only filenames, FINAL/FINAL2/NEW labels, and filenames that imply acceptance when status is only candidate.

## Required document header
- Document ID
- Title
- Version
- Date updated
- Status: DRAFT / CANDIDATE / ACCEPTED / FROZEN / HISTORICAL / SUPERSEDED
- Authority and approving decision (if any)
- Owner / maintainer
- Source documents and exact versions
- Dependencies
- Change summary

## Version rules
- MAJOR: owner-approved contract or architecture breaking change.
- MINOR: additive compatible change or new approved content.
- PATCH: editorial correction that does not change meaning.
- Draft edits must not be presented as accepted decisions.
- Never overwrite an accepted source to make it match a proposal; create a new candidate/revision and record supersession only after approval.

## Existing source policy
Existing P0 filenames are preserved until cross-reference analysis and migration approval. This standard governs newly created workspace documents and future approved migrations.