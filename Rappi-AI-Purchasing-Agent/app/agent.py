import json
import os
from copy import deepcopy

from dotenv import load_dotenv

from .data import get_product, SCENARIOS

load_dotenv()


DECISIONS = {"ACCEPT", "MODIFY", "REJECT", "INVESTIGATE"}


def tool_get_inventory(sku: str):
    p = get_product(sku)
    return {
        "sku": sku,
        "node": p["node"],
        "current_inventory": p["current_inventory"],
        "daily_demand": p["daily_demand"],
    }


def tool_get_forecast(sku: str, multiplier: float = 1.0):
    p = get_product(sku)
    return {
        "sku": sku,
        "forecast_7d": int(p["forecast_7d"] * multiplier + 0.5),
        "daily_demand": round(p["daily_demand"] * multiplier, 1),
        "confidence": p["forecast_confidence"],
        "safety_stock_days": p["safety_stock_days"],
    }


def tool_get_open_pos(sku: str):
    return get_product(sku)["open_pos"]


def tool_get_supplier_options(sku: str):
    p = get_product(sku)
    return {"primary": p["supplier"], "alternates": p["alternates"]}


def tool_get_constraints(sku: str):
    p = get_product(sku)
    return {
        "budget_remaining": p["budget_remaining"],
        "storage_available": p["storage_available"],
        "unit_volume": p["unit_volume"],
        "moq": p["supplier"]["moq"],
        "unit_price": p["supplier"]["unit_price"],
    }


def calculate_need(inventory: int, forecast_7d: int, inbound: int, safety_stock: int):
    target_stock = forecast_7d + safety_stock
    net_position = inventory + inbound
    return {
        "target_stock": target_stock,
        "net_position": net_position,
        "recommended_qty": max(0, target_stock - net_position),
    }


def validate_po(sku: str, qty: int, supplier_id: str):
    p = get_product(sku)
    supplier = (
        p["supplier"]
        if supplier_id == p["supplier"]["id"]
        else next((x for x in p["alternates"] if x["id"] == supplier_id), None)
    )
    if not supplier:
        return {"acceptable": False, "errors": ["Unknown supplier"], "warnings": [], "qty": qty}

    errors, warnings = [], []
    if qty <= 0:
        errors.append("Quantity must be greater than zero")
    if qty > 0 and qty < supplier["moq"]:
        errors.append(f"Quantity {qty} is below MOQ {supplier['moq']}")

    cost = qty * supplier["unit_price"]
    storage = qty * p["unit_volume"]
    if cost > p["budget_remaining"]:
        errors.append(f"Cost ${cost:.2f} exceeds remaining budget ${p['budget_remaining']:.2f}")
    if storage > p["storage_available"]:
        errors.append(
            f"Storage {storage:.1f} exceeds available {p['storage_available']:.1f} volume units"
        )
    if supplier["reliability"] < 0.90:
        warnings.append("Supplier reliability is below 90%; buyer review recommended")

    return {
        "acceptable": not errors,
        "supplier": supplier,
        "qty": qty,
        "cost": round(cost, 2),
        "storage": round(storage, 2),
        "errors": errors,
        "warnings": warnings,
    }


def validate_created_po(po: dict, expected_qty: int, expected_supplier_id: str):
    checks = [
        ("PO created", bool(po.get("created"))),
        ("Approved quantity preserved", po.get("qty") == expected_qty),
        ("Approved supplier preserved", po.get("supplier_id") == expected_supplier_id),
        ("Expected workflow status", po.get("status") == "PENDING_SUPPLIER_CONFIRMATION"),
    ]
    errors = [name for name, passed in checks if not passed]
    return {
        "acceptable": not errors,
        "errors": errors,
        "checks": [{"check": n, "passed": p} for n, p in checks],
    }


def _base_analysis(scenario_id: str):
    s = SCENARIOS[scenario_id]
    sku = s["sku"]
    p = get_product(sku)
    multiplier = s.get("demand_multiplier", 1.0)

    inv = tool_get_inventory(sku)
    fc = tool_get_forecast(sku, multiplier)
    pos = tool_get_open_pos(sku)
    suppliers = tool_get_supplier_options(sku)
    constraints = tool_get_constraints(sku)

    inbound = sum(x["qty"] for x in pos if x["status"] in ("confirmed", "open"))
    safety = round(fc["daily_demand"] * fc["safety_stock_days"])
    need = calculate_need(inv["current_inventory"], fc["forecast_7d"], inbound, safety)

    logs = [
        {"tool": "get_inventory", "result": inv},
        {"tool": "get_forecast", "result": fc},
        {"tool": "get_open_pos", "result": pos},
        {"tool": "get_supplier_options", "result": suppliers},
        {"tool": "get_constraints", "result": constraints},
    ]
    return s, p, inv, fc, pos, suppliers, constraints, need, logs


