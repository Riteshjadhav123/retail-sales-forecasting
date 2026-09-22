import pytest
import pandas as pd
from src.inventory.reorder_engine import ReorderDecisionEngine

def test_reorder_recommendations(tmp_path):
    summary = pd.DataFrame({
        "series_id": ["Central_Furniture", "East_Technology"],
        "avg_daily_demand": [20.0, 15.0],
        "std_daily_demand": [5.0, 3.0],
        "unit_price": [50.0, 100.0],
        "current_stock": [10.0, 200.0],
        "cv": [0.25, 0.20]
    })

    engine = ReorderDecisionEngine()
    json_p = str(tmp_path / "rec.json")
    parquet_p = str(tmp_path / "rec.parquet")

    rec_df = engine.generate_recommendations(summary, json_path=json_p, parquet_path=parquet_p)

    assert len(rec_df) == 2
    assert "reorder_status" in rec_df.columns
    row1 = rec_df[rec_df["series_id"] == "Central_Furniture"].iloc[0]
    assert row1["reorder_status"] == "REORDER_NOW"
    assert row1["recommended_order_quantity"] > 0
