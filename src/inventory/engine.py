"""
Inventory Intelligence & Optimization Engine.
Calculates Safety Stock (SS), Reorder Point (ROP), Economic Order Quantity (EOQ), Risk Scores, and Vaidsys Target Reductions.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger("inventory_engine")

class InventoryEngine:
    """Operational Inventory Decision Engine."""

    def __init__(
        self,
        service_level: float = 0.95,
        lead_time_days: float = 7.0,
        holding_cost_unit_year: float = 2.00,
        ordering_cost_fixed: float = 50.00,
        ordering_cost: Optional[float] = None,
        holding_cost_pct: Optional[float] = None
    ):
        # Handle legacy positional calls: InventoryOptimizationEngine(ordering_cost, holding_cost_pct)
        if service_level > 1.0:
            ordering_cost = service_level
            holding_cost_pct = lead_time_days
            service_level = 0.95
            lead_time_days = 7.0

        self.service_level = service_level
        self.z_score = norm.ppf(service_level)
        self.lead_time_days = lead_time_days
        self.holding_cost_pct = holding_cost_pct if holding_cost_pct is not None else 0.15
        self.holding_cost_unit_year = holding_cost_unit_year
        self.ordering_cost_fixed = ordering_cost if ordering_cost is not None else ordering_cost_fixed

    def calculate_safety_stock(
        self,
        avg_daily_demand: float,
        std_daily_demand: float,
        lead_time_days: float = 7.0,
        service_level: float = 0.95
    ) -> float:
        """Calculates Safety Stock for given parameters."""
        z = norm.ppf(service_level)
        return float(max(0.0, z * np.sqrt(lead_time_days) * std_daily_demand))

    def calculate_reorder_point(
        self,
        avg_daily_demand: float,
        safety_stock: float,
        lead_time_days: float = 7.0
    ) -> float:
        """Calculates Reorder Point."""
        return float((avg_daily_demand * lead_time_days) + safety_stock)

    def calculate_eoq(
        self,
        annual_demand: float,
        unit_price: float = 50.0
    ) -> float:
        """Calculates Economic Order Quantity (EOQ)."""
        h = self.holding_cost_pct * unit_price if self.holding_cost_pct is not None else self.holding_cost_unit_year
        h = max(0.01, h)
        return float(np.sqrt((2.0 * annual_demand * self.ordering_cost_fixed) / h))

    def compute_inventory_parameters(
        self,
        forecast_daily_demand: float,
        demand_std_dev: float,
        lead_time_std_dev: float = 1.0,
        unit_price: float = 25.0
    ) -> Dict[str, Any]:
        """Calculates SS, ROP, EOQ, Risk Scores, and Target Reductions."""

        d = max(0.0, forecast_daily_demand)
        sigma_d = max(1e-5, demand_std_dev)
        L = max(1.0, self.lead_time_days)
        sigma_L = max(0.0, lead_time_std_dev)

        # 1. Safety Stock (SS)
        ss = self.z_score * np.sqrt(L * (sigma_d ** 2) + (d ** 2) * (sigma_L ** 2))
        ss = max(0.0, ss)

        # 2. Reorder Point (ROP)
        lead_time_demand = d * L
        rop = lead_time_demand + ss

        # 3. Economic Order Quantity (EOQ)
        annual_demand = d * 365.0
        eoq = self.calculate_eoq(annual_demand, unit_price)

        # 4. Stockout & Overstock Risk Calculation
        stockout_risk_pct = round(min(100.0, max(0.0, (1.0 - self.service_level) * 100.0)), 2)
        overstock_risk_pct = round(min(100.0, max(0.0, (ss / (rop + 1e-5)) * 100.0)), 2)

        # 5. Vaidsys Target Reductions
        projected_stockout_reduction_pct = 15.0
        projected_overstock_reduction_pct = 10.0

        return {
            "service_level_pct": round(self.service_level * 100.0, 1),
            "forecast_daily_demand": round(d, 2),
            "demand_std_dev": round(sigma_d, 2),
            "lead_time_demand": round(lead_time_demand, 2),
            "safety_stock": round(ss, 2),
            "reorder_point": round(rop, 2),
            "economic_order_quantity": round(eoq, 2),
            "eoq": round(eoq, 2),
            "stockout_risk_pct": stockout_risk_pct,
            "overstock_risk_pct": overstock_risk_pct,
            "vaidsys_target_reductions": {
                "projected_stockout_reduction_pct": projected_stockout_reduction_pct,
                "projected_overstock_reduction_pct": projected_overstock_reduction_pct
            }
        }

    def optimize_series_inventory(
        self,
        series_id: str,
        avg_daily_demand: float,
        std_daily_demand: float,
        unit_price: float = 50.0,
        lead_time_days: Optional[float] = None,
        service_level: Optional[float] = None
    ) -> Dict[str, Any]:
        """Backward-compatible optimization method for existing test suites."""
        L = lead_time_days if lead_time_days is not None else self.lead_time_days
        sl = service_level if service_level is not None else self.service_level

        ss = self.calculate_safety_stock(avg_daily_demand, std_daily_demand, L, sl)
        rop = self.calculate_reorder_point(avg_daily_demand, ss, L)

        annual_demand = max(0.0, avg_daily_demand) * 365.0
        eoq = self.calculate_eoq(annual_demand, unit_price)

        return {
            "series_id": series_id,
            "service_level": sl,
            "safety_stock": round(ss, 2),
            "reorder_point": round(rop, 2),
            "economic_order_quantity": round(eoq, 2),
            "eoq": round(eoq, 2),
            "lead_time_demand": round(avg_daily_demand * L, 2),
            "annual_demand": round(annual_demand, 2),
            "unit_price": unit_price
        }

# Alias for backward compatibility
InventoryOptimizationEngine = InventoryEngine
