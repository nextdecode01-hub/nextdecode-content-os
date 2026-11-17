import pytest

from app.autonomy.execution_policy import ExecutionPolicy, load_execution_policy


def test_owner_selected_defaults():
    policy = load_execution_policy({})
    assert policy.as_dict() == {
        "mode": "approve_publish", "approval": "exceptions",
        "failure_handling": "auto_recover", "max_stage_attempts": 3,
        "max_provider_attempts": 2, "allow_public_auto_publish": False,
    }


def test_routine_stages_do_not_require_approval():
    policy = load_execution_policy({})
    for action in ("script_review", "storyboard_review", "render_review"):
        assert not policy.requires_human_approval(action)


def test_exceptions_and_public_publish_require_approval():
    policy = load_execution_policy({})
    assert policy.requires_human_approval("resolve_exception", unresolved_exception=True)
    assert not policy.requires_human_approval("resolve_exception")
    assert policy.requires_human_approval("publish_public")
    assert policy.requires_human_approval("publish_any")


def test_recovery_is_bounded_and_cannot_bypass_critical_gates():
    policy = load_execution_policy({})
    assert policy.may_auto_recover("provider_unavailable", attempt=0)
    assert policy.may_auto_recover("asset_irrelevant", attempt=2)
    assert not policy.may_auto_recover("provider_unavailable", attempt=3)
    for failure in ("unknown_asset_rights", "unsupported_claim", "qa_failed", "artifact_integrity_failure"):
        assert not policy.may_auto_recover(failure, attempt=0)


def test_invalid_policy_fails_closed():
    with pytest.raises(ValueError, match="unsupported approval policy"):
        load_execution_policy({"NEXTDECODE_APPROVAL_POLICY": "skip_everything"})
    with pytest.raises(ValueError, match="separate owner authorization"):
        ExecutionPolicy(allow_public_auto_publish=True)


def test_ask_on_failure_disables_automatic_recovery():
    policy = ExecutionPolicy(failure_handling="ask_on_failure")
    assert not policy.may_auto_recover("provider_unavailable", attempt=0)
