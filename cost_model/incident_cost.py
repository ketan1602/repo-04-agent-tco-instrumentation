from __future__ import annotations

from dataclasses import dataclass

_DETECTION_COST_USD = 120.0
_REMEDIATION_COST_USD = 850.0


@dataclass
class IncidentRecord:
    run_id: str
    detection_cost_usd: float
    remediation_cost_usd: float
    total_cost_usd: float


class IncidentCostTracker:
    """Tracks failures that escape detection and reach downstream remediation."""

    def __init__(self) -> None:
        self._incidents: list[IncidentRecord] = []

    def maybe_record(self, run_id: str, is_incident: bool) -> IncidentRecord | None:
        if not is_incident:
            return None
        record = IncidentRecord(
            run_id=run_id,
            detection_cost_usd=_DETECTION_COST_USD,
            remediation_cost_usd=_REMEDIATION_COST_USD,
            total_cost_usd=_DETECTION_COST_USD + _REMEDIATION_COST_USD,
        )
        self._incidents.append(record)
        return record

    def total_cost_usd(self) -> float:
        return sum(r.total_cost_usd for r in self._incidents)

    def incident_count(self) -> int:
        return len(self._incidents)

    def records(self) -> list[IncidentRecord]:
        return list(self._incidents)
