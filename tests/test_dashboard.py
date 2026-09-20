"""Dashboard route tests — all agent/harness calls mocked."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from dashboard.app import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_overview_returns_200(client):
    async with client as c:
        resp = await c.get("/")
    assert resp.status_code == 200
    assert "TCO" in resp.text


@pytest.mark.asyncio
async def test_demo_get_returns_200(client):
    async with client as c:
        resp = await c.get("/demo")
    assert resp.status_code == 200
    assert "Contract" in resp.text


@pytest.mark.asyncio
async def test_metrics_returns_200(client):
    async with client as c:
        resp = await c.get("/metrics")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_eval_get_returns_200(client):
    async with client as c:
        resp = await c.get("/eval")
    assert resp.status_code == 200
    assert "20" in resp.text


@pytest.mark.asyncio
async def test_api_overview_returns_json(client):
    async with client as c:
        resp = await c.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["article_number"] == "04"
    assert "TCO" in data["article_title"]


@pytest.mark.asyncio
async def test_api_eval_fixtures_returns_20_contracts(client):
    async with client as c:
        resp = await c.get("/api/eval/fixtures")
    assert resp.status_code == 200
    fixtures = resp.json()
    assert len(fixtures) == 20


@pytest.mark.asyncio
async def test_api_metrics_no_data_returns_seed_command(client):
    import tempfile
    from pathlib import Path

    with patch("dashboard.routes.metrics._MEASUREMENTS", Path(tempfile.mktemp())):
        async with client as c:
            resp = await c.get("/api/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["no_data"] is True
    assert "run_tco_simulation" in data["seed_command"]


@pytest.mark.asyncio
async def test_demo_post_success_with_mocked_harness(client):
    mock_output = MagicMock()
    mock_output.contract_id = "CTR-DEMO-001"
    mock_output.overall_risk = "high"
    mock_output.flag_count = 3
    mock_output.requires_legal_review = True
    mock_output.summary = "Multiple high-risk clauses found."
    mock_output.estimated_review_minutes = 45

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.output = mock_output
    mock_result.cost_usd = 0.001
    mock_result.duration_ms = 1500
    mock_result.run_id = "test-run-id"
    mock_result.token_usage = {"total_tokens": 800}
    mock_result.error = None

    mock_harness = AsyncMock()
    mock_harness.run.return_value = mock_result

    with patch("dashboard.routes.demo.build_harness", return_value=mock_harness):
        async with client as c:
            resp = await c.post(
                "/demo",
                data={
                    "contract_id": "CTR-DEMO-001",
                    "vendor_name": "Acme Software Ltd",
                    "contract_type": "service",
                    "page_count": "24",
                    "text_sample": "Auto-renewal clause with 180-day notice required.",
                },
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["output"]["overall_risk"] == "high"
    assert data["tco_breakdown"] is not None
    assert data["tco_breakdown"]["review_cost_usd"] > 0
