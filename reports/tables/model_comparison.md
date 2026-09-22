# Official Model Benchmarking Comparison Table

| Model                           |     MAE |    RMSE |   WAPE |    MAPE |      R2 |   Accuracy_Pct |
|:--------------------------------|--------:|--------:|-------:|--------:|--------:|---------------:|
| Naive Baseline                  | 185.526 | 406.664 | 0.8164 | 107.881 | -0.0177 |          18.36 |
| Moving Average (W=14)           | 179.426 | 389.051 | 0.7896 | 104.582 |  0.0686 |          21.04 |
| Seasonal Naive (S=7)            | 185.404 | 406.303 | 0.8159 | 107.74  | -0.0159 |          18.41 |
| Ridge Linear Regression         | 176.988 | 347.24  | 0.7789 | 349.909 |  0.258  |          22.11 |
| Random Forest Regressor         | 179.424 | 356.637 | 0.7896 | 357.903 |  0.2173 |          21.04 |
| LightGBM Regressor (Best Model) | 170.976 | 345.076 | 0.7524 | 345.949 |  0.2672 |          24.76 |