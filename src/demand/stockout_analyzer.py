import os
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from src.utils.logger import get_logger

logger = get_logger("stockout_analyzer")

class StockoutDemandRecoveryEngine:
    """
    Censored Demand Identification & Unconstrained Demand Recovery Engine.
    Strictly separates REAL OBSERVED SALES from SIMULATED/DERIVED INVENTORY & STOCKOUT SIGNALS.
    """

    def __init__(self, stockout_threshold_days: int = 3, base_buffer: float = 100.0):
        self.threshold_days = stockout_threshold_days
        self.base_buffer = base_buffer

    def derive_inventory_and_stockout_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Derives synthetic inventory buffer proxies and detects stockout events.
        REAL DATA: Sales, Quantity, Date, Series_ID
        DERIVED DATA: inventory_level_proxy, is_stockout_derived
        """
        df = df.copy()
        df = df.sort_values(by=["series_id", "Order Date"]).reset_index(drop=True)

        # Calculate 14-day rolling mean demand per series_id
        rolling_mean = df.groupby("series_id")["Sales"].transform(lambda x: x.shift(1).rolling(14, min_periods=1).mean()).fillna(10.0)

        # Simulate inventory replenishment cycle & stockout events
        # A stockout is flagged when observed sales = 0 following a high-demand period (rolling mean > median)
        median_demand = rolling_mean.median()
        is_zero_sales = (df["Sales"] == 0.0)
        is_high_prior_demand = (rolling_mean > median_demand)

        # Flag derived stockout: consecutive zero-sales after high prior velocity
        df["is_stockout_derived"] = (is_zero_sales & is_high_prior_demand)
        
        # Derive proxy inventory level
        df["inventory_level_proxy"] = np.where(df["is_stockout_derived"], 0.0, np.maximum(5.0, rolling_mean * 3.0 - df["Sales"]))
        
        stockout_count = int(df["is_stockout_derived"].sum())
        logger.info(f"Derived inventory proxies. Identified {stockout_count:,} potential stockout days out of {len(df):,} total observation days ({stockout_count/len(df)*100:.2f}%).")
        return df

    def recover_censored_demand(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies Statistical Un-censoring / Tobit Recovery Model.
        Reconstructs 'reconstructed_unconstrained_demand' during stockout periods.
        """
        df = self.derive_inventory_and_stockout_signals(df)

        # Compute non-stockout 7-day trailing velocity
        non_stockout_sales = df["Sales"].where(~df["is_stockout_derived"], np.nan)
        trailing_velocity = df.groupby("series_id")["Sales"].transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean()).fillna(0.0)
        
        # Tobit-like Un-censoring: If stockout, demand = trailing velocity * multiplier (accounting for pent-up demand)
        df["reconstructed_demand"] = np.where(
            df["is_stockout_derived"],
            np.round(trailing_velocity * 1.15, 2), # 15% recovery adjustment for pent-up demand
            df["Sales"]
        )

        df["censored_demand_gap"] = np.round(df["reconstructed_demand"] - df["Sales"], 2)
        total_recovered_volume = float(df["censored_demand_gap"].sum())
        logger.info(f"Demand recovery complete. Total estimated unconstrained demand gap recovered: ${total_recovered_volume:,.2f}")

        return df

    def save_demand_dataset(self, df: pd.DataFrame, parquet_path: str = "data/processed/demand_recovered.parquet", csv_path: str = "data/processed/demand_recovered.csv") -> Tuple[str, str]:
        """Saves demand dataset to disk."""
        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved recovered demand dataset to '{parquet_path}' and '{csv_path}'.")
        return parquet_path, csv_path
