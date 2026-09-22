# RetailMind-X Statistical Significance & Hypothesis Testing

**Test Sample Size ($N$):** 8580 evaluation windows

## Model Performance Benchmarks
- **Naive Baseline MAE:** $476.23$
- **Ridge Regression MAE:** $389.01$
- **LightGBM + Feature Engineering MAE:** $372.59$
- **LightGBM + Demand Recovery MAE:** $462.81$

---

## 1. LightGBM (FE) vs. Naive Baseline
- **Mean MAE Reduction:** $103.65$ (21.76% error reduction)
- **95% Confidence Interval:** [$91.12$, $116.18$]
- **Paired t-statistic:** $16.2173$ ($p = 2.7837e-58$)
- **Wilcoxon Signed-Rank Statistic:** $17502242.5$ ($p = 8.1497e-05$)
- **Cohen's d Effect Size:** $0.1751$
- **Statistical Significance ($lpha = 0.001$):** **PASS (p < 0.001)**

---

## 2. LightGBM (FE) vs. Ridge Regression
- **Mean MAE Reduction:** $16.42$ (4.22% error reduction)
- **95% Confidence Interval:** [$13.68$, $19.16$]
- **Paired t-statistic:** $11.7459$ ($p = 1.2928e-31$)
- **Wilcoxon Signed-Rank Statistic:** $15170246.0$ ($p = 3.6086e-45$)
- **Cohen's d Effect Size:** $0.1268$
- **Statistical Significance ($lpha = 0.001$):** **PASS (p < 0.001)**
