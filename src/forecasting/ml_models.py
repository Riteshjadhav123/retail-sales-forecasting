import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from src.utils.logger import get_logger

logger = get_logger("ml_forecasting")

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except Exception:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except Exception:
    HAS_LIGHTGBM = False

class MLForecaster:
    """Supervised Machine Learning Forecasting Suite."""

    def __init__(self, feature_cols: List[str], target_col: str = "Sales", random_state: int = 42):
        self.feature_cols = feature_cols
        self.target_col = target_col
        self.random_state = random_state
        self.models = {}

    def fit_ridge(self, X_train: pd.DataFrame, y_train: np.ndarray, alpha: float = 1.0) -> Ridge:
        """Trains Ridge Linear Regression model."""
        model = Ridge(alpha=alpha, random_state=self.random_state)
        model.fit(X_train[self.feature_cols].fillna(0.0), y_train)
        self.models["LinearRegression"] = model
        logger.info("Trained Ridge Linear Regression model.")
        return model

    def fit_random_forest(self, X_train: pd.DataFrame, y_train: np.ndarray, n_estimators: int = 100) -> RandomForestRegressor:
        """Trains Random Forest Regressor."""
        model = RandomForestRegressor(n_estimators=n_estimators, max_depth=12, random_state=self.random_state, n_jobs=-1)
        model.fit(X_train[self.feature_cols].fillna(0.0), y_train)
        self.models["RandomForest"] = model
        logger.info("Trained Random Forest Regressor.")
        return model

    def fit_xgboost(self, X_train: pd.DataFrame, y_train: np.ndarray, n_estimators: int = 100) -> Any:
        """Trains XGBoost or Gradient Boosting Regressor."""
        X_mat = X_train[self.feature_cols].fillna(0.0)
        if HAS_XGBOOST:
            try:
                model = xgb.XGBRegressor(
                    n_estimators=n_estimators,
                    max_depth=6,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.random_state,
                    n_jobs=-1
                )
                model.fit(X_mat, y_train)
                self.models["XGBoost"] = model
                logger.info("Trained XGBoost Regressor.")
                return model
            except Exception as e:
                logger.warning(f"XGBoost runtime error: {e}. Falling back to GradientBoostingRegressor.")
        
        model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=6,
            learning_rate=0.05,
            random_state=self.random_state
        )
        model.fit(X_mat, y_train)
        self.models["XGBoost"] = model
        logger.info("Trained GradientBoostingRegressor (Fallback for XGBoost).")
        return model

    def fit_lightgbm(self, X_train: pd.DataFrame, y_train: np.ndarray, n_estimators: int = 100) -> Any:
        """Trains LightGBM Regressor with HistGradientBoosting fallback."""
        X_mat = X_train[self.feature_cols].fillna(0.0)
        if HAS_LIGHTGBM:
            try:
                model = lgb.LGBMRegressor(
                    n_estimators=n_estimators,
                    max_depth=6,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.random_state,
                    n_jobs=-1,
                    verbose=-1
                )
                model.fit(X_mat, y_train)
                self.models["LightGBM"] = model
                logger.info("Trained LightGBM Regressor.")
                return model
            except Exception as e:
                logger.warning(f"LightGBM runtime error: {e}. Falling back to HistGradientBoostingRegressor.")

        model = HistGradientBoostingRegressor(
            max_iter=n_estimators,
            max_depth=6,
            learning_rate=0.05,
            random_state=self.random_state
        )
        model.fit(X_mat, y_train)
        self.models["LightGBM"] = model
        logger.info("Trained HistGradientBoostingRegressor (Fallback for LightGBM).")
        return model

    def predict(self, model_name: str, X_test: pd.DataFrame) -> np.ndarray:
        """Generates predictions for target model."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' has not been trained yet.")
        model = self.models[model_name]
        preds = model.predict(X_test[self.feature_cols].fillna(0.0))
        return np.maximum(0.0, preds)