def deterministic_analysis(scenario_id: str):
    s, p, inv, fc, pos, suppliers, constraints, need, logs = _base_analysis(scenario_id)
    proposed_orders = []

    if scenario_id == "recommendation_review":
        original = p["recommendation"]
        validation = validate_po(p["sku"], need["recommended_qty"], suppliers["primary"]["id"])
        logs.append({"tool": "validate_po", "result": validation})
        if validation["acceptable"]:
            decision = "MODIFY" if original != need["recommended_qty"] else "ACCEPT"
            action = (
                f"Prepare a PO for {need['recommended_qty']} units with "
                f"{suppliers['primary']['name']}; buyer approval is required before submission."
            )
            proposed_orders = [{
                "qty": need["recommended_qty"],
                "supplier_id": suppliers["primary"]["id"],
                "supplier_name": suppliers["primary"]["name"],
            }]
        else:
            decision = "INVESTIGATE"
            action = "Do not execute the recommendation until the blocking constraints are resolved."
        rationale = [
            f"System recommendation is {original} units, but evidence supports {need['recommended_qty']} incremental units.",
            f"7-day forecast is {fc['forecast_7d']} units and safety stock target is {round(fc['daily_demand'] * fc['safety_stock_days'])} units.",
            f"Current inventory plus confirmed inbound is {need['net_position']} units.",
        ]

    elif scenario_id == "supplier_shortage":
        shortfall = s["po_qty"] - s["available_qty"]
        alt = suppliers["alternates"][0]
        alt_qty = max(shortfall, alt["moq"])
        alt_validation = validate_po(p["sku"], alt_qty, alt["id"])
        logs.append({"tool": "validate_po", "result": alt_validation})
        if alt_validation["acceptable"]:
            decision = "MODIFY"
            action = (
                f"Split the purchase: accept {s['available_qty']} units from "
                f"{suppliers['primary']['name']} and source {alt_qty} units from "
                f"{alt['name']} after buyer approval."
            )
            proposed_orders = [
                {"qty": s["available_qty"], "supplier_id": suppliers["primary"]["id"], "supplier_name": suppliers["primary"]["name"]},
                {"qty": alt_qty, "supplier_id": alt["id"], "supplier_name": alt["name"]},
            ]
            rationale = [
                f"Primary supplier can fulfil only {s['available_qty']} of {s['po_qty']} units.",
                f"The shortfall is {shortfall} units.",
                f"Alternate {alt['name']} can cover the shortfall at ${alt['unit_price']:.2f}/unit with {alt['lead_time_days']}-day lead time.",
            ]
            validation = {"acceptable": True, "errors": [], "warnings": alt_validation.get("warnings", []), "split": proposed_orders}
        else:
            decision = "INVESTIGATE"
            action = "Do not create a replacement order until an alternate supplier or escalation path is approved."
            rationale = alt_validation["errors"]
            validation = alt_validation

    else:
        validation = validate_po(p["sku"], need["recommended_qty"], suppliers["primary"]["id"])
        logs.append({"tool": "validate_po", "result": validation})
        if need["recommended_qty"] <= 0:
            decision = "REJECT"
            action = "Do not purchase; inventory plus inbound stock covers forecast and safety stock."
            rationale = ["Net inventory position already meets the target stock level."]
        elif not validation["acceptable"]:
            decision = "INVESTIGATE"
            action = "Do not execute the nominal purchase. Resolve the hard constraint or escalate to the buyer."
            rationale = validation["errors"] + [f"Calculated incremental need is {need['recommended_qty']} units."]
        else:
            decision = "ACCEPT"
            action = f"Prepare a PO for {need['recommended_qty']} units with {suppliers['primary']['name']}; buyer approval is required."
            rationale = [f"Calculated incremental need is {need['recommended_qty']} units."]
            proposed_orders = [{"qty": need["recommended_qty"], "supplier_id": suppliers["primary"]["id"], "supplier_name": suppliers["primary"]["name"]}]

    return {
        "scenario_id": scenario_id,
        "scenario": s["label"],
        "sku": p["sku"],
        "product": p["name"],
        "decision": decision,
        "action": action,
        "rationale": rationale,
        "evidence": {
            "inventory": inv,
            "forecast": fc,
            "open_pos": pos,
            "suppliers": suppliers,
            "constraints": constraints,
            "calculation": need,
            "original_recommendation": p["recommendation"] if scenario_id == "recommendation_review" else None,
        },
        "validation": validation,
        "tool_log": logs,
        "proposed_orders": proposed_orders,
        "requires_human_approval": bool(proposed_orders),
        "agent_mode": "deterministic-safety-fallback",
    }


