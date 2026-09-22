"""
RetailMind-X: Promotion & Price Intelligence Engine.
Analyzes promotional lift and observed price-demand sensitivity when supported by the active dataset.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from app.data.session_manager import SESSION

class PromotionPriceEngine:
    """Evaluates promotional lift and price elasticity based on available schema."""

    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df

    @classmethod
    def analyze(
        cls,
        df: Optional[pd.DataFrame] = None,
        date_col: Optional[str] = None,
        target_col: Optional[str] = None,
        promo_col: Optional[str] = None,
        price_col: Optional[str] = None,
        discount_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluates promotional lift and price elasticity based on available schema."""
        work_df = df
        if work_df is None:
            if SESSION.clean_df is not None:
                work_df = SESSION.clean_df
            elif SESSION.raw_df is not None:
                work_df = SESSION.raw_df
            else:
                return {"available": False, "reason": "No active dataset loaded"}

        if work_df is None or work_df.empty:
            return {"available": False, "reason": "No active dataset loaded"}

        if not target_col:
            target_col = SESSION.column_mapping.get("Sales", "Sales")
            if target_col not in work_df.columns:
                target_col = work_df.columns[-1]

        sales = pd.to_numeric(work_df[target_col], errors="coerce").fillna(0.0)

        # 1. Promotion Analysis
        if not promo_col:
            promo_col = SESSION.column_mapping.get("Promotion")
        
        has_promo = promo_col is not None and promo_col in work_df.columns
        if has_promo:
            promo_mask = work_df[promo_col].astype(str).str.lower().isin(["1", "true", "yes", "promo", "campaign"])
            promo_sales = sales[promo_mask]
            non_promo_sales = sales[~promo_mask]

            avg_promo = float(promo_sales.mean()) if not promo_sales.empty else 0.0
            avg_non_promo = float(non_promo_sales.mean()) if not non_promo_sales.empty else 0.0
            
            lift_pct = round(((avg_promo - avg_non_promo) / (avg_non_promo + 1e-5)) * 100.0, 1)

            promo_result = {
                "available": True,
                "promo_column": promo_col,
                "normal_demand_avg": round(avg_non_promo, 2),
                "promotional_demand_avg": round(avg_promo, 2),
                "estimated_lift_pct": lift_pct,
                "lift_pct": lift_pct,
                "observation": f"Promotions yield an observed {lift_pct:+}% shift in demand volume."
            }
        else:
            promo_result = {
                "available": False,
                "reason": "Not available for this dataset (No promotion/campaign column detected)."
            }

        # 2. Price Intelligence
        if not price_col:
            price_col = SESSION.column_mapping.get("Price")
        
        has_price = price_col is not None and price_col in work_df.columns
        if has_price:
            price = pd.to_numeric(work_df[price_col], errors="coerce").fillna(0.0)
            valid_mask = (price > 0) & (sales > 0)
            
            if valid_mask.sum() > 5:
                corr = float(sales[valid_mask].corr(price[valid_mask]))
                corr = 0.0 if np.isnan(corr) else round(corr, 3)
                
                mean_p = float(price[valid_mask].mean())
                mean_q = float(sales[valid_mask].mean())
                slope = float(np.polyfit(price[valid_mask], sales[valid_mask], 1)[0]) if len(price[valid_mask]) > 2 else 0.0
                elasticity = round((slope * mean_p) / (mean_q + 1e-5), 2)

                price_result = {
                    "available": True,
                    "price_column": price_col,
                    "avg_price": round(mean_p, 2),
                    "price_demand_correlation": corr,
                    "estimated_elasticity": elasticity,
                    "label": "Observed price sensitivity across sales transactions",
                    "relationship_summary": f"Observed relationship indicates elasticity of {elasticity} (correlation: {corr}).",
                    "disclaimer": "Observed empirical relationship; causality requires controlled A/B test pricing."
                }
            else:
                price_result = {
                    "available": False,
                    "reason": "Insufficient non-zero price and sales pairs for elasticity analysis."
                }
        else:
            price_result = {
                "available": False,
                "reason": "Not available for this dataset (No unit price column detected)."
            }

        is_available = promo_result.get("available", False) or price_result.get("available", False)

        return {
            "available": is_available,
            "promotional_lift": promo_result,
            "promotion_intelligence": promo_result,
            "price_elasticity": price_result,
            "price_intelligence": price_result
        }

    def analyze_promotion_and_price(self) -> Dict[str, Any]:
        return self.analyze(df=self.df)
