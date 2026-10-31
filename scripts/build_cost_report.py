#!/usr/bin/env python3
"""Price the recorded runs: cost per successful run, direct versus harnessed. No model calls.

Reads measurements/cost_runs.json and the cost assumptions in the environment, so prices can be
changed and the report rebuilt without running the scenario again.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from economics import MissingAssumptionError
from economics.assumptions import Assumptions
from economics.report import build_report

RUNS, OUT = ROOT / "measurements" / "cost_runs.json", ROOT / "measurements" / "cost_results.json"


def _line(label: str, arm: dict) -> str:
    cost = arm["cost_per_success_usd"]
    per_success = "no successes" if cost is None else f"${cost:.4f} per success"
    return (f"  {label:<10} runs {arm['runs']:>3}  ok {arm['successes']:>3}  violations "
            f"{arm['violations']:>3}  {per_success}")


def main() -> int:
    load_dotenv()
    if not RUNS.exists():
        print("error: run scripts/run_live_cost.py first", file=sys.stderr)
        return 2
    try:
        assumptions = Assumptions.from_env()
    except MissingAssumptionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    recorded = json.loads(RUNS.read_text())
    report = build_report(recorded["rows"], assumptions, recorded["model"])
    OUT.write_text(json.dumps(report, indent=2))
    print(f"{report['model']}: {report['runs_per_arm']} runs per arm")
    print(_line("direct", report["direct"]))
    print(_line("harnessed", report["harnessed"]))
    print(f"  breakeven remediation per violation: {report['breakeven_remediation_usd']}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
