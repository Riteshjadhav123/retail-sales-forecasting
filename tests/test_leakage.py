import pytest
import pandas as pd
import numpy as np
from src.features.builder import FeatureBuilder
from src.forecasting.validation import TemporalValidator

def test_chronological_split_zero_leakage():
    df = pd.DataFrame({
        "Order Date": pd.date_range("2021-01-01", periods=100, freq="D"),
        "Sales": np.random.rand(100) * 100.0
    })
    validator = TemporalValidator(date_col="Order Date")
    train, val, test = validator.chronological_split(df, train_ratio=0.7, val_ratio=0.15)

    assert train["Order Date"].max() < val["Order Date"].min()
    assert val["Order Date"].max() < test["Order Date"].min()
    assert validator.verify_no_leakage(train, val, test) is True

def test_feature_lag_zero_leakage():
    dates = pd.date_range("2021-01-01", periods=10, freq="D")
    sales = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    df = pd.DataFrame({
        "Order Date": dates,
        "Region": ["Central"] * 10,
        "Category": ["Furniture"] * 10,
        "Sales": sales,
        "Quantity": [1] * 10,
        "Discount": [0.0] * 10,
        "Profit": [5.0] * 10,
        "Unit Price": [10.0] * 10
    })

    builder = FeatureBuilder()
    feat_df = builder.transform(df)

    # For day index 1 (sales=20.0), lag_1 MUST equal 10.0 (day 0 sales), NOT 20.0 (current day)
    day1_row = feat_df[feat_df["Order Date"] == dates[1]].iloc[0]
    assert day1_row["lag_1"] == 10.0
    assert day1_row["Sales"] == 20.0
