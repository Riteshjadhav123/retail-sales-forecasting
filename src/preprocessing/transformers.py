import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from sklearn.preprocessing import StandardScaler, LabelEncoder
from src.utils.logger import get_logger

logger = get_logger("data_transformers")

class FeatureTransformer:
    """Categorical Encoders & Numerical Scalers for RetailMind-X."""

    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler: Optional[StandardScaler] = None

    def fit_transform_categorical(self, df: pd.DataFrame, cat_cols: List[str]) -> pd.DataFrame:
        """Label encodes categorical columns."""
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
        df_out = df.copy()
        valid_cols = [c for c in num_cols if c in df_out.columns]
        if valid_cols:
            self.scaler = StandardScaler()
            scaled_vals = self.scaler.fit_transform(df_out[valid_cols])
            for idx, col in enumerate(valid_cols):
                df_out[f"{col}_scaled"] = scaled_vals[:, idx]
            logger.info(f"Scaled numerical columns: {valid_cols}.")
        return df_out
