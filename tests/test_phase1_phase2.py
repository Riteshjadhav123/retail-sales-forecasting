"""
Integration and Unit Tests for Phase 1 & Phase 2 Vaidsys Retail Sales Forecasting.
"""

import sys
import numpy as np
import pandas as pd
import pytest

sys.path.append(".")
from src.data_processing.loader import load_raw_dataset
from src.data_processing.quality import DataQualityAuditor
from src.data_processing.cleaner import DataCleaner
from src.feature_engineering.builder import FeatureBuilder
from src.evaluation.metrics import evaluate_all_metrics, accuracy_percentage
from src.evaluation.validator import TemporalValidator
from src.forecasting.horizons import MultiHorizonEvaluator
from src.forecasting.error_analysis import ErrorAnalyzer
from src.inventory.engine import InventoryEngine

def test_data_processing_and_quality():
    raw_df = load_raw_dataset()
    assert len(raw_df) > 0, "Raw dataset should not be empty."

    auditor = DataQualityAuditor(raw_df)
    report = auditor.audit()
    assert report["total_records"] == len(raw_df)
    assert "quality_status" in report

    cleaner = DataCleaner(raw_df)
    clean_df = cleaner.clean()
    assert len(clean_df) > 0
    assert "Sales_Clamped" in clean_df.columns

def test_feature_engineering_and_leakage():
    sample_data = {
        "Order Date": pd.date_range("2023-01-01", periods=100, freq="D"),
        "Sales": np.random.uniform(10, 100, 100),
        "Quantity": np.random.randint(1, 10, 100),
        "Discount": np.random.uniform(0, 0.2, 100),
        "series_id": ["SERIES_A"] * 100
    }
    df = pd.DataFrame(sample_data)

    builder = FeatureBuilder(df)
    featured_df = builder.build_features()

    assert "lag_1" in featured_df.columns
    assert "rolling_mean_7" in featured_df.columns
    assert "short_term_trend" in featured_df.columns

    validator = TemporalValidator(date_col="Order Date")
    train_df, val_df, test_df = validator.chronological_split(featured_df)
    assert len(train_df) + len(val_df) + len(test_df) == len(featured_df)

def test_evaluation_metrics_and_horizons():
    y_true = np.array([100.0, 150.0, 200.0, 250.0])
    y_pred = np.array([110.0, 140.0, 210.0, 240.0])

    metrics = evaluate_all_metrics(y_true, y_pred)
    assert "MAE" in metrics
    assert "RMSE" in metrics
    assert "WAPE" in metrics
    assert "Accuracy_Pct" in metrics

    mh = MultiHorizonEvaluator(horizons=[2, 4])
    results = mh.evaluate_horizons(y_true, y_pred)
    assert "2_days" in results
    assert "4_days" in results

def test_error_analysis_and_inventory_engine():
    df = pd.DataFrame({
        "Order Date": pd.date_range("2023-01-01", periods=50, freq="D"),
        "Product ID": ["SKU_1"] * 25 + ["SKU_2"] * 25
    })
    y_true = np.random.uniform(50, 200, 50)
    y_pred = np.random.uniform(50, 200, 50)

    analyzer = ErrorAnalyzer(df, y_true, y_pred)
    summary = analyzer.analyze()
    assert "overall_mae" in summary
    assert "volume_segmentation" in summary

    inv = InventoryEngine(service_level=0.95, lead_time_days=7.0)
    params = inv.compute_inventory_parameters(forecast_daily_demand=100.0, demand_std_dev=20.0)
    assert params["safety_stock"] > 0
    assert params["reorder_point"] > params["safety_stock"]
    assert params["economic_order_quantity"] > 0
