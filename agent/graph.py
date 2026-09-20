from __future__ import annotations

from harness_core import AgentHarness, load_config
from langgraph.graph import END, StateGraph

from agent.nodes import analyse_contract_node, assess_risk_node
from agent.schemas import AgentState, ContractInput, RiskSummary


def _build_graph():
    """Assemble the contract review LangGraph: analyse -> assess -> END."""
    graph = StateGraph(AgentState)
    graph.add_node("analyse_contract", analyse_contract_node)
    graph.add_node("assess_risk", assess_risk_node)
    graph.set_entry_point("analyse_contract")
    graph.add_edge("analyse_contract", "assess_risk")
    graph.add_edge("assess_risk", END)
    return graph.compile()


def build_harness() -> AgentHarness:
    """Return a fully configured AgentHarness wrapping the contract review graph."""
    config = load_config("config/harness.yaml")
    return AgentHarness(
        graph=_build_graph(),
        agent_name="legal-contract-review-agent",
        agent_version="1.0.0",
        input_schema=ContractInput,
        output_schema=RiskSummary,
        config=config,
    )
