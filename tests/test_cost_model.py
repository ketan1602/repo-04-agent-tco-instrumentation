"""Tests for the cost_model modules — no external calls required."""
from __future__ import annotations

from cost_model.incident_cost import IncidentCostTracker
from cost_model.review_queue import ReviewQueueSimulator
from cost_model.tco_aggregator import RunCost, TCOAggregator


def test_review_queue_returns_result():
    sim = ReviewQueueSimulator(seed=42)
    result = sim.simulate("high", 3)
    assert result.time_minutes > 0
    assert result.cost_usd > 0
    assert result.reviewer_tier == "senior"


def test_review_queue_acceptable_risk_is_cheaper():
    sim = ReviewQueueSimulator(seed=42)
    high = sim.simulate("high", 0)
    sim2 = ReviewQueueSimulator(seed=42)
    acceptable = sim2.simulate("acceptable", 0)
    assert high.cost_usd > acceptable.cost_usd


def test_review_queue_more_flags_increases_time():
    sim1 = ReviewQueueSimulator(seed=99)
    r1 = sim1.simulate("medium", 0)
    sim2 = ReviewQueueSimulator(seed=99)
    r2 = sim2.simulate("medium", 5)
    assert r2.time_minutes > r1.time_minutes


def test_incident_tracker_no_incident():
    tracker = IncidentCostTracker()
    record = tracker.maybe_record("run-001", False)
    assert record is None
    assert tracker.incident_count() == 0
    assert tracker.total_cost_usd() == 0.0


def test_incident_tracker_records_incident():
    tracker = IncidentCostTracker()
    record = tracker.maybe_record("run-001", True)
    assert record is not None
    assert record.total_cost_usd == record.detection_cost_usd + record.remediation_cost_usd
    assert tracker.incident_count() == 1
    assert tracker.total_cost_usd() > 0


def test_tco_aggregator_empty_summary():
    agg = TCOAggregator()
    summary = agg.summary()
    assert summary["total_runs"] == 0
    assert summary["total_cost_usd"] == 0


def test_tco_aggregator_accumulates():
    agg = TCOAggregator()
    agg.add(RunCost("r1", token_cost_usd=0.001, review_cost_usd=0.50,
                    eval_cost_usd=0.0002, incident_cost_usd=0.0, retry_cost_usd=0.0))
    agg.add(RunCost("r2", token_cost_usd=0.002, review_cost_usd=0.30,
                    eval_cost_usd=0.0003, incident_cost_usd=0.0, retry_cost_usd=0.0))
    summary = agg.summary()
    assert summary["total_runs"] == 2
    assert summary["total_cost_usd"] > 0
    assert summary["review_cost_pct"] > summary["token_cost_pct"]


def test_tco_aggregator_percentages_sum_to_100():
    agg = TCOAggregator()
    agg.add(RunCost("r1", token_cost_usd=0.01, review_cost_usd=0.50,
                    eval_cost_usd=0.05, incident_cost_usd=0.80, retry_cost_usd=0.02))
    s = agg.summary()
    total_pct = (s["token_cost_pct"] + s["review_cost_pct"] + s["eval_cost_pct"]
                 + s["incident_cost_pct"] + s["retry_cost_pct"])
    assert abs(total_pct - 100.0) < 0.5


def test_run_totals_returns_correct_length():
    agg = TCOAggregator()
    for i in range(5):
        agg.add(RunCost(f"r{i}", 0.001, 0.10, 0.0002, 0.0, 0.0))
    assert len(agg.run_totals()) == 5
