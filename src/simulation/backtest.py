import os
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from src.utils.logger import get_logger
from src.inventory.engine import InventoryOptimizationEngine
from src.inventory.metrics import compute_supply_chain_metrics

logger = get_logger("inventory_backtest")

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

        # Filter test series
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
        md_path = os.path.join(output_dir, "phase3_backtest_results.md")

        summary.to_csv(csv_path, index=False)
        summary.to_markdown(md_path, index=False)

        logger.info(f"Inventory decision backtest complete. Summary saved to '{csv_path}' and '{md_path}'.")
        return summary
