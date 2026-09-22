import sys
import os
sys.path.insert(0, os.path.abspath("."))

import pandas as pd
from src.utils.logger import get_logger
from src.inventory.reorder_engine import ReorderDecisionEngine
from src.inventory.abc_analysis import ABCClassificationEngine
from src.inventory.explainer import DecisionExplanationEngine
from src.simulation.scenario_lab import WhatIfScenarioLab
from src.simulation.digital_twin import DigitalRetailTwinSimulator
from src.simulation.backtest import InventoryBacktestEngine

logger = get_logger("run_phase3")

def main():
    logger.info("==================================================")
    logger.info("STARTING RETAILMIND-X PHASE 3 INVENTORY INTELLIGENCE SUITE")
    logger.info("==================================================")

    # Load Phase 1 & 2 demand dataset
    demand_file = "data/processed/demand_recovered.parquet"
    if not os.path.exists(demand_file):
        raise FileNotFoundError(f"Processed demand dataset '{demand_file}' not found. Please run Phase 1 & 2 first.")
    
    demand_df = pd.read_parquet(demand_file)

    # 1. ABC Analysis
    logger.info("[Step 1/6] Running Pareto ABC Revenue Classification...")
    abc_engine = ABCClassificationEngine()
    abc_df = abc_engine.classify_series(demand_df)
    abc_df.to_csv("reports/tables/abc_classification.csv", index=False)

    # 2. Automated Reorder Decision Engine
    logger.info("[Step 2/6] Generating Machine-Readable Reorder Recommendations...")
    series_summary = demand_df.groupby("series_id").agg({
        "Sales": ["mean", "std"],
        "Unit Price": "mean"
    }).reset_index()
    series_summary.columns = ["series_id", "avg_daily_demand", "std_daily_demand", "unit_price"]
    series_summary["current_stock"] = np.random.uniform(10, 150, len(series_summary))
    series_summary["cv"] = series_summary["std_daily_demand"] / series_summary["avg_daily_demand"].replace(0, 1)

    reorder_engine = ReorderDecisionEngine()
    rec_df = reorder_engine.generate_recommendations(series_summary)

    # 3. Decision Explanations
    logger.info("[Step 3/6] Generating Decision Explanations for SKUs...")
    explainer = DecisionExplanationEngine()
    sample_explanations = [explainer.explain_reorder_decision(row) for _, row in rec_df.head(5).iterrows()]
    pd.DataFrame(sample_explanations).to_markdown("reports/tables/decision_explanations_sample.md", index=False)

    # 4. What-If Scenario Lab
    logger.info("[Step 4/6] Running Interactive What-If Scenario Simulation Lab...")
    lab = WhatIfScenarioLab()
    scen_result = lab.run_scenario_simulation(
        base_avg_daily_demand=25.0,
        demand_growth_pct=20.0,
        scenario_lead_time_days=12.0
    )
    pd.DataFrame([scen_result["baseline"], scen_result["scenario"]]).to_markdown("reports/tables/whatif_scenario_sample.md", index=False)

    # 5. Digital Retail Twin Stress Tests
    logger.info("[Step 5/6] Executing Digital Retail Twin Simulation Stress Tests...")
    twin = DigitalRetailTwinSimulator()
    sample_demand = demand_df[demand_df["series_id"] == "Central_Furniture"]["reconstructed_demand"].values[:90]
    if len(sample_demand) < 90:
        sample_demand = np.random.exponential(25.0, 90)

    scenarios = ["NORMAL", "DEMAND_SPIKE", "SUPPLIER_DELAY", "PROMOTION_CAMPAIGN", "INVENTORY_SHORTAGE"]
    twin_results = [twin.simulate_series("Central_Furniture", sample_demand, scenario_name=s) for s in scenarios]
    dt_df = pd.DataFrame(twin_results)
    dt_df.to_csv("reports/tables/digital_twin_scenarios.csv", index=False)
    dt_df.to_markdown("reports/tables/digital_twin_scenarios.md", index=False)

    # 6. Decision-Level Inventory Strategy Backtest
    logger.info("[Step 6/6] Running Decision-Level Inventory Strategy Backtest...")
    backtester = InventoryBacktestEngine()
    bt_df = backtester.run_backtest(demand_df)

    logger.info("==================================================")
    logger.info("PHASE 3 INVENTORY INTELLIGENCE SUITE COMPLETED SUCCESSFULLY!")
    logger.info("==================================================")

if __name__ == "__main__":
    import numpy as np
    main()
