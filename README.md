# repo-04-agent-tco-instrumentation

**Article 04 — Beyond the Model: Agent TCO Instrumentation**

Full Total Cost of Ownership (TCO) breakdown across 100 production runs of a Legal Contract Review agent. Tokens are a minority of true TCO.

> **Key Finding:** Tokens represent a fraction of true agent TCO. Human review alone costs more than the model.

---

## What This Demonstrates

Most teams measure agent cost as: `token_count × price_per_token`. This repo shows that number is the smallest component of true operational cost. By instrumenting five TCO categories across 100 runs, the article reveals the real cost structure of a production agent.

| TCO Category | Description |
|---|---|
| **Token cost** | LLM API calls — input + output tokens |
| **Human review** | Legal reviewer time when agent flags contracts |
| **Eval share** | Amortised cost of maintaining the eval suite |
| **Incident cost** | Detection + remediation when missed issues reach downstream |
| **Retry cost** | Wasted API calls from transient failures |

---

## Agent: Legal Contract Review

A two-node LangGraph agent that reviews vendor contracts for risk:

1. **`analyse_contract_node`** — sends the contract text to the LLM; identifies risky or unusual clauses and the reasons they are problematic
2. **`assess_risk_node`** — aggregates the clause analysis into an overall risk assessment with routing decision

### Input Schema

```python
class ContractInput(BaseModel):
    contract_id: str
    vendor_name: str
    contract_type: str   # service | supply | nda
    page_count: int
    text_sample: str     # first ~2000 chars (simulated)
```

### Output Schema

```python
class RiskSummary(BaseModel):
    contract_id: str
    overall_risk: str           # high | medium | low | acceptable
    flag_count: int
    requires_legal_review: bool
    summary: str
    estimated_review_minutes: int
```

---

## Framework Decisions

### LangGraph (graph orchestration)
- Defines the two-node pipeline as a `StateGraph` with `AgentState` TypedDict
- Edges: `analyse_contract` → `assess_risk` → `END`
- Compiled graph is wrapped by `AgentHarness` for operational concerns

### AI Refinery SDK (LLM)
- All LLM calls go through `air.AsyncAIRefinery` via `agent/llm.py`
- Base URL: `https://sdk.airefinery.accenture.com/distiller`
- Model: `openai/gpt-oss-120b` (configurable via `AIR_MODEL` env var)
- `truststore.inject_into_ssl()` handles corporate certificate trust
- **No LangChain-Anthropic dependency** — LangGraph does not require LangChain for LLM calls

### agent-harness-core (operational wrapper)
- Wraps the compiled graph: lifecycle state machine, retry, audit, I/O validation
- Installed from local path (or GitHub tag for CI)
- Token tracking via callback is inactive when using air SDK directly — TCO is tracked by `cost_model/` instead

### Design Patterns Applied
- **Wrapper/Facade** — `AgentHarness` adds operational concerns without modifying the graph
- **Strategy** — `RetryPolicy` dispatch table (linear/exponential/jittered)
- **State Machine** — `LifecycleManager` with `VALID_TRANSITIONS` as sole authority
- **Single Responsibility** — each module owns one concern (graph, nodes, prompts, schemas, llm, cost_model)

---

## Cost Model Modules

```
cost_model/
├── review_queue.py      # Human reviewer simulation with time distribution
├── incident_cost.py     # Downstream failure detection + remediation cost
└── tco_aggregator.py    # Per-run RunCost accumulation → TCO summary dict
```

### `ReviewQueueSimulator`
- Base review time by risk level: `high=45min`, `medium=25min`, `low=12min`, `acceptable=5min`
- ±25% jitter + 3 min overhead per flag
- Hourly rate: $85/hr (senior reviewer for high/medium, junior otherwise)

### `IncidentCostTracker`
- Incident rate: 8% of runs (missed risk that reaches downstream)
- Per incident: $120 detection + $850 remediation = $970 total
- Tracks individual incident records

### `TCOAggregator`
- Accumulates `RunCost` dataclasses per run
- Computes absolute costs and percentages for all 5 categories
- `run_totals()` returns per-run total cost list (for trend chart)

