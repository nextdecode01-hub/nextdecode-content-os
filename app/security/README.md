# Security primitives

`approval_integrity.py` owns the shared, low-level primitives used by review and publishing workflows:

- SHA-256 file hashing for artifact binding.
- IST-local approval-date validation.
- The configured 20:00 IST upload-window check.

These helpers do not grant publishing authority. The single policy decision remains in the separate `publish_authorization.py` boundary. Keep the two concepts distinct.

The repository-root `approval_integrity.py` is a compatibility import shim. Application code must import `app.security.approval_integrity` directly. The root shim preserves legacy import identity for existing tests and external callers.
