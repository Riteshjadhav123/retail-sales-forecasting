"""
RetailMind-X: Statistical Significance & Hypothesis Testing Module
Performs paired t-tests, Wilcoxon signed-rank tests, Cohen's d effect size, and 95% CIs across baseline and candidate models.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from scipy import stats

sys.path.append(".")
from src.utils.logger import get_logger
from src.forecasting.validation import TemporalValidator
from src.forecasting.baselines import BaselineForecaster
from src.forecasting.ml_models import MLForecaster

logger = get_logger("stat_test")

def run_statistical_tests():
    logger.info("Starting Statistical Significance Tests for RetailMind-X models...")
    
    featured_df = pd.read_parquet("data/processed/featured_sales.parquet")
    demand_df = pd.read_parquet("data/processed/demand_recovered.parquet")
    
    validator = TemporalValidator(date_col="Order Date")
    train_c, val_c, test_c = validator.chronological_split(featured_df)
    train_d, val_d, test_d = validator.chronological_split(demand_df)
    
    y_true = test_c["Sales"].values
    
    # 1. Baseline Predictions (Naive)
    base = BaselineForecaster(target_col="Sales")
    preds_naive = base.predict_naive(test_c, train_c)
    err_naive_abs = np.abs(y_true - preds_naive)
    
    # 2. Linear Regression / Ridge Model Predictions
    feature_cols = [
        "day", "day_of_week", "week", "month", "quarter", "year", "is_weekend",
        "sin_month", "cos_month", "sin_day_of_week", "cos_day_of_week",
        "lag_1", "lag_7", "lag_14", "lag_28",
        "rolling_mean_7", "rolling_mean_14", "rolling_mean_28",
        "rolling_std_7", "rolling_std_28",
        "short_term_trend", "medium_term_trend", "demand_volatility"
    ]
    ml_ridge = MLForecaster(feature_cols=feature_cols, target_col="Sales")
    ml_ridge.fit_ridge(train_c, train_c["Sales"].values)
    preds_ridge = ml_ridge.predict("LinearRegression", test_c)
    err_ridge_abs = np.abs(y_true - preds_ridge)
    
    # 3. LightGBM + Feature Engineering (Scenario 2 - Target: Sales)
    ml_lgb_fe = MLForecaster(feature_cols=feature_cols, target_col="Sales")
    ml_lgb_fe.fit_lightgbm(train_c, train_c["Sales"].values)
    preds_lgb_fe = ml_lgb_fe.predict("LightGBM", test_c)
    err_lgb_fe_abs = np.abs(y_true - preds_lgb_fe)
    
    # 4. LightGBM + Demand Recovery (Scenario 3 - Target: reconstructed_demand)
    ml_lgb_rec = MLForecaster(feature_cols=feature_cols, target_col="reconstructed_demand")
    ml_lgb_rec.fit_lightgbm(train_d, train_d["reconstructed_demand"].values)
    preds_lgb_rec = ml_lgb_rec.predict("LightGBM", test_d)
    err_lgb_rec_abs = np.abs(y_true - preds_lgb_rec)
    
    # Hypothesis Test 1: LightGBM (FE) vs Naive Baseline (MAE)
    diff_naive = err_naive_abs - err_lgb_fe_abs
    ttest_naive = stats.ttest_rel(err_naive_abs, err_lgb_fe_abs)
    wilc_naive = stats.wilcoxon(err_naive_abs, err_lgb_fe_abs)
    d_naive = np.mean(diff_naive) / (np.std(diff_naive, ddof=1) + 1e-8)
    ci_low_naive, ci_high_naive = stats.t.interval(
        0.95, len(diff_naive) - 1,
        loc=np.mean(diff_naive),
        scale=stats.sem(diff_naive)
    )
    
    # Hypothesis Test 2: LightGBM (FE) vs Ridge (MAE)
    diff_ridge = err_ridge_abs - err_lgb_fe_abs
    ttest_ridge = stats.ttest_rel(err_ridge_abs, err_lgb_fe_abs)
    wilc_ridge = stats.wilcoxon(err_ridge_abs, err_lgb_fe_abs)
    d_ridge = np.mean(diff_ridge) / (np.std(diff_ridge, ddof=1) + 1e-8)
    ci_low_ridge, ci_high_ridge = stats.t.interval(
        0.95, len(diff_ridge) - 1,
        loc=np.mean(diff_ridge),
        scale=stats.sem(diff_ridge)
    )
    
    stat_summary = {
        "dataset_test_size": int(len(y_true)),
        "baseline_naive_mae": float(np.mean(err_naive_abs)),
        "ridge_mae": float(np.mean(err_ridge_abs)),
        "lightgbm_fe_mae": float(np.mean(err_lgb_fe_abs)),
        "lightgbm_demand_rec_mae": float(np.mean(err_lgb_rec_abs)),
        "lightgbm_fe_vs_naive": {
            "mean_mae_reduction": float(np.mean(diff_naive)),
            "pct_mae_reduction": float((np.mean(err_naive_abs) - np.mean(err_lgb_fe_abs)) / np.mean(err_naive_abs) * 100),
            "paired_ttest_statistic": float(ttest_naive.statistic),
            "paired_ttest_pvalue": float(ttest_naive.pvalue),
            "wilcoxon_statistic": float(wilc_naive.statistic),
            "wilcoxon_pvalue": float(wilc_naive.pvalue),
            "cohens_d": float(d_naive),
            "ci_95_mae_reduction": [float(ci_low_naive), float(ci_high_naive)],
            "statistically_significant_p001": bool(ttest_naive.pvalue < 0.001)
        },
        "lightgbm_fe_vs_ridge": {
            "mean_mae_reduction": float(np.mean(diff_ridge)),
            "pct_mae_reduction": float((np.mean(err_ridge_abs) - np.mean(err_lgb_fe_abs)) / np.mean(err_ridge_abs) * 100),
            "paired_ttest_statistic": float(ttest_ridge.statistic),
            "paired_ttest_pvalue": float(ttest_ridge.pvalue),
            "wilcoxon_statistic": float(wilc_ridge.statistic),
            "wilcoxon_pvalue": float(wilc_ridge.pvalue),
            "cohens_d": float(d_ridge),
            "ci_95_mae_reduction": [float(ci_low_ridge), float(ci_high_ridge)],
            "statistically_significant_p001": bool(ttest_ridge.pvalue < 0.001)
        }
    }
    
    os.makedirs("reports/tables", exist_ok=True)
    with open("reports/tables/statistical_tests.json", "w") as f:
        json.dump(stat_summary, f, indent=2)
        
    md_content = f"""# RetailMind-X Statistical Significance & Hypothesis Testing

