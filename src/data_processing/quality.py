"""
Data Quality Auditor for Vaidsys Retail Sales Forecasting.
Performs 11-point validation audit on raw sales datasets.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger("data_quality")

class DataQualityAuditor:
    """Rigorous Data Quality Audit Pipeline."""

    def __init__(self, raw_df: pd.DataFrame):
        self.df = raw_df.copy()
        self.report: Dict[str, Any] = {}

    def audit(self) -> Dict[str, Any]:
        """Runs complete 11-point data audit."""
        logger.info("Starting Data Quality Audit...")

        total_rows = len(self.df)
        total_cols = len(self.df.columns)

        missing_counts = self.df.isnull().sum().to_dict()
        duplicate_rows = int(self.df.duplicated().sum())

        # Date validation
        invalid_dates = 0
        min_date = "N/A"
        max_date = "N/A"
        if "Order Date" in self.df.columns:
            try:
                dates = pd.to_datetime(self.df["Order Date"], errors="coerce")
                invalid_dates = int(dates.isnull().sum())
                min_date = str(dates.min().date())
                max_date = str(dates.max().date())
            except Exception as e:
                logger.warning(f"Error checking dates: {e}")

        # Numerical anomalies
        negative_sales = int((self.df["Sales"] < 0).sum()) if "Sales" in self.df.columns else 0
        zero_sales = int((self.df["Sales"] == 0).sum()) if "Sales" in self.df.columns else 0
        negative_quantity = int((self.df["Quantity"] < 0).sum()) if "Quantity" in self.df.columns else 0

        # Unique counts
        skus = int(self.df["Product ID"].nunique()) if "Product ID" in self.df.columns else 0
        categories = int(self.df["Category"].nunique()) if "Category" in self.df.columns else 0
        markets = int(self.df["Market"].nunique()) if "Market" in self.df.columns else 0

        self.report = {
            "total_records": total_rows,
            "total_columns": total_cols,
            "duplicate_records": duplicate_rows,
            "missing_values": missing_counts,
            "invalid_dates": invalid_dates,
            "date_range": {"start": min_date, "end": max_date},
            "anomalies": {
                "negative_sales": negative_sales,
                "zero_sales": zero_sales,
                "negative_quantity": negative_quantity
            },
            "entities": {
                "unique_skus": skus,
                "unique_categories": categories,
                "unique_markets": markets
            },
            "quality_status": "PASSED" if duplicate_rows == 0 and invalid_dates == 0 else "WARNINGS_FOUND"
        }

        logger.info(f"Data Quality Audit Completed: {total_rows} rows, {skus} SKUs, Status={self.report['quality_status']}.")
        return self.report

    def export_report(self, output_dir: str = "reports/quality") -> str:
        """Exports report to JSON and Markdown."""
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, "quality_report.json")
        md_path = os.path.join(output_dir, "quality_report.md")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2)

        md_content = f"""# Data Quality Audit Report

**Status:** {self.report.get('quality_status')}  
**Total Records:** {self.report.get('total_records'):,}  
**Date Range:** {self.report.get('date_range', {}).get('start')} to {self.report.get('date_range', {}).get('end')}  

## Summary Checks
- **Duplicate Rows:** {self.report.get('duplicate_records')}
- **Invalid Dates:** {self.report.get('invalid_dates')}
- **Negative Sales:** {self.report.get('anomalies', {}).get('negative_sales')}
- **Zero Sales:** {self.report.get('anomalies', {}).get('zero_sales')}
- **Unique Products (SKUs):** {self.report.get('entities', {}).get('unique_skus')}
- **Unique Categories:** {self.report.get('entities', {}).get('unique_categories')}
- **Unique Markets:** {self.report.get('entities', {}).get('unique_markets')}
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return md_path
