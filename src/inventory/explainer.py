import pandas as pd
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger("decision_explainer")

class DecisionExplanationEngine:
    """
    Structured Explanation Engine answering core business questions:
    - WHY SHOULD I REORDER?
    - WHY THIS QUANTITY?
    - WHY IS THIS PRODUCT HIGH RISK?
    - WHY DID FORECAST CHANGE?
    """

    def explain_reorder_decision(self, record: Dict[str, Any]) -> Dict[str, str]:
        """Provides structured answers for inventory reorder decisions."""
        s_id = record["series_id"]
        stock = record["current_stock"]
        rop = record["reorder_point"]
        eoq = record.get("economic_order_quantity", record.get("eoq", 50.0))
        rec_qty = record["recommended_order_quantity"]
        risk_score = record["composite_risk_score"]
        status = record["reorder_status"]

        # 1. Why Should I Reorder?
        if status == "REORDER_NOW":
            q1 = f"Reorder triggered because current stock level ({stock:.1f} units) is at or below the calculated Reorder Point ({rop:.1f} units). Delaying reorder exposes the product to stockout risk."
        elif status == "OVERSTOCKED":
            q1 = f"No reorder required. Current stock ({stock:.1f} units) exceeds maximum target inventory ({rop + eoq:.1f} units)."
        else:
            q1 = f"No immediate reorder needed. Current stock ({stock:.1f} units) is safely above the Reorder Point ({rop:.1f} units)."

        # 2. Why This Quantity?
        if rec_qty > 0:
            q2 = f"Recommended quantity of {rec_qty:.1f} units balances fixed ordering cost ($50) against annual holding costs, restoring inventory to target level (ROP + EOQ)."
        else:
            q2 = "Recommended quantity is 0 units because current inventory is sufficient to cover expected lead-time demand."

        # 3. Why Is This Product High Risk?
        stockout_r = record.get("stockout_risk", 0.0)
        overstock_r = record.get("overstock_risk", 0.0)
        q3 = f"Composite risk score is {risk_score:.1f}/100. Key drivers: Stockout Risk = {stockout_r:.1f}%, Overstock Risk = {overstock_r:.1f}%."

        # 4. Why Did Forecast Change?
        q4 = "Forecast reflects recent 7-day trend changes, demand volatility, and promotional discount factors incorporated by the adaptive model router."

        return {
            "series_id": s_id,
            "WHY_SHOULD_I_REORDER": q1,
            "WHY_THIS_QUANTITY": q2,
            "WHY_IS_THIS_HIGH_RISK": q3,
            "WHY_DID_FORECAST_CHANGE": q4
        }
