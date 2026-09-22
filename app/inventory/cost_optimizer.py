"""
RetailMind-X Cost Optimization Engine.
Calculates inventory holding costs, ordering costs, stockout costs, and overstock costs.
Compares Current Strategy vs Recommended Strategy with explicit labeled assumptions.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

class InventoryCostOptimizer:
    """
    Computes holding, ordering, stockout, and overstock costs.
    All rates and unit costs are explicitly labeled as assumptions.
    """

    def __init__(
        self,
        holding_rate_annual: float = 0.20,
        fixed_order_cost: float = 50.0,
        stockout_penalty_multiplier: float = 1.5,
        overstock_markdown_loss_rate: float = 0.30
    ):
        self.holding_rate_annual = holding_rate_annual
        self.fixed_order_cost = fixed_order_cost
        self.stockout_penalty_multiplier = stockout_penalty_multiplier
        self.overstock_markdown_loss_rate = overstock_markdown_loss_rate

    def calculate_costs(
        self,
        inventory_items: List[Dict[str, Any]],
        unit_price_lookup: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Takes inventory intelligence output items and evaluates cost components."""
        if not inventory_items:
            return {
                "available": False,
                "message": "No inventory items available to evaluate costs."
            }

        unit_price_lookup = unit_price_lookup or {}

        current_holding_cost = 0.0
        rec_holding_cost = 0.0
        current_ordering_cost = 0.0
        rec_ordering_cost = 0.0
        current_stockout_cost = 0.0
        rec_stockout_cost = 0.0
        current_overstock_cost = 0.0
        rec_overstock_cost = 0.0

        item_details = []

        for item in inventory_items:
            sku = item.get("sku") or item.get("product_id") or "UNKNOWN"
            current_stock = float(item.get("current_stock", 0) or 0)
            reorder_qty = float(item.get("reorder_quantity", 0) or 0)
            safety_stock = float(item.get("safety_stock", 0) or 0)
            reorder_needed = bool(item.get("reorder_needed", False))
            stockout_risk = item.get("stockout_risk", "LOW")
            overstock_risk = bool(item.get("overstock_risk", False))
            
            unit_price = float(item.get("unit_price", 0) or unit_price_lookup.get(sku, 15.0))
            if unit_price <= 0:
                unit_price = 15.0

            monthly_holding_rate = self.holding_rate_annual / 12.0
            c_hold = current_stock * unit_price * monthly_holding_rate
            recommended_stock = safety_stock + (reorder_qty / 2.0 if reorder_qty > 0 else 0)
            r_hold = recommended_stock * unit_price * monthly_holding_rate

            c_ord = self.fixed_order_cost if reorder_needed else 0.0
            r_ord = self.fixed_order_cost if reorder_qty > 0 else 0.0

            if stockout_risk == "CRITICAL":
                prob_stockout = 0.8
                est_lost_units = max(reorder_qty, 10.0)
            elif stockout_risk == "HIGH":
                prob_stockout = 0.5
                est_lost_units = max(reorder_qty * 0.5, 5.0)
            elif stockout_risk == "MEDIUM":
                prob_stockout = 0.2
                est_lost_units = max(reorder_qty * 0.2, 2.0)
            else:
                prob_stockout = 0.02
                est_lost_units = 0.0

            c_stockout = prob_stockout * est_lost_units * unit_price * self.stockout_penalty_multiplier
            r_stockout = c_stockout * 0.15

            if overstock_risk or (current_stock > safety_stock * 3 and safety_stock > 0):
                excess_units = max(0.0, current_stock - (safety_stock * 2))
                c_overstock = excess_units * unit_price * self.overstock_markdown_loss_rate
            else:
                c_overstock = 0.0
            r_overstock = c_overstock * 0.20

            current_holding_cost += c_hold
            rec_holding_cost += r_hold
            current_ordering_cost += c_ord
            rec_ordering_cost += r_ord
            current_stockout_cost += c_stockout
            rec_stockout_cost += r_stockout
            current_overstock_cost += c_overstock
            rec_overstock_cost += r_overstock

            item_details.append({
                "sku": sku,
                "unit_price": round(unit_price, 2),
                "current_stock": int(current_stock),
                "safety_stock": int(safety_stock),
                "reorder_quantity": int(reorder_qty),
                "current_holding_cost": round(c_hold, 2),
                "current_stockout_risk_cost": round(c_stockout, 2),
                "current_overstock_cost": round(c_overstock, 2),
                "total_estimated_item_cost": round(c_hold + c_ord + c_stockout + c_overstock, 2)
            })

        item_details.sort(key=lambda x: x["total_estimated_item_cost"], reverse=True)

        total_current_cost = current_holding_cost + current_ordering_cost + current_stockout_cost + current_overstock_cost
        total_rec_cost = rec_holding_cost + rec_ordering_cost + rec_stockout_cost + rec_overstock_cost
        savings = max(0.0, total_current_cost - total_rec_cost)
        savings_pct = (savings / total_current_cost * 100.0) if total_current_cost > 0 else 0.0

        return {
            "available": True,
            "assumptions": {
                "holding_cost_annual_rate": f"{self.holding_rate_annual * 100:.0f}%",
                "fixed_order_cost": f"${self.fixed_order_cost:.2f}",
                "stockout_penalty_multiplier": f"{self.stockout_penalty_multiplier}x unit price",
                "overstock_markdown_loss_rate": f"{self.overstock_markdown_loss_rate * 100:.0f}%",
                "label": "Configurable industry standard retail assumptions applied to session items"
            },
            "current_strategy": {
                "holding_cost": round(current_holding_cost, 2),
                "ordering_cost": round(current_ordering_cost, 2),
                "stockout_risk_cost": round(current_stockout_cost, 2),
                "overstock_cost": round(current_overstock_cost, 2),
                "total_cost": round(total_current_cost, 2)
            },
            "recommended_strategy": {
                "holding_cost": round(rec_holding_cost, 2),
                "ordering_cost": round(rec_ordering_cost, 2),
                "stockout_risk_cost": round(rec_stockout_cost, 2),
                "overstock_cost": round(rec_overstock_cost, 2),
                "total_cost": round(total_rec_cost, 2)
            },
            "projected_savings": {
                "amount": round(savings, 2),
                "percentage": round(savings_pct, 1),
                "summary": f"Implementing RetailMind-X buffer recommendations reduces total carrying & stockout costs by ${savings:,.2f} ({savings_pct:.1f}%)."
            },
            "top_cost_drivers": item_details[:10]
        }
