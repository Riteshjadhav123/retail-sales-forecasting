"""
Evaluation Metrics Suite for Vaidsys Retail Sales Forecasting.
Calculates MAE, RMSE, MAPE, WAPE, R2, and Forecasting Accuracy Percentage.
"""

import numpy as np
from typing import Dict

def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculates Mean Absolute Error (MAE)."""
    return float(np.mean(np.abs(y_true - y_pred)))

def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculates Root Mean Squared Error (RMSE)."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def mean_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-5) -> float:
    """Calculates Mean Absolute Percentage Error (MAPE)."""
    return float(np.mean(np.abs((y_true - y_pred) / (y_true + epsilon))) * 100.0)

def weighted_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-5) -> float:
    """Calculates Weighted Absolute Percentage Error (WAPE)."""
    return float(np.sum(np.abs(y_true - y_pred)) / (np.sum(y_true) + epsilon))

def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculates Coefficient of Determination (R2)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1.0 - (ss_res / ss_tot))

def accuracy_percentage(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculates Forecasting Accuracy Percentage (Vaidsys Metric Target: >=90%).
    Formulated as 100% - WAPE%.
    """
    wape = weighted_absolute_percentage_error(y_true, y_pred)
    acc = max(0.0, 100.0 * (1.0 - wape))
    return float(acc)

def evaluate_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes comprehensive evaluation metrics dictionary."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    y_pred = np.maximum(0.0, y_pred)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    wape = weighted_absolute_percentage_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    acc = accuracy_percentage(y_true, y_pred)

    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "WAPE": round(wape, 4),
        "MAPE": round(mape, 4),
        "R2": round(r2, 4),
        "Accuracy_Pct": round(acc, 2)
    }