---

## Eval Fixtures: 20 Contract Scenarios

Designed to cover all risk levels across the three contract types:

| Risk Level | Count | Examples |
|---|---|---|
| `high` | 7 | Auto-renewal traps, unlimited indemnification, IP ownership transfer, data misuse clauses, predatory termination |
| `medium` | 5 | Delivery estimates, shared arbitration, CPI-linked pricing, quality standards |
| `low` | 3 | Standard NDAs, warranties with limited carve-outs, best-effort services |
| `acceptable` | 5 | Mutual NDAs, fixed fees, client-retains-IP, 30-day termination |

Fixture design principles:
- Each `text_sample` contains realistic contract language that drives the expected risk classification
- High-risk scenarios include multiple red flags (auto-renewal + fee escalation + IP assignment + class action waiver)
- Acceptable scenarios use standard balanced commercial terms

---

## Dashboard

Four pages following the series pattern:

| Page | Route | Content |
|---|---|---|
| Overview | `/` | Article context, central claim, key finding |
| Demo | `/demo` | Submit a contract, see risk assessment + per-run TCO table |
| Metrics | `/metrics` | TCO pie chart, cost trend line, token% stat card |
| Eval | `/eval` | 20 fixtures table, eval command, risk distribution |

Charts are server-side SVG (`dashboard/charts.py`, `dashboard/charts_tco.py`). No client-side chart library.

---

## TCO Simulation Script

```bash
python scripts/run_tco_simulation.py
```

- Runs 100 contract reviews against the live agent
- Simulates human review queue with `ReviewQueueSimulator`
- Injects incidents at 8% rate with `IncidentCostTracker`
- Writes `measurements/tco_results.json`
- Requires `AIREFINERY_API_KEY` to be set

---

## Project Structure

```
repo-04-agent-tco-instrumentation/
├── agent/
│   ├── graph.py         # LangGraph graph + AgentHarness factory
│   ├── llm.py           # AI Refinery async completion helper
│   ├── nodes.py         # analyse_contract_node, assess_risk_node
│   ├── prompts.py       # System prompts + user message templates
│   └── schemas.py       # ContractInput, RiskSummary, AgentState
├── cost_model/
│   ├── review_queue.py  # Human review time + cost simulation
│   ├── incident_cost.py # Incident detection + remediation tracker
│   └── tco_aggregator.py# RunCost + TCOAggregator
├── dashboard/
│   ├── app.py           # FastAPI app
│   ├── charts.py        # Core SVG charts (bar, progress, stat)
│   ├── charts_tco.py    # TCO charts (pie, trend line)
│   └── routes/          # overview, demo, metrics, eval_routes
├── eval/
│   ├── runner.py        # Eval harness (run fixtures, compare risk)
│   └── fixtures/
│       └── contracts.json   # 20 labelled contract scenarios
├── measurements/
│   └── tco_results.json # Written by run_tco_simulation.py
├── scripts/
│   └── run_tco_simulation.py
├── tests/
│   ├── test_agent.py    # Agent schema + node tests (LLM mocked)
│   ├── test_cost_model.py # Cost model unit tests (no external calls)
│   └── test_dashboard.py  # Dashboard route tests (harness mocked)
└── config/
    └── harness.yaml
```

---

## Installation

```bash
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set:

```
AIREFINERY_API_KEY=<your-key>
AIR_MODEL=openai/gpt-oss-120b
```

## Running

```bash
uvicorn dashboard.app:app --reload --port 8000
```

## Testing (no API key required)

```bash
pytest tests/ -v
```

---

## Series Context

| Repo | Article | Adds |
|---|---|---|
| `agent-harness-core` | Foundation | Operational wrapper for any LangGraph graph |
| `repo-01` | Article 01 | Baseline agent (IT triage) |
| `repo-02` | Article 02 | Before/after harness complexity measurement |
| `repo-03` | Article 03 | Framework swap experiment (LangGraph vs direct tool-calling) |
| **`repo-04`** | **Article 04** | **Full TCO breakdown — this repo** |
| `repo-05` | Article 05 | Fleet control plane |
