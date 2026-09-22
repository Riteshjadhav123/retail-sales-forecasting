"""
RetailMind-X Digital Retail Twin & Inventory Simulator Engine.
Simulates daily inventory dynamics, replenishment orders, lead times, stockouts,
and executes decision-level backtests comparing static vs dynamic policies.
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from app.core.logging import get_logger
from app.inventory.safety_stock import InventoryOptimizationEngine

logger = get_logger("inventory_simulator")

def compute_holding_cost(average_inventory_units: float, unit_price: float, holding_cost_pct: float = 0.15) -> float:
    """Computes annual holding cost: Average_Inventory * Unit_Price * Holding_Cost_Pct."""
    return float(average_inventory_units * unit_price * holding_cost_pct)

def compute_ordering_cost(number_of_orders: int, ordering_cost_per_order: float = 50.0) -> float:
    """Computes total ordering cost: Number_of_Orders * Ordering_Cost."""
    return float(number_of_orders * ordering_cost_per_order)

def compute_supply_chain_metrics(
    demand_series: np.ndarray,
    sales_series: np.ndarray,
    inventory_series: np.ndarray,
    rop_series: np.ndarray,
    unit_price: float = 50.0,
    ordering_cost_per_order: float = 50.0,
    holding_cost_pct: float = 0.15
) -> Dict[str, float]:
    """Calculates comprehensive operational and financial inventory performance metrics."""
    n_days = len(demand_series)
    total_demand = float(np.sum(demand_series))
    total_sales = float(np.sum(sales_series))

    # Fill Rate = Total Sales / Total Demand
    fill_rate_pct = (total_sales / total_demand * 100.0) if total_demand > 0 else 100.0

    # Stockout Rate = % days where stockout occurred (sales < demand or inventory == 0)
    stockout_days = np.sum((sales_series < demand_series) | (inventory_series <= 0))
    stockout_rate_pct = (stockout_days / n_days * 100.0) if n_days > 0 else 0.0

    # Service Level = 100 - Stockout Rate
    service_level_achieved = 100.0 - stockout_rate_pct

    # Overstock Rate = % days where inventory > 2 * ROP
    overstock_days = np.sum(inventory_series > (2.0 * rop_series))
    overstock_rate_pct = (overstock_days / n_days * 100.0) if n_days > 0 else 0.0

    # Financial Costs
    avg_inventory = float(np.mean(inventory_series))
    annual_holding_cost = compute_holding_cost(avg_inventory, unit_price, holding_cost_pct)
    
    # Estimate reorder frequencies
    reorder_events = np.sum(np.diff((inventory_series <= rop_series).astype(int)) > 0)
    annual_ordering_cost = compute_ordering_cost(reorder_events, ordering_cost_per_order)

    total_cost = annual_holding_cost + annual_ordering_cost

    return {
        "Fill_Rate_Pct": round(fill_rate_pct, 2),
        "Service_Level_Pct": round(service_level_achieved, 2),
        "Stockout_Rate_Pct": round(stockout_rate_pct, 2),
        "Overstock_Rate_Pct": round(overstock_rate_pct, 2),
        "Average_Inventory_Units": round(avg_inventory, 2),
        "Holding_Cost": round(annual_holding_cost, 2),
        "Ordering_Cost": round(annual_ordering_cost, 2),
        "Total_Supply_Chain_Cost": round(total_cost, 2)
    }

class DigitalRetailTwinSimulator:
    """
    Data-Driven Digital Retail Twin Simulator.
    Simulates daily inventory dynamics, replenishment orders, lead times,
    stockout events, and supply disruptions across a simulation horizon.
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
        """Runs daily inventory simulation loop under specified stress test scenario."""
        n_days = len(base_demand_series)
        demand = base_demand_series.copy()

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

        inventory_log = []
        sales_log = []
        stockout_days = 0
        pipeline_orders = []

        current_inv = initial_inventory

        for day in range(n_days):
            arrived_qty = sum(qty for arr_day, qty in pipeline_orders if arr_day == day)
            current_inv += arrived_qty
            pipeline_orders = [(arr_day, qty) for arr_day, qty in pipeline_orders if arr_day > day]

            d_t = demand[day]
            s_t = min(current_inv, d_t)
            if current_inv < d_t:
                stockout_days += 1
            current_inv -= s_t

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


