import numpy as np
from typing import Dict, Any, Optional

def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes Mean Absolute Error (MAE)."""
    return float(np.mean(np.abs(y_true - y_pred)))

def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes Root Mean Squared Error (RMSE)."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def weighted_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes Weighted Absolute Percentage Error (WAPE)."""
    denom = np.sum(np.abs(y_true))
    if denom == 0:
        return 0.0
    return float(np.sum(np.abs(y_true - y_pred)) / denom)

def mean_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-5) -> float:
    """Computes Mean Absolute Percentage Error (MAPE) safely."""
    denom = np.maximum(np.abs(y_true), eps)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)

def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes R-squared (Coefficient of Determination)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return float(1.0 - (ss_res / ss_tot))

def interval_coverage(y_true: np.ndarray, lower_bound: np.ndarray, upper_bound: np.ndarray) -> float:
    """Computes Empirical Prediction Interval Coverage Rate (PICR)."""
    covered = (y_true >= lower_bound) & (y_true <= upper_bound)
    return float(np.mean(covered) * 100.0)

def mean_interval_width(lower_bound: np.ndarray, upper_bound: np.ndarray) -> float:
    """Computes Mean Prediction Interval Width (MPIW)."""
    return float(np.mean(upper_bound - lower_bound))

def evaluate_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    lower_bound: Optional[np.ndarray] = None,
    upper_bound: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """Computes full suite of point and probabilistic forecast metrics."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    metrics = {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": root_mean_squared_error(y_true, y_pred),
        "WAPE": weighted_absolute_percentage_error(y_true, y_pred),
        "MAPE": mean_absolute_percentage_error(y_true, y_pred),
        "R2": r2_score(y_true, y_pred)
    }

    if lower_bound is not None and upper_bound is not None:
        lb = np.asarray(lower_bound, dtype=float)
        ub = np.asarray(upper_bound, dtype=float)
        metrics["Coverage_Pct"] = interval_coverage(y_true, lb, ub)
        metrics["Mean_Interval_Width"] = mean_interval_width(lb, ub)

    return metrics
