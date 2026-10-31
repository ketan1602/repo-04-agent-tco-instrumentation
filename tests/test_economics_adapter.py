"""Tests for economics adapter — no LLM calls required."""
from __future__ import annotations

import pytest

from cost_model.tco_aggregator import RunCost
from economics.adapter import PlatformCosts, RunMeta, to_cost_event
from economics.model import (
    AgentCostEvent,
    FailureScenario,
    HarnessInvestment,
    OutcomeEconomics,
    summarize,
)


def _meta(run_id: str = "r1", successful: bool = True) -> RunMeta:
    return RunMeta(
        run_id=run_id, agent_id="contract-review-agent",
        workflow="contract_review", owner="legal-ops",
        cost_center="CC200", successful=successful,
    )


def _run_cost(
    token: float = 0.010,
    review: float = 0.500,
    eval_: float = 0.0015,
    incident: float = 0.0,
    retry: float = 0.0,
) -> RunCost:
    return RunCost(
        run_id="r1", token_cost_usd=token, review_cost_usd=review,
        eval_cost_usd=eval_, incident_cost_usd=incident, retry_cost_usd=retry,
    )


def test_to_cost_event_maps_token_and_review():
    event = to_cost_event(_meta(), _run_cost(token=0.010, review=0.500))
    assert event.model == 0.010
    assert event.human_review == 0.500
    assert event.evaluation == 0.0015
    assert event.successful is True
    assert event.owner == "legal-ops"
    assert event.cost_center == "CC200"


def test_to_cost_event_incident_plus_retry_become_remediation():
    event = to_cost_event(_meta(), _run_cost(incident=0.85, retry=0.05))
    assert event.remediation == pytest.approx(0.90)


def test_to_cost_event_platform_costs_default_to_zero():
    event = to_cost_event(_meta(), _run_cost())
    assert event.runtime == 0.0
    assert event.observability == 0.0
    assert event.control == 0.0


def test_to_cost_event_with_explicit_platform_costs():
    platform = PlatformCosts(runtime_per_run=0.002, observability_per_run=0.001, control_per_run=0.001)
    event = to_cost_event(_meta(), _run_cost(), platform=platform)
    assert event.runtime == 0.002
    assert event.observability == 0.001
    assert event.control == 0.001


def test_platform_costs_from_env(monkeypatch):
    monkeypatch.setenv("PLATFORM_RUNTIME_COST_PER_RUN", "0.003")
    monkeypatch.setenv("PLATFORM_OBSERVABILITY_COST_PER_RUN", "0.001")
    monkeypatch.setenv("PLATFORM_CONTROL_COST_PER_RUN", "0.002")
    p = PlatformCosts.from_env()
    assert p.runtime_per_run == pytest.approx(0.003)
    assert p.observability_per_run == pytest.approx(0.001)
    assert p.control_per_run == pytest.approx(0.002)


def test_platform_costs_from_env_defaults_to_zero(monkeypatch):
    monkeypatch.delenv("PLATFORM_RUNTIME_COST_PER_RUN", raising=False)
    monkeypatch.delenv("PLATFORM_OBSERVABILITY_COST_PER_RUN", raising=False)
    monkeypatch.delenv("PLATFORM_CONTROL_COST_PER_RUN", raising=False)
    p = PlatformCosts.from_env()
    assert p.runtime_per_run == 0.0
    assert p.observability_per_run == 0.0
    assert p.control_per_run == 0.0


def test_summarize_counts_successes_correctly():
    events = [
        to_cost_event(_meta("r1", successful=True), _run_cost()),
        to_cost_event(_meta("r2", successful=True), _run_cost()),
        to_cost_event(_meta("r3", successful=False), _run_cost()),
    ]
    outcome = summarize(events)
    assert outcome.runs == 3
    assert outcome.successes == 2


def test_cost_per_success_exceeds_cost_per_run_when_failures_exist():
    events = [
        to_cost_event(_meta("r1", successful=True), _run_cost(token=0.01, review=0.50)),
        to_cost_event(_meta("r2", successful=False), _run_cost(token=0.01, review=0.30)),
    ]
    outcome = summarize(events)
    assert outcome.cost_per_success > outcome.cost_per_run


def test_token_cost_is_minority_of_tco():
    """The article's central claim: model tokens are not the dominant cost."""
    events = [
        to_cost_event(_meta(f"r{i}", successful=True), _run_cost(token=0.010, review=0.500))
        for i in range(20)
    ]
    outcome = summarize(events)
    total_token = sum(e.model for e in events)
    assert total_token / outcome.total_cost < 0.5


def test_harness_investment_amortizes_with_agent_count():
    inv = HarnessInvestment(initial_build=80_000, annual_operations=40_000, integration_per_agent=4_000)
    assert inv.cost_per_agent(1) > inv.cost_per_agent(10)
    assert inv.cost_per_agent(10) > inv.cost_per_agent(100)


def test_failure_scenario_expected_cost():
    scenario = FailureScenario(
        probability_per_transaction=0.002,
        impact_per_event=250,
        transactions=100_000,
        recovery_multiplier=1.4,
    )
    assert scenario.expected_cost == pytest.approx(70_000)


def test_negative_cost_raises():
    event = AgentCostEvent("r1", "a", "w", "o", "c", True, model=-0.01)
    with pytest.raises(ValueError, match="nonneg"):
        _ = event.cost
