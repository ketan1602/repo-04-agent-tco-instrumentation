from __future__ import annotations

import json

from agent.llm import complete
from agent.prompts import (
    ANALYSE_SYSTEM_PROMPT,
    ANALYSE_USER_TEMPLATE,
    ASSESS_SYSTEM_PROMPT,
    ASSESS_USER_TEMPLATE,
)
from agent.schemas import AgentState


async def analyse_contract_node(state: AgentState) -> dict:
    """Send the contract excerpt to the LLM; extract clause flags and risk factors."""
    user_msg = ANALYSE_USER_TEMPLATE.format(
        vendor_name=state["vendor_name"],
        contract_type=state["contract_type"],
        page_count=state["page_count"],
        text_sample=state["text_sample"],
    )
    content = await complete(ANALYSE_SYSTEM_PROMPT, user_msg)
    data = json.loads(content.strip())
    return {
        "clause_flags": data.get("clause_flags", []),
        "risk_factors": data.get("risk_factors", []),
        "errors": state.get("errors", []),
    }


async def assess_risk_node(state: AgentState) -> dict:
    """Aggregate clause analysis into an overall risk assessment."""
    flags = state.get("clause_flags") or []
    factors = state.get("risk_factors") or []
    user_msg = ASSESS_USER_TEMPLATE.format(
        contract_id=state["contract_id"],
        contract_type=state["contract_type"],
        vendor_name=state["vendor_name"],
        page_count=state["page_count"],
        clause_flags="\n".join(f"- {f}" for f in flags) or "None identified",
        risk_factors="\n".join(f"- {f}" for f in factors) or "None identified",
    )
    content = await complete(ASSESS_SYSTEM_PROMPT, user_msg)
    data = json.loads(content.strip())
    return {
        "overall_risk": data["overall_risk"],
        "requires_legal_review": bool(data["requires_legal_review"]),
        "summary": data["summary"],
        "estimated_review_minutes": int(data["estimated_review_minutes"]),
        "flag_count": len(flags),
    }
