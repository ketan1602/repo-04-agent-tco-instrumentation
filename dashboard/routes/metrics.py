from __future__ import annotations

import json
import math

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from dashboard import paths
from dashboard.charts import breakdown_chart

router = APIRouter()
SEED_COMMANDS = ["python scripts/run_live_cost.py --repeats 3", "python scripts/build_cost_report.py"]


def _finite(value):
    """JSON cannot carry Infinity or NaN; an unbounded cost per success becomes null."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _finite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_finite(v) for v in value]
    return value


def _charts(report: dict) -> dict:
    return {arm: breakdown_chart(f"{arm} cost per component (USD, share of total)",
                                 report[arm]["breakdown_usd"], report[arm]["share_pct"])
            for arm in ("direct", "harnessed")}


@router.get("/metrics")
async def metrics_page():
    return FileResponse(paths.STATIC / "metrics.html")


@router.get("/api/metrics")
async def metrics_data():
    if not paths.COST_RESULTS.exists():
        return JSONResponse({"no_data": True, "seed_commands": SEED_COMMANDS})
    report = _finite(json.loads(paths.COST_RESULTS.read_text()))
    return JSONResponse({**report, "no_data": False, "charts": _charts(report)})
