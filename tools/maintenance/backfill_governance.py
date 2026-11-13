#!/usr/bin/env python3
"""Owner-run governance backfill for legacy pre-governance artifacts.

DISABLED BY DEFAULT.  This utility is never invoked by any pipeline, scheduler,
CI step or test of production behavior: it exists solely so the OWNER can
grandfather one specific already-approved legacy artifact without regenerating
it.  A backfill run requires BOTH gates:

    * the flag ``--execute``, and
    * the environment variable ``BACKFILL_CONFIRM=YES``

Any other invocation prints the plan only (the digests it WOULD record) and
exits 2 without touching a single file.

Protocol (fail-closed, non-circular; see publish_authorization._backfill_journal_receipt)
----------------------------------------------------------------------------------------
1. Pre-checks: the current artifact must still be approved and hash-bound
   (``verify_approval_binding``) and must carry no governance stamp yet.
2. ``stamp-commit`` journal line: digests of the payload WITH the governance
   stamp but WITHOUT ``receipt_ref`` (canonical serialization ``json.dumps(
   payload, indent=2) + "\\n"``), plus the video digest, purpose, UTC
   timestamp, ``owner_note`` and ``prev_sha256`` (hash of the previous raw
   journal line; empty string at genesis).
3. The in-file stamp is written with ``receipt_ref`` = sha256 of the raw
   stamp-commit line — the only ref the file carries; no digests in-file.
4. ``stamped-artifact`` journal line: ``receipt_ref``, the digests of the
   FINAL stamped bytes, video digest, timestamp, ``prev_sha256`` =
   sha256 of the stamp-commit line.
5. Owner then re-approves: ``review_bundle`` -> ``approve_review`` binds the
   freshly stamped bytes through the normal approval flow.  Authorization
   requires BOTH the journal chain AND the standard approval binding.

Trust model / documented limitations
------------------------------------
* The hash chain is tamper-EVIDENT against every edit, splice, deletion or
  rebuild of past lines: ``publish_authorization`` re-verifies the whole chain
  from genesis at authorize time.  It is NOT crypto-protection against an
  operator who can rewrite ``data/governance_backfill.jsonl`` in place and
  recompute the whole chain (same-domain storage limitation).  That residual
  risk is accepted and mitigated operationally:
    - the journal is created with owner-only permissions (0600 on POSIX);
    - the workflow is strictly append-only (the utility never rewrites);
    - every line records ``owner_note`` and the plus-side whole-flow check is
      always the approval digest binding, which the journal cannot forge.
* The utility refuses to run if it cannot bind the CURRENT artifact through
  the normal approval flow first, so trust always enters through the owner's
  re-approval, never from file age or automatic rules.

Examples
--------
    # plan only (default, writes nothing)
    ./venv/bin/python backfill_governance.py --purpose short \\
        --owner-note "manual owner action: legacy artifact re-approved 2026-11-01"

    # real run (still owner-driven)
    BACKFILL_CONFIRM=YES ./venv/bin/python backfill_governance.py --purpose short \\
        --owner-note "..." --execute
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.publish.authorization import PACKAGES, PublishNotAuthorized, backfill_line_sha256, verify_approval_binding

JOURNAL_PATH = ROOT / "data" / "governance_backfill.jsonl"
EXECUTE_ENV = "BACKFILL_CONFIRM"
EXECUTE_ENV_VALUE = "YES"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_last_line_digest(journal: Path) -> str:
    """Digest of the last existing journal line; "" at genesis."""
    if not journal.is_file():
        return ""
    lines = [line for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
    return backfill_line_sha256(lines[-1]) if lines else ""


def _append_journal_line(journal: Path, record: dict) -> str:
    """Append one raw line to the journal; return the line's own sha256."""
    journal.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record)
    created = not journal.is_file()
    with journal.open("a", encoding="utf-8") as journal_file:
        journal_file.write(line + "\n")
    if created and os.name == "posix":
        # Journal tamper-evidence is the chain; these permissions are the
        # operational mitigation for the same-domain limitation above.
        try:
            journal.chmod(stat.S_IRWXU)  # 0o600: owner read/write only
        except OSError:
            pass
    return backfill_line_sha256(line)


