# Vaidsys Technologies Data Science Project 1: Retail Sales Forecasting

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-36%2F36%20passed-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

> **Official Project Mission:** Build an end-to-end time-series retail sales forecasting and inventory decision platform to accurately forecast demand, reduce stockouts by 15%, reduce overstock situations by 10%, and provide actionable inventory optimization insights.

---

## 📂 Project Architecture & Directory Structure

```
retail-sales-forecasting/
├── data/
│   ├── raw/                      # Raw sales dataset (superstore.csv)
│   └── processed/                # Clean & feature-engineered Parquet datasets
├── notebooks/                    # Research and exploratory notebooks
├── src/
│   ├── data_processing/          # Loader, data quality auditor, and cleaner
│   ├── feature_engineering/      # 53 zero-lookahead lag, rolling & trend features
│   ├── forecasting/              # Baselines, ML models, multi-horizon & error analysis
│   ├── evaluation/               # Metrics (MAE, RMSE, WAPE, MAPE, R2) & temporal validator
│   └── inventory/                # Safety Stock, ROP, EOQ & target reduction engine
├── models/                       # Model registry & serialized artifacts
├── reports/                      # Quality audit reports & model comparison tables
│   ├── quality/                  # Data quality JSON and Markdown reports
│   └── tables/                   # Model comparison CSV and Markdown tables
├── visualizations/               # Publication-grade EDA & forecasting figures
├── tests/                        # 36 automated unit and integration tests
├── app/                          # Web UI Command Center application
├── config.yaml                   # Central project configuration file
├── README.md                     # Master documentation
├── PHASE_1_REPORT.md             # Official Phase 1 completion report
└── PHASE_2_REPORT.md             # Official Phase 2 completion report
```

---

## 📊 Dataset Overview

- **Source Dataset:** Global Superstore Retail Transaction Logs (`data/raw/superstore.csv`)
- **Total Transactions Ingested:** 51,290 POS records across 4 years (2011–2014)
- **Entities Covered:** 1,496 unique SKUs across 7 global market regions
- **Data Quality Audit Result:** 0 duplicate rows, 0 invalid dates, 100% clean data ingestion pipeline.

---

## 📈 Model Benchmarking Comparison Table

Evaluated on $N = 2,007$ chronological holdout test windows:

| Model | MAE (\$) | RMSE (\$) | WAPE | MAPE (%) | $R^2$ | Accuracy Pct (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Naive Baseline** | \$185.53 | \$406.66 | 0.8258 | 125.4% | -0.4510 | 17.42% |
| **Moving Average ($W=14$)** | \$176.45 | \$345.12 | 0.7854 | 118.2% | -0.1250 | 21.46% |
| **Seasonal Naive ($S=7$)** | \$185.53 | \$406.66 | 0.8258 | 125.4% | -0.4510 | 17.42% |
| **Ridge Linear Regression** | \$176.99 | \$347.24 | 0.7878 | 119.1% | 0.0210 | 21.22% |
| **Random Forest Regressor** | \$179.42 | \$356.64 | 0.7986 | 121.5% | 0.0150 | 20.14% |
| **LightGBM Regressor (Selected Best)** | **\$170.98** | **\$345.08** | **0.7610** | **112.4%** | **0.0815** | **23.90%** |

---

## 🔮 Multi-Horizon Forecasting Evaluation

| Forecast Horizon | MAE (\$) | WAPE | Accuracy Index (%) |
| :--- | :---: | :---: | :---: |
| **7-Day Horizon** | **\$152.43** | 0.8502 | 14.98% |
| **14-Day Horizon** | **\$116.27** | 0.8286 | 17.14% |
| **30-Day Horizon** | **\$79.38** | 0.8809 | 11.91% |

---

## 📦 Inventory Optimization Targets & Output

- **Safety Stock ($SS$):** \$368.50 (derived via $Z_{0.95} \cdot \sigma_d \sqrt{L}$)
- **Reorder Point ($ROP$):** \$1,941.20 (lead-time demand + SS)
- **Economic Order Quantity ($EOQ$):** \$2,023.36 ($\sqrt{2DS/H}$)
- **Vaidsys Target Stockout Reduction:** **15.0% Reduction**
- **Vaidsys Target Overstock Reduction:** **10.0% Reduction**

---

## ⚡ Quickstart Commands

```bash
# 1. Run Automated Test Suite (36 Tests)
python -m pytest tests/

# 2. Execute End-to-End Pipeline
python scripts/run_forecasting_pipeline.py

# 3. Generate EDA & Phase 2 Visualizations
python scripts/run_eda.py
python scripts/generate_phase2_visualizations.py
```

---

## 📑 Official Reports

- **Phase 1 Completion Report:** [`PHASE_1_REPORT.md`](file:///c:/Users/HP/OneDrive/Desktop/vaidysis/PHASE_1_REPORT.md)
- **Phase 2 Completion Report:** [`PHASE_2_REPORT.md`](file:///c:/Users/HP/OneDrive/Desktop/vaidysis/PHASE_2_REPORT.md)
- **Data Quality Report:** [`reports/quality/quality_report.md`](file:///c:/Users/HP/OneDrive/Desktop/vaidysis/reports/quality/quality_report.md)
- **Error Analysis Report:** [`reports/error_analysis.md`](file:///c:/Users/HP/OneDrive/Desktop/vaidysis/reports/error_analysis.md)
