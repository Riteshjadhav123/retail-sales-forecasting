import pytest
import pandas as pd
from src.demand.stockout_analyzer import StockoutDemandRecoveryEngine

def test_stockout_demand_recovery():
    df = pd.DataFrame({
        "Order Date": pd.date_range("2021-01-01", periods=20, freq="D"),
        "series_id": ["Central_Furniture"] * 20,
        "Sales": [100.0] * 10 + [0.0] * 5 + [100.0] * 5
    })
    engine = StockoutDemandRecoveryEngine()
    demand_df = engine.recover_censored_demand(df)

    assert "is_stockout_derived" in demand_df.columns
    assert "reconstructed_demand" in demand_df.columns
    assert demand_df["reconstructed_demand"].sum() >= demand_df["Sales"].sum()
