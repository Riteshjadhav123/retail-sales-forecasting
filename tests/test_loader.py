import pytest
import pandas as pd
from src.data.loader import load_raw_dataset, RAW_REQUIRED_COLUMNS
from src.data.contracts import validate_raw_schema

def test_load_raw_dataset():
    df = load_raw_dataset()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert validate_raw_schema(df) is True

def test_raw_dataset_required_columns():
    df = load_raw_dataset()
    for col in ["Order Date", "Sales", "Quantity", "Category"]:
        assert col in df.columns
