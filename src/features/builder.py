import os
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger("feature_builder")

class FeatureBuilder:
    """Time-Series Feature Engineering Engine with Strict Zero-Leakage Guarantees."""

    def __init__(self, date_col: str = "Order Date", target_col: str = "Sales", series_cols: Optional[List[str]] = None):
        self.date_col = date_col
        self.target_col = target_col
        self.series_cols = series_cols or ["Region", "Category"]

    def build_date_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Derives calendar and cyclical date features."""
        df = df.copy()
        dates = pd.to_datetime(df[self.date_col])
        df["day"] = dates.dt.day
        df["day_of_week"] = dates.dt.dayofweek
        df["week"] = dates.dt.isocalendar().week.astype(int)
        df["month"] = dates.dt.month
        df["quarter"] = dates.dt.quarter
        df["year"] = dates.dt.year
        df["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)

        # Cyclical Encodings
        df["sin_month"] = np.round(np.sin(2 * np.pi * df["month"] / 12.0), 4)
        df["cos_month"] = np.round(np.cos(2 * np.pi * df["month"] / 12.0), 4)
        df["sin_day_of_week"] = np.round(np.sin(2 * np.pi * df["day_of_week"] / 7.0), 4)
        df["cos_day_of_week"] = np.round(np.cos(2 * np.pi * df["day_of_week"] / 7.0), 4)

        logger.info("Calendar & cyclical date features created.")
        return df

    def create_series_id(self, df: pd.DataFrame) -> pd.DataFrame:
        """Constructs unique time-series identifier for grouping."""
        df = df.copy()
        df["series_id"] = df[self.series_cols].astype(str).agg("_".join, axis=1)
        return df

    def aggregate_to_daily_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates transactional data to regular daily time-series per series_id."""
        df = self.create_series_id(df)
        df[self.date_col] = pd.to_datetime(df[self.date_col])

        # Daily aggregation
        daily_df = df.groupby(["series_id", self.date_col]).agg({
            self.target_col: "sum",
            "Quantity": "sum",
            "Discount": "mean",
            "Profit": "sum",
            "Unit Price": "mean"
        }).reset_index()

        # Reindex to fill complete date sequence per series_id (no missing dates)
        series_ids = daily_df["series_id"].unique()
        all_dates = pd.date_range(daily_df[self.date_col].min(), daily_df[self.date_col].max(), freq="D")
        full_idx = pd.MultiIndex.from_product([series_ids, all_dates], names=["series_id", self.date_col])

        full_df = daily_df.set_index(["series_id", self.date_col]).reindex(full_idx).reset_index()
        full_df[self.target_col] = full_df[self.target_col].fillna(0.0)
        full_df["Quantity"] = full_df["Quantity"].fillna(0)
        full_df["Discount"] = full_df["Discount"].fillna(0.0)
        full_df["Profit"] = full_df["Profit"].fillna(0.0)
        full_df["Unit Price"] = full_df["Unit Price"].ffill().fillna(0.0)

        logger.info(f"Aggregated daily time-series across {len(series_ids)} unique series ({len(full_df):,} total daily observations).")
        return full_df

    def build_lag_and_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Derives Lag, Rolling, and Volatility features with STRICT zero lookahead leakage.
        Crucially applies .shift(1) BEFORE rolling aggregations so time t cannot see target t.
        """
        df = df.copy()
        df = df.sort_values(by=["series_id", self.date_col]).reset_index(drop=True)

        grouped = df.groupby("series_id")[self.target_col]

        # Shifted target series to guarantee no leakage
        shifted_target = grouped.shift(1)

        # Lags
        df["lag_1"] = grouped.shift(1).fillna(0.0)
        df["lag_7"] = grouped.shift(7).fillna(0.0)
        df["lag_14"] = grouped.shift(14).fillna(0.0)
        df["lag_28"] = grouped.shift(28).fillna(0.0)

        # Rolling Stats on Shifted Target
        df["rolling_mean_7"] = df.groupby("series_id")["lag_1"].transform(lambda x: x.rolling(7, min_periods=1).mean()).fillna(0.0)
        df["rolling_mean_14"] = df.groupby("series_id")["lag_1"].transform(lambda x: x.rolling(14, min_periods=1).mean()).fillna(0.0)
        df["rolling_mean_28"] = df.groupby("series_id")["lag_1"].transform(lambda x: x.rolling(28, min_periods=1).mean()).fillna(0.0)

        df["rolling_std_7"] = df.groupby("series_id")["lag_1"].transform(lambda x: x.rolling(7, min_periods=1).std()).fillna(0.0)
        df["rolling_std_28"] = df.groupby("series_id")["lag_1"].transform(lambda x: x.rolling(28, min_periods=1).std()).fillna(0.0)

        # Trend & Volatility Indicators
        denom = df["rolling_mean_28"].replace(0, 1.0)
        df["short_term_trend"] = np.round(df["rolling_mean_7"] / denom, 4)
        df["medium_term_trend"] = np.round(df["rolling_mean_14"] / denom, 4)
        
        cv_denom = df["rolling_mean_7"].replace(0, 1.0)
        df["demand_volatility"] = np.round(df["rolling_std_7"] / cv_denom, 4)

        logger.info("Lag, Rolling, Trend, and Volatility features generated with zero leakage guarantee.")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full feature engineering pipeline."""
        logger.info("Starting Feature Engineering Pipeline...")
        daily_df = self.aggregate_to_daily_series(df)
        date_df = self.build_date_features(daily_df)
        feat_df = self.build_lag_and_rolling_features(date_df)
        logger.info(f"Feature engineering complete. Dataset shape: {feat_df.shape}")
        return feat_df

    def save_features(self, df: pd.DataFrame, parquet_path: str = "data/processed/featured_sales.parquet", csv_path: str = "data/processed/featured_sales.csv") -> Tuple[str, str]:
        """Saves feature dataset to disk."""
        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved featured dataset to '{parquet_path}' and '{csv_path}'.")
        return parquet_path, csv_path
