"""
Bridge: converts a RunCost produced by the harness into a fully-attributed
AgentCostEvent suitable for cost attribution and OutcomeEconomics aggregation.

RunCost carries five measured cost buckets populated from real LLM runs.
AgentCostEvent adds attribution metadata (owner, cost_center, workflow) and
platform overhead costs sourced from environment variables.

Platform overhead (runtime, observability, control) defaults to zero so the
adapter works without any configuration — set the env vars to allocate a per-run
share of shared platform costs to each run.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from cost_model.tco_aggregator import RunCost
from economics.model import AgentCostEvent


@dataclass(frozen=True)
class RunMeta:
    """Attribution metadata for one agent run."""
    run_id: str
    agent_id: str
    workflow: str
    owner: str
    cost_center: str
    successful: bool


@dataclass(frozen=True)
class PlatformCosts:
    """Per-run share of shared platform costs. Zero by default; set via env vars."""
    runtime_per_run: float = 0.0
    observability_per_run: float = 0.0
    control_per_run: float = 0.0

    @classmethod
    def from_env(cls) -> "PlatformCosts":
        def _get(key: str) -> float:
            return float(os.environ.get(key, "0"))

        return cls(
            runtime_per_run=_get("PLATFORM_RUNTIME_COST_PER_RUN"),
            observability_per_run=_get("PLATFORM_OBSERVABILITY_COST_PER_RUN"),
            control_per_run=_get("PLATFORM_CONTROL_COST_PER_RUN"),
        )


def to_cost_event(
    meta: RunMeta,
    run_cost: RunCost,
    platform: PlatformCosts | None = None,
) -> AgentCostEvent:
    """Convert a harness RunCost + run metadata into a fully-attributed AgentCostEvent.

    token_cost_usd      → model     (actual token cost from AI Refinery via harness)
    review_cost_usd     → human_review (time-based, driven by agent's RiskSummary output)
    eval_cost_usd       → evaluation
    incident + retry    → remediation (failure recovery cost)
    platform.*          → runtime / observability / control (shared platform allocation)
    tools/knowledge_memory remain 0 — this agent has no tool calls or vector DB.
    """
    p = platform or PlatformCosts()
    return AgentCostEvent(
        run_id=meta.run_id,
        agent_id=meta.agent_id,
        workflow=meta.workflow,
        owner=meta.owner,
        cost_center=meta.cost_center,
        successful=meta.successful,
        model=run_cost.token_cost_usd,
        human_review=run_cost.review_cost_usd,
        evaluation=run_cost.eval_cost_usd,
        remediation=run_cost.incident_cost_usd + run_cost.retry_cost_usd,
        runtime=p.runtime_per_run,
        observability=p.observability_per_run,
        control=p.control_per_run,
    )