def plan_backfill(root: Path, purpose: str, owner_note: str) -> dict:
    """Compute (without writing) everything a backfill of ONE artifact needs."""
    if purpose not in PACKAGES:
        raise SystemExit(f"unknown purpose {purpose!r}; expected one of {sorted(PACKAGES)}")
    root = Path(root)
    spec = PACKAGES[purpose]
    metadata_file = root / Path(*spec["metadata"])
    video_file = root / Path(*spec["video"])
    if not metadata_file.is_file() or not video_file.is_file():
        raise SystemExit(f"artifact missing for purpose {purpose}: {metadata_file} / {video_file}")
    try:
        payload = json.loads(metadata_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"metadata is unreadable or malformed: {exc}")
    if not isinstance(payload, dict):
        raise SystemExit("metadata is not a JSON object")
    if isinstance(payload.get("governance"), dict):
        raise SystemExit("metadata already carries a governance stamp; nothing to backfill")
    binding_issue = verify_approval_binding(data_root=root, purpose=purpose)
    if binding_issue:
        raise SystemExit(f"refusing: the CURRENT artifact is not approved/hash-bound ({binding_issue})")
    payload["governance"] = {"entry": "legacy-backfill", "publishable": True,
                             "stamped_at": _utcnow()}
    return payload


def apply_backfill(root: Path, purpose: str, owner_note: str) -> dict:
    """Stamp one approved legacy artifact and append its two journal records.

    Ordering is: pre-checks -> stamp-commit line (digests of the final-minus-ref
    serialization) -> in-file stamp write with receipt_ref -> stamped-artifact
    line (final digests).  The validator recomputes every step above.
    """
    payload = plan_backfill(root, purpose, owner_note)
    root = Path(root)
    spec = PACKAGES[purpose]
    metadata_file = root / Path(*spec["metadata"])
    video_file = root / Path(*spec["video"])

    commit_text = json.dumps(payload, indent=2) + "\n"
    commit_record = {
        "kind": "stamp-commit",
        "purpose": purpose,
        "metadata_sha256": hashlib.sha256(commit_text.encode("utf-8")).hexdigest(),
        "video_sha256": hashlib.sha256(video_file.read_bytes()).hexdigest(),
        "backfilled_at": payload["governance"]["stamped_at"],
        "owner_note": str(owner_note or "").strip(),
        "prev_sha256": _read_last_line_digest(JOURNAL_PATH),
    }
    receipt_ref = _append_journal_line(JOURNAL_PATH, commit_record)

    payload["governance"]["receipt_ref"] = receipt_ref
    # must differ from the commit serialization ONLY by receipt_ref
    stamped_text = json.dumps(payload, indent=2) + "\n"
    final_record = {
        "kind": "stamped-artifact",
        "receipt_ref": receipt_ref,
        "purpose": purpose,
        "metadata_sha256": hashlib.sha256(stamped_text.encode("utf-8")).hexdigest(),
        "video_sha256": commit_record["video_sha256"],
        "backfilled_at": _utcnow(),
        "prev_sha256": backfill_line_sha256(json.dumps(commit_record)),
    }
    metadata_file.write_bytes(stamped_text.encode("utf-8"))
    _append_journal_line(JOURNAL_PATH, final_record)
    return {"stamped_metadata": str(metadata_file),
            "receipt_ref": receipt_ref,
            "metadata_sha256": final_record["metadata_sha256"],
            "next_step": "re-approve: review_bundle -> approve_review binds the stamped bytes"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Owner-run legacy governance backfill (disabled by default)")
    parser.add_argument("--purpose", choices=sorted(PACKAGES), default="short")
    parser.add_argument("--owner-note", default="", help="operator identity / reference")
    parser.add_argument("--execute", action="store_true",
                        help="gate 1: without it nothing is ever written")
    args = parser.parse_args(argv)

    confirm = os.getenv(EXECUTE_ENV, "").strip().upper() == EXECUTE_ENV_VALUE
    if not (args.execute and confirm):
        try:
            payload = plan_backfill(ROOT, args.purpose, args.owner_note)
            print(json.dumps({"status": "plan-only",
                              "would_stamp": payload["governance"],
                              "owner_note": args.owner_note,
                              "journal": str(JOURNAL_PATH)}))
        except SystemExit as exc:
            print(json.dumps({"status": "plan-only", "error": str(exc)}))
        print("[backfill] disabled by default: pass --execute AND BACKFILL_CONFIRM=YES "
              "to record a backfill. Nothing was written.")
        return 2
    result = apply_backfill(ROOT, args.purpose, args.owner_note)
    print(json.dumps({"status": "backfilled", **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
