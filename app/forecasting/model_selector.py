"""
RetailMind-X Adaptive Model Router & Selector Engine.
Analyzes series demand dynamics (Intermittency, Volatility, Seasonality, Trend, Volume)
and dynamically routes each time-series to its optimal forecasting architecture.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from app.core.logging import get_logger

logger = get_logger("adaptive_router")

class AdaptiveModelRouter:
    """
    Self-Adaptive Model Router for RetailMind-X.
    Analyzes series demand dynamics (Intermittency, Volatility, Seasonality, Trend, Volume)
    and dynamically routes each time-series to its optimal forecasting architecture.
    """

    def __init__(self, target_col: str = "Sales", date_col: str = "Order Date"):
        self.target_col = target_col
        self.date_col = date_col

    def analyze_series_characteristics(self, series: pd.Series) -> Dict[str, float]:
        """Calculates quantitative demand characteristics for a given time-series."""
        vals = series.values.astype(float)
        n_obs = len(vals)
        non_zero_vals = vals[vals > 0]
        n_non_zero = len(non_zero_vals)

        # 1. Intermittency: Average Demand Interval (ADI)
        adi = (n_obs / n_non_zero) if n_non_zero > 0 else 999.0

        # 2. Volatility: Coefficient of Variation (CV)
        mean_val = np.mean(vals) if n_obs > 0 else 0.0
        std_val = np.std(vals) if n_obs > 0 else 0.0
        cv = (std_val / mean_val) if mean_val > 0 else 0.0

        # 3. Seasonality Autocorrelation at lag 7
        if n_obs >= 14:
            s_series = pd.Series(vals)
            autocorr_7 = float(s_series.autocorr(lag=7))
            if np.isnan(autocorr_7):
                autocorr_7 = 0.0
        else:
            autocorr_7 = 0.0

        # 4. Trend ratio (last 7 vs last 28)
        if n_obs >= 28:
            mean_7 = np.mean(vals[-7:])
            mean_28 = np.mean(vals[-28:])
            trend_ratio = (mean_7 / mean_28) if mean_28 > 0 else 1.0
        else:
            trend_ratio = 1.0

        return {
            "n_obs": float(n_obs),
            "adi": round(adi, 4),
            "cv": round(cv, 4),
            "autocorr_7": round(autocorr_7, 4),
            "trend_ratio": round(trend_ratio, 4)
        }

    def route_series(self, series_id: str, series_df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """
        Determines optimal model routing for a specific time-series.
        Returns selected model name and diagnostic characteristics.
        """
        chars = self.analyze_series_characteristics(series_df[self.target_col])
        n_obs = chars["n_obs"]
        adi = chars["adi"]
        cv = chars["cv"]
        autocorr_7 = chars["autocorr_7"]

        # Routing Logic
        if n_obs < 45:
            selected_model = "MovingAverage"
            rationale = "Short history (< 45 days). Routed to Moving Average to prevent overfitting."
        elif adi > 1.32 or cv > 1.2:
            selected_model = "LightGBM"
            rationale = "Intermittent/Lumpy demand profile (ADI > 1.32 or high CV). Routed to LightGBM Gradient Boosting."
        elif autocorr_7 > 0.35:
            selected_model = "SeasonalNaive"
            rationale = "Strong 7-day weekly seasonality (Autocorr > 0.35). Routed to Seasonal Naive / Holt-Winters."
        elif cv > 0.50:
            selected_model = "XGBoost"
            rationale = "Volatile demand profile. Routed to XGBoost with rolling time-series features."
        else:
            selected_model = "LinearRegression"
            rationale = "Smooth, continuous demand profile. Routed to Ridge Linear Regression."

        chars["selected_model"] = selected_model
        chars["rationale"] = rationale
        logger.info(f"Series '{series_id}' routed to '{selected_model}'. Rationale: {rationale}")
        return selected_model, chars

    def route_all_series(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Routes all series in dataset and returns routing map."""
        routing_map = {}
        for series_id, group in df.groupby("series_id"):
            model_name, diag = self.route_series(series_id, group)
            routing_map[series_id] = diag
        return routing_map
