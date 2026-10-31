"""
Run 100 contract reviews and collect empirical TCO data.

Usage:
    python scripts/run_tco_simulation.py

Requires AIREFINERY_API_KEY to be set in environment or .env file.
Writes:
  measurements/tco_results.json     — TCO category breakdown + trend
  measurements/economics_results.json — AgentCostEvent-based outcome economics
"""
from __future__ import annotations

import asyncio
import json
import random
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.graph import build_harness
from cost_model.incident_cost import IncidentCostTracker
from cost_model.review_queue import ReviewQueueSimulator
from cost_model.tco_aggregator import RunCost, TCOAggregator
from economics.adapter import PlatformCosts, RunMeta, to_cost_event
from economics.model import AgentCostEvent, summarize

_RUNS = 100
_INCIDENT_RATE = 0.08
_EVAL_SHARE_RATE = 0.15

_CONTRACT_TYPES = ["service", "supply", "nda"]
_VENDOR_NAMES = [
    "Acme Corp", "GlobalTech Ltd", "SafeVendor Inc", "RiskySupplier Co",
    "BalancedServices GmbH", "ClearTerms LLC", "DataVault Systems", "TrustFirst Corp",
]

_rng = random.Random(42)


def _make_contract(run_number: int) -> dict:
    return {
        "contract_id": f"CTR-SIM-{run_number:04d}",
        "vendor_name": _rng.choice(_VENDOR_NAMES),
        "contract_type": _rng.choice(_CONTRACT_TYPES),
        "page_count": _rng.randint(5, 60),
        "text_sample": (
            "This service agreement includes standard commercial terms. "
            "Vendor provides professional services as described in Exhibit A. "
            "Fees are fixed for the initial term with renewal options. "
            "Either party may terminate with 60-day written notice."
        ),
    }


_AGENT_ID = "contract-review-agent"
_WORKFLOW = "contract_review"
_OWNER = "legal-ops"
_COST_CENTER = "CC200"


async def _run_simulation() -> None:
    harness = build_harness()
    review_sim = ReviewQueueSimulator(seed=42)
    incident_tracker = IncidentCostTracker()
    tco = TCOAggregator()
    platform = PlatformCosts.from_env()
    cost_events: list[AgentCostEvent] = []

    print(f"Starting {_RUNS}-run TCO simulation…")

    for i in range(1, _RUNS + 1):
        contract = _make_contract(i)
        result = await harness.run(contract)

        token_cost = result.cost_usd
        overall_risk = "medium"
        flag_count = 2
        if result.success and result.output:
            overall_risk = result.output.overall_risk
            flag_count = result.output.flag_count

        review = review_sim.simulate(overall_risk, flag_count)
        eval_cost = token_cost * _EVAL_SHARE_RATE

        is_incident = _rng.random() < _INCIDENT_RATE
        incident_record = incident_tracker.maybe_record(contract["contract_id"], is_incident)
        incident_cost = incident_record.total_cost_usd if incident_record else 0.0

        run_cost = RunCost(
            run_id=result.run_id,
            token_cost_usd=token_cost,
            review_cost_usd=review.cost_usd,
            eval_cost_usd=eval_cost,
            incident_cost_usd=incident_cost,
            retry_cost_usd=0.0,
        )
        tco.add(run_cost)

        meta = RunMeta(
            run_id=result.run_id, agent_id=_AGENT_ID, workflow=_WORKFLOW,
            owner=_OWNER, cost_center=_COST_CENTER, successful=result.success,
        )
        cost_events.append(to_cost_event(meta, run_cost, platform))

        if i % 10 == 0:
            print(f"  Completed {i}/{_RUNS} runs…")

    out_dir = Path("measurements")
    out_dir.mkdir(exist_ok=True)

    summary = tco.summary()
    summary["run_totals"] = tco.run_totals()
    with open(out_dir / "tco_results.json", "w") as f:  # noqa: ASYNC230
        json.dump(summary, f, indent=2)

    outcome = summarize(cost_events)
    econ = {
        "disclaimer": "Empirical — token costs from real AI Refinery runs via harness",
        "runs": outcome.runs,
        "successful_outcomes": outcome.successes,
        "total_cost_usd": round(outcome.total_cost, 4),
        "cost_per_run_usd": round(outcome.cost_per_run, 4),
        "cost_per_success_usd": round(outcome.cost_per_success, 4),
        "model_share_pct": round(
            100 * sum(e.model for e in cost_events) / outcome.total_cost, 1
        ) if outcome.total_cost > 0 else 0.0,
        "human_review_share_pct": round(
            100 * sum(e.human_review for e in cost_events) / outcome.total_cost, 1
        ) if outcome.total_cost > 0 else 0.0,
    }
    with open(out_dir / "economics_results.json", "w") as f:  # noqa: ASYNC230
        json.dump(econ, f, indent=2)

    print(f"\nSimulation complete.")
    print(f"  TCO breakdown  → measurements/tco_results.json")
    print(f"  Outcome econ   → measurements/economics_results.json")
    print(f"  Total cost: ${summary['total_cost_usd']:.4f}")
    print(f"  Token cost: {summary['token_cost_pct']:.1f}% of TCO")
    print(f"  Review cost: {summary['review_cost_pct']:.1f}% of TCO")
    print(f"  Cost/success: ${econ['cost_per_success_usd']:.4f}")
    print(f"  Incidents: {incident_tracker.incident_count()} ({incident_tracker.total_cost_usd():.2f} USD)")


if __name__ == "__main__":
    asyncio.run(_run_simulation())