TOOLS = {
    "get_inventory": tool_get_inventory,
    "get_forecast": tool_get_forecast,
    "get_open_pos": tool_get_open_pos,
    "get_supplier_options": tool_get_supplier_options,
    "get_constraints": tool_get_constraints,
    "validate_po": validate_po,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "get_inventory",
        "description": "Get current inventory and daily demand for a SKU.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_forecast",
        "description": "Get the 7-day demand forecast, confidence and safety-stock parameters. For scenario demand changes, use the multiplier provided by the scenario.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string"}, "multiplier": {"type": "number"}},
            "required": ["sku"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_open_pos",
        "description": "Get existing open or confirmed purchase orders for a SKU.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_supplier_options",
        "description": "Get primary and alternate supplier terms including MOQ, price, lead time and reliability.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_constraints",
        "description": "Get remaining purchasing budget, storage capacity and unit volume.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "validate_po",
        "description": "Deterministically validate a proposed purchase order against MOQ, budget, storage and supplier reliability.",
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {"type": "string"},
                "qty": {"type": "integer"},
                "supplier_id": {"type": "string"},
            },
            "required": ["sku", "qty", "supplier_id"],
            "additionalProperties": False,
        },
    },
]


LLM_OUTPUT_SCHEMA = {
    "type": "json_schema",
    "name": "procurement_decision",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": sorted(DECISIONS)},
            "action": {"type": "string"},
            "rationale": {"type": "array", "items": {"type": "string"}},
            "proposed_orders": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "qty": {"type": "integer"},
                        "supplier_id": {"type": "string"},
                        "supplier_name": {"type": "string"},
                    },
                    "required": ["qty", "supplier_id", "supplier_name"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["decision", "action", "rationale", "proposed_orders"],
        "additionalProperties": False,
    },
}


def _parse_llm_proposal(response):
    raw = (response.output_text or "").strip()
    if not raw:
        raise ValueError("LLM returned no final procurement decision")
    proposal = json.loads(raw)
    if proposal.get("decision") not in DECISIONS:
        raise ValueError("LLM returned an invalid decision")
    if not isinstance(proposal.get("proposed_orders"), list):
        raise ValueError("LLM proposed_orders must be an array")
    return proposal


def _guardrail_llm_proposal(scenario_id: str, proposal: dict, evidence: dict):
    """Validate an LLM proposal without letting the LLM bypass deterministic business rules."""
    orders = proposal.get("proposed_orders", [])
    errors = []
    validated_orders = []

    for order in orders:
        try:
            qty = int(order["qty"])
            supplier_id = str(order["supplier_id"])
        except (KeyError, TypeError, ValueError):
            errors.append("Malformed proposed order")
            continue
        check = validate_po(evidence["sku"], qty, supplier_id)
        validated_orders.append({"order": order, "validation": check})
        if not check["acceptable"]:
            errors.extend(check["errors"])

    # Scenario-specific invariants protect against an LLM making a superficially valid but wrong purchase.
    if scenario_id == "recommendation_review" and orders:
        expected = evidence["calculation"]["recommended_qty"]
        total = sum(int(o.get("qty", 0)) for o in orders)
        if total != expected:
            errors.append(f"Recommendation review requires {expected} incremental units; proposed total was {total}")
        if not any(o.get("supplier_id") == evidence["suppliers"]["primary"]["id"] for o in orders):
            errors.append("Recommendation review must use the validated primary supplier for this demo")

    if scenario_id == "supplier_shortage" and orders:
        scenario = SCENARIOS[scenario_id]
        total = sum(int(o.get("qty", 0)) for o in orders)
        if total != scenario["po_qty"]:
            errors.append(f"Supplier shortage plan must cover {scenario['po_qty']} units; proposed total was {total}")

    if proposal["decision"] in {"ACCEPT", "MODIFY"} and not orders:
        errors.append("An executable ACCEPT/MODIFY decision must contain at least one proposed order")

    if errors:
        return {
            "acceptable": False,
            "errors": errors,
            "warnings": [],
            "validated_orders": validated_orders,
        }

    return {
        "acceptable": True,
        "errors": [],
        "warnings": [w for x in validated_orders for w in x["validation"].get("warnings", [])],
        "validated_orders": validated_orders,
    }


