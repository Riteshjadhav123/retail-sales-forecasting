import pytest
import pandas as pd
from src.data.loader import load_raw_dataset
from src.preprocessing.cleaner import DataCleaner
from src.data.contracts import validate_clean_schema

def test_data_cleaner_transform():
    raw_df = load_raw_dataset().head(500)
    cleaner = DataCleaner()
    clean_df = cleaner.transform(raw_df)

    assert isinstance(clean_df, pd.DataFrame)
    assert len(clean_df) > 0
    assert "Unit Price" in clean_df.columns
    assert clean_df["Sales"].isnull().sum() == 0
    assert validate_clean_schema(clean_df) is True
