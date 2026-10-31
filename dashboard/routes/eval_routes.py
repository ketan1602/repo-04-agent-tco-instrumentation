from __future__ import annotations

import json
from collections import Counter

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from dashboard import paths
from scenario.cases import expected_label

router = APIRouter()


@router.get("/eval")
async def eval_page():
    return FileResponse(paths.STATIC / "eval.html")


@router.get("/api/eval/cases")
async def eval_cases():
    cases = json.loads(paths.CASES.read_text())
    rows = [{"id": c["id"], "category": c["category"], "control": c["control"],
             "expected": expected_label(c), "violation": c["violation"]} for c in cases]
    return JSONResponse({"cases": rows, "categories": dict(Counter(c["category"] for c in cases))})
