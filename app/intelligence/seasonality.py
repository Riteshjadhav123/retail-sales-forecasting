"""
RetailMind-X: Retail Seasonal Intelligence Engine.
Computes day-of-week, monthly, and peak period demand patterns with real baseline comparison.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from app.data.session_manager import SESSION

class SeasonalityEngine:
    """Retail Seasonal Intelligence Engine."""

    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df

    @classmethod
    def calculate_seasonality(
        cls,
        df: Optional[pd.DataFrame] = None,
        date_col: Optional[str] = None,
        target_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates day-of-week lift and monthly seasonal patterns."""
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

        if not date_col:
            date_col = SESSION.column_mapping.get("Date", "Order Date")
            if date_col not in work_df.columns:
                date_cands = [c for c in work_df.columns if "date" in c.lower() or "time" in c.lower()]
                date_col = date_cands[0] if date_cands else work_df.columns[0]

        if not target_col:
            target_col = SESSION.column_mapping.get("Sales", "Sales")
            if target_col not in work_df.columns:
                num_cols = work_df.select_dtypes(include=[np.number]).columns
                target_col = num_cols[-1] if len(num_cols) > 0 else work_df.columns[-1]

        work = work_df.copy()
        work["_dt"] = pd.to_datetime(work[date_col], errors="coerce")
        work = work.dropna(subset=["_dt"])

        if len(work) < 7:
            return {
                "available": False,
                "reason": "Insufficient temporal observations for seasonality analysis (requires >= 7 dates)."
            }

        work["_sales"] = pd.to_numeric(work[target_col], errors="coerce").fillna(0.0)
        overall_mean = float(work["_sales"].mean()) if not work.empty else 1.0
        overall_mean = max(overall_mean, 1e-5)

        # Day of Week Analysis
        work["day_name"] = work["_dt"].dt.day_name()
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow_avg = work.groupby("day_name")["_sales"].mean().reindex(days_order).fillna(overall_mean)
        
        dow_patterns = []
        for day, avg_val in dow_avg.items():
            lift_pct = round(((avg_val - overall_mean) / overall_mean) * 100.0, 1)
            dow_patterns.append({
                "day": day,
                "day_name": day,
                "avg_sales": round(float(avg_val), 2),
                "lift_pct": lift_pct,
                "lift_vs_baseline_pct": lift_pct
            })

        best_day = max(dow_patterns, key=lambda x: x["avg_sales"])
        lowest_day = min(dow_patterns, key=lambda x: x["avg_sales"])

        # Monthly Pattern
        work["month_name"] = work["_dt"].dt.strftime("%b")
        months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_avg = work.groupby("month_name")["_sales"].mean().reindex(months_order).dropna()
        
        monthly_patterns = []
        for m, avg_val in month_avg.items():
            m_lift = round(((avg_val - overall_mean) / overall_mean) * 100.0, 1)
            monthly_patterns.append({
                "month": m,
                "month_name": m,
                "avg_sales": round(float(avg_val), 2),
                "lift_pct": m_lift,
                "lift_vs_baseline_pct": m_lift
            })

        return {
            "available": True,
            "overall_mean_sales": round(overall_mean, 2),
            "baseline_average_demand": round(overall_mean, 2),
            "peak_day": best_day["day"],
            "peak_day_lift": f"+{best_day['lift_pct']}% vs baseline" if best_day["lift_pct"] > 0 else f"{best_day['lift_pct']}% vs baseline",
            "lowest_day": lowest_day["day"],
            "lowest_day_lift": f"{lowest_day['lift_pct']}% vs baseline",
            "day_of_week": dow_patterns,
            "day_of_week_patterns": dow_patterns,
            "monthly": monthly_patterns,
            "monthly_patterns": monthly_patterns
        }

    def analyze_seasonality(self) -> Dict[str, Any]:
        return self.calculate_seasonality(df=self.df)
