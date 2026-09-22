import numpy as np
import pandas as pd
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger("risk_engine")

class InventoryRiskEngine:
    """
    Multi-Dimensional Risk Engine for RetailMind-X.
    Evaluates Stockout, Overstock, Volatility, Uncertainty, and Lead-Time Risk scores (0 to 100).
    """

    def __init__(self):
        # Weights for Composite Risk Index
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
        eoq: float,
        cv: float = 0.5,
        lower_bound: float = 8.0,
        median_forecast: float = 10.0,
        upper_bound: float = 12.0,
        std_lead_time: float = 1.0
    ) -> Dict[str, Any]:
        """Evaluates all 5 risk dimensions and returns Composite Risk Index."""
        r_stockout = self.compute_stockout_risk(current_stock, reorder_point)
        r_overstock = self.compute_overstock_risk(current_stock, reorder_point, eoq)
        r_volatility = self.compute_volatility_risk(cv)
        r_uncertainty = self.compute_uncertainty_risk(lower_bound, median_forecast, upper_bound)
        r_leadtime = self.compute_leadtime_risk(std_lead_time)

        composite_risk = (
            self.w_stockout * r_stockout +
            self.w_overstock * r_overstock +
            self.w_uncertainty * r_uncertainty +
            self.w_volatility * r_volatility +
            self.w_leadtime * r_leadtime
        )
        composite_risk = float(np.round(composite_risk, 2))

        # Categorize Composite Risk
        if composite_risk >= 70.0:
            category = "CRITICAL_HIGH"
        elif composite_risk >= 40.0:
            category = "MODERATE"
        else:
            category = "LOW"

        return {
            "composite_risk_score": composite_risk,
            "risk_category": category,
            "risk_breakdown": {
                "stockout_risk": round(r_stockout, 2),
                "overstock_risk": round(r_overstock, 2),
                "volatility_risk": round(r_volatility, 2),
                "uncertainty_risk": round(r_uncertainty, 2),
                "leadtime_risk": round(r_leadtime, 2)
            }
        }
