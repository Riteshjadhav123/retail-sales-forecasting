import sys
import os
sys.path.insert(0, os.path.abspath("."))

from src.data.loader import load_raw_dataset
from src.data.quality import DataQualityEngine
from src.preprocessing.cleaner import DataCleaner
from src.features.builder import FeatureBuilder
from src.demand.stockout_analyzer import StockoutDemandRecoveryEngine
from src.utils.logger import get_logger

logger = get_logger("run_pipeline")

def run_phase_1_pipeline():
    logger.info("==================================================")
    logger.info("STARTING RETAILMIND-X PHASE 1 DATA PIPELINE")
    logger.info("==================================================")

    # 1. Data Ingestion
    logger.info("[Step 1/5] Ingesting Raw Dataset...")
    raw_df = load_raw_dataset()

    # 2. Data Quality Engine
    logger.info("[Step 2/5] Running Automated Data Quality Assessment Engine...")
    quality_engine = DataQualityEngine(raw_df)
    quality_report = quality_engine.generate_reports()

    # 3. Data Cleaning & Preprocessing
    logger.info("[Step 3/5] Preprocessing & Cleaning Dataset...")
    cleaner = DataCleaner()
    clean_df = cleaner.transform(raw_df)
    cleaner.save_processed(clean_df)

    # 4. Feature Engineering
    logger.info("[Step 4/5] Engineering Time-Series Features (Zero Leakage)...")
    builder = FeatureBuilder()
    featured_df = builder.transform(clean_df)
    builder.save_features(featured_df)

    # 5. Hidden Demand / Stockout Recovery
    logger.info("[Step 5/5] Performing Censored Demand Recovery Analysis...")
    stockout_engine = StockoutDemandRecoveryEngine()
    demand_df = stockout_engine.recover_censored_demand(featured_df)
    stockout_engine.save_demand_dataset(demand_df)

    logger.info("==================================================")
    logger.info("PHASE 1 DATA PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("==================================================")
    return demand_df

if __name__ == "__main__":
    run_phase_1_pipeline()
