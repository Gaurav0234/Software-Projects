import json
import os
import sqlite3
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from .agent import run_agent, validate_po, validate_created_po
from .data import SCENARIOS, get_product

load_dotenv()

DB = os.getenv("DATABASE_PATH", "purchasing.db")
app = FastAPI(title="AI Purchasing Agent", version="2.0.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class ExecuteRequest(BaseModel):
    scenario_id: str
    approved: bool = False
    orders: list[dict] | None = None
    simulate_failure: bool = False


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, scenario TEXT, event TEXT, decision TEXT, action TEXT, details TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS purchase_orders (po_id TEXT PRIMARY KEY, sku TEXT, qty INTEGER, supplier_id TEXT, status TEXT, created_at TEXT)")
    c.commit(); return c

@app.get("/")
def index(): return FileResponse("app/static/index.html")

@app.get("/api/scenarios")
def scenarios(): return SCENARIOS

@app.get("/api/health")
def health():
    return {"status": "ok", "llm_enabled": bool(os.getenv("OPENAI_API_KEY")), "model": os.getenv("OPENAI_MODEL", "gpt-5.6-luna") if os.getenv("OPENAI_API_KEY") else None}

@app.post("/api/analyze")
def analyze(payload: dict):
    scenario_id = payload.get("scenario_id")
    try: result = run_agent(scenario_id)
    except Exception as e: raise HTTPException(400, str(e))
    c = db(); c.execute("INSERT INTO audit_log(ts,scenario,event,decision,action,details) VALUES(?,?,?,?,?,?)", (datetime.now(timezone.utc).isoformat(), scenario_id, "ANALYZE", result["decision"], result["action"], json.dumps({"mode": result.get("agent_mode"), "tool_count": len(result.get("tool_log", []))}))); c.commit(); c.close()
    return result


def make_po(sku, qty, supplier_id, suffix=""):
    validation = validate_po(sku, qty, supplier_id)
    if not validation["acceptable"]: return {"created": False, "validation": validation}
    po_id = f"PO-AI-{sku[-3:]}-{supplier_id[-3:]}-{qty}{suffix}"
    return {"created": True, "po_id": po_id, "sku": sku, "qty": qty, "supplier_id": supplier_id, "status": "PENDING_SUPPLIER_CONFIRMATION", "validation": validation}

@app.post("/api/execute")
def execute(req: ExecuteRequest):
    if not req.approved: raise HTTPException(403, "Human approval is required before creating a PO")
    analysis = run_agent(req.scenario_id)
    if not analysis.get("proposed_orders"): raise HTTPException(409, "No executable purchase order is proposed for this scenario")
    orders = req.orders or analysis["proposed_orders"]
    # Re-validate the approved payload at execution time; never trust stale UI state.
    for o in orders:
        check = validate_po(analysis["sku"], int(o["qty"]), o["supplier_id"])
        if not check["acceptable"]: raise HTTPException(409, {"message": "Execution blocked by deterministic guardrail", "validation": check})
    c = db(); created = []; post_checks = []
    for i, o in enumerate(orders, 1):
        po = make_po(analysis["sku"], int(o["qty"]), o["supplier_id"], f"-{i}" if len(orders) > 1 else "")
        if not po["created"]: raise HTTPException(409, po)
        # Failure injection demonstrates the feedback loop during evaluation.
        persisted_qty = po["qty"] + 1 if req.simulate_failure and i == 1 else po["qty"]
        c.execute("INSERT OR REPLACE INTO purchase_orders(po_id,sku,qty,supplier_id,status,created_at) VALUES(?,?,?,?,?,?)", (po["po_id"], po["sku"], persisted_qty, po["supplier_id"], po["status"], datetime.now(timezone.utc).isoformat()))
        row = dict(c.execute("SELECT * FROM purchase_orders WHERE po_id=?", (po["po_id"],)).fetchone())
        pv = validate_created_po({"created": True, **row}, int(o["qty"]), o["supplier_id"])
        post_checks.append({"po_id": po["po_id"], "validation": pv})
        created.append({**po, "persisted_qty": persisted_qty})
    all_ok = all(x["validation"]["acceptable"] for x in post_checks)
    feedback = ("Post-action validation passed: persisted POs match the approved intent and can proceed to supplier confirmation." if all_ok else "Post-action validation failed: the persisted PO differs from approved intent. Execution outcome is escalated instead of silently continuing.")
    c.execute("INSERT INTO audit_log(ts,scenario,event,decision,action,details) VALUES(?,?,?,?,?,?)", (datetime.now(timezone.utc).isoformat(), req.scenario_id, "EXECUTE", "EXECUTE" if all_ok else "ESCALATE", "Create purchase order(s)", json.dumps({"created": created, "post_action_validation": post_checks, "feedback": feedback})))
    c.commit(); c.close()
    return {"created": True, "purchase_orders": created, "post_action_validation": {"acceptable": all_ok, "orders": post_checks}, "feedback": feedback, "escalated": not all_ok}

@app.get("/api/audit")
def audit():
    c = db(); rows = [dict(r) for r in c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 30")]; c.close(); return rows
