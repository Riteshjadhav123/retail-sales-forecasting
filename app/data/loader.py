"""
RetailMind-X Data Loader Module
Handles downloading raw datasets and loading raw / processed CSV and Parquet files.
"""

import os
import pandas as pd
import urllib.request
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("data_loader")

DEFAULT_DATASET_URL = "https://raw.githubusercontent.com/pplonski/datasets-for-start/master/superstore-sales/superstore_dataset2011-2015.csv"
SAMPLE_DATA_PATH = "data/sample/sample_retail_sales_dataset.csv"
RAW_DATA_PATH = SAMPLE_DATA_PATH if os.path.exists(SAMPLE_DATA_PATH) else "data/raw/superstore.csv"

RAW_REQUIRED_COLUMNS = [
    "Order ID", "Order Date", "Ship Date", "Ship Mode",
    "Customer ID", "Segment", "City", "State", "Country",
    "Region", "Market", "Category", "Sub-Category",
    "Product ID", "Product Name", "Sales", "Quantity",
    "Discount", "Profit"
]

def download_raw_dataset(url: str = DEFAULT_DATASET_URL, target_path: str = RAW_DATA_PATH, force: bool = False) -> str:
    """Downloads raw dataset if not present locally."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    if os.path.exists(target_path) and not force:
        logger.info(f"Raw dataset already exists at '{target_path}'. Skipping download.")
        return target_path

    logger.info(f"Downloading raw retail sales dataset from '{url}'...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(target_path, "wb") as out_file:
        out_file.write(response.read())
    logger.info(f"Dataset successfully downloaded and saved to '{target_path}'.")
    return target_path

def load_raw_dataset(path: Optional[str] = None) -> pd.DataFrame:
    """Loads and returns the raw retail dataframe."""
    target_path = path or RAW_DATA_PATH
    if not os.path.exists(target_path):
        download_raw_dataset(target_path=target_path)

    logger.info(f"Loading raw dataset from '{target_path}'...")
    df = pd.read_csv(target_path, encoding="latin1")
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    missing_cols = [c for c in RAW_REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        logger.warning(f"Raw dataset is missing some expected columns: {missing_cols}")

    return df

def load_processed_data(path: str) -> pd.DataFrame:
    """Loads processed CSV or Parquet dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file '{path}' not found.")
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)
