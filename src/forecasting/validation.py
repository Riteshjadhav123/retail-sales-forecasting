import numpy as np
import pandas as pd
from typing import Tuple, List, Generator
from src.utils.logger import get_logger

logger = get_logger("temporal_validation")

class TemporalValidator:
    """Chronological Validation & Time-Series Split Engine with Leakage Prevention."""

    def __init__(self, date_col: str = "Order Date"):
        self.date_col = date_col

    def chronological_split(self, df: pd.DataFrame, train_ratio: float = 0.70, val_ratio: float = 0.15) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits DataFrame chronologically into Train, Validation, and Test sets.
        STRICT REQUIREMENT: NO random shuffling!
        """
        df_sorted = df.sort_values(by=self.date_col).reset_index(drop=True)
        unique_dates = df_sorted[self.date_col].drop_duplicates().sort_values().values
        
        n_dates = len(unique_dates)
        train_end_idx = int(n_dates * train_ratio)
        val_end_idx = int(n_dates * (train_ratio + val_ratio))

        train_dates = unique_dates[:train_end_idx]
        val_dates = unique_dates[train_end_idx:val_end_idx]
        test_dates = unique_dates[val_end_idx:]

        train_df = df_sorted[df_sorted[self.date_col].isin(train_dates)].copy()
        val_df = df_sorted[df_sorted[self.date_col].isin(val_dates)].copy()
        test_df = df_sorted[df_sorted[self.date_col].isin(test_dates)].copy()

        self.verify_no_leakage(train_df, val_df, test_df)

        logger.info(
            f"Chronological Split Completed:\n"
            f"  - Train Set: {len(train_df):,} rows ({train_dates[0]} to {train_dates[-1]})\n"
            f"  - Val Set:   {len(val_df):,} rows ({val_dates[0]} to {val_dates[-1]})\n"
            f"  - Test Set:  {len(test_df):,} rows ({test_dates[0]} to {test_dates[-1]})"
        )
        return train_df, val_df, test_df

    def walk_forward_splits(self, df: pd.DataFrame, n_splits: int = 3, val_window_days: int = 30) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
        """Generates Walk-Forward Rolling Train/Val splits for time-series evaluation."""
        df_sorted = df.sort_values(by=self.date_col).reset_index(drop=True)
        max_date = df_sorted[self.date_col].max()

        for step in range(n_splits, 0, -1):
            val_end = max_date - pd.Timedelta(days=(step - 1) * val_window_days)
            val_start = val_end - pd.Timedelta(days=val_window_days)

            train = df_sorted[df_sorted[self.date_col] < val_start].copy()
            val = df_sorted[(df_sorted[self.date_col] >= val_start) & (df_sorted[self.date_col] <= val_end)].copy()

            if len(train) > 0 and len(val) > 0:
                yield train, val

    def verify_no_leakage(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
        """Verifies strict chronological boundary rule (Train Max Date < Val Min Date < Test Min Date)."""
        train_max = train_df[self.date_col].max()
        val_min = val_df[self.date_col].min()
        val_max = val_df[self.date_col].max()
        test_min = test_df[self.date_col].min()

        if train_max >= val_min:
            raise ValueError(f"CRITICAL LEAKAGE DETECTED: Train Max Date ({train_max}) >= Val Min Date ({val_min})!")
        if val_max >= test_min:
            raise ValueError(f"CRITICAL LEAKAGE DETECTED: Val Max Date ({val_max}) >= Test Min Date ({test_min})!")

        logger.info("Chronological leakage verification PASSED successfully (Zero Lookahead Leakage).")
        return True
