"""
RetailMind-X Inventory Risk Matrix & Risk Scoring Engine.
Evaluates Stockout, Overstock, Volatility, Uncertainty, and Lead-Time Risk scores (0 to 100),
and classifies SKUs into 2D Risk Quadrants (LOW, MEDIUM, HIGH, CRITICAL).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from app.core.logging import get_logger

logger = get_logger("risk_matrix")

class InventoryRiskEngine:
    """
    Multi-Dimensional Risk Engine for RetailMind-X.
    Evaluates Stockout, Overstock, Volatility, Uncertainty, and Lead-Time Risk scores (0 to 100).
    """

    def __init__(self):
        self.w_stockout = 0.30
        self.w_overstock = 0.25
        self.w_uncertainty = 0.20
        self.w_volatility = 0.15
        self.w_leadtime = 0.10

    def compute_stockout_risk(self, current_stock: float, reorder_point: float) -> float:
        """Calculates Stockout Risk (0-100). High risk when current stock < ROP."""
        if reorder_point <= 0:
            return 0.0
        gap = reorder_point - current_stock
        risk = (gap / reorder_point) * 100.0 if gap > 0 else 0.0
        return float(np.clip(risk, 0.0, 100.0))

    def compute_overstock_risk(self, current_stock: float, reorder_point: float, eoq: float) -> float:
        """Calculates Overstock Risk (0-100). High risk when current stock > ROP + EOQ."""
        max_desired = reorder_point + eoq
        if max_desired <= 0 or current_stock <= max_desired:
            return 0.0
        excess = current_stock - max_desired
        risk = (excess / current_stock) * 100.0
        return float(np.clip(risk, 0.0, 100.0))

    def compute_volatility_risk(self, coefficient_of_variation: float) -> float:
        """Calculates Volatility Risk (0-100). High risk for high CV."""
        risk = coefficient_of_variation * 50.0
        return float(np.clip(risk, 0.0, 100.0))

    def compute_uncertainty_risk(self, lower_bound: float, median_forecast: float, upper_bound: float) -> float:
        """Calculates Forecast Uncertainty Risk (0-100) based on prediction interval relative width."""
        if median_forecast <= 0:
            return 50.0
        relative_width = (upper_bound - lower_bound) / median_forecast
        risk = relative_width * 40.0
        return float(np.clip(risk, 0.0, 100.0))

    def compute_leadtime_risk(self, std_lead_time_days: float) -> float:
        """Calculates Lead-Time Variability Risk (0-100)."""
        risk = std_lead_time_days * 20.0
        return float(np.clip(risk, 0.0, 100.0))

    def evaluate_risk(
        self,
        current_stock: float,
        reorder_point: float,
        eoq: float = 50.0,
        cv: float = 0.5,
        lower_bound: Optional[float] = None,
        median_forecast: Optional[float] = None,
        upper_bound: Optional[float] = None,
        std_lead_time_days: float = 1.0
    ) -> Dict[str, Any]:
        """Synthesizes all individual risk components into an overall Composite Risk Index."""
        r_stockout = self.compute_stockout_risk(current_stock, reorder_point)
        r_overstock = self.compute_overstock_risk(current_stock, reorder_point, eoq)
        r_volatility = self.compute_volatility_risk(cv)

        if lower_bound is not None and median_forecast is not None and upper_bound is not None:
            r_uncertainty = self.compute_uncertainty_risk(lower_bound, median_forecast, upper_bound)
        else:
            r_uncertainty = 30.0

        r_leadtime = self.compute_leadtime_risk(std_lead_time_days)

        composite_score = (
            self.w_stockout * r_stockout +
            self.w_overstock * r_overstock +
            self.w_uncertainty * r_uncertainty +
            self.w_volatility * r_volatility +
            self.w_leadtime * r_leadtime
        )
        composite_score = float(np.clip(composite_score, 0.0, 100.0))

        if composite_score >= 70.0:
            category = "CRITICAL"
        elif composite_score >= 45.0:
            category = "HIGH"
        elif composite_score >= 25.0:
            category = "MEDIUM"
        else:
            category = "LOW"

        return {
            "composite_risk_score": round(composite_score, 2),
            "risk_category": category,
            "risk_breakdown": {
                "stockout_risk": round(r_stockout, 2),
                "overstock_risk": round(r_overstock, 2),
                "uncertainty_risk": round(r_uncertainty, 2),
                "volatility_risk": round(r_volatility, 2),
                "leadtime_risk": round(r_leadtime, 2)
            }
        }


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
        quadrant_counts = {k: len(v) for k, v in quadrants.items()}
        quadrant_pcts = {k: round((len(v) / total_skus) * 100.0, 1) if total_skus > 0 else 0.0 for k, v in quadrants.items()}

        return {
            "total_skus": total_skus,
            "quadrant_counts": quadrant_counts,
            "quadrant_pcts": quadrant_pcts,
            "quadrants": quadrants
        }

    def _empty_matrix(self) -> Dict[str, Any]:
        return {
            "total_skus": 0,
            "quadrant_counts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "quadrant_pcts": {"CRITICAL": 0.0, "HIGH": 0.0, "MEDIUM": 0.0, "LOW": 0.0},
            "quadrants": {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        }
