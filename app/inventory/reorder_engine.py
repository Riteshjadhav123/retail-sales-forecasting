"""
RetailMind-X Automated Machine-Readable Reorder Recommendation Engine.
Calculates safety stocks, reorder points, economic order quantities, and generates structured reorder actions.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from app.core.logging import get_logger
from app.inventory.safety_stock import InventoryOptimizationEngine
from app.inventory.risk_matrix import InventoryRiskEngine

logger = get_logger("reorder_engine")

class ReorderDecisionEngine:
    """Automated Machine-Readable Reorder Recommendation Engine for RetailMind-X."""

    def __init__(self, ordering_cost: float = 50.0, holding_cost_pct: float = 0.15):
        self.opt_engine = InventoryOptimizationEngine(ordering_cost, holding_cost_pct)
        self.risk_engine = InventoryRiskEngine()

    def generate_recommendations(
        self,
        series_demand_summary: pd.DataFrame,
        json_path: str = "data/processed/reorder_recommendations.json",
        parquet_path: str = "data/processed/reorder_recommendations.parquet"
    ) -> pd.DataFrame:
        """
        Generates structured reorder recommendations across all series.
        Expected columns in summary: ['series_id', 'avg_daily_demand', 'std_daily_demand', 'unit_price', 'current_stock', 'cv']
        """
        recommendations = []

        for idx, row in series_demand_summary.iterrows():
            s_id = row["series_id"]
            d_avg = float(row.get("avg_daily_demand", 10.0))
            d_std = float(row.get("std_daily_demand", 5.0))
            price = float(row.get("unit_price", 50.0))
            current_stock = float(row.get("current_stock", 50.0))
            cv = float(row.get("cv", 0.5))

            sl_target = 0.95
            opt_params = self.opt_engine.optimize_series_inventory(
                series_id=s_id,
                avg_daily_demand=d_avg,
                std_daily_demand=d_std,
                unit_price=price,
                service_level=sl_target
            )

            ss = opt_params["safety_stock"]
            rop = opt_params["reorder_point"]
            eoq = opt_params["economic_order_quantity"]

            risk_info = self.risk_engine.evaluate_risk(
                current_stock=current_stock,
                reorder_point=rop,
                eoq=eoq,
                cv=cv
            )

            # Reorder Logic
            if current_stock <= rop:
                status = "REORDER_NOW"
                rec_qty = float(np.round(max(eoq, rop + eoq - current_stock), 2))
                reason = f"Current stock ({current_stock:.1f}) is at or below Reorder Point ({rop:.1f}). Order {rec_qty:.1f} units immediately to maintain {sl_target*100:.0f}% service level."
            elif current_stock > (rop + eoq):
                status = "OVERSTOCKED"
                rec_qty = 0.0
                reason = f"Current stock ({current_stock:.1f}) exceeds ROP + EOQ threshold ({rop + eoq:.1f}). Hold new orders to reduce holding costs."
            else:
                status = "HEALTHY"
                rec_qty = 0.0
                reason = f"Current stock ({current_stock:.1f}) is above ROP ({rop:.1f}). Inventory level is healthy."

            rec_entry = {
                "series_id": s_id,
                "current_stock": current_stock,
                "avg_daily_demand": d_avg,
                "safety_stock": ss,
                "reorder_point": rop,
                "economic_order_quantity": eoq,
                "recommended_order_quantity": rec_qty,
                "reorder_status": status,
                "composite_risk_score": risk_info["composite_risk_score"],
                "risk_category": risk_info["risk_category"],
                "stockout_risk": risk_info["risk_breakdown"]["stockout_risk"],
                "overstock_risk": risk_info["risk_breakdown"]["overstock_risk"],
                "reasoning": reason
            }
            recommendations.append(rec_entry)

        rec_df = pd.DataFrame(recommendations)

        try:
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            rec_df.to_json(json_path, orient="records", indent=2)
            rec_df.to_parquet(parquet_path, index=False)
        except Exception as e:
            logger.warning(f"Could not write recommendations files: {e}")

        reorder_now_count = (rec_df["reorder_status"] == "REORDER_NOW").sum()
        logger.info(f"Reorder recommendations generated. Total SKUs flagged for immediate reorder: {reorder_now_count} out of {len(rec_df)}.")
        return rec_df
