import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger("model_explainer")

try:
    import shap
    HAS_SHAP = True
except Exception:
    HAS_SHAP = False

class ModelExplainer:
    """Model Explainability Engine using Feature Importances & SHAP."""

    def __init__(self, feature_cols: List[str]):
        self.feature_cols = feature_cols

    def get_tree_feature_importance(self, model: Any) -> pd.DataFrame:
        """Extracts normalized feature importances for tree-based models."""
        if hasattr(model, "feature_importances_"):
            imp = model.feature_importances_
            df_imp = pd.DataFrame({
                "feature": self.feature_cols,
                "importance": imp
            }).sort_values(by="importance", ascending=False).reset_index(drop=True)
            df_imp["importance_pct"] = np.round((df_imp["importance"] / df_imp["importance"].sum()) * 100.0, 2)
            return df_imp
        else:
            df_imp = pd.DataFrame({
                "feature": self.feature_cols,
                "importance": np.ones(len(self.feature_cols)) / len(self.feature_cols)
            })
            df_imp["importance_pct"] = np.round(100.0 / len(self.feature_cols), 2)
            return df_imp

    def explain_sample_shap(self, model: Any, X_sample: pd.DataFrame, max_display: int = 5) -> Dict[str, Any]:
        """Calculates SHAP values for sample observations with graceful fallback."""
        X_mat = X_sample[self.feature_cols].fillna(0.0)
        if HAS_SHAP:
            try:
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_mat)
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]

                mean_abs_shap = np.abs(shap_values).mean(axis=0)
                df_shap = pd.DataFrame({
                    "feature": self.feature_cols,
                    "mean_abs_shap": mean_abs_shap
                }).sort_values(by="mean_abs_shap", ascending=False).head(max_display)

                top_features = df_shap.to_dict(orient="records")
                logger.info(f"SHAP explanation completed. Top driver: '{top_features[0]['feature']}'.")
                return {
                    "top_feature_drivers": top_features,
                    "base_value": float(explainer.expected_value) if hasattr(explainer, "expected_value") else 0.0
                }
            except Exception as e:
                logger.warning(f"SHAP calculation fallback: {e}")

        imp_df = self.get_tree_feature_importance(model).head(max_display)
        return {"top_feature_drivers": imp_df.to_dict(orient="records")}
