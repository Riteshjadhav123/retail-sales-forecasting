import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.utils.logger import get_logger
from src.utils.metrics import evaluate_all_metrics
from src.forecasting.baselines import BaselineForecaster
from src.forecasting.ml_models import MLForecaster
from src.forecasting.validation import TemporalValidator
from src.forecasting.router import AdaptiveModelRouter
from src.forecasting.probabilistic import ProbabilisticForecaster
from src.forecasting.registry import ModelRegistry
from src.forecasting.experiments import ExperimentTracker

logger = get_logger("ablation_study")

class AblationStudyEngine:
    """
    Executes Systematic 5-Step Ablation Experiments for RetailMind-X:
    1. Scenario 1: Baseline (Naive)
    2. Scenario 2: Baseline + Feature Engineering (LightGBM on engineered features)
    3. Scenario 3: Baseline + Demand Recovery (LightGBM on unconstrained demand)
    4. Scenario 4: Adaptive Router (Dynamic algorithm routing per series)
    5. Scenario 5: Full RetailMind-X (Demand Recovery + FE + Adaptive Router + Probabilistic Quantiles)
    """

    def __init__(self, raw_clean_df: pd.DataFrame, featured_df: pd.DataFrame, demand_df: pd.DataFrame):
        self.raw_clean_df = raw_clean_df
        self.featured_df = featured_df
        self.demand_df = demand_df
        self.validator = TemporalValidator(date_col="Order Date")
        self.tracker = ExperimentTracker()
        self.registry = ModelRegistry()

        self.feature_cols = [
            "day", "day_of_week", "week", "month", "quarter", "year", "is_weekend",
            "sin_month", "cos_month", "sin_day_of_week", "cos_day_of_week",
            "lag_1", "lag_7", "lag_14", "lag_28",
            "rolling_mean_7", "rolling_mean_14", "rolling_mean_28",
            "rolling_std_7", "rolling_std_28",
            "short_term_trend", "medium_term_trend", "demand_volatility"
        ]

    def run_ablation_study(self, output_dir: str = "reports/tables") -> pd.DataFrame:
        """Executes all 5 ablation scenarios and returns metrics comparison DataFrame."""
        os.makedirs(output_dir, exist_ok=True)
        results = []

        logger.info("Executing Scenario 1: Baseline (Naive Forecast)...")
        train_c, val_c, test_c = self.validator.chronological_split(self.featured_df)
        base = BaselineForecaster(target_col="Sales")
        y_test = test_c["Sales"].values
        preds_s1 = base.predict_naive(test_c, train_c)
        m1 = evaluate_all_metrics(y_test, preds_s1)
        m1["Scenario"] = "1. Baseline (Naive)"
        results.append(m1)
        self.tracker.log_experiment("EXP_001_Baseline", "Naive", "v1.0", [], {}, m1)

        logger.info("Executing Scenario 2: Baseline + Feature Engineering (LightGBM)...")
        ml_s2 = MLForecaster(feature_cols=self.feature_cols, target_col="Sales")
        ml_s2.fit_lightgbm(train_c, train_c["Sales"].values)
        preds_s2 = ml_s2.predict("LightGBM", test_c)
        m2 = evaluate_all_metrics(y_test, preds_s2)
        m2["Scenario"] = "2. Baseline + Feature Engineering"
        results.append(m2)
        self.tracker.log_experiment("EXP_002_FE_LightGBM", "LightGBM", "v1.0", self.feature_cols, {"n_estimators": 100}, m2)
        self.registry.register_model("LightGBM_FE", "1.0", self.feature_cols, m2, {"n_estimators": 100}, ml_s2.models["LightGBM"])

        logger.info("Executing Scenario 3: Baseline + Demand Recovery (Unconstrained Demand)...")
        train_d, val_d, test_d = self.validator.chronological_split(self.demand_df)
        ml_s3 = MLForecaster(feature_cols=self.feature_cols, target_col="reconstructed_demand")
        ml_s3.fit_lightgbm(train_d, train_d["reconstructed_demand"].values)
        preds_s3 = ml_s3.predict("LightGBM", test_d)
        m3 = evaluate_all_metrics(test_d["Sales"].values, preds_s3)
        m3["Scenario"] = "3. Baseline + Demand Recovery"
        results.append(m3)
        self.tracker.log_experiment("EXP_003_DemandRecovery", "LightGBM_DemandRecovered", "v1.0", self.feature_cols, {}, m3)

        logger.info("Executing Scenario 4: Adaptive Model Router...")
        router = AdaptiveModelRouter(target_col="reconstructed_demand")
        route_map = router.route_all_series(train_d)
        
        # Batch Vectorized Predictions per Model Choice
        preds_s4 = np.zeros(len(test_d))
        lgb_preds = ml_s3.predict("LightGBM", test_d)
        ma_preds = base.predict_moving_average(test_d, train_d)

        for i, (idx, row) in enumerate(test_d.iterrows()):
            s_id = row["series_id"]
            m_choice = route_map.get(s_id, {}).get("selected_model", "LightGBM")
            if m_choice in ["SeasonalNaive", "MovingAverage"]:
                preds_s4[i] = ma_preds[i]
            else:
                preds_s4[i] = lgb_preds[i]

        m4 = evaluate_all_metrics(test_d["Sales"].values, preds_s4)
        m4["Scenario"] = "4. Adaptive Model Router"
        results.append(m4)
        self.tracker.log_experiment("EXP_004_AdaptiveRouter", "AdaptiveRouter", "v1.0", self.feature_cols, {}, m4)

        logger.info("Executing Scenario 5: Full RetailMind-X (Router + Probabilistic Forecasting)...")
        prob_forecaster = ProbabilisticForecaster(feature_cols=self.feature_cols)
        prob_forecaster.fit(train_d, train_d["reconstructed_demand"].values)
        prob_dict = prob_forecaster.predict_intervals(test_d)
        
        m5 = evaluate_all_metrics(
            test_d["Sales"].values,
            prob_dict["median"],
            lower_bound=prob_dict["lower_bound"],
            upper_bound=prob_dict["upper_bound"]
        )
        m5["Scenario"] = "5. Full RetailMind-X (Uncertainty-Aware)"
        results.append(m5)
        self.tracker.log_experiment("EXP_005_Full_RetailMindX", "Full_RetailMindX", "v1.0", self.feature_cols, {"quantiles": [0.1, 0.5, 0.9]}, m5)
        self.registry.register_model("Full_RetailMindX", "1.0", self.feature_cols, m5, {"quantiles": [0.1, 0.5, 0.9]}, prob_forecaster)

        # Output Results
        df_res = pd.DataFrame(results)
        cols_order = ["Scenario", "MAE", "RMSE", "WAPE", "MAPE", "R2", "Coverage_Pct", "Mean_Interval_Width"]
        existing_cols = [c for c in cols_order if c in df_res.columns]
        df_res = df_res[existing_cols]

        csv_path = os.path.join(output_dir, "ablation_study_results.csv")
        md_path = os.path.join(output_dir, "ablation_study_results.md")

        df_res.to_csv(csv_path, index=False)
        df_res.to_markdown(md_path, index=False)

        logger.info(f"Ablation Study completed successfully. Saved results to '{csv_path}' and '{md_path}'.")
        return df_res
