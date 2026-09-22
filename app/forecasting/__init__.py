"""RetailMind-X Demand Forecasting Suite."""
from app.forecasting.pipeline import DataPipelineExecutor
from app.forecasting.model_selector import AdaptiveModelRouter
from app.forecasting.model_registry import ModelRegistry
from app.forecasting.confidence import ProbabilisticForecaster, interval_coverage, mean_interval_width
from app.forecasting.diagnostics import DataDriftDetector
from app.forecasting.anomaly_detection import DemandAnomalyEngine
from app.forecasting.evaluator import (
    TemporalValidator, ErrorAnalyzer, MultiHorizonEvaluator,
    mean_absolute_error, root_mean_squared_error, weighted_absolute_percentage_error,
    mean_absolute_percentage_error, r2_score, evaluate_all_metrics
)
from app.forecasting.models import (
    BaselineForecaster, MLForecaster, DeepForecaster, TimeSeriesStatForecaster
)

__all__ = [
    "DataPipelineExecutor",
    "AdaptiveModelRouter",
    "ModelRegistry",
    "ProbabilisticForecaster",
    "interval_coverage",
    "mean_interval_width",
    "DataDriftDetector",
    "DemandAnomalyEngine",
    "TemporalValidator",
    "ErrorAnalyzer",
    "MultiHorizonEvaluator",
    "mean_absolute_error",
    "root_mean_squared_error",
    "weighted_absolute_percentage_error",
    "mean_absolute_percentage_error",
    "r2_score",
    "evaluate_all_metrics",
    "BaselineForecaster",
    "MLForecaster",
    "DeepForecaster",
    "TimeSeriesStatForecaster",
]
