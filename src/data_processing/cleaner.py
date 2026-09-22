"""
Data Cleaner Pipeline for Vaidsys Retail Sales Forecasting.
Handles date parsing, chronological sorting, missing value imputation, IQR outlier clamping, and series aggregation.
"""

import os
import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger("data_cleaner")

class DataCleaner:
    """Robust Data Preprocessing & Cleaning Engine."""

    def __init__(self, raw_df: pd.DataFrame, date_col: str = "Order Date"):
        self.df = raw_df.copy()
        self.date_col = date_col

    def clean(self) -> pd.DataFrame:
        """Executes full cleaning pipeline."""
        logger.info("Starting Data Cleaning Pipeline...")

        # 1. Parse Date & Chronological Sort
        self.df[self.date_col] = pd.to_datetime(self.df[self.date_col], errors="coerce")
        self.df = self.df.dropna(subset=[self.date_col]).sort_values(self.date_col).reset_index(drop=True)

        # 2. Impute Missing Values
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for c in numeric_cols:
            self.df[c] = self.df[c].fillna(0.0)

        categorical_cols = self.df.select_dtypes(include=["object"]).columns
        for c in categorical_cols:
            self.df[c] = self.df[c].fillna("Unknown")

        # 3. Create Series Identifier
        if "Product ID" in self.df.columns and "Market" in self.df.columns:
            self.df["series_id"] = self.df["Market"].astype(str) + "_" + self.df["Product ID"].astype(str)
        elif "Product ID" in self.df.columns:
            self.df["series_id"] = self.df["Product ID"].astype(str)
        else:
            self.df["series_id"] = "DEFAULT_SERIES"

        # 4. Filter Negative Sales
        if "Sales" in self.df.columns:
            self.df["Sales"] = np.maximum(0.0, self.df["Sales"])

        # 5. Outlier Clamping (IQR method)
        if "Sales" in self.df.columns:
            q1 = self.df["Sales"].quantile(0.25)
            q3 = self.df["Sales"].quantile(0.75)
            iqr = q3 - q1
            upper_bound = q3 + 3.0 * iqr
            self.df["Sales_Clamped"] = np.minimum(self.df["Sales"], upper_bound)
        else:
            self.df["Sales_Clamped"] = 0.0

        logger.info(f"Data Cleaning Completed: {len(self.df)} records prepared.")
        return self.df

    def save_clean_data(self, output_path: str = "data/processed/clean_sales.parquet") -> str:
        """Saves cleaned DataFrame to Parquet and CSV."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.df.to_parquet(output_path, index=False)
        csv_path = output_path.replace(".parquet", ".csv")
        self.df.to_csv(csv_path, index=False)
        logger.info(f"Cleaned dataset saved to '{output_path}' and '{csv_path}'.")
        return output_path
