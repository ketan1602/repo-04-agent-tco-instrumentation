from __future__ import annotations

import random
from dataclasses import dataclass

_HOURLY_RATE_USD = 85.0
_BASE_REVIEW_MINUTES: dict[str, float] = {
    "high": 45.0,
    "medium": 25.0,
    "low": 12.0,
    "acceptable": 5.0,
}
_JITTER_FACTOR = 0.25
_FLAG_OVERHEAD_MINUTES = 3.0


@dataclass
class ReviewResult:
    time_minutes: float
    cost_usd: float
    reviewer_tier: str


class ReviewQueueSimulator:
    """Simulates human contract review time and cost with realistic variance."""

    def __init__(
        self,
        hourly_rate_usd: float = _HOURLY_RATE_USD,
        seed: int | None = None,
    ) -> None:
        self._rate = hourly_rate_usd
        self._rng = random.Random(seed)

    def simulate(self, overall_risk: str, flag_count: int) -> ReviewResult:
        base = _BASE_REVIEW_MINUTES.get(overall_risk, 15.0)
        jitter = base * _JITTER_FACTOR * (self._rng.random() * 2 - 1)
        flag_overhead = flag_count * _FLAG_OVERHEAD_MINUTES
        minutes = max(2.0, base + jitter + flag_overhead)
        cost_usd = (minutes / 60.0) * self._rate
        tier = "senior" if overall_risk in ("high", "medium") else "junior"
        return ReviewResult(
            time_minutes=round(minutes, 1),
            cost_usd=round(cost_usd, 4),
            reviewer_tier=tier,
        )
