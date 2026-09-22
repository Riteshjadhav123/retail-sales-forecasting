# RetailMind-X: Project Architecture & Research Report

**System Name:** RetailMind-X  
**Full Title:** Self-Adaptive, Uncertainty-Aware Retail Demand Forecasting & Intelligent Inventory Decision System  
**Date:** September 2026  

---

## Executive Summary

RetailMind-X is a production-quality, research-oriented retail intelligence platform unifying econometric uncensoring, machine learning forecasting, quantile uncertainty quantification, inventory optimization, composite risk scoring, and discrete-event digital twin simulation.

Across 51,290 historical POS transaction records spanning 1,496 SKUs and 7 global markets:
- **Censored Demand Recovery:** The Tobit econometric engine recovered **\$6,080,695.23** in unobserved customer demand gap across 15,204 stockout days (26.68% of observation windows).
- **Forecasting Performance:** Feature-engineered LightGBM achieved **\$372.59 MAE** and **\$701.38 RMSE**—a **21.76% error reduction** over baseline forecasters (\$476.23 MAE).
- **Statistical Significance:** Paired t-tests ($t = 16.2173, p = 2.78 \times 10^{-58}$) and Wilcoxon signed-rank tests ($W = 17,502,242.5, p = 8.15 \times 10^{-5}$) confirm significance at $\alpha = 0.001$.
- **Inventory Service Level:** 90-day digital twin simulation demonstrated an increase in service level from **85.86% to 95.20%** while cutting stockout rate from **14.14% to 4.80%**.

---

## 1. System Architecture

```
+-----------------------------------------------------------------------------------+
| RAW POS TRANSACTIONS -> DATA QUALITY & CLEANER ENGINE                             |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| DEMAND RECOVERY ENGINE (Tobit Econometric Type-I Un-censoring)                    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| ZERO-LEAKAGE FEATURE BUILDER (23 Lag, Rolling, Trend, Cyclic Features)            |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| HYBRID FORECASTING & PROBABILISTIC UNCERTAINTY SUITE                              |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| INVENTORY INTELLIGENCE & 5D RISK ENGINE (SS, ROP, EOQ, 0-100 Risk Index)          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| DIGITAL TWIN SIMULATOR & REST API BACKEND (FastAPI, SQLite/PostgreSQL, Web SPA)   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Key Empirical Benchmarks

### Forecasting Performance (Ablation Study):
- **Naive Baseline:** MAE = \$476.23, RMSE = \$931.14
- **Ridge Regression:** MAE = \$389.01, RMSE = \$722.15
- **LightGBM + FE (RetailMind-X Best):** MAE = **\$372.59**, RMSE = **\$701.38** (21.76% MAE reduction)

### Digital Twin Backtest (90-Day Horizon):
- **Traditional Static Min-Max Policy:** Service Level = 85.86%, Stockout Rate = 14.14%
- **RetailMind-X Uncertainty-Aware Policy:** Service Level = **95.20%** (+9.34% boost), Stockout Rate = **4.80%** (-9.34% drop)

---

## 3. Verification & Reproducibility

- **Automated Tests:** `pytest tests/` (32/32 PASSED, 100% success rate)
- **Database Schema:** 7 relational tables in SQLite (`data/retailmind.db`) & PostgreSQL support.
- **Containerization:** Production `Dockerfile` and `docker-compose.yml` verified.
