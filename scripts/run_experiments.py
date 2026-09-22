import sys
import os
sys.path.insert(0, os.path.abspath("."))

import pandas as pd
from src.utils.logger import get_logger
from scripts.run_pipeline import run_phase_1_pipeline
from src.forecasting.ablation import AblationStudyEngine

logger = get_logger("run_experiments")

def main():
    logger.info("==================================================")
    logger.info("STARTING RETAILMIND-X EXPERIMENT & ABLATION SUITE")
    logger.info("==================================================")

    # 1. Run Phase 1 Data Pipeline
    demand_df = run_phase_1_pipeline()

    clean_df = pd.read_parquet("data/processed/clean_sales.parquet")
    featured_df = pd.read_parquet("data/processed/featured_sales.parquet")

    # 2. Run Phase 2 Ablation Study
    logger.info("Running Phase 2 Model Training & Systematic Ablation Study...")
    ablation_engine = AblationStudyEngine(clean_df, featured_df, demand_df)
    results_df = ablation_engine.run_ablation_study()

    logger.info("Ablation Results Summary:\n" + results_df.to_string())
    logger.info("==================================================")
    logger.info("EXPERIMENT SUITE COMPLETED SUCCESSFULLY!")
    logger.info("==================================================")

if __name__ == "__main__":
    main()
