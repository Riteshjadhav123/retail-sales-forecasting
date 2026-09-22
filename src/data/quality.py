import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger("data_quality")

class DataQualityEngine:
    """Automated Data Quality Assessment Engine for RetailMind-X."""

    def __init__(self, df: pd.DataFrame, date_col: str = "Order Date", sales_col: str = "Sales"):
        self.df = df.copy()
        self.date_col = date_col
        self.sales_col = sales_col

    def run_assessment(self) -> Dict[str, Any]:
        """Runs comprehensive data quality checks and returns report dictionary."""
        df = self.df
        row_count = len(df)
        col_count = len(df.columns)

        if row_count == 0 or col_count == 0:
            return self._empty_assessment()

        # Fallback date_col & sales_col if mapped columns missing
        date_c = self.date_col if self.date_col in df.columns else (
            [c for c in df.columns if any(m in c.lower() for m in ["date", "time", "day"])][0]
            if [c for c in df.columns if any(m in c.lower() for m in ["date", "time", "day"])]
            else df.columns[0]
        )

        sales_c = self.sales_col if self.sales_col in df.columns else (
            [c for c in df.columns if any(m in c.lower() for m in ["sales", "revenue", "quant", "unit"])][0]
            if [c for c in df.columns if any(m in c.lower() for m in ["sales", "revenue", "quant", "unit"])]
            else df.columns[-1]
        )

        # 1. Missing Values
        null_counts = df.isnull().sum().to_dict()
        total_missing = sum(null_counts.values())
        missing_pct = float((total_missing / (row_count * col_count)) * 100.0) if row_count * col_count > 0 else 0.0

        # 2. Duplicates
        duplicate_count = int(df.duplicated().sum())

        # 3. Date Checks & Coverage
        date_series = pd.to_datetime(df[date_c], errors="coerce")
        invalid_dates_count = int(date_series.isnull().sum())
        min_date = date_series.min().strftime("%Y-%m-%d") if date_series.notnull().any() else "N/A"
        max_date = date_series.max().strftime("%Y-%m-%d") if date_series.notnull().any() else "N/A"
        
        # 4. Numerical & Sales Anomalies
        sales = pd.to_numeric(df[sales_c], errors="coerce")
        invalid_numerical_count = int(sales.isnull().sum())
        negative_sales_count = int((sales < 0).sum())
        zero_sales_count = int((sales == 0).sum())

        # 5. Outliers Detection (IQR method)
        valid_sales = sales.dropna()
        q1 = float(valid_sales.quantile(0.25)) if len(valid_sales) > 0 else 0.0
        q3 = float(valid_sales.quantile(0.75)) if len(valid_sales) > 0 else 0.0
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_count = int(((valid_sales < lower_bound) | (valid_sales > upper_bound)).sum())

        # 6. Data Types & Uniques
        data_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
        unique_products = int(df["Product ID"].nunique()) if "Product ID" in df.columns else (int(df["Sub-Category"].nunique()) if "Sub-Category" in df.columns else 0)
        unique_stores = int(df["Region"].nunique()) if "Region" in df.columns else (int(df["Country"].nunique()) if "Country" in df.columns else 0)
        unique_categories = int(df["Category"].nunique()) if "Category" in df.columns else 0

        # 7. Quality Score (0-100) & Status Synthesis
        dup_pct = float((duplicate_count / row_count) * 100.0) if row_count > 0 else 0.0
        invalid_date_pct = float((invalid_dates_count / row_count) * 100.0) if row_count > 0 else 0.0
        outlier_pct = float((outlier_count / row_count) * 100.0) if row_count > 0 else 0.0

        score_deduction = (missing_pct * 0.5) + (dup_pct * 0.5) + (invalid_date_pct * 1.0) + (outlier_pct * 0.2)
        quality_score = round(max(0.0, min(100.0, 100.0 - score_deduction)), 1)

        if quality_score >= 85.0:
            quality_status = "GOOD"
        elif quality_score >= 65.0:
            quality_status = "WARNING"
        else:
            quality_status = "CRITICAL"

        explanations = []
        if total_missing == 0:
            explanations.append("✓ Zero missing cells detected across dataset.")
        else:
            explanations.append(f"⚠ {total_missing:,} missing values ({missing_pct:.2f}%) detected.")

        if duplicate_count == 0:
            explanations.append("✓ Zero duplicate rows detected.")
        else:
            explanations.append(f"⚠ {duplicate_count:,} duplicate records ({dup_pct:.2f}%) detected.")

        if invalid_dates_count == 0:
            explanations.append("✓ 100% valid timestamp coverage.")
        else:
            explanations.append(f"⚠ {invalid_dates_count} unparseable timestamps found.")

        explanations.append(f"ℹ {outlier_count} IQR sales outliers ({outlier_pct:.1f}%) identified and prepared for clipping.")

        # Synthesis
        report = {
            "quality_score": quality_score,
            "quality_status": quality_status,
            "quality_explanations": explanations,
            "summary": {
                "row_count": row_count,
                "column_count": col_count,
                "total_missing_cells": total_missing,
                "missing_percentage": round(missing_pct, 4),
                "duplicate_count": duplicate_count,
                "date_coverage": {
                    "start_date": min_date,
                    "end_date": max_date,
                    "invalid_dates": invalid_dates_count
                },
                "uniques": {
                    "categories": unique_categories,
                    "products": unique_products,
                    "regions_stores": unique_stores
                }
            },
            "numerical_anomalies": {
                "invalid_numerical_values": invalid_numerical_count,
                "negative_sales": negative_sales_count,
                "zero_sales_records": zero_sales_count,
                "outliers_iqr": {
                    "q1": round(q1, 2),
                    "q3": round(q3, 2),
                    "iqr": round(iqr, 2),
                    "outlier_count": outlier_count,
                    "outlier_percentage": round((outlier_count / row_count) * 100.0, 2) if row_count > 0 else 0.0
                }
            },
            "null_breakdown_by_column": {col: int(cnt) for col, cnt in null_counts.items() if cnt > 0},
            "data_types": data_types
        }
        return report

    def generate_reports(self, json_path: str = "reports/quality/quality_report.json", md_path: str = "reports/quality/quality_report.md") -> Dict[str, Any]:
        """Runs assessment and outputs JSON and Markdown report artifacts."""
        report = self.run_assessment()

        # Save JSON
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Save Markdown
        md_content = f"""# RetailMind-X Data Quality Assessment Report

## Executive Summary
- **Row Count**: `{report['summary']['row_count']:,}`
- **Column Count**: `{report['summary']['column_count']}`
- **Overall Missing Percentage**: `{report['summary']['missing_percentage']}%`
- **Duplicate Row Count**: `{report['summary']['duplicate_count']:,}`
- **Date Range**: `{report['summary']['date_coverage']['start_date']}` to `{report['summary']['date_coverage']['end_date']}`
- **Unique Products**: `{report['summary']['uniques']['products']:,}`
- **Unique Regions/Stores**: `{report['summary']['uniques']['regions_stores']}`

## Data Quality Diagnostics
- **Invalid Dates**: `{report['summary']['date_coverage']['invalid_dates']}`
- **Negative Sales**: `{report['numerical_anomalies']['negative_sales']}`
- **Zero Sales Records**: `{report['numerical_anomalies']['zero_sales_records']}`
- **Sales Outliers (IQR)**: `{report['numerical_anomalies']['outliers_iqr']['outlier_count']:,}` ({report['numerical_anomalies']['outliers_iqr']['outlier_percentage']}%)

## Column Null Count Breakdown
"""
        nulls = report["null_breakdown_by_column"]
        if not nulls:
            md_content += "- *No missing values detected across any column.*\n"
        else:
            for col, count in nulls.items():
                md_content += f"- **{col}**: `{count:,}` missing\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Data quality reports generated: '{json_path}' and '{md_path}'.")
        return report

    def _empty_assessment(self) -> Dict[str, Any]:
        return {
            "quality_score": 100.0,
            "quality_status": "GOOD",
            "quality_explanations": ["✓ No dataset loaded."],
            "summary": {
                "row_count": 0, "column_count": 0, "total_missing_cells": 0,
                "missing_percentage": 0.0, "duplicate_count": 0,
                "date_coverage": {"start_date": "N/A", "end_date": "N/A", "invalid_dates": 0},
                "uniques": {"categories": 0, "products": 0, "regions_stores": 0}
            },
            "numerical_anomalies": {
                "invalid_numerical_values": 0, "negative_sales": 0, "zero_sales_records": 0,
                "outliers_iqr": {"q1": 0.0, "q3": 0.0, "iqr": 0.0, "outlier_count": 0, "outlier_percentage": 0.0}
            },
            "null_breakdown_by_column": {},
            "data_types": {}
        }