class InventoryBacktestEngine:
    """
    Decision-Level Backtest Engine comparing:
    1. Traditional Static Min-Max Inventory Policy
    2. RetailMind-X Uncertainty-Aware Dynamic Strategy
    """

    def __init__(self, ordering_cost: float = 50.0, holding_cost_pct: float = 0.15):
        self.opt_engine = InventoryOptimizationEngine(ordering_cost, holding_cost_pct)

    def run_backtest(
        self,
        demand_df: pd.DataFrame,
        output_dir: str = "reports/tables",
        horizon_days: int = 90,
        **kwargs
    ) -> pd.DataFrame:
        """Runs backtest across historical test dataset and returns strategy comparative performance."""
        os.makedirs(output_dir, exist_ok=True)
        results = []

        series_list = demand_df["series_id"].unique()[:10]

        for s_id in series_list:
            s_df = demand_df[demand_df["series_id"] == s_id].sort_values(by="Order Date")
            if len(s_df) < 5:
                continue

            demand = s_df["reconstructed_demand"].values if "reconstructed_demand" in s_df.columns else s_df["Sales"].values
            sales = s_df["Sales"].values
            unit_price = float(s_df["Unit_Price"].mean()) if "Unit_Price" in s_df.columns else 50.0
            n_days = min(len(demand), horizon_days)
            demand = demand[:n_days]
            sales = sales[:n_days]

            # Strategy 1: Traditional Static Min-Max
            static_mean = float(np.mean(demand[:30]))
            static_std = float(np.std(demand[:30]))
            stat_params = self.opt_engine.optimize_series_inventory(s_id, static_mean, static_std, unit_price)

            stat_inv = np.zeros(n_days)
            stat_inv[0] = stat_params["reorder_point"] + stat_params["economic_order_quantity"]
            for d in range(1, n_days):
                stat_inv[d] = max(0.0, stat_inv[d-1] - sales[d])
                if stat_inv[d] <= stat_params["reorder_point"]:
                    stat_inv[d] += stat_params["economic_order_quantity"]

            m_trad = compute_supply_chain_metrics(
                demand_series=demand,
                sales_series=sales,
                inventory_series=stat_inv,
                rop_series=np.full(n_days, stat_params["reorder_point"]),
                unit_price=unit_price
            )
            m_trad["Strategy"] = "Traditional Static Min-Max"
            m_trad["series_id"] = s_id
            results.append(m_trad)

            # Strategy 2: RetailMind-X Uncertainty-Aware Dynamic Strategy
            dyn_mean = float(np.mean(demand))
            dyn_std = float(np.std(demand))
            dyn_params = self.opt_engine.optimize_series_inventory(s_id, dyn_mean, dyn_std, unit_price, service_level=0.99)

            dyn_inv = np.zeros(n_days)
            dyn_inv[0] = dyn_params["reorder_point"] + dyn_params["economic_order_quantity"]
            for d in range(1, n_days):
                dyn_inv[d] = max(0.0, dyn_inv[d-1] - sales[d])
                if dyn_inv[d] <= dyn_params["reorder_point"]:
                    dyn_inv[d] += dyn_params["economic_order_quantity"]

            m_rmx = compute_supply_chain_metrics(
                demand_series=demand,
                sales_series=sales,
                inventory_series=dyn_inv,
                rop_series=np.full(n_days, dyn_params["reorder_point"]),
                unit_price=unit_price
            )
            m_rmx["Strategy"] = "RetailMind-X Uncertainty-Aware"
            m_rmx["series_id"] = s_id
            results.append(m_rmx)

        df_res = pd.DataFrame(results)
        summary = df_res.groupby("Strategy").agg({
            "Fill_Rate_Pct": "mean",
            "Service_Level_Pct": "mean",
            "Stockout_Rate_Pct": "mean",
            "Holding_Cost": "mean",
            "Ordering_Cost": "mean",
            "Total_Supply_Chain_Cost": "mean"
        }).reset_index()

        csv_path = os.path.join(output_dir, "phase3_backtest_results.csv")
        summary.to_csv(csv_path, index=False)

        logger.info(f"Inventory decision backtest complete. Summary saved to '{csv_path}'.")
        return summary
