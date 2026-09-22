"""
RetailMind-X: Dataset Session Manager
Manages active dataset sessions, state transitions, schema mappings, and pipeline outputs.
Ensures zero data leakage between separate dataset uploads.
"""

import uuid
import time
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from enum import Enum
from app.core.logging import get_logger

logger = get_logger("session_manager")

class AppState(str, Enum):
    NO_DATASET = "NO_DATASET"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    PROFILING = "PROFILING"
    VALIDATING = "VALIDATING"
    DATASET_READY = "DATASET_READY"
    PROCESSING = "PROCESSING"
    ANALYZING = "ANALYZING"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    ERROR = "ERROR"

class DatasetSession:
    def __init__(self):
        self.session_id: Optional[str] = None
        self.state: AppState = AppState.NO_DATASET
        self.filename: Optional[str] = None
        self.dataset_name: Optional[str] = None
        self.file_size_bytes: int = 0
        self.upload_timestamp: Optional[str] = None
        self.raw_df: Optional[pd.DataFrame] = None
        self.clean_df: Optional[pd.DataFrame] = None
        self.featured_df: Optional[pd.DataFrame] = None
        
        # Profiling, Mapping & Semantic Target Metadata
        self.detected_schema: Dict[str, Any] = {}
        self.column_mapping: Dict[str, str] = {}
        self.quality_report: Dict[str, Any] = {}
        self.confidence_score: float = 0.0
        self.has_inventory_data: bool = False
        self.target_column: Optional[str] = None
        self.date_column: Optional[str] = None
        self.promo_column: Optional[str] = None
        self.target_type: str = "monetary" # "monetary" or "units"
        self.target_display: str = "Monetary (Sales / Revenue)"
        self.detected_frequency: str = "Daily"
        self.capability_matrix: Dict[str, Any] = {}
        self.semantic_metadata: Dict[str, Any] = {}
        self.vaidsys_target_accuracy_pct: float = 90.0
        
        # Pipeline Results
        self.models_performance: List[Dict[str, Any]] = []
        self.selected_model_name: Optional[str] = None
        self.forecast_data: Dict[str, Any] = {}
        self.forecast_results: Dict[str, Any] = {}
        self.inventory_items: List[Dict[str, Any]] = []
        self.reorder_recommendations: List[Dict[str, Any]] = []
        self.verticals_summary: List[Dict[str, Any]] = []
        self.insights: List[Dict[str, Any]] = []
        self.ablation_results: List[Dict[str, Any]] = []
        self.error_message: Optional[str] = None
        
    def create_new_session(self, filename: str, raw_df: pd.DataFrame, file_size: int) -> str:
        """Clears any existing dataset session and initializes a clean new session."""
        self.clear_session()
        self.session_id = str(uuid.uuid4())[:8]
        self.state = AppState.UPLOADED
        self.filename = filename
        self.dataset_name = filename
        self.file_size_bytes = file_size
        self.upload_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.raw_df = raw_df
        logger.info(f"Created new Dataset Session '{self.session_id}' for file '{filename}' ({len(raw_df)} rows).")
        return self.session_id

    def clear_session(self):
        """Clears all dataset state and resets application state to NO_DATASET."""
        self.session_id = None
        self.state = AppState.NO_DATASET
        self.filename = None
        self.dataset_name = None
        self.file_size_bytes = 0
        self.upload_timestamp = None
        self.raw_df = None
        self.clean_df = None
        self.featured_df = None
        self.detected_schema = {}
        self.column_mapping = {}
        self.quality_report = {}
        self.confidence_score = 0.0
        self.has_inventory_data = False
        self.target_column = None
        self.date_column = None
        self.promo_column = None
        self.target_type = "monetary"
        self.target_display = "Monetary (Sales / Revenue)"
        self.detected_frequency = "Daily"
        self.capability_matrix = {}
        self.semantic_metadata = {}
        self.models_performance = []
        self.selected_model_name = None
        self.forecast_data = {}
        self.forecast_results = {}
        self.inventory_items = []
        self.reorder_recommendations = []
        self.verticals_summary = []
        self.insights = []
        self.ablation_results = []
        self.error_message = None
        logger.info("Dataset session state completely cleared. Reset to NO_DATASET.")

    def get_summary(self) -> Dict[str, Any]:
        if self.state == AppState.NO_DATASET or self.raw_df is None:
            return {
                "state": self.state.value,
                "has_dataset": False
            }
        
        sales_col = self.column_mapping.get("Sales", self.target_column or "Sales")
        series_col = self.column_mapping.get("Product", "series_id")
        
        df = self.clean_df if self.clean_df is not None else self.raw_df
        sales_series = pd.to_numeric(df[sales_col], errors="coerce").fillna(0) if sales_col in df.columns else pd.Series([0.0])
        total_sales = float(sales_series.sum())
        skus_count = int(df[series_col].nunique()) if series_col in df.columns else int(df["series_id"].nunique()) if "series_id" in df.columns else 1
        
        # Calculate real dynamic stockout risk rate from reorder recommendations if available
        if len(self.reorder_recommendations) > 0:
            reorder_now_cnt = sum(1 for r in self.reorder_recommendations if r.get("reorder_status") == "REORDER_NOW")
            overstock_cnt = sum(1 for r in self.reorder_recommendations if r.get("reorder_status") == "OVERSTOCKED")
            tot_recs = len(self.reorder_recommendations)
            stockout_risk_rate = round((reorder_now_cnt / tot_recs) * 100, 1)
            overstock_risk_rate = round((overstock_cnt / tot_recs) * 100, 1)
        else:
            stockout_risk_rate = 0.0
            overstock_risk_rate = 0.0

        # Dynamic production model accuracy
        prod_model = next((m for m in self.models_performance if m.get("Status") == "Selected Production"), None)
        if prod_model and "Accuracy_Pct" in prod_model:
            accuracy_pct = float(prod_model["Accuracy_Pct"])
        elif prod_model and "WAPE" in prod_model:
            accuracy_pct = round(max(0.0, 100.0 * (1.0 - float(prod_model["WAPE"]))), 2)
        else:
            accuracy_pct = 0.0

        inv_label = "Actual Stock Data" if self.has_inventory_data else "Inventory data unavailable (Simulated / Assumed)"

        # Date range formatting
        date_col = self.column_mapping.get("Date", "Order Date")
        if date_col in df.columns:
            dt_series = pd.to_datetime(df[date_col], errors="coerce").dropna()
            date_range_str = f"{dt_series.min().strftime('%Y-%m-%d')} to {dt_series.max().strftime('%Y-%m-%d')}" if not dt_series.empty else "N/A"
        else:
            date_range_str = "N/A"

        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "has_dataset": True,
            "filename": self.filename,
            "file_size_bytes": self.file_size_bytes,
            "upload_timestamp": self.upload_timestamp,
            "row_count": len(self.raw_df),
            "column_count": len(self.raw_df.columns),
            "columns_available": self.raw_df.columns.tolist() if self.raw_df is not None else [],
            "column_mapping": self.column_mapping,
            "date_range": date_range_str,
            "target_column": self.target_column or sales_col,
            "target_type": self.target_type,
            "target_display": self.target_display,
            "detected_frequency": self.detected_frequency,
            "capability_matrix": self.capability_matrix,
            "semantic_metadata": self.semantic_metadata,
            "total_sales_dollar": round(total_sales, 2) if self.target_type == "monetary" else 0.0,
            "total_units": round(total_sales, 0) if self.target_type == "units" else 0,
            "total_series_count": skus_count,
            "forecast_horizon_days": 90,
            "selected_model": self.selected_model_name or "LightGBM Quantile Regressor",
            "stockout_risk_rate_pct": stockout_risk_rate,
            "overstock_risk_rate_pct": overstock_risk_rate,
            "vaidsys_target_accuracy_pct": self.vaidsys_target_accuracy_pct,
            "actual_accuracy_pct": accuracy_pct,
            "has_inventory_data": self.has_inventory_data,
            "inventory_status_label": inv_label,
            "confidence_score": self.confidence_score
        }

# Global singleton session instance
SESSION = DatasetSession()
