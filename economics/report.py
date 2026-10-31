"""Cost per successful run, direct versus harnessed, from measured scenario runs."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, replace

from economics.adapter import DIRECT, HARNESSED, RunMeta, to_cost_event
from economics.assumptions import Assumptions
from economics.model import AgentCostEvent, summarize

AGENT_ID, WORKFLOW, OWNER = "support-agent", "support", "customer-platform"
SWEEP_REMEDIATION_USD = (0.0, 50.0, 250.0, 1000.0, 5000.0)
COMPONENTS = ("model", "runtime", "observability", "control", "human_review", "remediation")
LIMITS = [
    "Tokens are measured from the model's usage field. Every other price is an assumption.",
    ("Twelve of the sixteen cases were authored to provoke a violation, so violations per run here "
     "are a property of the suite, not a production rate. Read the remediation sweep and the "
     "breakeven, not the absolute totals."),
    ("Downstream cases replay the decision the model made on the direct path, so both paths are "
     "costed on the same measured tokens."),
    "Tools are simulated, so the tools and knowledge_memory cost categories are 0 in this scenario.",
    "Human review is the approver's time on runs the harness escalated; the direct path has none.",
]


def _events(rows: list[dict], arm: str, a: Assumptions) -> list[AgentCostEvent]:
    return [to_cost_event(RunMeta(f"{arm}-{i}", AGENT_ID, WORKFLOW, OWNER), arm, r[arm], a)
            for i, r in enumerate(rows)]


def _arm(rows: list[dict], arm: str, a: Assumptions) -> dict:
    events = _events(rows, arm, a)
    outcome = summarize(events)
    parts = {c: round(sum(getattr(e, c) for e in events), 6) for c in COMPONENTS}
    out = {"runs": outcome.runs, "successes": outcome.successes,
           "violations": sum(r[arm]["violated"] for r in rows),
           "tokens": sum(r[arm]["tokens"] for r in rows),
           "total_cost_usd": round(outcome.total_cost, 6),
           "cost_per_run_usd": round(outcome.cost_per_run, 6),
           "cost_per_success_usd": round(outcome.cost_per_success, 6) if outcome.successes else None,
           "breakdown_usd": parts,
           "share_pct": {c: round(100 * v / outcome.total_cost, 3) if outcome.total_cost else 0.0
                         for c, v in parts.items()}}
    if arm == HARNESSED:
        out.update({k: sum(r[arm][k] for r in rows) for k in ("vetoed", "escalated", "retried")})
    return out


def breakeven(rows: list[dict], a: Assumptions) -> float | None:
    """Remediation cost per violation above which the harnessed path costs less per success.
    0.0: cheaper at any remediation cost. None: never cheaper."""
    d, h = _arm(rows, DIRECT, a), _arm(rows, HARNESSED, a)
    r = a.remediation_per_violation
    base_d, base_h = d["total_cost_usd"] - d["violations"] * r, h["total_cost_usd"] - h["violations"] * r
    if not h["successes"]:
        return None
    if not d["successes"]:
        return 0.0
    num = base_h * d["successes"] - base_d * h["successes"]
    den = d["violations"] * h["successes"] - h["violations"] * d["successes"]
    if den <= 0:
        return 0.0 if num <= 0 else None
    return round(max(0.0, num / den), 2)


def _sweep(rows: list[dict], a: Assumptions) -> list[dict]:
    out = []
    for value in SWEEP_REMEDIATION_USD:
        point = replace(a, remediation_per_violation=value)
        out.append({"remediation_per_violation_usd": value,
                    "direct_cost_per_success_usd": _arm(rows, DIRECT, point)["cost_per_success_usd"],
                    "harnessed_cost_per_success_usd":
                        _arm(rows, HARNESSED, point)["cost_per_success_usd"]})
    return out


def _by_category(rows: list[dict]) -> dict:
    cats: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        c = cats[r["category"]]
        c["runs"] += 1
        c["direct_violated"] += r[DIRECT]["violated"]
        c["harnessed_violated"] += r[HARNESSED]["violated"]
        c["escalated"] += r[HARNESSED]["escalated"]
        c["retried"] += r[HARNESSED]["retried"]
    return {k: dict(v) for k, v in cats.items()}


def build_report(rows: list[dict], a: Assumptions, model: str) -> dict:
    return {"model": model, "runs_per_arm": len(rows),
            "assumptions": {**asdict(a), "approval_cost_usd": a.approval_cost},
            DIRECT: _arm(rows, DIRECT, a), HARNESSED: _arm(rows, HARNESSED, a),
            "breakeven_remediation_usd": breakeven(rows, a),
            "remediation_sweep": _sweep(rows, a), "by_category": _by_category(rows),
            "limits": LIMITS}
