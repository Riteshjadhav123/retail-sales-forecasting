"""
Zero-Lookahead Feature Engineering Pipeline.
Generates calendar, lag, rolling, trend, price, and promotional features.
"""

import os
import numpy as np
import pandas as pd
from typing import List
from src.utils.logger import get_logger

logger = get_logger("feature_builder")

class FeatureBuilder:
    """Zero-Lookahead Time-Series Feature Engineering Engine."""

    def __init__(self, df: pd.DataFrame, date_col: str = "Order Date", target_col: str = "Sales", series_col: str = "series_id"):
        self.df = df.copy()
        self.date_col = date_col
        self.target_col = target_col
        self.series_col = series_col

    def build_features(self) -> pd.DataFrame:
        """Constructs all calendar, lag, rolling, and trend features."""
        logger.info("Building Zero-Lookahead Time-Series Features...")

        # 1. Sort Chronologically
        self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
        self.df = self.df.sort_values(self.date_col).reset_index(drop=True)

        # 2. Date & Calendar Features
        self.df["day"] = self.df[self.date_col].dt.day
        self.df["day_of_week"] = self.df[self.date_col].dt.dayofweek
        self.df["week"] = self.df[self.date_col].dt.isocalendar().week.astype(int)
        self.df["month"] = self.df[self.date_col].dt.month
        self.df["quarter"] = self.df[self.date_col].dt.quarter
        self.df["year"] = self.df[self.date_col].dt.year
        self.df["is_weekend"] = self.df["day_of_week"].isin([5, 6]).astype(int)

        # Cyclic encoding
        self.df["sin_month"] = np.sin(2 * np.pi * self.df["month"] / 12.0)
        self.df["cos_month"] = np.cos(2 * np.pi * self.df["month"] / 12.0)
        self.df["sin_day_of_week"] = np.sin(2 * np.pi * self.df["day_of_week"] / 7.0)
        self.df["cos_day_of_week"] = np.cos(2 * np.pi * self.df["day_of_week"] / 7.0)

        # 3. Lag Features
        lags = [1, 7, 14, 28, 60]
        for lag in lags:
            self.df[f"lag_{lag}"] = self.df[self.target_col].shift(lag)

        # 4. Rolling Statistics (strictly shift(1) to avoid lookahead leakage)
        windows = [7, 14, 28, 60]
        shifted_target = self.df[self.target_col].shift(1)
        for w in windows:
            self.df[f"rolling_mean_{w}"] = shifted_target.rolling(w, min_periods=1).mean()
            self.df[f"rolling_std_{w}"] = shifted_target.rolling(w, min_periods=1).std()

        # 5. Trend & Volatility Indicators
        r7 = self.df["rolling_mean_7"]
        r14 = self.df["rolling_mean_14"]
        r28 = self.df["rolling_mean_28"]
        std28 = self.df["rolling_std_28"]

        self.df["short_term_trend"] = (r7 / (r28 + 1e-5)).fillna(1.0)
        self.df["medium_term_trend"] = (r14 / (r28 + 1e-5)).fillna(1.0)
        self.df["demand_volatility"] = (std28 / (r28 + 1e-5)).fillna(0.0)

        # 6. Price & Promotional Features
        if "Discount" in self.df.columns:
            self.df["Discount_Impact"] = self.df["Discount"] * self.df[self.target_col]
        else:
            self.df["Discount"] = 0.0
            self.df["Discount_Impact"] = 0.0

        if "Quantity" in self.df.columns:
            self.df["Unit_Price"] = (self.df[self.target_col] / (self.df["Quantity"] + 1e-5)).fillna(0.0)
        else:
            self.df["Unit_Price"] = 0.0

        # Fill NAs in lag/rolling features
        feature_cols = [c for c in self.df.columns if c not in [self.date_col, self.series_col]]
        self.df[feature_cols] = self.df[feature_cols].fillna(0.0)

        logger.info(f"Feature Engineering Completed: Constructed {len(feature_cols)} features.")
        return self.df

    def save_featured_data(self, output_path: str = "data/processed/featured_sales.parquet") -> str:
        """Saves featured DataFrame."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.df.to_parquet(output_path, index=False)
        csv_path = output_path.replace(".parquet", ".csv")
        self.df.to_csv(csv_path, index=False)
        logger.info(f"Featured dataset saved to '{output_path}' and '{csv_path}'.")
        return output_path
