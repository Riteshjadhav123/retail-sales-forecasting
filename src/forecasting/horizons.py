"""
Multi-Horizon Forecasting Module for Vaidsys Retail Sales Forecasting.
Evaluates forecasting performance across 7-day, 14-day, and 30-day forecast horizons.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.utils.logger import get_logger
from src.evaluation.metrics import evaluate_all_metrics

logger = get_logger("multi_horizon")

class MultiHorizonEvaluator:
    """Multi-Horizon Forecasting Evaluator Engine."""

    def __init__(self, horizons: List[int] = [7, 14, 30]):
        self.horizons = horizons

    def evaluate_horizons(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """Evaluates metrics across specified forecast window horizons."""
        results = {}
        total_len = len(y_true)

        for h in self.horizons:
            if h <= total_len:
                h_true = y_true[:h]
                h_pred = y_pred[:h]
            else:
                h_true = y_true
                h_pred = y_pred

            metrics = evaluate_all_metrics(h_true, h_pred)
            results[f"{h}_days"] = metrics
            logger.info(f"Horizon {h}-Days Performance -> MAE: ${metrics['MAE']:.2f}, WAPE: {metrics['WAPE']:.4f}, Accuracy: {metrics['Accuracy_Pct']:.2f}%.")

        return results
