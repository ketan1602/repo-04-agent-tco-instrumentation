from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.graph import build_harness

_FIXTURES_PATH = Path("eval/fixtures/contracts.json")
_PASS_THRESHOLD = 0.80


def load_fixtures() -> list[dict]:
    if not _FIXTURES_PATH.exists():
        return []
    with open(_FIXTURES_PATH) as f:
        return json.load(f)


def _risk_matches(actual: str, expected: str) -> bool:
    return actual.lower() == expected.lower()


async def run_single(fixture: dict[str, Any]) -> dict:
    harness = build_harness()
    result = await harness.run({
        "contract_id": fixture["contract_id"],
        "vendor_name": fixture["vendor_name"],
        "contract_type": fixture["contract_type"],
        "page_count": fixture["page_count"],
        "text_sample": fixture["text_sample"],
    })
    if not result.success:
        return {"passed": False, "fixture_id": fixture["contract_id"], "error": result.error}

    actual_risk = result.output.overall_risk if result.output else "unknown"
    passed = _risk_matches(actual_risk, fixture.get("expected_risk", ""))
    return {
        "passed": passed,
        "fixture_id": fixture["contract_id"],
        "expected_risk": fixture.get("expected_risk"),
        "actual_risk": actual_risk,
        "flag_count": result.output.flag_count if result.output else 0,
    }


async def run_all() -> dict:
    fixtures = load_fixtures()
    if not fixtures:
        return {"error": "No fixtures found", "pass_rate": 0.0, "results": []}

    results = []
    for fixture in fixtures:
        result = await run_single(fixture)
        results.append(result)

    passed = sum(1 for r in results if r.get("passed"))
    pass_rate = passed / len(results) if results else 0.0
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate": pass_rate,
        "above_threshold": pass_rate >= _PASS_THRESHOLD,
        "results": results,
    }
