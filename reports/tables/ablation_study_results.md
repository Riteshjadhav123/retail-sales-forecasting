| Scenario                                 |     MAE |    RMSE |    WAPE |        MAPE |           R2 |   Coverage_Pct |   Mean_Interval_Width |
|:-----------------------------------------|--------:|--------:|--------:|------------:|-------------:|---------------:|----------------------:|
| 1. Baseline (Naive)                      | 476.234 | 931.143 | 1.40977 | 1.29855e+09 | -0.579491    |       nan      |               nan     |
| 2. Baseline + Feature Engineering        | 372.587 | 701.377 | 1.10295 | 1.15993e+09 |  0.103837    |       nan      |               nan     |
| 3. Baseline + Demand Recovery            | 462.808 | 738.389 | 1.37002 | 1.94565e+09 |  0.0067588   |       nan      |               nan     |
| 4. Adaptive Model Router                 | 462.808 | 738.389 | 1.37002 | 1.94565e+09 |  0.0067588   |       nan      |               nan     |
| 5. Full RetailMind-X (Uncertainty-Aware) | 399.122 | 740.784 | 1.1815  | 1.2348e+09  |  0.000305286 |        53.1235 |               817.204 |