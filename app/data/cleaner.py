"""
RetailMind-X Data Cleaning & Preprocessing Engine.
Handles date parsing, chronological sorting, missing value imputation, IQR outlier clamping,
series aggregation, and unit price derivation with zero data leakage.
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from app.core.logging import get_logger
from app.data.schema_mapper import validate_clean_schema

logger = get_logger("data_cleaner")

class DataCleaner:
    """Robust data preprocessing and cleaning engine for retail sales data."""

    def __init__(self, raw_df: Optional[pd.DataFrame] = None, date_col: str = "Order Date", sales_col: str = "Sales"):
        self.df = raw_df.copy() if raw_df is not None else None
        self.date_col = date_col
        self.sales_col = sales_col
        self.audit_log = []

    def log_action(self, action: str, details: str):
        """Records audit log entry for data cleaning actions."""
        entry = f"[{action}] {details}"
        self.audit_log.append(entry)
        logger.info(entry)

    def parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parses date columns flexibly with fallback handling."""
        df = df.copy()
        for col in [self.date_col, "Ship Date"]:
            if col in df.columns:
                before_nulls = df[col].isnull().sum()
                df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
                after_nulls = df[col].isnull().sum()
                new_nulls = after_nulls - before_nulls
                self.log_action(
                    "DATE_PARSING",
                    f"Parsed column '{col}' into datetime64[ns]. Invalid dates converted to NaT: {new_nulls} rows."
                )
        return df

    def clean_numerics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans numerical columns, clamps outliers, and computes Unit Price."""
        df = df.copy()
        numeric_cols = ["Sales", "Quantity", "Discount", "Profit"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # Handle negative sales (clip at 0.0)
        if "Sales" in df.columns:
            neg_sales = (df["Sales"] < 0).sum()
            if neg_sales > 0:
                df["Sales"] = df["Sales"].clip(lower=0.0)
                self.log_action("NUMERIC_CLEANING", f"Clipped {neg_sales} negative sales values to 0.0.")

            # IQR Clamping
            q1 = df["Sales"].quantile(0.25)
            q3 = df["Sales"].quantile(0.75)
            iqr = q3 - q1
            upper_bound = q3 + 3.0 * iqr
            df["Sales_Clamped"] = np.minimum(df["Sales"], upper_bound)
        elif self.sales_col in df.columns:
            df["Sales_Clamped"] = np.maximum(0.0, df[self.sales_col])
        else:
            df["Sales_Clamped"] = 0.0

        # Compute Unit Price = Sales / Quantity
        if "Sales" in df.columns and "Quantity" in df.columns:
            qty_clean = df["Quantity"].replace(0, 1)
            df["Unit Price"] = np.round(df["Sales"] / qty_clean, 4)
            self.log_action("FEATURE_DERIVATION", "Calculated 'Unit Price' column (Sales / Quantity).")
        return df

    def handle_missing_and_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handles missing values and drops exact duplicate transaction records."""
        df = df.copy()
        
        # Drop rows missing critical dates or sales identifiers
        initial_len = len(df)
        if self.date_col in df.columns:
            df = df.dropna(subset=[self.date_col])
            date_dropped = initial_len - len(df)
            if date_dropped > 0:
                self.log_action("MISSING_VALUE", f"Dropped {date_dropped} rows with unparseable Order Date.")

        # Impute non-critical text fields
        for col in ["Postal Code", "Market", "Region", "Category", "Sub-Category"]:
            if col in df.columns:
                df[col] = df[col].fillna("Unknown")

        # Create series identifier
        if "Product ID" in df.columns and "Market" in df.columns:
            df["series_id"] = df["Market"].astype(str) + "_" + df["Product ID"].astype(str)
        elif "Product ID" in df.columns:
            df["series_id"] = df["Product ID"].astype(str)
        elif "series_id" not in df.columns:
            df["series_id"] = "DEFAULT_SERIES"

        # Deduplicate
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            df = df.drop_duplicates()
            self.log_action("DEDUPLICATION", f"Removed {dup_count} exact duplicate rows.")

        return df

    def sort_chronologically(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sorts DataFrame chronologically by date and key grouping columns."""
        df = df.copy()
        if self.date_col in df.columns:
            sort_cols = [self.date_col]
            for col in ["Market", "Region", "Category", "Sub-Category", "Product ID"]:
                if col in df.columns:
                    sort_cols.append(col)
            df = df.sort_values(by=sort_cols).reset_index(drop=True)
            self.log_action("SORTING", f"Sorted dataset chronologically by {sort_cols}.")
        return df

    def transform(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Runs complete cleaning pipeline on passed DataFrame or stored DataFrame."""
        target_df = df if df is not None else self.df
        if target_df is None:
            raise ValueError("No DataFrame provided to transform.")

        logger.info("Starting Data Cleaning Pipeline...")
        target_df = self.parse_dates(target_df)
        target_df = self.clean_numerics(target_df)
        target_df = self.handle_missing_and_duplicates(target_df)
        target_df = self.sort_chronologically(target_df)
        
        # Validation if standard columns present
        if all(c in target_df.columns for c in ["Order Date", "Sales", "Category", "Sub-Category", "Quantity", "Unit Price", "Market", "Region"]):
            validate_clean_schema(target_df)

        self.df = target_df
        logger.info(f"Data Cleaning complete. Output clean records: {len(target_df):,}")
        return target_df

    def clean(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Alias for transform() to support both calling conventions."""
        return self.transform(df)

    def save_clean_data(self, output_path: str = "data/processed/clean_sales.parquet") -> str:
        """Saves cleaned DataFrame to Parquet and CSV."""
        if self.df is None:
            raise ValueError("No cleaned DataFrame to save.")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.df.to_parquet(output_path, index=False)
        csv_path = output_path.replace(".parquet", ".csv")
        self.df.to_csv(csv_path, index=False)
        logger.info(f"Cleaned dataset saved to '{output_path}' and '{csv_path}'.")
        return output_path

    def save_processed(self, df: pd.DataFrame, parquet_path: str = "data/processed/clean_sales.parquet", csv_path: str = "data/processed/clean_sales.csv") -> Tuple[str, str]:
        """Saves clean processed dataset to Parquet and CSV."""
        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        df_export = df.copy()
        for col in df_export.select_dtypes(include=["object"]).columns:
            df_export[col] = df_export[col].astype(str)
        try:
            df_export.to_parquet(parquet_path, index=False)
        except Exception as e:
            logger.warning(f"Parquet export warning: {e}. Defaulting to CSV export.")
        df_export.to_csv(csv_path, index=False)
        self.log_action("EXPORT", f"Saved clean dataset to '{parquet_path}' and '{csv_path}'.")
        return parquet_path, csv_path
