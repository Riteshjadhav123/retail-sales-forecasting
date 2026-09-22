import pytest
import numpy as np
import pandas as pd
from src.forecasting.router import AdaptiveModelRouter

def test_adaptive_model_router():
    dates = pd.date_range("2021-01-01", periods=100, freq="D")
    
    # Series 1: Smooth continuous
    df1 = pd.DataFrame({"Order Date": dates, "Sales": np.linspace(10, 100, 100)})
    
    # Series 2: Intermittent zeros
    df2 = pd.DataFrame({"Order Date": dates, "Sales": [0.0] * 80 + [50.0] * 20})

    router = AdaptiveModelRouter()
    model1, diag1 = router.route_series("smooth_series", df1)
    model2, diag2 = router.route_series("intermittent_series", df2)

    assert isinstance(model1, str)
    assert isinstance(model2, str)
    assert diag2["adi"] > 1.0
