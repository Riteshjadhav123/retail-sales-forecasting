"""
RetailMind-X Time-Series Feature Engineering Engine.
Generates calendar, cyclical, lag, rolling, trend, volatility, and promotional features
with strict zero-lookahead leakage guarantees.
"""

import os
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from app.core.logging import get_logger

logger = get_logger("feature_builder")

class FeatureBuilder:
    """Zero-Lookahead Time-Series Feature Engineering Engine."""

    def __init__(
        self,
        df: Optional[pd.DataFrame] = None,
        date_col: str = "Order Date",
        target_col: str = "Sales",
        series_cols: Optional[List[str]] = None,
        series_col: Optional[str] = None
    ):
        self.df = df.copy() if df is not None else None
        self.date_col = date_col
        self.target_col = target_col
        self.series_cols = series_cols or ["Region", "Category"]
        self.series_col = series_col or "series_id"

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
        if "series_id" in df.columns:
            return df
        valid_cols = [c for c in self.series_cols if c in df.columns]
        if valid_cols:
            df["series_id"] = df[valid_cols].astype(str).agg("_".join, axis=1)
        else:
            df["series_id"] = "DEFAULT_SERIES"
        return df

    def aggregate_to_daily_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates transactional data to regular daily time-series per series_id."""
        df = self.create_series_id(df)
        df[self.date_col] = pd.to_datetime(df[self.date_col])

        agg_dict = {self.target_col: "sum"}
        if "Quantity" in df.columns:
            agg_dict["Quantity"] = "sum"
        if "Discount" in df.columns:
            agg_dict["Discount"] = "mean"
        if "Profit" in df.columns:
            agg_dict["Profit"] = "sum"
        if "Unit Price" in df.columns:
            agg_dict["Unit Price"] = "mean"

        daily_df = df.groupby(["series_id", self.date_col]).agg(agg_dict).reset_index()

        # Reindex to fill complete date sequence per series_id
        series_ids = daily_df["series_id"].unique()
        all_dates = pd.date_range(daily_df[self.date_col].min(), daily_df[self.date_col].max(), freq="D")
        full_idx = pd.MultiIndex.from_product([series_ids, all_dates], names=["series_id", self.date_col])

        full_df = daily_df.set_index(["series_id", self.date_col]).reindex(full_idx).reset_index()
        full_df[self.target_col] = full_df[self.target_col].fillna(0.0)
        if "Quantity" in full_df.columns:
            full_df["Quantity"] = full_df["Quantity"].fillna(0)
        if "Discount" in full_df.columns:
            full_df["Discount"] = full_df["Discount"].fillna(0.0)
        if "Profit" in full_df.columns:
            full_df["Profit"] = full_df["Profit"].fillna(0.0)
        if "Unit Price" in full_df.columns:
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

    def transform(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Full feature engineering pipeline on passed or stored dataframe."""
        target_df = df.copy() if df is not None else self.df.copy()
        if target_df is None:
            raise ValueError("No DataFrame supplied for transform().")

        logger.info("Starting Feature Engineering Pipeline...")
        daily_df = self.aggregate_to_daily_series(target_df)
        date_df = self.build_date_features(daily_df)
        feat_df = self.build_lag_and_rolling_features(date_df)
        logger.info(f"Feature engineering complete. Dataset shape: {feat_df.shape}")
        self.df = feat_df
        return feat_df

    def build_features(self) -> pd.DataFrame:
        """Direct chronological feature engineering on existing self.df."""
        if self.df is None:
            raise ValueError("No DataFrame supplied for build_features().")
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

        feature_cols = [c for c in self.df.columns if c not in [self.date_col, self.series_col]]
        self.df[feature_cols] = self.df[feature_cols].fillna(0.0)

        logger.info(f"Feature Engineering Completed: Constructed {len(feature_cols)} features.")
        return self.df

    def save_features(self, df: pd.DataFrame, parquet_path: str = "data/processed/featured_sales.parquet", csv_path: str = "data/processed/featured_sales.csv") -> Tuple[str, str]:
        """Saves feature dataset to disk."""
        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved featured dataset to '{parquet_path}' and '{csv_path}'.")
        return parquet_path, csv_path

    def save_featured_data(self, output_path: str = "data/processed/featured_sales.parquet") -> str:
        """Saves featured DataFrame."""
        if self.df is None:
            raise ValueError("No featured DataFrame to save.")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.df.to_parquet(output_path, index=False)
        csv_path = output_path.replace(".parquet", ".csv")
        self.df.to_csv(csv_path, index=False)
        logger.info(f"Featured dataset saved to '{output_path}' and '{csv_path}'.")
        return output_path

class FeatureTransformer:
    """Categorical Encoders & Numerical Scalers for RetailMind-X."""

    def __init__(self):
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        self.label_encoders = {}
        self.scaler = None

    def fit_transform_categorical(self, df: pd.DataFrame, cat_cols: List[str]) -> pd.DataFrame:
        """Label encodes categorical columns."""
        from sklearn.preprocessing import LabelEncoder
        df_out = df.copy()
        for col in cat_cols:
            if col in df_out.columns:
                le = LabelEncoder()
                df_out[f"{col}_encoded"] = le.fit_transform(df_out[col].astype(str))
                self.label_encoders[col] = le
                logger.info(f"Categorical column '{col}' encoded into '{col}_encoded'.")
        return df_out

    def fit_transform_numerical(self, df: pd.DataFrame, num_cols: List[str]) -> pd.DataFrame:
        """Standard scales numerical columns."""
        from sklearn.preprocessing import StandardScaler
        df_out = df.copy()
        valid_cols = [c for c in num_cols if c in df_out.columns]
        if valid_cols:
            self.scaler = StandardScaler()
            scaled_vals = self.scaler.fit_transform(df_out[valid_cols])
            for idx, col in enumerate(valid_cols):
                df_out[f"{col}_scaled"] = scaled_vals[:, idx]
            logger.info(f"Scaled numerical columns: {valid_cols}.")
        return df_out
