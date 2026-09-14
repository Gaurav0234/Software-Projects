from copy import deepcopy

PRODUCTS = {
    "SKU-APPLE-001": {
        "sku": "SKU-APPLE-001", "name": "Royal Gala Apples 1kg", "node": "Delhi-NCR Dark Store 01",
        "current_inventory": 420, "daily_demand": 120, "forecast_7d": 840, "forecast_confidence": 0.86,
        "open_pos": [{"po_id": "PO-1042", "qty": 300, "eta_days": 2, "status": "confirmed"}],
        "supplier": {"id": "SUP-APL", "name": "FreshFarm Foods", "lead_time_days": 2, "moq": 100, "unit_price": 1.8, "reliability": 0.96},
        "alternates": [{"id": "SUP-ALT", "name": "GreenBasket Wholesale", "lead_time_days": 4, "moq": 200, "unit_price": 2.05, "reliability": 0.91}],
        "budget_remaining": 1800, "storage_available": 500, "unit_volume": 0.5, "safety_stock_days": 1.5,
        "recommendation": 800,
    },
    "SKU-MILK-002": {
        "sku": "SKU-MILK-002", "name": "Full Cream Milk 1L", "node": "Delhi-NCR Dark Store 02",
        "current_inventory": 180, "daily_demand": 90, "forecast_7d": 630, "forecast_confidence": 0.92,
        "open_pos": [{"po_id": "PO-2077", "qty": 250, "eta_days": 1, "status": "confirmed"}],
        "supplier": {"id": "SUP-MILK", "name": "DailyDairy", "lead_time_days": 1, "moq": 50, "unit_price": 1.2, "reliability": 0.98},
        "alternates": [{"id": "SUP-DAIRY2", "name": "City Dairy Co", "lead_time_days": 2, "moq": 100, "unit_price": 1.35, "reliability": 0.95}],
        "budget_remaining": 700, "storage_available": 100, "unit_volume": 1.0, "safety_stock_days": 1,
        "recommendation": 300,
    },
    "SKU-COFFEE-003": {
        "sku": "SKU-COFFEE-003", "name": "Ground Coffee 250g", "node": "Delhi-NCR Dark Store 03",
        "current_inventory": 90, "daily_demand": 35, "forecast_7d": 245, "forecast_confidence": 0.78,
        "open_pos": [{"po_id": "PO-3091", "qty": 100, "eta_days": 3, "status": "confirmed"}],
        "supplier": {"id": "SUP-COF", "name": "BeanHouse", "lead_time_days": 3, "moq": 100, "unit_price": 4.2, "reliability": 0.89},
        "alternates": [{"id": "SUP-COF2", "name": "RoastWorks", "lead_time_days": 2, "moq": 100, "unit_price": 4.4, "reliability": 0.94}],
        "budget_remaining": 250, "storage_available": 80, "unit_volume": 0.3, "safety_stock_days": 2,
        "recommendation": 200,
    },
}

SCENARIOS = {
    "recommendation_review": {"label": "Scenario 1 — Purchase Recommendation Review", "description": "Review an 800-unit recommendation against inventory, demand, inbound POs, supplier conditions, budget and storage.", "sku": "SKU-APPLE-001"},
    "supplier_shortage": {"label": "Scenario 2 — Supplier Cannot Fulfil Purchase", "description": "A 500-unit PO is constrained to 250 units. Decide whether to split the order, source elsewhere or escalate.", "sku": "SKU-APPLE-001", "po_qty": 500, "available_qty": 250},
    "forecast_change": {"label": "Scenario 3 — Demand / Forecast Changed", "description": "Actual demand increased significantly. Recalculate whether current inventory plus inbound stock is still sufficient.", "sku": "SKU-MILK-002", "demand_multiplier": 1.55},
    "constraint": {"label": "Scenario 4 — Purchasing Constraint", "description": "Additional stock is needed, but a hard purchasing constraint prevents the nominal purchase from being executed.", "sku": "SKU-COFFEE-003"},
}

def get_product(sku: str):
    if sku not in PRODUCTS:
        raise KeyError(f"Unknown SKU: {sku}")
    return deepcopy(PRODUCTS[sku])
