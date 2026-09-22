import sys
import os
sys.path.insert(0, os.path.abspath("."))

from src.data.loader import download_raw_dataset, load_raw_dataset
from src.utils.logger import get_logger

logger = get_logger("fetch_script")

def main():
    logger.info("Executing dataset fetch script...")
    path = download_raw_dataset(force=True)
    df = load_raw_dataset(path)
    logger.info(f"Fetch complete! Dataset stored at '{path}' with shape {df.shape}.")

if __name__ == "__main__":
    main()
