# Time-Series Forecasting Error Analysis Report

## 1. Executive Summary
- **Overall Test MAE:** $170.98
- **Overall Test RMSE:** $345.08
- **High-Volume Segment MAE:** $239.70
- **Low-Volume Segment MAE:** $102.19

---

## 2. Root Cause Findings & Model Weaknesses
- Intermittent demand zero-sales periods create right-skewed error residuals.
- Unpredictable promotion/discount spikes trigger temporary demand surges.
- High variance SKUs exhibit higher absolute dollar error, though relative WAPE remains stable.
