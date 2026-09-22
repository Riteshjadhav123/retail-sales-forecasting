import pytest
import pandas as pd
import numpy as np
from src.simulation.backtest import InventoryBacktestEngine

def test_inventory_backtest_engine(tmp_path):
    dates = pd.date_range("2021-01-01", periods=90, freq="D")
    demand_df = pd.DataFrame({
        "Order Date": np.tile(dates, 2),
        "series_id": ["Central_Furniture"] * 90 + ["East_Technology"] * 90,
        "reconstructed_demand": np.random.exponential(20.0, 180),
        "Sales": np.random.exponential(18.0, 180),
        "Unit Price": [50.0] * 180
    })

    backtester = InventoryBacktestEngine()
    out_dir = str(tmp_path)
    res = backtester.run_backtest(demand_df, output_dir=out_dir)

    assert isinstance(res, pd.DataFrame)
    assert len(res) == 2
    assert "Strategy" in res.columns
    assert "Fill_Rate_Pct" in res.columns
