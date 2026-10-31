from __future__ import annotations

import pytest

from economics import DIRECT, HARNESSED
from economics.runs import compact
from scenario.cases import load_cases, run_case


async def test_every_case_records_measured_tokens_on_both_paths(fake_llm):
    fake_llm.total_tokens = 250
    for case in load_cases():
        row = compact(await run_case(case))
        assert row[DIRECT]["tokens"] in (0, 250, 500), case["id"]
        assert row[HARNESSED]["tokens"] in (0, 250, 500), case["id"]


async def test_a_replayed_decision_is_costed_on_the_tokens_it_cost(fake_llm):
    fake_llm.total_tokens = 300
    case = next(c for c in load_cases() if c["id"] == "unauthorized_tool-1")
    result = await run_case(case)
    assert result["paired"]
    assert result["direct"]["tokens"] == result["harnessed"]["tokens"] == 300
    assert len(fake_llm.calls) == 1


async def test_the_harness_stops_what_the_direct_path_does(fake_llm):
    case = next(c for c in load_cases() if c["id"] == "unauthorized_tool-1")
    row = compact(await run_case(case))
    assert row[DIRECT]["violated"] and not row[HARNESSED]["violated"]
    assert row[HARNESSED]["vetoed"] and row[HARNESSED]["passed"]


async def test_a_paused_refund_is_an_escalation(fake_llm):
    case = next(c for c in load_cases() if c["id"] == "refund_pending-1")
    row = compact(await run_case(case))
    assert row[HARNESSED]["escalated"]


async def test_a_transient_failure_crashes_the_direct_path_and_the_harness_retries(fake_llm):
    case = next(c for c in load_cases() if c["id"] == "transient_failure-1")
    row = compact(await run_case(case))
    assert row[DIRECT]["status"].startswith("raised:")
    assert row[HARNESSED]["retried"] and row[HARNESSED]["passed"]


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
async def test_the_harness_never_violates_on_any_case(fake_llm, case):
    assert not compact(await run_case(case))[HARNESSED]["violated"]
