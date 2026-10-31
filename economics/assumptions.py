"""Every cost input that is not measured. Each one comes from the environment, none has a default."""
from __future__ import annotations

import os
from dataclasses import dataclass


class MissingAssumptionError(RuntimeError):
    """Raised when a cost assumption is not set, so a report is never built on a silent zero."""


def _number(name: str) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        raise MissingAssumptionError(f"{name} must be set (see .env.example)")
    value = float(raw)
    if value < 0:
        raise MissingAssumptionError(f"{name} must not be negative")
    return value


@dataclass(frozen=True)
class PlatformCosts:
    """Per-run share of shared platform cost. Observability and control exist only because of the harness."""

    runtime_per_run: float
    observability_per_run: float
    control_per_run: float

    @classmethod
    def from_env(cls) -> PlatformCosts:
        return cls(_number("PLATFORM_RUNTIME_COST_PER_RUN"),
                   _number("PLATFORM_OBSERVABILITY_COST_PER_RUN"),
                   _number("PLATFORM_CONTROL_COST_PER_RUN"))


@dataclass(frozen=True)
class Assumptions:
    token_price_per_1k: float
    approval_minutes: float
    reviewer_rate_per_hour: float
    remediation_per_violation: float
    cost_center: str
    platform: PlatformCosts

    @property
    def approval_cost(self) -> float:
        return self.approval_minutes / 60.0 * self.reviewer_rate_per_hour

    @classmethod
    def from_env(cls) -> Assumptions:
        center = os.environ.get("COST_CENTER", "").strip()
        if not center:
            raise MissingAssumptionError("COST_CENTER must be set (see .env.example)")
        return cls(_number("LLM_COST_PER_1K_TOKENS"), _number("HUMAN_APPROVAL_MINUTES"),
                   _number("HUMAN_REVIEW_RATE_PER_HOUR"), _number("VIOLATION_REMEDIATION_COST_USD"),
                   center, PlatformCosts.from_env())
