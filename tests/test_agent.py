"""Tests for agent schemas, nodes, and graph — all LLM calls mocked."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agent.graph import build_harness
from agent.schemas import AgentState, ContractInput, RiskSummary


def test_contract_input_schema_valid():
    contract = ContractInput(
        contract_id="CTR-001",
        vendor_name="Acme Corp",
        contract_type="service",
        page_count=24,
        text_sample="Sample contract text for testing purposes.",
    )
    assert contract.contract_id == "CTR-001"
    assert contract.page_count == 24


def test_risk_summary_schema_valid():
    summary = RiskSummary(
        contract_id="CTR-001",
        overall_risk="high",
        flag_count=3,
        requires_legal_review=True,
        summary="Multiple high-risk clauses identified.",
        estimated_review_minutes=45,
    )
    assert summary.overall_risk == "high"
    assert summary.requires_legal_review is True


def test_risk_summary_flag_count_non_negative():
    with pytest.raises(ValueError):
        RiskSummary(
            contract_id="CTR-001",
            overall_risk="low",
            flag_count=-1,
            requires_legal_review=False,
            summary="Clean contract.",
            estimated_review_minutes=5,
        )


def test_build_harness_returns_harness():
    harness = build_harness()
    assert harness is not None
    assert harness.run_count == 0


@pytest.mark.asyncio
async def test_analyse_contract_node_parses_llm_response():
    from agent.nodes import analyse_contract_node

    mock_content = '{"clause_flags": ["auto-renewal", "fee-increase"], "risk_factors": ["180-day notice", "15% annual"]}'

    state: AgentState = {
        "contract_id": "CTR-001",
        "vendor_name": "Acme Corp",
        "contract_type": "service",
        "page_count": 24,
        "text_sample": "Auto-renewal with 180-day notice. Fees may increase 15% annually.",
        "clause_flags": None,
        "risk_factors": None,
        "overall_risk": None,
        "flag_count": None,
        "requires_legal_review": None,
        "summary": None,
        "estimated_review_minutes": None,
        "errors": [],
        "run_id": "test-run",
    }

    with patch("agent.nodes.complete", AsyncMock(return_value=mock_content)):
        result = await analyse_contract_node(state)

    assert result["clause_flags"] == ["auto-renewal", "fee-increase"]
    assert len(result["risk_factors"]) == 2


@pytest.mark.asyncio
async def test_assess_risk_node_parses_llm_response():
    from agent.nodes import assess_risk_node

    mock_content = (
        '{"overall_risk": "high", "requires_legal_review": true, '
        '"summary": "High-risk contract with multiple concerning clauses.", '
        '"estimated_review_minutes": 45}'
    )

    state: AgentState = {
        "contract_id": "CTR-001",
        "vendor_name": "Acme Corp",
        "contract_type": "service",
        "page_count": 24,
        "text_sample": "Sample text.",
        "clause_flags": ["auto-renewal", "fee-increase"],
        "risk_factors": ["180-day notice required", "15% uncapped increase"],
        "overall_risk": None,
        "flag_count": None,
        "requires_legal_review": None,
        "summary": None,
        "estimated_review_minutes": None,
        "errors": [],
        "run_id": "test-run",
    }

    with patch("agent.nodes.complete", AsyncMock(return_value=mock_content)):
        result = await assess_risk_node(state)

    assert result["overall_risk"] == "high"
    assert result["requires_legal_review"] is True
    assert result["flag_count"] == 2
    assert result["estimated_review_minutes"] == 45
