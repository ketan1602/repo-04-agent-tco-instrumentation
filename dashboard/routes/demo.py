from __future__ import annotations

import json
import uuid

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from dashboard import paths
from economics import (
    DIRECT,
    HARNESSED,
    Assumptions,
    MissingAssumptionError,
    RunMeta,
    succeeded,
    to_cost_event,
)
from economics.report import COMPONENTS
from economics.runs import compact
from scenario.cases import run_case
from scenario.llm import config_error

router = APIRouter()


class RunBody(BaseModel):
    case_id: str


def _cost(arm: str, row: dict, assumptions: Assumptions, run_id: str) -> dict:
    meta = RunMeta(f"{arm}-{run_id}", "support-agent", "support", "customer-platform")
    event = to_cost_event(meta, arm, row, assumptions)
    return {"status": row["status"], "tokens": row["tokens"], "violated": row["violated"],
            "success": succeeded(arm, row),
            "cost_usd": {c: getattr(event, c) for c in COMPONENTS}, "total_usd": event.cost}


def _unavailable(message: str) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=503)


@router.get("/demo")
async def demo_page():
    return FileResponse(paths.STATIC / "demo.html")


@router.get("/api/demo/cases")
async def demo_cases():
    cases = json.loads(paths.CASES.read_text())
    return JSONResponse([{"id": c["id"], "category": c["category"], "utterance": c["utterance"]}
                         for c in cases])


@router.post("/api/demo/run")
async def demo_run(body: RunBody):
    case = next((c for c in json.loads(paths.CASES.read_text()) if c["id"] == body.case_id), None)
    if case is None:
        return JSONResponse({"error": f"unknown case_id: {body.case_id}"}, status_code=404)
    if error := config_error():
        return _unavailable(error)
    try:
        assumptions = Assumptions.from_env()
    except MissingAssumptionError as exc:
        return _unavailable(str(exc))
    row = compact(await run_case(case))
    run_id = uuid.uuid4().hex[:8]
    harnessed = {**_cost(HARNESSED, row[HARNESSED], assumptions, run_id),
                 **{k: row[HARNESSED][k] for k in ("vetoed", "escalated", "retried")}}
    return JSONResponse({"case": case["id"], "category": case["category"],
                         DIRECT: _cost(DIRECT, row[DIRECT], assumptions, run_id),
                         HARNESSED: harnessed})
