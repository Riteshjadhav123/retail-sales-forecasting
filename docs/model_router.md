# Adaptive Model Router Methodology

## Purpose
The Adaptive Model Router dynamically analyzes the statistical properties of each time-series and routes it to the most defensible forecasting model rather than applying a single global architecture across all products.

## Diagnostic Metrics Computed
1. **Average Demand Interval (ADI)**: $\text{ADI} = \frac{N_{\text{total}}}{N_{\text{non-zero}}}$. Measures demand intermittency.
2. **Coefficient of Variation (CV)**: $\text{CV} = \frac{\sigma}{\mu}$. Measures demand volatility.
3. **Weekly Autocorrelation ($r_7$)**: Autocorrelation at lag 7. Measures 7-day seasonality.
4. **Data Volume ($N$)**: Total days of historical observations available.

## Routing Decision Rules

```mermaid
flowchart TD
    Series[Time-Series Evaluation] --> History{Volume N < 45?}
    History -->|Yes| MA[Moving Average]
    History -->|No| ADI_Check{ADI > 1.32 or CV > 1.2?}
    ADI_Check -->|Yes| LGBM[LightGBM Quantile]
    ADI_Check -->|No| Season_Check{Autocorr_7 > 0.35?}
    Season_Check -->|Yes| SNaive[Seasonal Naive / Holt-Winters]
    Season_Check -->|No| Vol_Check{CV > 0.50?}
    Vol_Check -->|Yes| XGB[XGBoost Regressor]
    Vol_Check -->|No| Ridge[Ridge Linear Regression]
```

## Rationale & Justification
- **Intermittent/Lumpy Demand (ADI > 1.32)**: Tree-based gradient boosting (LightGBM) naturally handles sparse zero-inflated target distributions without bias.
- **Volatile High-Variance Series (CV > 0.50)**: Non-linear decision trees (XGBoost/LightGBM) capture complex feature interactions between price discounts and calendar effects.
- **Strong Seasonal Series ($r_7 > 0.35$)**: Seasonal Naive explicitly preserves 7-day cyclic patterns.
- **Smooth Continuous Series**: Linear models provide stable, low-variance forecasts.
