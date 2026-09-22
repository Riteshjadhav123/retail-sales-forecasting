"""
Temporal Validation Engine for Vaidsys Retail Sales Forecasting.
Enforces strict chronological train/val/test splits without random shuffling.
"""

import pandas as pd
from typing import Tuple
from src.utils.logger import get_logger

logger = get_logger("temporal_validation")

class TemporalValidator:
    """Chronological Split & Validation Manager."""

    def __init__(
        self,
        date_col: str = "Order Date",
        train_ratio: float = 0.80,
        val_ratio: float = 0.10,
        test_ratio: float = 0.10
    ):
        self.date_col = date_col
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

    def chronological_split(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Splits DataFrame strictly chronologically."""
        df_sorted = df.sort_values(self.date_col).reset_index(drop=True)
        n = len(df_sorted)

        train_end = int(n * self.train_ratio)
        val_end = int(n * (self.train_ratio + self.val_ratio))

        train_df = df_sorted.iloc[:train_end].copy()
        val_df = df_sorted.iloc[train_end:val_end].copy()
        test_df = df_sorted.iloc[val_end:].copy()

        self.verify_no_leakage(train_df, val_df, test_df)

        logger.info(f"Chronological Split Completed:\n  - Train: {len(train_df)} rows\n  - Val:   {len(val_df)} rows\n  - Test:  {len(test_df)} rows")
        return train_df, val_df, test_df

    def verify_no_leakage(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
        """Verifies zero temporal boundary overlap between sets."""
        max_train = train_df[self.date_col].max()
        min_val = val_df[self.date_col].min()
        max_val = val_df[self.date_col].max()
        min_test = test_df[self.date_col].min()

        if max_train > min_val or max_val > min_test:
            raise ValueError(f"Temporal Data Leakage Detected!\n  Max Train Date ({max_train}) > Min Val Date ({min_val})\n  or Max Val Date ({max_val}) > Min Test Date ({min_test})")

        logger.info("Chronological leakage verification PASSED (Zero Lookahead Leakage).")
        return True