**Test Sample Size ($N$):** {stat_summary['dataset_test_size']} evaluation windows

## Model Performance Benchmarks
- **Naive Baseline MAE:** ${stat_summary['baseline_naive_mae']:.2f}$
- **Ridge Regression MAE:** ${stat_summary['ridge_mae']:.2f}$
- **LightGBM + Feature Engineering MAE:** ${stat_summary['lightgbm_fe_mae']:.2f}$
- **LightGBM + Demand Recovery MAE:** ${stat_summary['lightgbm_demand_rec_mae']:.2f}$

---

## 1. LightGBM (FE) vs. Naive Baseline
- **Mean MAE Reduction:** ${stat_summary['lightgbm_fe_vs_naive']['mean_mae_reduction']:.2f}$ ({stat_summary['lightgbm_fe_vs_naive']['pct_mae_reduction']:.2f}% error reduction)
- **95% Confidence Interval:** [${stat_summary['lightgbm_fe_vs_naive']['ci_95_mae_reduction'][0]:.2f}$, ${stat_summary['lightgbm_fe_vs_naive']['ci_95_mae_reduction'][1]:.2f}$]
- **Paired t-statistic:** ${stat_summary['lightgbm_fe_vs_naive']['paired_ttest_statistic']:.4f}$ ($p = {stat_summary['lightgbm_fe_vs_naive']['paired_ttest_pvalue']:.4e}$)
- **Wilcoxon Signed-Rank Statistic:** ${stat_summary['lightgbm_fe_vs_naive']['wilcoxon_statistic']:.1f}$ ($p = {stat_summary['lightgbm_fe_vs_naive']['wilcoxon_pvalue']:.4e}$)
- **Cohen's d Effect Size:** ${stat_summary['lightgbm_fe_vs_naive']['cohens_d']:.4f}$
- **Statistical Significance ($\alpha = 0.001$):** **{"PASS (p < 0.001)" if stat_summary['lightgbm_fe_vs_naive']['statistically_significant_p001'] else "FAIL"}**

---

## 2. LightGBM (FE) vs. Ridge Regression
- **Mean MAE Reduction:** ${stat_summary['lightgbm_fe_vs_ridge']['mean_mae_reduction']:.2f}$ ({stat_summary['lightgbm_fe_vs_ridge']['pct_mae_reduction']:.2f}% error reduction)
- **95% Confidence Interval:** [${stat_summary['lightgbm_fe_vs_ridge']['ci_95_mae_reduction'][0]:.2f}$, ${stat_summary['lightgbm_fe_vs_ridge']['ci_95_mae_reduction'][1]:.2f}$]
- **Paired t-statistic:** ${stat_summary['lightgbm_fe_vs_ridge']['paired_ttest_statistic']:.4f}$ ($p = {stat_summary['lightgbm_fe_vs_ridge']['paired_ttest_pvalue']:.4e}$)
- **Wilcoxon Signed-Rank Statistic:** ${stat_summary['lightgbm_fe_vs_ridge']['wilcoxon_statistic']:.1f}$ ($p = {stat_summary['lightgbm_fe_vs_ridge']['wilcoxon_pvalue']:.4e}$)
- **Cohen's d Effect Size:** ${stat_summary['lightgbm_fe_vs_ridge']['cohens_d']:.4f}$
- **Statistical Significance ($\alpha = 0.001$):** **{"PASS (p < 0.001)" if stat_summary['lightgbm_fe_vs_ridge']['statistically_significant_p001'] else "FAIL"}**
"""
    with open("reports/tables/statistical_tests.md", "w") as f:
        f.write(md_content)
        
    logger.info("Statistical significance testing completed successfully.")
    print(json.dumps(stat_summary, indent=2))
    return stat_summary

if __name__ == "__main__":
    run_statistical_tests()
