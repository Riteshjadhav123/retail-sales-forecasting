"""
RetailMind-X AI Decision Center.
Synthesizes forecasting, inventory health, risk assessments, and anomaly detection
into prioritized operational recommendations with What / Why / Action rationale.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

class AIDecisionCenter:
    """
    Evaluates current session data and produces:
    - Today's Priorities summary count
    - Ranked Top Operational Actions with What/Why/Action explanations
    """

    @staticmethod
    def generate_decision_dashboard(
        inventory_items: Optional[List[Dict[str, Any]]] = None,
        anomalies: Optional[List[Dict[str, Any]]] = None,
        forecast_metrics: Optional[Dict[str, Any]] = None,
        target_display: Optional[str] = None
    ) -> Dict[str, Any]:
        inventory_items = inventory_items or []
        anomalies = anomalies or []
        forecast_metrics = forecast_metrics or {}
        
        is_monetary = bool(target_display and any(term in target_display.lower() for term in ["monetary", "$", "revenue", "sales"]))
        def fmt_val(v: float) -> str:
            val_int = int(round(v))
            if is_monetary:
                return f"${val_int:,}"
            return f"{val_int:,} units"

        critical_count = 0
        reorder_count = 0
        overstock_count = 0
        healthy_count = 0
        low_confidence_count = 0

        actions = []

        # 1. Analyze Inventory Items
        for item in inventory_items:
            sku = str(item.get("sku") or item.get("product_id") or "UNKNOWN")
            stock = float(item.get("current_stock", 0) or 0)
            reorder_qty = float(item.get("reorder_quantity", 0) or 0)
            safety = float(item.get("safety_stock", 0) or 0)
            risk = str(item.get("stockout_risk", "LOW")).upper()
            overstock = bool(item.get("overstock_risk", False))
            reorder_needed = bool(item.get("reorder_needed", False))
            lead_time = item.get("lead_time_days", 7)

            if risk == "CRITICAL" or (stock == 0 and reorder_qty > 0):
                critical_count += 1
                actions.append({
                    "sku": sku,
                    "title": f"Critical Stockout Alert — {sku}",
                    "priority": "CRITICAL",
                    "what": f"Current stock is {fmt_val(stock)}. Buffer is exhausted.",
                    "why": f"Safety threshold is {fmt_val(safety)}. Immediate demand risk detected with lead time of {lead_time} days.",
                    "action": f"Issue emergency Purchase Order for {fmt_val(reorder_qty)} immediately to avoid lost revenue.",
                    "impact": f"Protects customer fulfillment for SKU {sku} during next cycle."
                })
            elif reorder_needed or risk == "HIGH":
                reorder_count += 1
                actions.append({
                    "sku": sku,
                    "title": f"Reorder Recommended — {sku}",
                    "priority": "HIGH",
                    "what": f"Stock level ({fmt_val(stock)}) has dipped below reorder point.",
                    "why": f"Safety stock is {fmt_val(safety)} and predicted demand will deplete remaining inventory within normal lead time.",
                    "action": f"Place standard replenishment order for {fmt_val(reorder_qty)}.",
                    "impact": f"Prevents transition to stockout state while optimizing order batching."
                })
            elif overstock:
                overstock_count += 1
                actions.append({
                    "sku": sku,
                    "title": f"Excess Inventory Detected — {sku}",
                    "priority": "MEDIUM",
                    "what": f"Holding {fmt_val(stock)} exceeds 2.5x buffer requirements ({fmt_val(safety)}).",
                    "why": "Carrying costs are accumulating with slow inventory turnover.",
                    "action": "Consider targeted promotional bundle or pause upcoming replenishment cycles.",
                    "impact": "Free up working capital and reduce carrying costs."
                })
            else:
                healthy_count += 1

        # 2. Analyze Anomalies
        high_severity_anomalies = [a for a in anomalies if a.get("severity") == "HIGH"]
        for anom in high_severity_anomalies[:3]:
            anom_type = anom.get("type", "SPIKE")
            date_str = anom.get("date", "Recent")
            val = anom.get("value", 0)
            dev = anom.get("deviation_pct", 0)
            attribution = anom.get("causal_attribution", "Requires review")
            
            actions.append({
                "sku": "AGGREGATE",
                "title": f"Demand {anom_type} on {date_str}",
                "priority": "HIGH" if anom_type == "DROP" else "MEDIUM",
                "what": f"Unusual {anom_type.lower()} of {val} ({'+' if dev > 0 else ''}{dev:.1f}% vs baseline).",
                "why": attribution,
                "action": "Audit sales logs and marketing activity for external promotional triggers or system outages.",
                "impact": "Improves forecast accuracy by isolating transient shocks."
            })

        # 3. Analyze Forecast Quality
        mape = forecast_metrics.get("mape")
        if mape is not None and mape > 25.0:
            low_confidence_count += 1
            actions.append({
                "sku": "MODEL",
                "title": "Model Calibration Advisory",
                "priority": "LOW",
                "what": f"Current best model MAPE is {mape:.1f}%.",
                "why": "Higher variance or volatility detected in recent historical series.",
                "action": "Consider feature engineering with promotion indicators or expanding historical window.",
                "impact": "Refines forward-looking forecast confidence interval."
            })

        prio_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        actions.sort(key=lambda a: prio_order.get(a["priority"], 99))

        return {
            "priorities": {
                "critical_stockouts": critical_count,
                "reorders_needed": reorder_count,
                "demand_anomalies": len(anomalies),
                "overstock_items": overstock_count,
                "healthy_items": healthy_count
            },
            "top_actions": actions[:8],
            "total_actions": len(actions)
        }
