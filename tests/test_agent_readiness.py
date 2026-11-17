from datetime import datetime, timedelta, timezone

import pytest

from app.autonomy.agent_runtime import (
    AgentReadinessEvidence,
    AgentRuntimeRegistry,
    AgentSpec,
)


def _registry(*specs: AgentSpec) -> AgentRuntimeRegistry:
    return AgentRuntimeRegistry(specs)


def test_unknown_agent_is_not_in_readiness_records(monkeypatch):
    registry = _registry(AgentSpec("known", "Known", "known-cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: None)
    assert registry.get_readiness("unknown") is None
    assert [item["agent_id"] for item in registry.readiness()["agents"]] == ["known"]


def test_missing_executable_is_discovered_but_not_installed_or_available(monkeypatch):
    registry = _registry(AgentSpec("missing", "Missing", "missing-cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: None)
    record = registry.get_readiness("missing")
    assert record["states"]["discovered"]["value"] is True
    assert record["states"]["installed"]["value"] is False
    assert record["states"]["available"]["value"] is False
    assert record["states"]["invocation_authorized"]["value"] is False


def test_missing_authentication_and_qualification_remain_unverified(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli", ("CLI_AUTH",)))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    monkeypatch.delenv("CLI_AUTH", raising=False)
    record = registry.get_readiness("cli")
    assert record["states"]["configured"]["value"] is False
    assert record["states"]["qualified"]["value"] is False
    assert record["states"]["qualification_pending"]["value"] is True


def test_stale_availability_evidence_is_not_available(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    stale = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    evidence = {"cli": AgentReadinessEvidence(configured=True, qualification_reference="local-test", qualification_passed=True, qualification_evidence_sha256="a" * 64, qualification_capabilities=("review",), availability_observed_at=stale, availability=True)}
    record = registry.get_readiness("cli", evidence=evidence, stale_after_seconds=60)
    assert record["states"]["available"]["value"] is False
    assert record["states"]["available"]["reason"] == "availability_evidence_stale"


def test_revocation_and_invocation_denial_override_other_positive_evidence(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    evidence = {"cli": AgentReadinessEvidence(configured=True, qualification_reference="local-test", availability_observed_at=datetime.now(timezone.utc).isoformat(), availability=True, revoked=True, invocation_authorized=True)}
    record = registry.get_readiness("cli", evidence=evidence)
    assert record["states"]["revoked"]["value"] is True
    assert record["states"]["available"]["value"] is False
    assert record["states"]["invocation_authorized"]["value"] is False


def test_secret_values_are_not_emitted(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli", ("CLI_AUTH",)))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    monkeypatch.setenv("CLI_AUTH", "top-secret-value")
    assert "top-secret-value" not in str(registry.get_readiness("cli"))


def test_readiness_does_not_invoke_or_open_network(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    report = registry.readiness()
    assert report["network_access"] is False
    assert report["invocation_enabled"] is False
    source = __import__("app.autonomy.agent_runtime", fromlist=["x"]).__file__
    assert "subprocess" not in open(source, encoding="utf-8").read()


def test_readiness_cli_does_not_initialize_the_task_store(capsys, monkeypatch):
    from app.autonomy import cli

    monkeypatch.setattr(cli, "_store", lambda *_: pytest.fail("readiness must not initialize task storage"))
    assert cli.main(["agent-readiness"]) == 0
    assert '"invocation_enabled": false' in capsys.readouterr().out



def test_future_availability_observation_is_not_fresh(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    evidence = {"cli": AgentReadinessEvidence(
        configured=True, qualification_reference="qualification",
        qualification_passed=True, qualification_evidence_sha256="a" * 64,
        qualification_capabilities=("review",),
        availability_observed_at=future, availability=True,
    )}
    record = registry.get_readiness("cli", evidence=evidence)
    assert record["states"]["available"]["value"] is False
    assert record["states"]["available"]["reason"] == "availability_evidence_stale"


def test_qualification_reference_alone_does_not_prove_qualification(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    evidence = {"cli": AgentReadinessEvidence(
        configured=True, qualification_reference="arbitrary-string",
        availability_observed_at=datetime.now(timezone.utc).isoformat(),
        availability=True,
    )}
    record = registry.get_readiness("cli", evidence=evidence)
    assert record["states"]["qualified"]["value"] is False
    assert record["states"]["available"]["value"] is False


# --- Review-finding regression tests ---------------------------------------
# Finding 2: availability observations are only fresh within a bounded
# clock-skew window; finding 3: qualification evidence must be digest-verifiable.


def test_small_future_clock_skew_stays_fresh_within_bound(monkeypatch):
    """An observation slightly ahead of the clock (<= 60 s skew) is still fresh."""
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    evidence = {"cli": AgentReadinessEvidence(
        configured=True, qualification_reference="qualification",
        qualification_passed=True, qualification_evidence_sha256="a" * 64,
        qualification_capabilities=("review",),
        availability_observed_at=(datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
        availability=True,
    )}
    record = registry.get_readiness("cli", evidence=evidence)
    assert record["states"]["available"]["value"] is True
    assert record["states"]["available"]["reason"] == "fresh_explicit_observation"


def test_minutes_ahead_observation_is_outside_the_skew_bound(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    evidence = {"cli": AgentReadinessEvidence(
        configured=True, qualification_reference="qualification",
        qualification_passed=True, qualification_evidence_sha256="a" * 64,
        qualification_capabilities=("review",),
        availability_observed_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        availability=True,
    )}
    record = registry.get_readiness("cli", evidence=evidence)
    assert record["states"]["available"]["value"] is False
    assert record["states"]["available"]["reason"] == "availability_evidence_stale"


def test_passed_flag_with_arbitrary_reference_is_not_verifiable(monkeypatch):
    """A passed flag plus an arbitrary reference string is not qualification evidence."""
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    evidence = {"cli": AgentReadinessEvidence(
        configured=True, qualification_reference="arbitrary-string",
        qualification_passed=True,
        availability_observed_at=datetime.now(timezone.utc).isoformat(),
        availability=True,
    )}
    record = registry.get_readiness("cli", evidence=evidence)
    assert record["states"]["qualified"]["value"] is False
    assert record["states"]["qualified"]["reason"] == "qualification_evidence_not_verifiable"
    assert record["states"]["available"]["value"] is False


def test_malformed_qualification_digest_is_not_verifiable(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    evidence = {"cli": AgentReadinessEvidence(
        configured=True, qualification_reference="qualification",
        qualification_passed=True, qualification_evidence_sha256="not-a-digest",
        qualification_capabilities=("review",),
        availability_observed_at=datetime.now(timezone.utc).isoformat(),
        availability=True,
    )}
    record = registry.get_readiness("cli", evidence=evidence)
    assert record["states"]["qualified"]["value"] is False
    assert record["states"]["qualified"]["reason"] == "qualification_evidence_not_verifiable"
    assert record["states"]["available"]["value"] is False


def test_digest_verified_qualification_establishes_qualified_state(monkeypatch):
    registry = _registry(AgentSpec("cli", "CLI", "cli", ("review",), 1, "unknown", "cli"))
    monkeypatch.setattr("app.autonomy.agent_runtime.shutil.which", lambda _: "/bin/cli")
    evidence = {"cli": AgentReadinessEvidence(
        configured=True, qualification_reference="qualification",
        qualification_passed=True, qualification_evidence_sha256="a" * 64,
        qualification_capabilities=("review",),
        availability_observed_at=datetime.now(timezone.utc).isoformat(),
        availability=True,
    )}
    record = registry.get_readiness("cli", evidence=evidence)
    assert record["states"]["qualified"]["value"] is True
    assert record["states"]["qualified"]["reason"] == "qualification_evidence_recorded"
    assert record["states"]["available"]["value"] is True
