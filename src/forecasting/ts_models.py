import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from src.utils.logger import get_logger

logger = get_logger("ts_forecasting")

class TimeSeriesStatForecaster:
    """Statistical Classical Time-Series Models (ARIMA & Holt-Winters)."""

    def __init__(self, target_col: str = "Sales"):
        self.target_col = target_col

    def fit_predict_arima(self, train_series: pd.Series, horizon: int, order: tuple = (1, 1, 1)) -> np.ndarray:
        """Fits ARIMA model on single time series and forecasts horizon steps."""
        vals = train_series.values.astype(float)
        if len(vals) < 10 or np.all(vals == 0):
            return np.full(horizon, np.mean(vals) if len(vals) > 0 else 0.0)

        try:
            model = ARIMA(vals, order=order)
            fitted = model.fit()
            forecast = fitted.forecast(steps=horizon)
            return np.maximum(0.0, forecast)
        except Exception as e:
            logger.warning(f"ARIMA fitting exception: {e}. Falling back to trailing mean.")
            return np.full(horizon, np.mean(vals[-7:]) if len(vals) >= 7 else np.mean(vals))

    def fit_predict_exponential_smoothing(self, train_series: pd.Series, horizon: int, seasonal_periods: int = 7) -> np.ndarray:
        """Fits Holt-Winters Exponential Smoothing model."""
        vals = train_series.values.astype(float)
        if len(vals) < 2 * seasonal_periods or np.all(vals == 0):
            return np.full(horizon, np.mean(vals) if len(vals) > 0 else 0.0)

        try:
            model = ExponentialSmoothing(vals, trend="add", seasonal="add", seasonal_periods=seasonal_periods)
            fitted = model.fit()
            forecast = fitted.forecast(steps=horizon)
            return np.maximum(0.0, forecast)
        except Exception as e:
            logger.warning(f"ExponentialSmoothing exception: {e}. Falling back to simple average.")
            return np.full(horizon, np.mean(vals[-14:]) if len(vals) >= 14 else np.mean(vals))
