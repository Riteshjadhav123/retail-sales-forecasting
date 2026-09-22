"""
src/forecasting/drift_detector.py
Data Drift Detection Engine for RetailMind-X
Evaluates statistical distribution shifts between historical baseline and recent window
(mean, standard deviation, KS test p-value, zero-demand fraction).
100% session-grounded; no synthetic/fabricated numbers.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats


class DataDriftDetector:
    """
    Evaluates distribution drift across time windows in the session's clean data.
    """

    @staticmethod
    def detect_drift(
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        split_ratio: float = 0.70
    ) -> Dict[str, Any]:
        """
        Splits temporal series into Baseline (older 70%) and Current (recent 30%),
        and tests for statistical drift.
        """
        if df is None or df.empty or target_col not in df.columns or date_col not in df.columns:
            return {
                "available": False,
                "message": "Insufficient data to perform drift analysis."
            }

        data = df.sort_values(date_col).copy()
        target_series = pd.to_numeric(data[target_col], errors="coerce").dropna()

        if len(target_series) < 30:
            return {
                "available": False,
                "message": f"Requires at least 30 observations for reliable drift detection (found {len(target_series)})."
            }

        split_idx = int(len(target_series) * split_ratio)
        baseline = target_series.iloc[:split_idx].values
        recent = target_series.iloc[split_idx:].values

        if len(baseline) == 0 or len(recent) == 0:
            return {"available": False, "message": "Unable to segment baseline and recent windows."}

        # Statistical Metrics
        b_mean = float(np.mean(baseline))
        r_mean = float(np.mean(recent))
        mean_diff_pct = float(((r_mean - b_mean) / b_mean * 100.0)) if b_mean != 0 else 0.0

        b_std = float(np.std(baseline))
        r_std = float(np.std(recent))
        std_diff_pct = float(((r_std - b_std) / b_std * 100.0)) if b_std != 0 else 0.0

        b_zeros_pct = float((np.sum(baseline == 0) / len(baseline) * 100.0))
        r_zeros_pct = float((np.sum(recent == 0) / len(recent) * 100.0))

        # Two-sample Kolmogorov-Smirnov test
        ks_stat, ks_pval = stats.ks_2samp(baseline, recent)

        # Drift severity evaluation
        # p-value < 0.05 indicates different distributions
        if ks_pval < 0.01 or abs(mean_diff_pct) > 35.0:
            drift_status = "SIGNIFICANT_DRIFT"
            drift_detected = True
            action_recommendation = "Significant distribution shift detected. Retraining forecasting models on recent window is strongly advised."
        elif ks_pval < 0.05 or abs(mean_diff_pct) > 20.0:
            drift_status = "MODERATE_DRIFT"
            drift_detected = True
            action_recommendation = "Moderate drift observed. Monitor forecast errors and consider scheduled retraining."
        else:
            drift_status = "NO_DRIFT"
            drift_detected = False
            action_recommendation = "Distribution is stable. Existing model weights remain valid."

        return {
            "available": True,
            "drift_detected": drift_detected,
            "drift_status": drift_status,
            "confidence_score": round(float((1.0 - ks_pval) * 100.0), 1) if drift_detected else round(float(ks_pval * 100.0), 1),
            "baseline_window": {
                "sample_count": len(baseline),
                "mean": round(b_mean, 2),
                "std": round(b_std, 2),
                "zero_demand_pct": round(b_zeros_pct, 1)
            },
            "recent_window": {
                "sample_count": len(recent),
                "mean": round(r_mean, 2),
                "std": round(r_std, 2),
                "zero_demand_pct": round(r_zeros_pct, 1)
            },
            "differences": {
                "mean_shift_pct": round(mean_diff_pct, 1),
                "std_shift_pct": round(std_diff_pct, 1),
                "ks_statistic": round(float(ks_stat), 4),
                "ks_p_value": round(float(ks_pval), 4)
            },
            "recommendation": action_recommendation
        }
