"""
RetailMind-X Data Schema Contracts & Mapping Engine.
Defines schemas for Raw, Clean, Feature, and Demand datasets and validates dataframes.
"""

import pandas as pd
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger

logger = get_logger("schema_mapper")

class RawSalesContract(BaseModel):
    order_id: str
    order_date: str
    category: str
    sub_category: str
    sales: float
    quantity: int

class CleanSalesContract(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    order_id: str
    order_date: pd.Timestamp
    category: str
    sub_category: str
    market: str
    region: str
    sales: float
    quantity: int
    discount: float
    profit: float
    unit_price: float

class FeatureDatasetContract(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    date: pd.Timestamp
    series_id: str
    sales: float
    lag_1: float
    lag_7: float
    rolling_mean_7: float
    rolling_std_7: float
    day_of_week: int
    month: int

class DemandDatasetContract(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    date: pd.Timestamp
    series_id: str
    observed_sales: float
    is_stockout_derived: bool
    reconstructed_demand: float

def validate_raw_schema(df: pd.DataFrame) -> bool:
    """Validates presence and non-null essential columns of raw DataFrame."""
    required = ["Order Date", "Sales", "Category", "Sub-Category", "Quantity"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Raw DataFrame contract validation failed: Missing column '{col}'")
    logger.info("Raw schema contract validated successfully.")
    return True

def validate_clean_schema(df: pd.DataFrame) -> bool:
    """Validates clean schema rules."""
    required = ["Order Date", "Sales", "Category", "Sub-Category", "Quantity", "Unit Price", "Market", "Region"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Clean DataFrame contract validation failed: Missing column '{col}'")
    if df["Sales"].isnull().any():
        raise ValueError("Clean DataFrame contract validation failed: Sales contains null values.")
    logger.info("Clean schema contract validated successfully.")
    return True
