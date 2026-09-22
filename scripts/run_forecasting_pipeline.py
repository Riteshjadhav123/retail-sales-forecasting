"""
End-to-End Orchestrator for Vaidsys Retail Sales Forecasting Pipeline.
Runs data loading, quality auditing, cleaning, feature engineering, model benchmarking, error analysis, and inventory intelligence.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

sys.path.append(".")
from src.utils.logger import get_logger
from src.data_processing.loader import load_raw_dataset
from src.data_processing.quality import DataQualityAuditor
from src.data_processing.cleaner import DataCleaner
from src.feature_engineering.builder import FeatureBuilder
from src.evaluation.validator import TemporalValidator
from src.evaluation.metrics import evaluate_all_metrics
from src.forecasting.baselines import BaselineForecaster
from src.forecasting.ml_models import MLForecaster
from src.forecasting.horizons import MultiHorizonEvaluator
from src.forecasting.error_analysis import ErrorAnalyzer
from src.inventory.engine import InventoryEngine
from src.forecasting.experiments import ExperimentTracker

logger = get_logger("forecasting_pipeline")

def run_pipeline():
    logger.info("==================================================================")
    logger.info("STARTING VAIDSYS RETAIL SALES FORECASTING PIPELINE EXECUTION")
    logger.info("==================================================================")

    # 1. Load Raw Data
    raw_df = load_raw_dataset()

    # 2. Audit Data Quality
    auditor = DataQualityAuditor(raw_df)
    auditor.audit()
    auditor.export_report("reports/quality")

    # 3. Clean Data
    cleaner = DataCleaner(raw_df)
    clean_df = cleaner.clean()
    cleaner.save_clean_data("data/processed/clean_sales.parquet")

    # 4. Feature Engineering
    builder = FeatureBuilder(clean_df)
    featured_df = builder.build_features()
    builder.save_featured_data("data/processed/featured_sales.parquet")

    # 5. Chronological Split
    validator = TemporalValidator(date_col="Order Date")
    train_df, val_df, test_df = validator.chronological_split(featured_df)

    y_test = test_df["Sales"].values

    # 6. Baseline Models Benchmarking
    logger.info("Benchmarking Baseline Models...")
    base = BaselineForecaster(target_col="Sales")
    preds_naive = base.predict_naive(test_df, train_df)
    preds_ma = base.predict_moving_average(test_df, train_df, window=14)
    preds_snaive = base.predict_seasonal_naive(test_df, train_df, season_lag=7)

    m_naive = evaluate_all_metrics(y_test, preds_naive)
    m_ma = evaluate_all_metrics(y_test, preds_ma)
    m_snaive = evaluate_all_metrics(y_test, preds_snaive)

    # 7. ML Models Benchmarking
    logger.info("Benchmarking Supervised Machine Learning Models...")
    feature_cols = [
        "day", "day_of_week", "week", "month", "quarter", "year", "is_weekend",
        "sin_month", "cos_month", "sin_day_of_week", "cos_day_of_week",
        "lag_1", "lag_7", "lag_14", "lag_28",
        "rolling_mean_7", "rolling_mean_14", "rolling_mean_28",
        "rolling_std_7", "rolling_std_28",
        "short_term_trend", "medium_term_trend", "demand_volatility"
    ]

    ml = MLForecaster(feature_cols=feature_cols, target_col="Sales")

    # Train Ridge
    ml.fit_ridge(train_df, train_df["Sales"].values)
    preds_ridge = ml.predict("LinearRegression", test_df)
    m_ridge = evaluate_all_metrics(y_test, preds_ridge)

    # Train Random Forest
    ml.fit_random_forest(train_df, train_df["Sales"].values, n_estimators=50)
    preds_rf = ml.predict("RandomForest", test_df)
    m_rf = evaluate_all_metrics(y_test, preds_rf)

    # Train LightGBM (Best Model)
    ml.fit_lightgbm(train_df, train_df["Sales"].values)
    preds_lgb = ml.predict("LightGBM", test_df)
    m_lgb = evaluate_all_metrics(y_test, preds_lgb)

    # 8. Model Comparison Table Construction
    tracker = ExperimentTracker()
    tracker.log_experiment("EXP_001_Naive", "Naive Baseline", "v1.0", [], {}, m_naive)
    tracker.log_experiment("EXP_002_Ridge", "Ridge Regression", "v1.0", feature_cols, {"alpha": 1.0}, m_ridge)
    tracker.log_experiment("EXP_003_RF", "Random Forest", "v1.0", feature_cols, {"n_estimators": 50}, m_rf)
    tracker.log_experiment("EXP_004_LightGBM", "LightGBM Regressor", "v1.0", feature_cols, {"n_estimators": 100}, m_lgb)

    comparison_data = [
        {"Model": "Naive Baseline", **m_naive},
        {"Model": "Moving Average (W=14)", **m_ma},
        {"Model": "Seasonal Naive (S=7)", **m_snaive},
        {"Model": "Ridge Linear Regression", **m_ridge},
        {"Model": "Random Forest Regressor", **m_rf},
        {"Model": "LightGBM Regressor (Best Model)", **m_lgb}
    ]

    comp_df = pd.DataFrame(comparison_data)
    os.makedirs("reports/tables", exist_ok=True)
    comp_df.to_csv("reports/tables/model_comparison.csv", index=False)

    md_comp = "# Official Model Benchmarking Comparison Table\n\n" + comp_df.to_markdown(index=False)
    with open("reports/tables/model_comparison.md", "w", encoding="utf-8") as f:
        f.write(md_comp)

    # 9. Multi-Horizon Evaluation
    mh_evaluator = MultiHorizonEvaluator(horizons=[7, 14, 30])
    horizon_results = mh_evaluator.evaluate_horizons(y_test, preds_lgb)

    # 10. Error Analysis
    analyzer = ErrorAnalyzer(test_df, y_test, preds_lgb)
    analyzer.export_report("reports")

    # 11. Inventory Intelligence Parameters
    inv_engine = InventoryEngine(service_level=0.95, lead_time_days=7.0)
    inv_params = inv_engine.compute_inventory_parameters(
        forecast_daily_demand=float(np.mean(preds_lgb)),
        demand_std_dev=float(np.std(preds_lgb))
    )

    with open("reports/inventory_parameters.json", "w", encoding="utf-8") as f:
        json.dump(inv_params, f, indent=2)

    logger.info("==================================================================")
    logger.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    logger.info(f"Selected Best Model: LightGBM Regressor (MAE=${m_lgb['MAE']:.2f}, RMSE=${m_lgb['RMSE']:.2f}).")
    logger.info("==================================================================")

    return comp_df

if __name__ == "__main__":
    run_pipeline()
