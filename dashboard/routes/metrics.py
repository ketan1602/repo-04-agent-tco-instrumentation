from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from dashboard.charts import stat_card
from dashboard.charts_tco import pie_chart, trend_line

router = APIRouter()

_MEASUREMENTS = Path("measurements/tco_results.json")


@router.get("/metrics")
async def metrics_page():
    return FileResponse("dashboard/static/metrics.html")


@router.get("/api/metrics")
async def metrics_data():
    if not _MEASUREMENTS.exists():
        return JSONResponse({
            "no_data": True,
            "seed_command": "python scripts/run_tco_simulation.py",
        })

    with open(_MEASUREMENTS) as f:  # noqa: ASYNC230
        data = json.load(f)

    token_pct = data.get("token_cost_pct", 0)
    slices = [
        ("Tokens", data.get("token_cost_usd", 0)),
        ("Human Review", data.get("review_cost_usd", 0)),
        ("Eval", data.get("eval_cost_usd", 0)),
        ("Incidents", data.get("incident_cost_usd", 0)),
        ("Retries", data.get("retry_cost_usd", 0)),
    ]
    tco_pie = pie_chart([(l, v) for l, v in slices if v > 0], "TCO Breakdown (100 runs)")

    run_totals = data.get("run_totals", [])
    cost_trend = trend_line(run_totals, "Per-Run Cost Trend") if run_totals else ""

    token_stat = stat_card(
        value=f"{token_pct:.0f}%",
        label="Tokens as % of TCO",
        sublabel="the number that surprises everyone",
        color="#6366f1",
    )
    review_stat = stat_card(
        value=f"${data.get('review_cost_usd', 0):.2f}",
        label="Human review cost",
        sublabel="100 runs total",
        color="#f59e0b",
    )

    return JSONResponse({
        "no_data": False,
        "data": data,
        "charts": {
            "tco_pie": tco_pie,
            "cost_trend": cost_trend,
            "token_stat": token_stat,
            "review_stat": review_stat,
        },
        "key_finding": (
            f"Tokens represent {token_pct:.0f}% of true agent TCO. "
            "Human review alone costs more than the model."
        ),
    })
