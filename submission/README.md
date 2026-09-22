# RetailMind-X Submission Package

**Project Name:** RetailMind-X  
**Full Title:** Self-Adaptive, Uncertainty-Aware Retail Demand Forecasting & Intelligent Inventory Decision System  
**Submission Target:** Vaidsys Evaluation Platform / Internship / GitHub Portfolio / Academic Review  
**Date:** September 2026  

---

## 1. Package Contents & Directory Structure

```
submission/
├── README.md                 # Submission overview and system setup guide
├── Project_Report.md         # Comprehensive engineering & research report
└── DEMO_INSTRUCTIONS.md      # Step-by-step instructions for running interactive demo
```

---

## 2. Quickstart Execution Guide

To launch and test RetailMind-X locally:

### Step 1: Install Dependencies & Run Tests
```bash
python -m pip install -r requirements.txt
python -m pytest tests/
```

### Step 2: Run End-to-End Pipeline & Generate Figures
```bash
python scripts/run_pipeline.py
python research/stat_test.py
python scripts/generate_paper_figures.py
```

### Step 3: Launch Web AI Command Center
```bash
python scripts/run_app.py
```
Open your browser at `http://localhost:8000`.

---

## 3. Key Achievements & Benchmarks

1. **Tobit Demand Recovery:** Recovered **\$6,080,695.23** in lost customer demand across 15,204 stockout days.
2. **Forecasting Accuracy:** Feature-engineered LightGBM achieved **\$372.59 MAE** (21.76% error reduction over Naive baseline).
3. **Statistical Significance:** Paired t-test ($t = 16.2173, p = 2.78 \times 10^{-58}$) and Wilcoxon test ($W = 17,502,242.5, p = 8.15 \times 10^{-5}$) confirm significance at $\alpha = 0.001$.
4. **Digital Twin Simulation:** Uncertainty-aware inventory policy achieved **95.20% Service Level** and reduced stockout rate to **4.80%**.
5. **System Quality:** **32/32 tests passing** on Pytest. Zero data leakage.
