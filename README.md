# repo-04-agent-tco-instrumentation

**ENG-07: The Cost of an Agent Is NOT Tokens.**

The series' running scenario, the support agent from article 01, costed on two paths: **direct**
(the same live model and tools, no controls) and **harnessed** (`agent-harness-core`). The cases,
the agent and the harness are the ones from `repo-02`; this repo adds the cost.

> On the harnessed path the cost per successful run was $1.78, and 99.7% of the total was a human
> approving refunds. Tokens were 0.11%. On the direct path the money went to remediating violations.

## Measured, assumed, and what neither can tell you

| | Source |
|---|---|
| Tokens per run | **Measured**: the `usage` field of the model's response, on both paths |
| Whether a violation happened | **Measured**: from what the tools actually did (a `delete_customer` side effect, an unapproved refund, a leaked field, a duplicate ticket) |
| Whether the harness escalated, vetoed or retried | **Measured**: reported by the harness |
| Price per 1,000 tokens, approver minutes and hourly rate, cost to remediate one violation, platform cost per run | **Assumed**: environment variables, no defaults, the report refuses to build without them |

The assumed values used for the results below are in [`measurements/cost_results.json`](measurements/cost_results.json)
under `assumptions`. They are illustrative. Change them and rebuild, no model call needed.

## Result (48 runs per path, `openai/gpt-oss-120b`)

16 cases x 3 repeats. Costs use the assumptions recorded in the results file.

| | Direct | Harnessed |
|---|---|---|
| Runs / successes | 48 / 12 | 48 / 48 |
| Violations (real bad outcomes) | 33 | 0 |
| Tokens | 16,599 | 19,092 |
| Total cost | $32,010 | $85.23 |
| **Cost per successful run** | **$2,667.51** | **$1.78** |
| Largest cost component | remediation, 99.999% | human approval, 99.74% |
| Model (tokens) share | 0.0003% | 0.11% |

The harnessed path escalated 12 runs to a human, vetoed 24, and retried 3 (the direct path crashed on
all 3 of those). The harnessed path used more tokens (19,092 against 16,599), most likely because upstream
controls (context, memory, knowledge) make it ask the model for itself with more in the prompt; this
was not isolated. Downstream cases replay the direct path's decision, so both are costed on the same tokens.

### Sensitivity to the one number nobody can measure for you

The cost of a real violation is the assumption that decides the comparison, so the report sweeps it:

| Cost to remediate one violation | Direct, per success | Harnessed, per success |
|---|---|---|
| $0 | $0.01 | $1.78 |
| $50 | $137.51 | $1.78 |
| $250 | $687.51 | $1.78 |
| $1,000 | $2,750.01 | $1.78 |

**Breakeven: $0.64 per violation.** Above that, the harnessed path costs less per success on this
suite. Below it, the harness is pure overhead: if a violation really cost nothing, the harness
would cost about 120x more per success, because a human approves refunds.

## What this does not show

- **The violation rate is a property of the suite, not of production.** Twelve of the sixteen cases
  were authored to provoke a violation. Read the sweep and the breakeven, not the totals.
- **One model, three repeats.** Nothing here generalises to other models.
- **Downstream results replay a decision**, so they say what the harness does when a model errs, not
  how often it errs.
- **Tools are simulated**, so the `tools` and `knowledge_memory` cost categories are 0.
- **Human approval is an assumed cost.** The scenario scripts the human step; no person was timed.
- The harness's own Evaluation capability runs in-process, so its marginal cost is taken as 0.

## How it works

```
scenario/cases.json ──► run_case(case)  ──► direct run      ─┐
 (16 cases, repo-02)     live model          harnessed run   ─┤ measured: tokens, violation,
                                                              │ vetoed / escalated / retried
                                      economics.runs.compact ─┘
                                                │ measurements/cost_runs.json (raw rows)
                                                ▼
 env assumptions ──► economics.adapter.to_cost_event ──► AgentCostEvent ──► summarize()
                                                                              │
                                    economics.report: cost per success, sweep, breakeven
                                                                              ▼
                                                      measurements/cost_results.json
```

`AgentCostEvent` fields: `model` from measured tokens; `human_review` only on runs the harness
escalated; `remediation` only when a violation actually occurred; `runtime` on both paths;
`observability` and `control` on the harnessed path only, because they exist only with the harness.
A direct run succeeds if nothing harmful happened and it did not crash. A harnessed run succeeds if
the Evaluation capability passed its expectation and nothing harmful happened.

## Running it

```bash
cp .env.example .env     # fill LLM_API_KEY, LLM_BASE_URL and every cost assumption
pip install -e ".[dev]"

python scripts/run_live_cost.py --category unauthorized_tool   # smoke test (needs the model)
python scripts/run_live_cost.py --repeats 3                    # the full measured run
python scripts/build_cost_report.py                            # price it, no model calls

uvicorn dashboard.app:app --port 8000                          # overview, demo, metrics, eval
pytest tests/ -v                                               # no API calls
```

Change an assumption in `.env` and rerun `build_cost_report.py`: the recorded runs are reused.

## Layout

```
scenario/    the support agent and its 16 cases (from repo-02), with measured-token tracking
economics/   assumptions, RunCost -> AgentCostEvent adapter, summarize(), report
scripts/     run_live_cost.py (measure), build_cost_report.py (price)
dashboard/   FastAPI + static HTML: overview, demo, metrics, eval
measurements/cost_runs.json     raw measured rows
measurements/cost_results.json  priced report
tests/       economics, scenario cost, dashboard (fake model client, no network)
```

## Series context

| Repo | Article | Adds |
|---|---|---|
| `repo-02` | ENG-05 | The harness model, the support scenario, conformance |
| `repo-03` | ENG-06 | Framework swap, same scenario |
| **`repo-04`** | **ENG-07** | **What the scenario costs, with and without the harness** |
