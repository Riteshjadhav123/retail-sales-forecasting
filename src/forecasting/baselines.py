import numpy as np
import pandas as pd
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger("baseline_forecasting")

class BaselineForecaster:
    """Mandatory Research Baselines for Time-Series Demand Forecasting."""

    def __init__(self, target_col: str = "Sales"):
        self.target_col = target_col

    def predict_naive(self, test_df: pd.DataFrame, train_df: pd.DataFrame) -> np.ndarray:
        """Naive Forecast: Predicts last observed value from train_df per series_id."""
        last_obs = train_df.groupby("series_id")[self.target_col].last().to_dict()
        preds = test_df["series_id"].map(last_obs).fillna(0.0).values
        return preds

    def predict_seasonal_naive(self, test_df: pd.DataFrame, train_df: pd.DataFrame, season_lag: int = 7) -> np.ndarray:
        """Seasonal Naive: Predicts value from season_lag days prior."""
        snaive_obs = train_df.groupby("series_id")[self.target_col].apply(
            lambda x: x.iloc[-season_lag] if len(x) >= season_lag else (x.iloc[-1] if len(x) > 0 else 0.0)
        ).to_dict()
        preds = test_df["series_id"].map(snaive_obs).fillna(0.0).values
        return preds

    def predict_moving_average(self, test_df: pd.DataFrame, train_df: pd.DataFrame, window: int = 7) -> np.ndarray:
        """Moving Average Forecast: Predicts trailing 7-day mean from train_df per series_id."""
        ma_obs = train_df.groupby("series_id")[self.target_col].apply(lambda x: x.tail(window).mean()).to_dict()
        preds = test_df["series_id"].map(ma_obs).fillna(0.0).values
        return preds

    def predict_simple_statistical(self, test_df: pd.DataFrame, train_df: pd.DataFrame, alpha: float = 0.3) -> np.ndarray:
        """Simple Exponential Smoothing (SES) Baseline."""
        ses_obs = {}
        for series_id, group in train_df.groupby("series_id"):
            vals = group[self.target_col].values
            if len(vals) == 0:
                ses_obs[series_id] = 0.0
                continue
            s = vals[0]
            for v in vals[1:]:
                s = alpha * v + (1 - alpha) * s
            ses_obs[series_id] = s
        preds = test_df["series_id"].map(ses_obs).fillna(0.0).values
        return preds
