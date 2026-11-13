# Local Review Approval Trust Boundary

Status: local operational documentation; not a canonical contract or identity specification.

## Reviewer identity

The `--reviewer` argument accepted by `approve_review.py` is a locally asserted reviewer label. It is not authenticated by an identity provider, operating-system credential challenge, digital signature, or independent second factor. The resulting approval record provides a traceable assertion and rationale; it does not provide authenticated identity, non-repudiation, or proof that the named person personally invoked the command.

## Operational responsibility

Only the accountable human reviewer should be permitted to invoke the approval command and write the local review-approval state. Access to the workstation, repository, approval package, and local data directory is part of the trust boundary. Operators must not treat a reviewer string as proof of identity.

## Integrity binding

The approval process parses the review package from one byte buffer and calculates the recorded SHA-256 digest from that same buffer. Publishing authorization later compares the current package bytes against that digest. A package changed after approval is therefore rejected by authorization.

## Scope and limitations

This is a local Shorts Studio operational control only. It does not define or change canonical CF-21 fields, entities, events, schemas, reviewer identity semantics, or authorization relationships. Stronger identity assurance requires a separately owner-approved authentication design and corresponding security/QA acceptance.

Public publishing remains disabled. No external identity provider, provider API, upload, or network action is part of this control.
