from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from dashboard import paths

router = APIRouter()


@router.get("/")
async def overview_page():
    return FileResponse(paths.STATIC / "index.html")


@router.get("/api/overview")
async def overview_data():
    return JSONResponse({
        "article": "ENG-07",
        "title": "The Cost of an Agent Is NOT Tokens",
        "claim": ("The cost of an agent is the cost per successful run, not the price of its "
                  "tokens. We cost the same support agent with and without the harness."),
        "use_case": ("Support agent: opens tickets, issues refunds, and can be tricked into "
                     "deleting a customer. 16 scenario cases, run on a direct path (no harness) "
                     "and a harnessed path."),
        "framing": ("Tokens are measured from the model's usage field. Every other price "
                    "(runtime, observability, control, reviewer time, remediation) is an "
                    "assumption set in the environment, and the page labels it as such."),
    })
