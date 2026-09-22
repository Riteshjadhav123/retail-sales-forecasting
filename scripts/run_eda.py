"""
Historical Sales EDA Visualizations Generator for Vaidsys Retail Sales Forecasting.
Saves figures to visualizations/
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(".")
from src.utils.logger import get_logger

logger = get_logger("run_eda")

def generate_eda_visualizations(data_path: str = "data/raw/superstore.csv", output_dir: str = "visualizations"):
    os.makedirs(output_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")
    logger.info("Generating EDA Visualizations...")

    df = pd.read_csv(data_path, encoding="latin1")
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="mixed", errors="coerce")

    # 1. Daily, Weekly, Monthly Sales Trends
    df_daily = df.groupby("Order Date")["Sales"].sum().reset_index()
    df_weekly = df.set_index("Order Date").resample("W")["Sales"].sum().reset_index()
    df_monthly = df.set_index("Order Date").resample("ME")["Sales"].sum().reset_index()

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=False)
    axes[0].plot(df_daily["Order Date"], df_daily["Sales"], color="#1f77b4", linewidth=1.0)
    axes[0].set_title("Daily Total Sales Trend")
    axes[0].set_ylabel("Sales ($)")

    axes[1].plot(df_weekly["Order Date"], df_weekly["Sales"], color="#ff7f0e", linewidth=1.5)
    axes[1].set_title("Weekly Total Sales Trend")
    axes[1].set_ylabel("Sales ($)")

    axes[2].plot(df_monthly["Order Date"], df_monthly["Sales"], color="#2ca02c", linewidth=2.0, marker="o")
    axes[2].set_title("Monthly Total Sales Trend")
    axes[2].set_ylabel("Sales ($)")
    axes[2].set_xlabel("Date")

    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "daily_weekly_monthly_sales.png")
    fig.savefig(fig1_path, dpi=300)
    plt.close(fig)

    # 2. Category & Store / Market Sales
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    if "Category" in df.columns:
        cat_sales = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
        sns.barplot(x=cat_sales.values, y=cat_sales.index, ax=axes[0], palette="viridis")
        axes[0].set_title("Sales by Retail Category")
        axes[0].set_xlabel("Total Sales ($)")

    if "Market" in df.columns:
        mkt_sales = df.groupby("Market")["Sales"].sum().sort_values(ascending=False)
        sns.barplot(x=mkt_sales.values, y=mkt_sales.index, ax=axes[1], palette="magma")
        axes[1].set_title("Sales by Market Region")
        axes[1].set_xlabel("Total Sales ($)")

    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "category_store_sales.png")
    fig.savefig(fig2_path, dpi=300)
    plt.close(fig)

    # 3. Seasonality & Demand Fluctuations (Month vs Day of Week)
    df["month"] = df["Order Date"].dt.month
    df["day_of_week"] = df["Order Date"].dt.day_name()
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.boxplot(data=df, x="month", y="Sales", ax=axes[0], palette="crest", showfliers=False)
    axes[0].set_title("Monthly Sales Distribution (Seasonality)")
    axes[0].set_xlabel("Month")
    axes[0].set_ylabel("Sales ($)")

    sns.barplot(data=df, x="day_of_week", y="Sales", order=dow_order, ax=axes[1], palette="flare", errorbar=None)
    axes[1].set_title("Average Sales by Day of Week")
    axes[1].set_xlabel("Day of Week")
    axes[1].set_ylabel("Average Sales ($)")
    axes[1].tick_params(axis="x", rotation=30)

    plt.tight_layout()
    fig3_path = os.path.join(output_dir, "seasonality_trends.png")
    fig.savefig(fig3_path, dpi=300)
    plt.close(fig)

    logger.info(f"All EDA Visualizations successfully saved to '{output_dir}/'.")

if __name__ == "__main__":
    generate_eda_visualizations()
