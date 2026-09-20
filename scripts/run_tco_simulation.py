"""
Run 100 contract reviews with simulated TCO components.

Usage:
    python scripts/run_tco_simulation.py

Requires AIREFINERY_API_KEY to be set in environment or .env file.
Writes measurements/tco_results.json on completion.
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


async def _run_simulation() -> None:
    harness = build_harness()
    review_sim = ReviewQueueSimulator(seed=42)
    incident_tracker = IncidentCostTracker()
    tco = TCOAggregator()

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

        tco.add(RunCost(
            run_id=result.run_id,
            token_cost_usd=token_cost,
            review_cost_usd=review.cost_usd,
            eval_cost_usd=eval_cost,
            incident_cost_usd=incident_cost,
            retry_cost_usd=0.0,
        ))

        if i % 10 == 0:
            print(f"  Completed {i}/{_RUNS} runs…")

    summary = tco.summary()
    summary["run_totals"] = tco.run_totals()

    out_path = Path("measurements/tco_results.json")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:  # noqa: ASYNC230
        json.dump(summary, f, indent=2)

    print(f"\nSimulation complete. Results written to {out_path}")
    print(f"  Total cost: ${summary['total_cost_usd']:.4f}")
    print(f"  Token cost: {summary['token_cost_pct']:.1f}% of TCO")
    print(f"  Review cost: {summary['review_cost_pct']:.1f}% of TCO")
    print(f"  Incidents: {incident_tracker.incident_count()} ({incident_tracker.total_cost_usd():.2f} USD)")


if __name__ == "__main__":
    asyncio.run(_run_simulation())
