"""
RetailMind-X: Dynamic Inventory Risk Matrix Engine
Classifies SKUs across 2D Risk Matrix: Demand Volatility (CV) vs. Stockout / Overstock Risk Score.
Matrix Quadrants: LOW, MEDIUM, HIGH, CRITICAL.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger("risk_matrix")

class InventoryRiskMatrixEngine:
    """Classifies SKUs into 2D Risk Quadrants based on Empirical Volatility and Reorder Status."""

    def __init__(self, reorder_recs: List[Dict[str, Any]]):
        self.recs = reorder_recs

    def build_matrix(self) -> Dict[str, Any]:
        """Constructs filterable Risk Matrix data breakdown."""
        if not self.recs:
            return self._empty_matrix()

        quadrants = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }

        for r in self.recs:
            series_id = r.get("series_id", "Unknown")
            cv = float(r.get("cv", 0.5))
            risk_score = float(r.get("composite_risk_score", r.get("stockout_risk_score", 50.0)))
            reorder_status = r.get("reorder_status", "NORMAL")

            # Determine Quadrant
            if risk_score >= 75.0 or (cv > 0.8 and reorder_status == "REORDER_NOW"):
                quadrant = "CRITICAL"
            elif risk_score >= 55.0 or cv > 0.7:
                quadrant = "HIGH"
            elif risk_score >= 35.0 or cv > 0.4:
                quadrant = "MEDIUM"
            else:
                quadrant = "LOW"

            item = {
                "series_id": series_id,
                "cv": round(cv, 2),
                "risk_score": round(risk_score, 1),
                "current_stock": round(float(r.get("current_stock", 0.0)), 1),
                "reorder_point": round(float(r.get("reorder_point", 0.0)), 1),
                "reorder_status": reorder_status,
                "quadrant": quadrant
            }
            quadrants[quadrant].append(item)

        total_skus = len(self.recs)

        return {
            "summary": {
                "total_skus": total_skus,
                "critical_count": len(quadrants["CRITICAL"]),
                "high_count": len(quadrants["HIGH"]),
                "medium_count": len(quadrants["MEDIUM"]),
                "low_count": len(quadrants["LOW"]),
                "critical_pct": round((len(quadrants["CRITICAL"]) / max(1, total_skus)) * 100, 1),
                "high_pct": round((len(quadrants["HIGH"]) / max(1, total_skus)) * 100, 1)
            },
            "quadrants": quadrants
        }

    def _empty_matrix(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_skus": 0, "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0
            },
            "quadrants": {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        }
