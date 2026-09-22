# RetailMind-X Demo Instructions & Walkthrough

This document provides step-by-step instructions to launch, explore, and evaluate the **RetailMind-X AI Command Center**.

---

## 1. Environment Setup & Launch

1. Ensure Python 3.10+ is installed on your system.
2. Open a terminal in the project root directory:
   ```bash
   cd c:\Users\HP\OneDrive\Desktop\vaidysis
   ```
3. Run the application launch script:
   ```bash
   python scripts/run_app.py
   ```
4. Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

---

## 2. Interactive UI Feature Walkthrough (9 Experiences)

Once the application is running, test each of the 9 live experiences:

### Experience 1: System Overview & Executive KPI Summary
- Inspect top KPI cards: Total Revenue (\$12.64M), Active SKUs (1,496), Recovered Lost Demand (\$6.08M), Forecast MAE (\$372.59), and Average Inventory Risk Score.

### Experience 2: Multi-Category Sales Analytics & Data Intelligence
- View historical sales trends, market breakdowns across 7 global regions, and Pareto ABC classification charts.

### Experience 3: Tobit Censored Demand Recovery Engine
- Inspect observed sales vs. Tobit recovered customer demand gap across 15,204 stockout days.

### Experience 4: Feature Engineering & Time-Series Inspector
- Explore zero-lookahead feature correlation matrix, 23 lag/rolling features, and seasonal decomposition.

### Experience 5: Research Engine & 5-Step Model Ablation Study
- Compare MAE, RMSE, WAPE, and R² across Naive, Ridge, Random Forest, XGBoost, and LightGBM models.

### Experience 6: Dynamic Model Router & Series Profiling
- Review series volatility clustering and dynamic algorithm routing per store-item series.

### Experience 7: Probabilistic Quantile Uncertainty Fan Chart
- View $p10$, $p50$, and $p90$ demand forecast intervals with shaded 80% coverage bounds.

### Experience 8: Inventory Decision Engine & Composite Risk Inspector
- Calculate optimal Safety Stock ($SS$), Reorder Point ($ROP$), Economic Order Quantity ($EOQ$), and inspect 5D Composite Risk scores (Stockout, Overstock, Volatility, Uncertainty, Lead-Time).

### Experience 9: Digital Twin 90-Day Discrete-Event Simulator & Scenario Lab
- Run 90-day inventory simulations and perform What-If stress testing (+50% Black Friday surge, +5 day supplier delays).

---

## 3. Automated Command Line Verification

To verify the underlying ML & API backend without the web interface:

```bash
# Run unit and integration test suite (32 tests)
python -m pytest tests/

# Run statistical significance tests
python research/stat_test.py

# Generate 300 DPI publication figures
python scripts/generate_paper_figures.py
```
