"""Bridge: one measured scenario run on one path becomes an attributed AgentCostEvent.

Measured: tokens, whether a violation happened, whether the harness escalated to a human.
Assumed: every price, the approver's time, the remediation cost (see economics/assumptions.py).
`tools`, `knowledge_memory` and `evaluation` stay 0: the tools are simulated, and the harness's
own Evaluation capability runs in-process with no marginal cost.
"""
from __future__ import annotations

from dataclasses import dataclass

from economics.assumptions import Assumptions
from economics.model import AgentCostEvent

DIRECT, HARNESSED = "direct", "harnessed"


@dataclass(frozen=True)
class RunMeta:
    run_id: str
    agent_id: str
    workflow: str
    owner: str


def succeeded(arm: str, row: dict) -> bool:
    """Direct: nothing harmful happened and the run did not crash. Harnessed: the Evaluation
    capability passed the expectation and nothing harmful happened."""
    if arm == DIRECT:
        return not row["violated"] and not row["status"].startswith("raised:")
    return bool(row["passed"]) and not row["violated"]


def to_cost_event(meta: RunMeta, arm: str, row: dict, a: Assumptions) -> AgentCostEvent:
    harnessed = arm == HARNESSED
    return AgentCostEvent(
        run_id=meta.run_id, agent_id=meta.agent_id, workflow=meta.workflow,
        owner=meta.owner, cost_center=a.cost_center, successful=succeeded(arm, row),
        model=row["tokens"] / 1000.0 * a.token_price_per_1k,
        human_review=a.approval_cost if harnessed and row["escalated"] else 0.0,
        remediation=a.remediation_per_violation if row["violated"] else 0.0,
        runtime=a.platform.runtime_per_run,
        observability=a.platform.observability_per_run if harnessed else 0.0,
        control=a.platform.control_per_run if harnessed else 0.0,
    )
