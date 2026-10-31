"""
Cost attribution model for agent runs.

AgentCostEvent carries the full, owner-attributed cost breakdown for one run.
OutcomeEconomics aggregates over many runs to produce cost-per-success.
HarnessInvestment models platform amortization across agent count.
FailureScenario computes actuarial expected failure cost.

This module is intentionally free of I/O and framework dependencies so it
can be unit-tested without any infrastructure.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentCostEvent:
    run_id: str
    agent_id: str
    workflow: str
    owner: str
    cost_center: str
    successful: bool
    model: float = 0.0
    tools: float = 0.0
    knowledge_memory: float = 0.0
    runtime: float = 0.0
    observability: float = 0.0
    evaluation: float = 0.0
    human_review: float = 0.0
    control: float = 0.0
    remediation: float = 0.0

    @property
    def cost(self) -> float:
        values = (
            self.model, self.tools, self.knowledge_memory,
            self.runtime, self.observability, self.evaluation,
            self.human_review, self.control, self.remediation,
        )
        if any(v < 0 for v in values):
            raise ValueError("Costs must be nonnegative")
        return sum(values)


@dataclass(frozen=True)
class OutcomeEconomics:
    runs: int
    successes: int
    total_cost: float

    @property
    def cost_per_run(self) -> float:
        return self.total_cost / self.runs if self.runs else float("inf")

    @property
    def cost_per_success(self) -> float:
        return self.total_cost / self.successes if self.successes else float("inf")


def summarize(
    events: Iterable[AgentCostEvent],
    fixed_allocation: float = 0.0,
    expected_residual_loss: float = 0.0,
) -> OutcomeEconomics:
    rows = list(events)
    if fixed_allocation < 0 or expected_residual_loss < 0:
        raise ValueError("Allocations must be nonnegative")
    return OutcomeEconomics(
        len(rows),
        sum(e.successful for e in rows),
        sum(e.cost for e in rows) + fixed_allocation + expected_residual_loss,
    )


@dataclass(frozen=True)
class HarnessInvestment:
    initial_build: float
    annual_operations: float
    integration_per_agent: float

    def cost_per_agent(self, agents: int) -> float:
        if agents <= 0:
            raise ValueError("agents must be positive")
        return (
            self.initial_build + self.annual_operations + self.integration_per_agent * agents
        ) / agents


@dataclass(frozen=True)
class FailureScenario:
    probability_per_transaction: float
    impact_per_event: float
    transactions: int
    recovery_multiplier: float = 1.0

    @property
    def expected_cost(self) -> float:
        if (
            not 0 <= self.probability_per_transaction <= 1
            or min(self.impact_per_event, self.transactions, self.recovery_multiplier) < 0
        ):
            raise ValueError("Invalid failure scenario")
        return (
            self.probability_per_transaction
            * self.impact_per_event
            * self.transactions
            * self.recovery_multiplier
        )
