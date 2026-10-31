from __future__ import annotations

from dataclasses import replace

import pytest

from economics import (
    DIRECT,
    HARNESSED,
    Assumptions,
    MissingAssumptionError,
    PlatformCosts,
    RunMeta,
    succeeded,
    to_cost_event,
)
from economics.report import SWEEP_REMEDIATION_USD, breakeven, build_report

META = RunMeta("r-1", "support-agent", "support", "customer-platform")
PLATFORM = PlatformCosts(runtime_per_run=0.002, observability_per_run=0.001, control_per_run=0.0005)
ASSUME = Assumptions(token_price_per_1k=0.01, approval_minutes=6, reviewer_rate_per_hour=60,
                     remediation_per_violation=100.0, cost_center="CC1", platform=PLATFORM)

ENV = {"LLM_COST_PER_1K_TOKENS": "0.01", "HUMAN_APPROVAL_MINUTES": "6",
       "HUMAN_REVIEW_RATE_PER_HOUR": "60", "VIOLATION_REMEDIATION_COST_USD": "100",
       "COST_CENTER": "CC1", "PLATFORM_RUNTIME_COST_PER_RUN": "0.002",
       "PLATFORM_OBSERVABILITY_COST_PER_RUN": "0.001", "PLATFORM_CONTROL_COST_PER_RUN": "0.0005"}


def direct(tokens=1000, violated=False, status="executed"):
    return {"tokens": tokens, "violated": violated, "status": status}


def harnessed(tokens=1000, violated=False, passed=True, escalated=False, vetoed=False, retried=False):
    return {"tokens": tokens, "violated": violated, "passed": passed, "escalated": escalated,
            "vetoed": vetoed, "retried": retried, "status": "completed"}


def row(d, h, category="normal_ticket"):
    return {"case": "c", "category": category, "paired": True, "direct": d, "harnessed": h}


def test_assumptions_from_env(monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    loaded = Assumptions.from_env()
    assert loaded == ASSUME
    assert loaded.approval_cost == pytest.approx(6.0)


@pytest.mark.parametrize("missing", sorted(ENV))
def test_a_missing_assumption_is_a_loud_error(monkeypatch, missing):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv(missing)
    with pytest.raises(MissingAssumptionError, match=missing):
        Assumptions.from_env()


def test_a_negative_assumption_is_refused(monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("HUMAN_APPROVAL_MINUTES", "-1")
    with pytest.raises(MissingAssumptionError):
        Assumptions.from_env()


def test_direct_event_has_no_observability_control_or_review():
    event = to_cost_event(META, DIRECT, direct(tokens=2000, violated=True) | {"escalated": True}, ASSUME)
    assert event.model == pytest.approx(0.02)
    assert (event.observability, event.control, event.human_review) == (0.0, 0.0, 0.0)
    assert event.runtime == 0.002
    assert event.remediation == 100.0 and not event.successful


def test_harnessed_event_pays_platform_overhead_and_the_approver():
    event = to_cost_event(META, HARNESSED, harnessed(escalated=True), ASSUME)
    assert event.observability == 0.001 and event.control == 0.0005
    assert event.human_review == pytest.approx(6.0)
    assert event.remediation == 0.0 and event.successful
    assert (event.owner, event.cost_center) == ("customer-platform", "CC1")


def test_success_definitions_differ_by_path():
    assert not succeeded(DIRECT, direct(status="raised:APIConnectionError"))
    assert not succeeded(DIRECT, direct(violated=True))
    assert succeeded(DIRECT, direct())
    assert not succeeded(HARNESSED, harnessed(passed=False))
    assert not succeeded(HARNESSED, harnessed(violated=True))
    assert succeeded(HARNESSED, harnessed(vetoed=True))


def two_runs():
    return [row(direct(), harnessed()),
            row(direct(violated=True), harnessed(vetoed=True, escalated=True), "unauthorized_tool")]


def test_report_counts_and_costs_each_path():
    report = build_report(two_runs(), ASSUME, "m")
    d, h = report[DIRECT], report[HARNESSED]
    assert (d["runs"], d["successes"], d["violations"]) == (2, 1, 1)
    assert (h["runs"], h["successes"], h["violations"]) == (2, 2, 0)
    assert (h["vetoed"], h["escalated"]) == (1, 1)
    assert d["total_cost_usd"] == pytest.approx(2 * 0.01 + 2 * 0.002 + 100.0)
    assert h["total_cost_usd"] == pytest.approx(2 * 0.01 + 2 * (0.002 + 0.001 + 0.0005) + 6.0)
    assert d["cost_per_success_usd"] > h["cost_per_success_usd"]
    assert report["by_category"]["unauthorized_tool"]["direct_violated"] == 1


def test_breakeven_matches_the_sweep():
    rows = two_runs()
    value = breakeven(rows, ASSUME)
    assert value is not None and 0 < value < 100
    below = build_report(rows, replace(ASSUME, remediation_per_violation=value - 1), "m")
    above = build_report(rows, replace(ASSUME, remediation_per_violation=value + 1), "m")
    assert below[HARNESSED]["cost_per_success_usd"] > below[DIRECT]["cost_per_success_usd"]
    assert above[HARNESSED]["cost_per_success_usd"] < above[DIRECT]["cost_per_success_usd"]


def test_breakeven_is_none_when_the_harness_prevents_nothing():
    rows = [row(direct(), harnessed(escalated=True))]
    assert breakeven(rows, ASSUME) is None


def test_breakeven_is_zero_when_the_harness_is_cheaper_at_any_price():
    rows = [row(direct(status="raised:X"), harnessed())]
    assert breakeven(rows, ASSUME) == 0.0


def test_sweep_covers_every_remediation_price():
    sweep = build_report(two_runs(), ASSUME, "m")["remediation_sweep"]
    assert [p["remediation_per_violation_usd"] for p in sweep] == list(SWEEP_REMEDIATION_USD)
    gaps = [p["direct_cost_per_success_usd"] - p["harnessed_cost_per_success_usd"] for p in sweep]
    assert gaps == sorted(gaps)


def test_a_path_with_no_successes_reports_null_not_infinity():
    import json

    report = build_report([row(direct(status="raised:X"), harnessed())], ASSUME, "m")
    assert report[DIRECT]["cost_per_success_usd"] is None
    assert "Infinity" not in json.dumps(report)
