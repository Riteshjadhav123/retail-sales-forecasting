"""
RetailMind-X: Retail Demand Anomaly Detection Engine
Detects demand spikes, sharp volume drops, and extreme SKU deviations with causal attribution.
100% session-grounded.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from src.data.session_manager import SESSION


class DemandAnomalyEngine:
    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df

    @classmethod
    def detect_anomalies(
        cls,
        df: Optional[pd.DataFrame] = None,
        date_col: Optional[str] = None,
        target_col: Optional[str] = None,
        promo_col: Optional[str] = None,
        threshold_std: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Scans time series per SKU to detect significant demand spikes and drops."""
        work_df = df
        if work_df is None:
            if SESSION.clean_df is not None:
                work_df = SESSION.clean_df
            elif SESSION.raw_df is not None:
                work_df = SESSION.raw_df
            else:
                return []

        if work_df is None or work_df.empty:
            return []

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

        series_col = SESSION.column_mapping.get("Product", "sku")
        if series_col not in work_df.columns:
            series_cands = [c for c in work_df.columns if any(w in c.lower() for w in ["sku", "product", "series", "item"])]
            series_col = series_cands[0] if series_cands else work_df.columns[0]

        if not promo_col:
            promo_col = SESSION.column_mapping.get("Promotion")
        has_promo = promo_col is not None and promo_col in work_df.columns

        anomalies = []
        unique_skus = work_df[series_col].astype(str).unique() if series_col in work_df.columns else ["AGGREGATE"]

        for sku in unique_skus[:10]:
            s_df = work_df[work_df[series_col].astype(str) == sku].copy() if series_col in work_df.columns else work_df.copy()
            if len(s_df) < 5:
                continue

            if date_col in s_df.columns and pd.api.types.is_datetime64_any_dtype(s_df[date_col]):
                s_df = s_df.sort_values(by=date_col)
            
            s_sales = pd.to_numeric(s_df[target_col], errors="coerce").fillna(0.0)
            mean_demand = float(s_sales.mean())
            std_demand = float(s_sales.std()) if len(s_sales) > 1 else max(1.0, mean_demand * 0.25)
            
            if std_demand <= 1e-5:
                continue

            recent_rows = s_df.tail(40)
            for idx, row in recent_rows.iterrows():
                val = float(pd.to_numeric(row.get(target_col, 0.0), errors="coerce") or 0.0)
                z_score = (val - mean_demand) / (std_demand + 1e-5)
                
                if abs(z_score) >= threshold_std:
                    is_promo = False
                    if has_promo:
                        p_val = str(row.get(promo_col, "")).lower()
                        is_promo = p_val in ["1", "true", "yes", "promo"]

                    date_val = str(row.get(date_col, idx))
                    if isinstance(row.get(date_col), pd.Timestamp):
                        date_val = row[date_col].strftime("%Y-%m-%d")

                    dev_pct = round(((val - mean_demand) / (mean_demand + 1e-5)) * 100.0, 1)

                    if z_score > 0:
                        anom_type = "SPIKE"
                        attr = "Potential promotional or seasonal surge" if is_promo else "Unusual demand surge (investigate marketing/stocking)"
                    else:
                        anom_type = "DROP"
                        attr = "Potential stockout, supply outage, or channel disruption"

                    anomalies.append({
                        "sku": sku,
                        "date": date_val,
                        "type": anom_type,
                        "value": round(val, 2),
                        "baseline_mean": round(mean_demand, 2),
                        "z_score": round(z_score, 2),
                        "deviation_pct": dev_pct,
                        "severity": "HIGH" if abs(z_score) >= 3.0 else ("MEDIUM" if abs(z_score) >= 2.5 else "LOW"),
                        "causal_attribution": attr
                    })

        return anomalies
