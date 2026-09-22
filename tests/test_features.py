import pytest
import pandas as pd
from src.data.loader import load_raw_dataset
from src.preprocessing.cleaner import DataCleaner
from src.features.builder import FeatureBuilder

def test_feature_builder_transform():
    raw_df = load_raw_dataset().head(1000)
    clean_df = DataCleaner().transform(raw_df)
    builder = FeatureBuilder()
    feat_df = builder.transform(clean_df)

    assert "lag_1" in feat_df.columns
    assert "lag_7" in feat_df.columns
    assert "rolling_mean_7" in feat_df.columns
    assert "day_of_week" in feat_df.columns
    assert feat_df["lag_1"].isnull().sum() == 0
