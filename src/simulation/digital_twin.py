import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.utils.logger import get_logger
from src.inventory.engine import InventoryOptimizationEngine

logger = get_logger("digital_twin")

class DigitalRetailTwinSimulator:
    """
    Data-Driven Digital Retail Twin Simulator.
    Simulates daily inventory dynamics, replenishment orders, lead times,
    stockout events, and supply disruptions across a 90-day simulation horizon.
    """

    def __init__(self, ordering_cost: float = 50.0, holding_cost_pct: float = 0.15):
        self.opt_engine = InventoryOptimizationEngine(ordering_cost, holding_cost_pct)

    def simulate_series(
        self,
        series_id: str,
        base_demand_series: np.ndarray,
        unit_price: float = 50.0,
        initial_inventory: float = 200.0,
        lead_time_days: int = 7,
        scenario_name: str = "NORMAL"
    ) -> Dict[str, Any]:
        """Runs 90-day daily inventory simulation loop under specified stress test scenario."""
        n_days = len(base_demand_series)
        demand = base_demand_series.copy()

        # Apply Scenario Stress Test Multipliers
        lt = lead_time_days
        if scenario_name == "DEMAND_SPIKE":
            demand *= 1.50
        elif scenario_name == "SUPPLIER_DELAY":
            lt += 7
        elif scenario_name == "PROMOTION_CAMPAIGN":
            demand *= 1.40
            unit_price *= 0.85
        elif scenario_name == "DEMAND_DROP":
            demand *= 0.60
        elif scenario_name == "INVENTORY_SHORTAGE":
            initial_inventory *= 0.50

        avg_d = float(np.mean(demand))
        std_d = float(np.std(demand))
        opt_params = self.opt_engine.optimize_series_inventory(
            series_id=series_id,
            avg_daily_demand=avg_d,
            std_daily_demand=std_d,
            unit_price=unit_price,
            lead_time_days=lt
        )

        rop = opt_params["reorder_point"]
        eoq = opt_params["economic_order_quantity"]

        # Simulation Loop state
        inventory_log = []
        sales_log = []
        stockout_days = 0
        pipeline_orders = [] # list of (arrival_day, qty)

        current_inv = initial_inventory

        for day in range(n_days):
            # 1. Process arriving replenishment orders
            arrived_qty = sum(qty for arr_day, qty in pipeline_orders if arr_day == day)
            current_inv += arrived_qty
            pipeline_orders = [(arr_day, qty) for arr_day, qty in pipeline_orders if arr_day > day]

            # 2. Observe daily customer demand
            d_t = demand[day]
            s_t = min(current_inv, d_t) # Realized sales
            if current_inv < d_t:
                stockout_days += 1
            current_inv -= s_t

            # 3. Check reorder trigger
            # Total inventory position = Current + Pipeline
            pipeline_qty = sum(qty for _, qty in pipeline_orders)
            inv_position = current_inv + pipeline_qty

            if inv_position <= rop:
                arrival_day = day + lt
                pipeline_orders.append((arrival_day, eoq))

            inventory_log.append(current_inv)
            sales_log.append(s_t)

        inv_arr = np.asarray(inventory_log)
        sales_arr = np.asarray(sales_log)
        total_demand = float(np.sum(demand))
        total_sales = float(np.sum(sales_arr))

        fill_rate = (total_sales / total_demand * 100.0) if total_demand > 0 else 100.0
        avg_inv = float(np.mean(inv_arr))
        holding_cost = avg_inv * unit_price * 0.15 * (n_days / 365.0)

        logger.info(f"Digital Twin simulation '{scenario_name}' completed for '{series_id}': Fill Rate={fill_rate:.2f}%, Stockout Days={stockout_days}/{n_days}.")

        return {
            "series_id": series_id,
            "scenario": scenario_name,
            "horizon_days": n_days,
            "lead_time_days": lt,
            "total_demand_units": round(total_demand, 2),
            "total_sales_units": round(total_sales, 2),
            "fill_rate_pct": round(fill_rate, 2),
            "stockout_days": stockout_days,
            "average_inventory_units": round(avg_inv, 2),
            "holding_cost_dollar": round(holding_cost, 2),
            "reorder_point": rop,
            "eoq": eoq
        }
