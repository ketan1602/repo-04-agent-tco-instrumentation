"""Dashboard tests: no network, the model is the autouse fake in conftest."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from dashboard import paths
from dashboard.app import app
from economics import Assumptions
from economics.report import build_report
from tests.test_economics import ENV, direct, harnessed, row

client = TestClient(app)


@pytest.fixture
def assumptions_env(monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)


@pytest.mark.parametrize("path", ["/", "/metrics", "/demo", "/eval"])
def test_pages_return_html(path):
    resp = client.get(path)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_overview_api():
    body = client.get("/api/overview").json()
    assert body["article"] == "ENG-07"
    assert "support" in body["use_case"].lower()


def test_metrics_no_data(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "COST_RESULTS", tmp_path / "missing.json")
    body = client.get("/api/metrics").json()
    assert body["no_data"] is True
    assert "python scripts/build_cost_report.py" in body["seed_commands"]


def test_metrics_with_data(monkeypatch, tmp_path, assumptions_env):
    rows = [row(direct(violated=True), harnessed(vetoed=True), "unauthorized_tool"),
            row(direct(), harnessed())]
    report = build_report(rows, Assumptions.from_env(), "test-model")
    target = tmp_path / "cost_results.json"
    target.write_text(json.dumps(report))
    monkeypatch.setattr(paths, "COST_RESULTS", target)
    body = client.get("/api/metrics").json()
    assert body["no_data"] is False
    assert body["harnessed"]["violations"] == 0 and body["direct"]["violations"] == 1
    assert set(body["charts"]) == {"direct", "harnessed"}
    assert "<svg" in body["charts"]["harnessed"]


def test_metrics_unbounded_cost_per_success_is_null(monkeypatch, tmp_path, assumptions_env):
    report = build_report([row(direct(violated=True), harnessed())], Assumptions.from_env(), "m")
    text = json.dumps(report).replace('"cost_per_success_usd": null', '"cost_per_success_usd": Infinity', 1)
    target = tmp_path / "cost_results.json"
    target.write_text(text)
    monkeypatch.setattr(paths, "COST_RESULTS", target)
    body = client.get("/api/metrics").json()
    assert body["direct"]["cost_per_success_usd"] is None


def test_demo_cases_lists_sixteen():
    cases = client.get("/api/demo/cases").json()
    assert len(cases) == 16
    assert {"id", "category", "utterance"} <= set(cases[0])


def test_demo_run_costs_both_paths(assumptions_env, fake_llm):
    resp = client.post("/api/demo/run", json={"case_id": "unauthorized_tool-1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["direct"]["violated"] is True and body["direct"]["success"] is False
    assert body["harnessed"]["violated"] is False and body["harnessed"]["vetoed"] is True
    assert body["direct"]["tokens"] == body["harnessed"]["tokens"] == fake_llm.total_tokens
    assert body["direct"]["cost_usd"]["remediation"] == pytest.approx(100.0)
    assert body["harnessed"]["total_usd"] < body["direct"]["total_usd"]


def test_demo_run_needs_every_assumption(assumptions_env, monkeypatch):
    monkeypatch.delenv("COST_CENTER")
    resp = client.post("/api/demo/run", json={"case_id": "unauthorized_tool-1"})
    assert resp.status_code == 503
    assert "COST_CENTER" in resp.json()["error"]


def test_demo_run_needs_the_llm(assumptions_env, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY")
    resp = client.post("/api/demo/run", json={"case_id": "unauthorized_tool-1"})
    assert resp.status_code == 503
    assert "LLM_API_KEY" in resp.json()["error"]


def test_demo_run_unknown_case(assumptions_env):
    assert client.post("/api/demo/run", json={"case_id": "nope"}).status_code == 404


def test_eval_cases_lists_sixteen():
    body = client.get("/api/eval/cases").json()
    assert len(body["cases"]) == 16
    assert sum(body["categories"].values()) == 16
    assert {"id", "category", "control", "expected", "violation"} <= set(body["cases"][0])
