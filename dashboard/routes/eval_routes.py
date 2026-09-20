from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()

_FIXTURES = Path("eval/fixtures/contracts.json")


@router.get("/eval")
async def eval_page():
    return FileResponse("dashboard/static/eval.html")


@router.get("/api/eval/fixtures")
async def eval_fixtures():
    if not _FIXTURES.exists():
        return JSONResponse([])
    with open(_FIXTURES) as f:  # noqa: ASYNC230
        return JSONResponse(json.load(f))


@router.get("/api/eval/summary")
async def eval_summary():
    if not _FIXTURES.exists():
        return JSONResponse({"error": "No fixtures found", "fixture_count": 0})
    with open(_FIXTURES) as f:  # noqa: ASYNC230
        fixtures = json.load(f)
    risk_dist: dict[str, int] = {}
    for item in fixtures:
        expected = item.get("expected_risk", "unknown")
        risk_dist[expected] = risk_dist.get(expected, 0) + 1
    return JSONResponse({
        "fixture_count": len(fixtures),
        "risk_distribution": risk_dist,
        "pass_threshold": 0.80,
        "eval_command": "pytest tests/ -v",
    })
