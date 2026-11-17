from fastapi import APIRouter, HTTPException, Query

from .service import build_brain_overview

router = APIRouter(prefix="/brain", tags=["central-brain"])


@router.get("/overview")
def brain_overview(limit: int = Query(default=20, ge=1, le=30)):
    try:
        return build_brain_overview(limit=limit)
    except (OSError, ValueError):
        raise HTTPException(status_code=503, detail="brain_context_unavailable") from None


@router.get("/context")
def brain_context():
    try:
        overview = build_brain_overview(limit=1)
        return {
            key: overview[key]
            for key in (
                "schema", "brain_version", "project", "identity", "production",
                "guardrails", "authority",
            )
        }
    except (OSError, ValueError):
        raise HTTPException(status_code=503, detail="brain_context_unavailable") from None


@router.get("/operations")
def brain_operations():
    """Read-only local operations snapshot; explicitly not canonical P0 state."""
    try:
        overview = build_brain_overview(limit=1)
        return {
            "schema": "nextdecode.brain.operations.v1",
            "brain_version": overview["brain_version"],
            "authority": "non_canonical_operational_observation",
            "operations": overview["operations"],
        }
    except (OSError, ValueError):
        raise HTTPException(status_code=503, detail="brain_operations_unavailable") from None


@router.get("/decision")
def brain_next_decision():
    try:
        overview = build_brain_overview(limit=1)
        return {
            "brain_version": overview["brain_version"],
            "decision": overview["next_action"],
            "observed_state": overview["observed_state"],
            "operations": overview["operations"],
        }
    except (OSError, ValueError):
        raise HTTPException(status_code=503, detail="brain_context_unavailable") from None
