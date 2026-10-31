#!/usr/bin/env python3
"""Run the support scenario on both paths with a live model and record what each run measured.

Needs LLM_API_KEY and LLM_BASE_URL. Writes measurements/cost_runs.json (raw measured rows).
Price it afterwards, with no model calls, using scripts/build_cost_report.py.
    python scripts/run_live_cost.py --category unauthorized_tool      # smoke test
    python scripts/run_live_cost.py --repeats 3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from economics.runs import compact
from scenario.cases import load_cases, run_case
from scenario.llm import config_error, model_id

OUT = ROOT / "measurements" / "cost_runs.json"


async def collect(cases: list[dict], repeats: int, model_name: str) -> list[dict]:
    rows = []
    for case in cases:
        for n in range(repeats):
            rows.append(compact(await run_case(case, model_name=model_name)))
            print(f"  {case['id']} run {n + 1}/{repeats} done", flush=True)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=None)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--category", default=None)
    args = parser.parse_args()
    load_dotenv()
    if error := config_error():
        print(f"error: {error}", file=sys.stderr)
        return 2
    cases = [c for c in load_cases() if args.category in (None, c["category"])]
    if not cases:
        print(f"error: no case in category {args.category!r}", file=sys.stderr)
        return 2
    name = model_id(args.model)
    print(f"{len(cases)} cases x {args.repeats} repeats on {name}")
    rows = asyncio.run(collect(cases, args.repeats, name))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"model": name, "repeats": args.repeats, "generated_at":
                               datetime.now(UTC).isoformat(timespec="seconds"), "rows": rows},
                              indent=2))
    print(f"wrote {len(rows)} runs to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
