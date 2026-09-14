# AI Purchasing Agent — Rappi Turbo Assignment

A backend-heavy full-stack prototype for purchasing decisions across quick-commerce fulfillment nodes. It investigates operational evidence, challenges a system recommendation, applies deterministic procurement guardrails, requires buyer approval, executes mock purchase orders, and validates the persisted result.

## Assignment alignment

The assignment asks for an agent that can investigate a purchasing situation, make an appropriate decision, take action where appropriate, and validate the outcome. It also explicitly says the recommendation should not automatically be assumed correct and asks for a feedback loop around actions.

This implementation prioritizes Scenario 1 end-to-end and includes three additional scenarios for evaluation.

## Architecture

See [`architecture.svg`](architecture.svg).

```text
Buyer UI → FastAPI → Agent → read-only procurement tools → deterministic validator
                         ↓                              ↓
                       LLM                         human approval
                                                        ↓
                                                   PO service
                                                        ↓
                                                post-action validator
                                                        ↓
                                                     audit log
```

### Trust boundaries

- **LLM:** investigates with tools and proposes a decision. It is not trusted for arithmetic or policy enforcement.
- **Deterministic validator:** source of truth for MOQ, budget, storage and supplier checks.
- **Human approval:** mandatory before any PO write.
- **Post-action validator:** reads the persisted PO back and compares it with approved intent.
- **Audit log:** records analysis, execution, success and escalation events.

## Scenarios

### 1. Purchase Recommendation Review

The system recommends **800 apples**. The agent finds:

- inventory = 420
- confirmed inbound = 300
- 7-day forecast = 840
- safety stock = 180
- net position = 720
- incremental need = **300**

The agent therefore **MODIFIES** the recommendation to 300 rather than blindly accepting 800. The 300-unit PO passes MOQ, budget and storage validation.

### 2. Supplier Cannot Fulfil

A 500-unit purchase can only receive 250 units from the primary supplier. The agent identifies a 250-unit shortfall and proposes a split: 250 primary + 250 alternate, subject to buyer approval.

### 3. Demand / Forecast Changed

Milk demand is increased by 55%. Forecast becomes 977 units and calculated incremental need becomes 687 units. The primary supplier cost would exceed the remaining $700 budget, so the agent **INVESTIGATES** instead of executing.

### 4. Purchasing Constraint

Coffee needs 125 additional units, but the 125-unit purchase would cost $525 against a $250 budget. The agent blocks execution and escalates the constraint.

## Feedback loop

The execution path is deliberately two-stage:

1. Validate proposed order.
2. Require buyer approval.
3. Create and persist the PO.
4. Read the persisted PO back.
5. Validate quantity, supplier and expected workflow status.
6. If the outcome differs from approved intent, mark the outcome as failed/escalated rather than silently continuing.

The UI includes **Simulate ERP quantity mismatch** to demonstrate this failure path during evaluation.

## Run locally

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

## LLM tool-calling mode

Copy `.env.example` to `.env` and add an OpenAI API key and a model available to your account:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.6-luna
```

With a key, the agent uses the OpenAI Responses API and function tools to investigate the scenario. The LLM proposal is then checked by deterministic business guardrails before it can reach the human approval gate. If the LLM call fails or times out, the deterministic safety workflow takes over and the UI exposes the fallback mode.

The default model is `gpt-5.6-luna`; set `OPENAI_MODEL` to another model available to your API account if needed. The API key is loaded from `.env` and is never sent to the browser or committed to the repository.

**Do not commit `.env` or API keys.**

## Tests

Run:

```bash
pytest -q
```

The tests cover:

- recommendation correction
- supplier shortage split
- forecast change and budget constraint
- hard constraint blocking
- post-action mismatch detection

## API surface

- `GET /api/health` — runtime/LLM mode
- `GET /api/scenarios` — demo scenarios
- `POST /api/analyze` — investigate and decide
- `POST /api/execute` — approved PO execution + post-action validation
- `GET /api/audit` — audit history

## Evaluation checklist

| Criterion | Demonstration |
|---|---|
| Correct decision | Scenario 1 changes 800 → 300 |
| Necessary information | Tool trace shows inventory, forecast, POs, suppliers and constraints |
| Constraint compliance | Deterministic validation |
| Appropriate action | Human-approved PO creation only when executable |
| Validation | Proposed-order + post-action validation |
| Failed action | ERP mismatch simulation causes escalation |
| Auditability | SQLite audit trail |

## Demo script

1. Run Scenario 1 and show the original 800-unit recommendation versus the calculated 300-unit need.
2. Show the tool trace and deterministic validation.
3. Approve the PO and show post-action validation passing.
4. Run Scenario 2 and show the split between primary and alternate suppliers.
5. Run Scenario 4 and show that the budget constraint prevents execution.
6. Re-run Scenario 1 with **Simulate ERP quantity mismatch** enabled and show that post-action validation fails and the system escalates.
7. Explain that production versions would replace the mock tools with inventory/ERP/supplier/email services while preserving the same guardrails and approval boundary.
