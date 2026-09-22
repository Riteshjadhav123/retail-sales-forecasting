"""
RetailMind-X Probabilistic & Confidence Prediction Engine.
Provides quantile regression (p10, p50, p90) and empirical interval coverage evaluation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import HistGradientBoostingRegressor
from app.core.logging import get_logger

logger = get_logger("probabilistic_forecasting")

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except Exception:
    HAS_LIGHTGBM = False

def interval_coverage(y_true: np.ndarray, lower_bound: np.ndarray, upper_bound: np.ndarray) -> float:
    """Computes Empirical Prediction Interval Coverage Rate (PICR)."""
    covered = (y_true >= lower_bound) & (y_true <= upper_bound)
    return float(np.mean(covered) * 100.0)

def mean_interval_width(lower_bound: np.ndarray, upper_bound: np.ndarray) -> float:
    """Computes Mean Prediction Interval Width (MPIW)."""
    return float(np.mean(upper_bound - lower_bound))

class ProbabilisticForecaster:
    """Probabilistic Uncertainty-Aware Demand Forecasting Engine."""

    def __init__(self, feature_cols: List[str], quantiles: List[float] = [0.10, 0.50, 0.90], random_state: int = 42):
        self.feature_cols = feature_cols
        self.quantiles = sorted(quantiles)
        self.random_state = random_state
        self.models: Dict[float, Any] = {}

    def fit(self, X_train: pd.DataFrame, y_train: np.ndarray):
        """Fits Quantile Regressors for each target quantile."""
        X_mat = X_train[self.feature_cols].fillna(0.0)
        for q in self.quantiles:
            if HAS_LIGHTGBM:
                try:
                    model = lgb.LGBMRegressor(
                        objective="quantile",
                        alpha=q,
                        n_estimators=80,
                        max_depth=6,
                        learning_rate=0.05,
                        random_state=self.random_state,
                        n_jobs=-1,
                        verbose=-1
                    )
                    model.fit(X_mat, y_train)
                    self.models[q] = model
                    logger.info(f"Trained LightGBM Quantile Regressor for quantile p={q:.2f}.")
                    continue
                except Exception as e:
                    logger.warning(f"LightGBM Quantile Regressor exception: {e}. Falling back to HistGradientBoostingRegressor.")

            # Fallback Scikit-Learn Quantile Model
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=q,
                max_iter=80,
                max_depth=6,
                learning_rate=0.05,
                random_state=self.random_state
            )
            model.fit(X_mat, y_train)
            self.models[q] = model
            logger.info(f"Trained HistGradientBoosting Quantile Regressor (Fallback) for quantile p={q:.2f}.")

    def predict_intervals(self, X_test: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Generates lower (p10), median (p50), and upper (p90) prediction intervals."""
        X_mat = X_test[self.feature_cols].fillna(0.0)
        predictions = {}
        for q, model in self.models.items():
            key = f"p{int(q*100)}"
            preds = model.predict(X_mat)
            predictions[key] = np.maximum(0.0, preds)

        p10 = predictions.get("p10", np.zeros(len(X_test)))
        p50 = predictions.get("p50", np.zeros(len(X_test)))
        p90 = predictions.get("p90", np.zeros(len(X_test)))

        p50_adj = np.maximum(p10, p50)
        p90_adj = np.maximum(p50_adj, p90)

        return {
            "lower_bound": p10,
            "median": p50_adj,
            "upper_bound": p90_adj
        }

    def evaluate_uncertainty(self, y_true: np.ndarray, lower_bound: np.ndarray, upper_bound: np.ndarray, target_alpha: float = 0.80) -> Dict[str, float]:
        """Evaluates empirical coverage, width, and calibration error."""
        cov = interval_coverage(y_true, lower_bound, upper_bound)
        width = mean_interval_width(lower_bound, upper_bound)
        calibration_error = abs(cov - (target_alpha * 100.0))

        logger.info(f"Probabilistic Uncertainty Metrics: Coverage={cov:.2f}% (Target: {target_alpha*100:.0f}%), Mean Width={width:.2f}, Calibration Error={calibration_error:.2f}%")
        return {
            "Coverage_Pct": round(cov, 2),
            "Mean_Interval_Width": round(width, 2),
            "Calibration_Error": round(calibration_error, 2)
        }
