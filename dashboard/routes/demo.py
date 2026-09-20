from fastapi import APIRouter, Form
from fastapi.responses import FileResponse, JSONResponse

from agent.graph import build_harness
from cost_model.review_queue import ReviewQueueSimulator

router = APIRouter()

_EXAMPLE_CONTRACT = {
    "contract_id": "CTR-DEMO-001",
    "vendor_name": "Acme Software Ltd",
    "contract_type": "service",
    "page_count": 24,
    "text_sample": (
        "This Agreement shall automatically renew for successive one-year terms unless either party "
        "provides written notice of non-renewal at least 180 days prior to the end of the then-current "
        "term. Vendor may increase fees by up to 15% per annum without consent. Vendor retains all "
        "intellectual property created under this Agreement. Client waives the right to participate in "
        "any class action relating to this Agreement. Disputes shall be resolved exclusively by "
        "arbitration in Delaware, USA under AAA Commercial Arbitration Rules."
    ),
}

_review_sim = ReviewQueueSimulator(seed=42)


@router.get("/demo")
async def demo_page():
    return FileResponse("dashboard/static/demo.html")


@router.get("/api/demo/example")
async def demo_example():
    return JSONResponse(_EXAMPLE_CONTRACT)


@router.post("/demo")
async def demo_post(
    contract_id: str = Form(default="CTR-DEMO-001"),
    vendor_name: str = Form(...),
    contract_type: str = Form(default="service"),
    page_count: int = Form(default=24),
    text_sample: str = Form(...),
):
    harness = build_harness()
    result = await harness.run({
        "contract_id": contract_id,
        "vendor_name": vendor_name,
        "contract_type": contract_type,
        "page_count": page_count,
        "text_sample": text_sample,
    })

    tco_breakdown = None
    if result.success and result.output:
        output = result.output
        review = _review_sim.simulate(output.overall_risk, output.flag_count)
        eval_share = round(result.cost_usd * 0.15, 6)
        total = round(result.cost_usd + review.cost_usd + eval_share, 6)
        tco_breakdown = {
            "token_cost_usd": round(result.cost_usd, 6),
            "review_cost_usd": round(review.cost_usd, 6),
            "eval_cost_usd": eval_share,
            "incident_cost_usd": 0.0,
            "total_cost_usd": total,
        }

    return JSONResponse({
        "success": result.success,
        "run_id": result.run_id,
        "duration_ms": result.duration_ms,
        "cost_usd": result.cost_usd,
        "token_usage": result.token_usage,
        "error": result.error,
        "output": {
            "contract_id": result.output.contract_id,
            "overall_risk": result.output.overall_risk,
            "flag_count": result.output.flag_count,
            "requires_legal_review": result.output.requires_legal_review,
            "summary": result.output.summary,
            "estimated_review_minutes": result.output.estimated_review_minutes,
        } if result.success and result.output else None,
        "tco_breakdown": tco_breakdown,
    })
