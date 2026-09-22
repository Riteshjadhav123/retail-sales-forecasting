"""
RetailMind-X Model & Decision Explainability Engine.
Provides DecisionExplanationEngine for business rationale (Why Reorder, Why This Quantity, Risk Drivers)
and ModelExplainer for SHAP / Tree-based feature importances.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from app.core.logging import get_logger

logger = get_logger("decision_explainer")

try:
    import shap
    HAS_SHAP = True
except Exception:
    HAS_SHAP = False

class DecisionExplanationEngine:
    """
    Structured Explanation Engine answering core business questions:
    - WHY SHOULD I REORDER?
    - WHY THIS QUANTITY?
    - WHY IS THIS PRODUCT HIGH RISK?
    - WHY DID FORECAST CHANGE?
    """

    def explain_reorder_decision(self, record: Dict[str, Any]) -> Dict[str, str]:
        """Provides structured answers for inventory reorder decisions."""
        s_id = record["series_id"]
        stock = record["current_stock"]
        rop = record["reorder_point"]
        eoq = record.get("economic_order_quantity", record.get("eoq", 50.0))
        rec_qty = record["recommended_order_quantity"]
        risk_score = record["composite_risk_score"]
        status = record["reorder_status"]

        # 1. Why Should I Reorder?
        if status == "REORDER_NOW":
            q1 = f"Reorder triggered because current stock level ({stock:.1f} units) is at or below the calculated Reorder Point ({rop:.1f} units). Delaying reorder exposes the product to stockout risk."
        elif status == "OVERSTOCKED":
            q1 = f"No reorder required. Current stock ({stock:.1f} units) exceeds maximum target inventory ({rop + eoq:.1f} units)."
        else:
            q1 = f"No immediate reorder needed. Current stock ({stock:.1f} units) is safely above the Reorder Point ({rop:.1f} units)."

        # 2. Why This Quantity?
        if rec_qty > 0:
            q2 = f"Recommended quantity of {rec_qty:.1f} units balances fixed ordering cost ($50) against annual holding costs, restoring inventory to target level (ROP + EOQ)."
        else:
            q2 = "Recommended quantity is 0 units because current inventory is sufficient to cover expected lead-time demand."

        # 3. Why Is This Product High Risk?
        stockout_r = record.get("stockout_risk", 0.0)
        overstock_r = record.get("overstock_risk", 0.0)
        q3 = f"Composite risk score is {risk_score:.1f}/100. Key drivers: Stockout Risk = {stockout_r:.1f}%, Overstock Risk = {overstock_r:.1f}%."

        # 4. Why Did Forecast Change?
        q4 = "Forecast reflects recent 7-day trend changes, demand volatility, and promotional discount factors incorporated by the adaptive model router."

        return {
            "series_id": s_id,
            "WHY_SHOULD_I_REORDER": q1,
            "WHY_THIS_QUANTITY": q2,
            "WHY_IS_THIS_HIGH_RISK": q3,
            "WHY_DID_FORECAST_CHANGE": q4
        }


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
