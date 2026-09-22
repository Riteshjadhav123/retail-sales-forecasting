import os
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from src.utils.logger import get_logger
from src.data.contracts import validate_clean_schema

logger = get_logger("data_cleaner")

class DataCleaner:
    """Robust data preprocessing and cleaning engine for retail sales data."""

    def __init__(self, date_col: str = "Order Date", sales_col: str = "Sales"):
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
        """Cleans numerical columns and computes Unit Price."""
        df = df.copy()
        numeric_cols = ["Sales", "Quantity", "Discount", "Profit"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # Handle negative sales (clip at 0.0)
        neg_sales = (df["Sales"] < 0).sum()
        if neg_sales > 0:
            df["Sales"] = df["Sales"].clip(lower=0.0)
            self.log_action("NUMERIC_CLEANING", f"Clipped {neg_sales} negative sales values to 0.0.")

        # Compute Unit Price = Sales / Quantity
        qty_clean = df["Quantity"].replace(0, 1)
        df["Unit Price"] = np.round(df["Sales"] / qty_clean, 4)
        self.log_action("FEATURE_DERIVATION", "Calculated 'Unit Price' column (Sales / Quantity).")
        return df

    def handle_missing_and_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handles missing values and drops exact duplicate transaction records."""
        df = df.copy()
        
        # Drop rows missing critical dates or sales identifiers
        initial_len = len(df)
        df = df.dropna(subset=[self.date_col])
        date_dropped = initial_len - len(df)
        if date_dropped > 0:
            self.log_action("MISSING_VALUE", f"Dropped {date_dropped} rows with unparseable Order Date.")

        # Impute non-critical text fields
        for col in ["Postal Code", "Market", "Region", "Category", "Sub-Category"]:
            if col in df.columns:
                df[col] = df[col].fillna("Unknown")

        # Deduplicate
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            df = df.drop_duplicates()
            self.log_action("DEDUPLICATION", f"Removed {dup_count} exact duplicate rows.")

        return df

    def sort_chronologically(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sorts DataFrame chronologically by date and key grouping columns."""
        df = df.copy()
        sort_cols = [self.date_col]
        for col in ["Market", "Region", "Category", "Sub-Category", "Product ID"]:
            if col in df.columns:
                sort_cols.append(col)
        df = df.sort_values(by=sort_cols).reset_index(drop=True)
        self.log_action("SORTING", f"Sorted dataset chronologically by {sort_cols}.")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Runs complete cleaning pipeline."""
        logger.info("Starting Data Cleaning Pipeline...")
        df = self.parse_dates(df)
        df = self.clean_numerics(df)
        df = self.handle_missing_and_duplicates(df)
        df = self.sort_chronologically(df)
        
        # Validation
        validate_clean_schema(df)
        logger.info(f"Data Cleaning complete. Output clean records: {len(df):,}")
        return df

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
