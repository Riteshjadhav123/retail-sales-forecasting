import pytest
import numpy as np
import pandas as pd
from src.forecasting.probabilistic import ProbabilisticForecaster

def test_probabilistic_forecaster():
    feature_cols = ["f1", "f2"]
    X_train = pd.DataFrame({"f1": np.random.rand(100), "f2": np.random.rand(100)})
    y_train = np.random.rand(100) * 100.0

    X_test = pd.DataFrame({"f1": np.random.rand(20), "f2": np.random.rand(20)})
    y_test = np.random.rand(20) * 100.0

    prob = ProbabilisticForecaster(feature_cols=feature_cols)
    prob.fit(X_train, y_train)
    intervals = prob.predict_intervals(X_test)

    assert "lower_bound" in intervals
    assert "median" in intervals
    assert "upper_bound" in intervals

    # Order check
    assert (intervals["lower_bound"] <= intervals["median"]).all()
    assert (intervals["median"] <= intervals["upper_bound"]).all()

    metrics = prob.evaluate_uncertainty(y_test, intervals["lower_bound"], intervals["upper_bound"])
    assert "Coverage_Pct" in metrics
    assert "Mean_Interval_Width" in metrics
