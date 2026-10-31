from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunCost:
    run_id: str
    token_cost_usd: float
    review_cost_usd: float
    eval_cost_usd: float
    incident_cost_usd: float
    retry_cost_usd: float

    @property
    def total(self) -> float:
        return (
            self.token_cost_usd
            + self.review_cost_usd
            + self.eval_cost_usd
            + self.incident_cost_usd
            + self.retry_cost_usd
        )


class TCOAggregator:
    """Accumulates per-run costs across all five TCO categories."""

    def __init__(self) -> None:
        self._runs: list[RunCost] = []

    def add(self, run: RunCost) -> None:
        self._runs.append(run)

    def run_totals(self) -> list[float]:
        return [r.total for r in self._runs]

    def summary(self) -> dict:
        if not self._runs:
            return self._zero_summary()

        total = sum(r.total for r in self._runs)
        token = sum(r.token_cost_usd for r in self._runs)
        review = sum(r.review_cost_usd for r in self._runs)
        eval_ = sum(r.eval_cost_usd for r in self._runs)
        incident = sum(r.incident_cost_usd for r in self._runs)
        retry = sum(r.retry_cost_usd for r in self._runs)

        def pct(v: float) -> float:
            return round(v / total * 100, 3) if total > 0 else 0.0

        return {
            "total_runs": len(self._runs),
            "token_cost_usd": round(token, 4),
            "review_cost_usd": round(review, 4),
            "eval_cost_usd": round(eval_, 4),
            "incident_cost_usd": round(incident, 4),
            "retry_cost_usd": round(retry, 4),
            "total_cost_usd": round(total, 4),
            "token_cost_pct": pct(token),
            "review_cost_pct": pct(review),
            "eval_cost_pct": pct(eval_),
            "incident_cost_pct": pct(incident),
            "retry_cost_pct": pct(retry),
            "avg_cost_per_run_usd": round(total / len(self._runs), 4),
        }

    @staticmethod
    def _zero_summary() -> dict:
        keys = [
            "total_runs", "token_cost_usd", "review_cost_usd", "eval_cost_usd",
            "incident_cost_usd", "retry_cost_usd", "total_cost_usd",
            "token_cost_pct", "review_cost_pct", "eval_cost_pct",
            "incident_cost_pct", "retry_cost_pct", "avg_cost_per_run_usd",
        ]
        return dict.fromkeys(keys, 0)