def run_llm_agent(scenario_id: str):
    from openai import OpenAI

    s = SCENARIOS[scenario_id]
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    prompt = f"""
You are the procurement decision agent for a quick-commerce buyer.

Scenario: {s['label']}
Description: {s['description']}
SKU: {s['sku']}

You must investigate before deciding. Use the available tools to obtain the evidence you need.
Do not invent inventory, forecast, PO, supplier, price, budget or storage data.
The purchasing system recommendation is only a proposal; challenge it when the evidence disagrees.

Decision choices: ACCEPT, MODIFY, REJECT, INVESTIGATE.
- ACCEPT means the recommendation is appropriate and an executable order can be proposed.
- MODIFY means the recommendation/order should be changed and an executable order can be proposed.
- REJECT means no purchase should be made.
- INVESTIGATE means a blocking constraint, uncertainty or missing information prevents safe execution.

You may propose purchase orders, but you must NEVER claim that you executed them. Human approval is required before any write.
Before your final answer, use validate_po for every proposed order.
Return only the structured procurement decision requested by the output schema.
""".strip()

    items = [{"role": "user", "content": prompt}]
    calls = []

    for _ in range(8):
        response = client.responses.create(
            model=model,
            input=items,
            tools=TOOL_SCHEMAS,
            text={"format": LLM_OUTPUT_SCHEMA},
        )
        items.extend(response.output)
        function_calls = [x for x in response.output if getattr(x, "type", None) == "function_call"]

        if not function_calls:
            proposal = _parse_llm_proposal(response)
            deterministic = deterministic_analysis(scenario_id)
            guardrail = _guardrail_llm_proposal(scenario_id, proposal, {**deterministic["evidence"], "sku": deterministic["sku"]})

            if not guardrail["acceptable"]:
                # The LLM's reasoning is retained for auditability, but the deterministic boundary wins.
                deterministic["agent_mode"] = "openai-tool-calling + deterministic-guardrail"
                deterministic["llm_proposal"] = proposal
                deterministic["llm_tool_log"] = calls
                deterministic["llm_guardrail"] = guardrail
                deterministic["llm_error"] = "LLM proposal blocked by deterministic guardrails"
                return deterministic

            result = deepcopy(deterministic)
            result["decision"] = proposal["decision"]
            result["action"] = proposal["action"]
            result["rationale"] = proposal["rationale"]
            result["proposed_orders"] = proposal["proposed_orders"]
            result["validation"] = guardrail
            result["requires_human_approval"] = bool(proposal["proposed_orders"])
            result["agent_mode"] = "openai-tool-calling + deterministic-guardrail"
            result["llm_proposal"] = proposal
            result["llm_tool_log"] = calls
            result["llm_guardrail"] = guardrail
            return result

        for call in function_calls:
            args = json.loads(call.arguments or "{}")
            if call.name == "get_forecast" and "multiplier" not in args:
                args["multiplier"] = s.get("demand_multiplier", 1.0)
            fn = TOOLS.get(call.name)
            if not fn:
                result = {"error": f"Unknown tool: {call.name}"}
            else:
                result = fn(**args)
            calls.append({"tool": call.name, "arguments": args, "result": result})
            items.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(result),
            })

    raise RuntimeError("LLM tool loop exceeded the maximum of 8 rounds")


def run_agent(scenario_id: str):
    if scenario_id not in SCENARIOS:
        raise ValueError("Unknown scenario")

    if os.getenv("OPENAI_API_KEY"):
        try:
            return run_llm_agent(scenario_id)
        except Exception as exc:
            result = deterministic_analysis(scenario_id)
            result["llm_error"] = str(exc)
            return result

    return deterministic_analysis(scenario_id)
