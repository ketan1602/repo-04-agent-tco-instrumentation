from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field


class ContractInput(BaseModel):
    contract_id: str
    vendor_name: str
    contract_type: str  # service | supply | nda
    page_count: int
    text_sample: str  # first 2000 chars of contract (simulated)


class RiskSummary(BaseModel):
    contract_id: str
    overall_risk: str  # high | medium | low | acceptable
    flag_count: int = Field(ge=0)
    requires_legal_review: bool
    summary: str
    estimated_review_minutes: int = Field(ge=0)


class AgentState(TypedDict):
    contract_id: str
    vendor_name: str
    contract_type: str
    page_count: int
    text_sample: str
    clause_flags: list[str] | None
    risk_factors: list[str] | None
    overall_risk: str | None
    flag_count: int | None
    requires_legal_review: bool | None
    summary: str | None
    estimated_review_minutes: int | None
    errors: list[str]
    run_id: str
