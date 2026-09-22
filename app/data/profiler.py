"""
RetailMind-X: Flexible Dataset Profiler & Semantic Column Mapping Engine
Inspects uploaded retail datasets (CSV, Parquet, XLSX) and detects schema,
frequency, data types, capability matrix, and semantic confidence.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from app.core.logging import get_logger

logger = get_logger("profiler")

class DatasetProfiler:
    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df if df is not None else pd.DataFrame()
        
    def profile(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Alias for profile_schema supporting passing df directly."""
        if df is not None:
            self.df = df
        return self.profile_schema()

    def profile_schema(self) -> Dict[str, Any]:
        """Auto-detects candidate column mappings, frequency, and capability matrix."""
        cols = self.df.columns.tolist() if self.df is not None else []
        cols_lower = [str(c).lower().strip() for c in cols]
        
        detected = {
            "Date": self._find_column(cols, cols_lower, [
                "date", "order date", "order_date", "invoicedate", "invoice_date",
                "transaction_date", "transactiondate", "timestamp", "time", "day",
                "orderdate", "sales_date"
            ]),
            "Product": self._find_column(cols, cols_lower, [
                "series_id", "product id", "product_id", "sku", "stockcode", "stock_code",
                "product", "item_id", "item", "product name", "item_name", "model",
                "product_name"
            ]),
            "Sales": self._find_column(cols, cols_lower, [
                "sales", "revenue", "amount", "total_sales", "turnover", "net_sales",
                "sales_clamped", "total_amount", "sales_amount", "revenue_amount"
            ]),
            "Quantity": self._find_column(cols, cols_lower, [
                "quantity", "units", "volume", "qty", "demand", "units_sold"
            ]),
            "Store": self._find_column(cols, cols_lower, [
                "region", "store", "market", "store_id", "branch", "location",
                "country", "store_name", "branch_id", "shop"
            ]),
            "Category": self._find_column(cols, cols_lower, [
                "category", "sub-category", "sub_category", "vertical", "department",
                "segment", "product_category", "class"
            ]),
            "Price": self._find_column(cols, cols_lower, [
                "unit_price", "unit price", "price", "unitprice", "cost", "selling_price"
            ]),
            "Discount": self._find_column(cols, cols_lower, [
                "discount", "promo_discount", "rebate", "discount_pct", "discount_percentage"
            ]),
            "Promotion": self._find_column(cols, cols_lower, [
                "promo", "promotion", "is_promo", "on_sale", "campaign", "promotion_flag"
            ]),
            "Supplier": self._find_column(cols, cols_lower, [
                "supplier", "supplier_id", "vendor", "supplier_name"
            ]),
            "Inventory": self._find_column(cols, cols_lower, [
                "current_stock", "stock", "inventory", "on_hand", "stock_level", "available_stock"
            ]),
            "LeadTime": self._find_column(cols, cols_lower, [
                "lead_time", "leadtime", "supplier_lead_time", "delivery_days"
            ])
        }
        
        # Required columns validation: Date and (Sales or Quantity)
        has_date = detected["Date"] is not None
        has_sales_or_qty = detected["Sales"] is not None or detected["Quantity"] is not None

        if not has_date or not has_sales_or_qty:
            is_valid = False
            confidence = 0.0
            error_msg = "Analysis cannot start because a valid date column and/or sales/demand column could not be identified."
        else:
            is_valid = True
            detected_cnt = sum(1 for v in detected.values() if v is not None)
            confidence = min(1.0, round(0.75 + (detected_cnt / len(detected)) * 0.25, 2))
            error_msg = None

        # Determine target type (MONETARY vs UNIT DEMAND)
        if detected["Sales"] is not None:
            target_col = detected["Sales"]
            target_type = "monetary"
            target_display = "Monetary (Sales / Revenue)"
        elif detected["Quantity"] is not None:
            target_col = detected["Quantity"]
            target_type = "units"
            target_display = "Unit Demand (Quantity / Units Sold)"
            detected["Sales"] = detected["Quantity"]
        else:
            target_col = None
            target_type = "monetary"
            target_display = "Monetary"

        # Frequency Detection
        detected_frequency = "Daily"
        if has_date:
            try:
                date_series = pd.to_datetime(self.df[detected["Date"]], errors="coerce").dropna().drop_duplicates().sort_values()
                if len(date_series) > 3:
                    diffs = date_series.diff().dt.days.dropna()
                    median_diff = float(diffs.median())
                    if median_diff <= 1.5:
                        detected_frequency = "Daily"
                    elif 6.0 <= median_diff <= 8.0:
                        detected_frequency = "Weekly"
                    elif 27.0 <= median_diff <= 32.0:
                        detected_frequency = "Monthly"
                    else:
                        detected_frequency = f"Custom ({round(median_diff, 1)}d interval)"
            except Exception as ex:
                logger.debug(f"Frequency detection fallback: {ex}")
                detected_frequency = "Daily"

        # Semantic Mapping Confidence & Reasons
        semantic_metadata = {}
        for role, mapped_col in detected.items():
            if mapped_col:
                col_dtype = str(self.df[mapped_col].dtype)
                col_nunique = int(self.df[mapped_col].nunique())
                if role == "Date":
                    reason = "temporal keyword + datetime parser match"
                    conf_pct = 98
                elif role in ["Sales", "Price"]:
                    reason = "numeric + revenue/monetary keywords match"
                    conf_pct = 96
                elif role in ["Quantity", "Inventory", "LeadTime"]:
                    reason = "numeric + volume/stock keywords match"
                    conf_pct = 94
                elif role in ["Product", "Store", "Category", "Supplier"]:
                    reason = f"categorical/identifier keywords match (cardinality={col_nunique})"
                    conf_pct = 92
                else:
                    reason = "keyword semantic pattern match"
                    conf_pct = 88
                
                meta_item = {
                    "mapped_column": mapped_col,
                    "confidence_pct": conf_pct,
                    "role_description": role,
                    "role": role.upper(),
                    "reason": reason,
                    "data_type": col_dtype
                }
                semantic_metadata[role] = meta_item
                semantic_metadata[mapped_col] = meta_item
            else:
                semantic_metadata[role] = {
                    "mapped_column": None,
                    "confidence_pct": 0,
                    "role_description": role,
                    "role": role.upper(),
                    "reason": "Not found in dataset schema",
                    "data_type": "N/A"
                }

        # Dataset Capability Matrix
        capability_matrix = {
            "Forecasting": {
                "enabled": is_valid,
                "label": "Time-Series Forecasting",
                "status": "AVAILABLE" if is_valid else "UNAVAILABLE",
                "reason": f"Active target: {target_col} ({target_type})"
            },
            "Inventory_Optimization": {
                "enabled": detected["Product"] is not None,
                "label": "Inventory Optimization & ROP",
                "status": "AVAILABLE" if detected["Product"] else "LIMITED",
                "reason": "Product SKU identifiers mapped" if detected["Product"] else "Requires product column for SKU-level optimization"
            },
            "Actual_Inventory": {
                "enabled": detected["Inventory"] is not None,
                "label": "Actual Stock Position",
                "status": "AVAILABLE" if detected["Inventory"] else "UNAVAILABLE",
                "reason": "Actual on-hand inventory data available" if detected["Inventory"] else "Inventory data unavailable (Simulated / Assumed)"
            },
            "Price_Analysis": {
                "enabled": detected["Price"] is not None,
                "label": "Price Sensitivity & Elasticity",
                "status": "AVAILABLE" if detected["Price"] else "UNAVAILABLE",
                "reason": "Unit price column mapped" if detected["Price"] else "Not available for this dataset"
            },
            "Discount_Impact": {
                "enabled": detected["Discount"] is not None,
                "label": "Discount Impact Analysis",
                "status": "AVAILABLE" if detected["Discount"] else "UNAVAILABLE",
                "reason": "Discount column mapped" if detected["Discount"] else "Not available for this dataset"
            },
            "Promotion_Analysis": {
                "enabled": detected["Promotion"] is not None,
                "label": "Promotion Campaign Lift",
                "status": "AVAILABLE" if detected["Promotion"] else "UNAVAILABLE",
                "reason": "Promotion indicators mapped" if detected["Promotion"] else "Not available for this dataset"
            },
            "Supplier_Intelligence": {
                "enabled": detected["Supplier"] is not None,
                "label": "Supplier Lead-Time Tracking",
                "status": "AVAILABLE" if detected["Supplier"] else "UNAVAILABLE",
                "reason": "Supplier/vendor identifiers mapped" if detected["Supplier"] else "Not available for this dataset"
            },
            "Lead_Time_Analysis": {
                "enabled": detected["LeadTime"] is not None,
                "label": "Dynamic Lead Time Intelligence",
                "status": "AVAILABLE" if detected["LeadTime"] else "ASSUMED",
                "reason": "Supplier lead time mapped" if detected["LeadTime"] else "Default 10-day supplier lead time assumed"
            },
            # Boolean convenience keys
            "forecasting": is_valid,
            "inventory_intelligence": detected["Product"] is not None,
            "seasonality_intelligence": detected["Date"] is not None,
            "promotional_impact": detected["Promotion"] is not None,
            "price_elasticity": detected["Price"] is not None,
            "demand_anomalies": is_valid,
            "data_drift_monitoring": is_valid
        }

        # Build mapping status dictionary
        mapping_status = {}
        for req_field, mapped_col in detected.items():
            mapping_status[req_field] = {
                "dataset_column": mapped_col,
                "is_detected": mapped_col is not None,
                "data_type": str(self.df[mapped_col].dtype) if mapped_col and mapped_col in self.df.columns else "N/A"
            }
            
        logger.info(f"Dataset profiling completed. Detected {sum(1 for v in detected.values() if v is not None)} / {len(detected)} fields. Target: {target_col} ({target_type}). Frequency: {detected_frequency}. Confidence: {confidence}. Valid: {is_valid}")
        
        return {
            "is_valid": is_valid,
            "confidence_score": confidence,
            "error_message": error_msg,
            "target_column": target_col,
            "target_type": target_type,
            "target_display": target_display,
            "detected_frequency": detected_frequency,
            "columns_available": cols,
            "detected_mappings": detected,
            "mapping_status": mapping_status,
            "semantic_metadata": semantic_metadata,
            "capability_matrix": capability_matrix
        }
        
    def _find_column(self, cols: List[str], cols_lower: List[str], candidates: List[str]) -> Optional[str]:
        for cand in candidates:
            if cand in cols_lower:
                idx = cols_lower.index(cand)
                return cols[idx]
        # Clean snake_case match
        clean_cols = [c.replace(" ", "_").replace("-", "_") for c in cols_lower]
        for cand in candidates:
            clean_cand = cand.replace(" ", "_").replace("-", "_")
            if clean_cand in clean_cols:
                idx = clean_cols.index(clean_cand)
                return cols[idx]
        # Partial match fallback (avoid matching product codes like 'stockcode' as inventory stock)
        for cand in candidates:
            for i, col_l in enumerate(cols_lower):
                if cand in col_l:
                    if cand == "stock" and ("code" in col_l or "id" in col_l):
                        continue
                    return cols[i]
        return None
