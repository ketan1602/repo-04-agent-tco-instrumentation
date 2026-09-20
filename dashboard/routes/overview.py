from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()


@router.get("/")
async def overview_page():
    return FileResponse("dashboard/static/index.html")


@router.get("/api/overview")
async def overview_data():
    return JSONResponse({
        "article_number": "04",
        "article_title": "Beyond the Model: Agent TCO Instrumentation",
        "central_claim": (
            "Token cost is a minority of true agent TCO. "
            "Human review, incident remediation, and eval infrastructure dominate."
        ),
        "key_finding": (
            "Tokens represent X% of true agent TCO. "
            "Human review alone costs more than the model."
        ),
        "use_case": "Legal Contract Review — risk classification, clause flagging, reviewer routing",
        "repo_name": "repo-04-agent-tco-instrumentation",
        "series_position": "Article 04 — Full TCO breakdown across 100 production runs",
        "next_repo": "repo-05-agent-control-plane-mvp",
    })
