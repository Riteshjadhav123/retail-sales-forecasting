"""
RetailMind-X: Dynamic Pareto ABC Inventory Classification Engine
Categorizes SKUs into Class A (Top 80% revenue/volume), Class B (Next 15%), and Class C (Bottom 5%)
derived strictly from the active dataset session.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger("abc_analysis")

class ABCInventoryClassifier:
    """Dynamic ABC Inventory Classifier based on Empirical Pareto Value Distribution."""

    def __init__(self, df: pd.DataFrame, series_col: str = "series_id", sales_col: str = "Sales"):
        self.df = df.copy()
        self.series_col = series_col if series_col in self.df.columns else self.df.columns[0]
        self.sales_col = sales_col if sales_col in self.df.columns else self.df.columns[-1]

    def classify(self) -> Dict[str, Any]:
        """Executes Pareto ABC classification and returns summary matrix."""
        df = self.df
        if len(df) == 0:
            return self._empty_result()

        # Aggregate total revenue / volume per series
        df[self.sales_col] = pd.to_numeric(df[self.sales_col], errors="coerce").fillna(0.0)
        grouped = df.groupby(self.series_col)[self.sales_col].sum().reset_index()
        grouped.columns = ["series_id", "total_value"]
        
        total_aggregate = float(grouped["total_value"].sum())
        if total_aggregate <= 0:
            total_aggregate = 1.0

        # Sort descending
        grouped = grouped.sort_values("total_value", ascending=False).reset_index(drop=True)
        
        # Cumulative metrics
        grouped["value_share_pct"] = (grouped["total_value"] / total_aggregate) * 100.0
        grouped["cum_value_share_pct"] = grouped["value_share_pct"].cumsum()

        # Class allocation
        def assign_class(cum_pct):
            if cum_pct <= 80.0:
                return "A"
            elif cum_pct <= 95.0:
                return "B"
            else:
                return "C"

        grouped["abc_class"] = grouped["cum_value_share_pct"].apply(assign_class)

        # Class Summaries
        class_a = grouped[grouped["abc_class"] == "A"]
        class_b = grouped[grouped["abc_class"] == "B"]
        class_c = grouped[grouped["abc_class"] == "C"]

        a_val = float(class_a["total_value"].sum())
        b_val = float(class_b["total_value"].sum())
        c_val = float(class_c["total_value"].sum())

        total_skus = len(grouped)

        result = {
            "methodology": "Pareto Analysis (Class A: <=80% cumulative value, Class B: 80-95%, Class C: >95%)",
            "total_aggregate_value": round(total_aggregate, 2),
            "total_skus": total_skus,
            "classes": {
                "A": {
                    "class_name": "Class A (Tight Control)",
                    "sku_count": len(class_a),
                    "sku_share_pct": round((len(class_a) / max(1, total_skus)) * 100, 1),
                    "total_value": round(a_val, 2),
                    "value_share_pct": round((a_val / total_aggregate) * 100, 1),
                    "recommended_policy": "Strict inventory control, frequent cycle counts, high target service level (95-99%)."
                },
                "B": {
                    "class_name": "Class B (Moderate Control)",
                    "sku_count": len(class_b),
                    "sku_share_pct": round((len(class_b) / max(1, total_skus)) * 100, 1),
                    "total_value": round(b_val, 2),
                    "value_share_pct": round((b_val / total_aggregate) * 100, 1),
                    "recommended_policy": "Moderate control, bi-weekly review, standard service level (90-95%)."
                },
                "C": {
                    "class_name": "Class C (Simplified Control)",
                    "sku_count": len(class_c),
                    "sku_share_pct": round((len(class_c) / max(1, total_skus)) * 100, 1),
                    "total_value": round(c_val, 2),
                    "value_share_pct": round((c_val / total_aggregate) * 100, 1),
                    "recommended_policy": "Automated reordering, bulk purchasing, standard service level (85-90%)."
                }
            },
            "sku_details": grouped.head(50).to_dict(orient="records")
        }
        return result

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "methodology": "Pareto Analysis",
            "total_aggregate_value": 0.0,
            "total_skus": 0,
            "classes": {
                "A": {"sku_count": 0, "value_share_pct": 0.0, "total_value": 0.0},
                "B": {"sku_count": 0, "value_share_pct": 0.0, "total_value": 0.0},
                "C": {"sku_count": 0, "value_share_pct": 0.0, "total_value": 0.0}
            },
            "sku_details": []
        }
