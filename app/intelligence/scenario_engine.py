"""
RetailMind-X Interactive What-If Simulation Lab.
Evaluates BASELINE vs SCENARIO sensitivity under parameter shifts:
Demand Growth, Promotion Surges, Price Adjustments, Lead-time Disruptions & Target Service Levels.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from app.core.logging import get_logger
from app.inventory.safety_stock import InventoryOptimizationEngine
from app.inventory.risk_matrix import InventoryRiskEngine

logger = get_logger("scenario_lab")

class WhatIfScenarioLab:
    """
    Interactive What-If Simulation Lab for RetailMind-X.
    Evaluates BASELINE vs SCENARIO sensitivity under parameter shifts:
    Demand Growth, Promotion Surges, Price Adjustments, Lead-time Disruptions & Target Service Levels.
    """

    def __init__(self):
        self.opt_engine = InventoryOptimizationEngine()
        self.risk_engine = InventoryRiskEngine()

    def run_scenario_simulation(
        self,
        base_avg_daily_demand: float = 20.0,
        base_std_daily_demand: float = 8.0,
        base_unit_price: float = 50.0,
        base_current_stock: float = 120.0,
        base_lead_time_days: float = 7.0,
        base_service_level: float = 0.95,
        # Scenario Parameters
        demand_growth_pct: float = 0.0,
        promo_boost_pct: float = 0.0,
        price_change_pct: float = 0.0,
        scenario_lead_time_days: float = 7.0,
        scenario_service_level: float = 0.95,
        scenario_current_stock: float = 120.0
    ) -> Dict[str, Any]:
        """Runs BASELINE vs SCENARIO simulation and computes delta impact."""

        # 1. BASELINE Run
        base_params = self.opt_engine.optimize_series_inventory(
            series_id="BASELINE",
            avg_daily_demand=base_avg_daily_demand,
            std_daily_demand=base_std_daily_demand,
            unit_price=base_unit_price,
            lead_time_days=base_lead_time_days,
            service_level=base_service_level
        )
        base_risk = self.risk_engine.evaluate_risk(
            current_stock=base_current_stock,
            reorder_point=base_params["reorder_point"],
            eoq=base_params["economic_order_quantity"],
            cv=base_std_daily_demand / base_avg_daily_demand if base_avg_daily_demand > 0 else 0.5
        )

        # 2. SCENARIO Run
        effective_demand_growth = 1.0 + (demand_growth_pct / 100.0) + (promo_boost_pct / 100.0)
        scen_avg_demand = base_avg_daily_demand * effective_demand_growth
        scen_std_demand = base_std_daily_demand * np.sqrt(max(0.1, effective_demand_growth))
        scen_unit_price = base_unit_price * (1.0 + (price_change_pct / 100.0))

        scen_params = self.opt_engine.optimize_series_inventory(
            series_id="SCENARIO",
            avg_daily_demand=scen_avg_demand,
            std_daily_demand=scen_std_demand,
            unit_price=scen_unit_price,
            lead_time_days=scenario_lead_time_days,
            service_level=scenario_service_level
        )
        scen_risk = self.risk_engine.evaluate_risk(
            current_stock=scenario_current_stock,
            reorder_point=scen_params["reorder_point"],
            eoq=scen_params["economic_order_quantity"],
            cv=scen_std_demand / scen_avg_demand if scen_avg_demand > 0 else 0.5
        )

        # Delta Calculation
        delta_ss = scen_params["safety_stock"] - base_params["safety_stock"]
        delta_rop = scen_params["reorder_point"] - base_params["reorder_point"]
        delta_eoq = scen_params["economic_order_quantity"] - base_params["economic_order_quantity"]
        delta_risk = scen_risk["composite_risk_score"] - base_risk["composite_risk_score"]

        return {
            "baseline": {
                "avg_daily_demand": base_avg_daily_demand,
                "unit_price": base_unit_price,
                "lead_time_days": base_lead_time_days,
                "service_level": base_service_level,
                "safety_stock": base_params["safety_stock"],
                "reorder_point": base_params["reorder_point"],
                "eoq": base_params["economic_order_quantity"],
                "composite_risk_score": base_risk["composite_risk_score"]
            },
            "scenario": {
                "avg_daily_demand": round(scen_avg_demand, 2),
                "unit_price": round(scen_unit_price, 2),
                "lead_time_days": scenario_lead_time_days,
                "service_level": scenario_service_level,
                "safety_stock": scen_params["safety_stock"],
                "reorder_point": scen_params["reorder_point"],
                "eoq": scen_params["economic_order_quantity"],
                "composite_risk_score": scen_risk["composite_risk_score"]
            },
            "impact_delta": {
                "safety_stock_delta": round(delta_ss, 2),
                "reorder_point_delta": round(delta_rop, 2),
                "eoq_delta": round(delta_eoq, 2),
                "risk_score_delta": round(delta_risk, 2)
            }
        }
