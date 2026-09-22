import pytest
import numpy as np
import pandas as pd
from src.forecasting.baselines import BaselineForecaster
from src.forecasting.ml_models import MLForecaster
from src.forecasting.dl_models import DeepForecaster

def test_baseline_forecaster():
    train_df = pd.DataFrame({
        "series_id": ["Central_Furniture"] * 10,
        "Order Date": pd.date_range("2021-01-01", periods=10, freq="D"),
        "Sales": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    })
    test_df = pd.DataFrame({
        "series_id": ["Central_Furniture"] * 3,
        "Order Date": pd.date_range("2021-01-11", periods=3, freq="D")
    })

    base = BaselineForecaster()
    preds_naive = base.predict_naive(test_df, train_df)
    assert len(preds_naive) == 3
    assert preds_naive[0] == 100.0

def test_ml_forecaster():
    feature_cols = ["f1", "f2"]
    train_df = pd.DataFrame({"f1": [1, 2, 3, 4], "f2": [10, 20, 30, 40], "Sales": [15, 25, 35, 45]})
    test_df = pd.DataFrame({"f1": [5, 6], "f2": [50, 60]})

    ml = MLForecaster(feature_cols=feature_cols)
    ml.fit_ridge(train_df, train_df["Sales"].values)
    preds_ridge = ml.predict("LinearRegression", test_df)
    assert len(preds_ridge) == 2
    assert (preds_ridge >= 0).all()

def test_deep_forecaster():
    feature_cols = ["f1", "f2"]
    train_df = pd.DataFrame({"f1": np.random.rand(50), "f2": np.random.rand(50), "Sales": np.random.rand(50) * 100.0})
    test_df = pd.DataFrame({"f1": np.random.rand(10), "f2": np.random.rand(10)})

    dl = DeepForecaster(feature_cols=feature_cols, epochs=3)
    dl.fit(train_df, train_df["Sales"].values)
    preds = dl.predict(test_df)
    assert len(preds) == 10
    assert (preds >= 0).all()
