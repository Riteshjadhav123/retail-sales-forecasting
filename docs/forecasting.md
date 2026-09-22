# Forecasting Engine & Model Architectures

## Baseline Models (`src/forecasting/baselines.py`)
- **Naive Forecast**: Predicts last observed value ($y_{t-1}$).
- **Seasonal Naive**: Predicts value from 7 days prior ($y_{t-7}$).
- **Moving Average**: Predicts 7-day trailing mean.
- **Simple Exponential Smoothing (SES)**: Exponentially weighted average ($\alpha = 0.3$).

## Supervised ML Models (`src/forecasting/ml_models.py`)
- **Ridge Linear Regression**: L2 regularization ($\alpha=1.0$).
- **Random Forest Regressor**: 100 trees, max depth 12.
- **XGBoost Regressor**: Gradient boosting with colsample/subsample regularization.
- **LightGBM Regressor**: Fast histogram gradient boosting.

## Classical Time-Series Models (`src/forecasting/ts_models.py`)
- **ARIMA(1,1,1)**: Auto-Regressive Integrated Moving Average for univariate daily series.
- **Holt-Winters Exponential Smoothing**: Additive trend and 7-day additive seasonality.

## Deep Learning Models (`src/forecasting/dl_models.py`)
- **PyTorch Deep MLP**: Multi-layer neural network with BatchNorm, Dropout (0.2), and ReLU activations.

## Probabilistic Quantile Forecasting (`src/forecasting/probabilistic.py`)
- Fits Quantile LightGBM models for quantiles $p=0.10, 0.50, 0.90$.
- Produces calibrated prediction intervals (Lower Bound, Median, Upper Bound).
