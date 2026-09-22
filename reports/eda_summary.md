# RetailMind-X Exploratory Data Analysis (EDA) Report

## 1. Executive Revenue Summary
- **Total Gross Revenue**: `$12,642,501.91`
- **Total Units Sold**: `178,312`
- **Total Orders**: `25,035`
- **Average Order Value (AOV)**: `$504.99`

## 2. Key Business & Research Insights
1. **Temporal Dynamics**: Monthly sales demonstrate consistent Q4 demand surges (September to December holiday peak).
2. **Category & Product Breakdown**: High revenue categories are led by Technology and Furniture. Top sub-categories generate over 50% of gross volume.
3. **Discount & Profitability Erosion**: Heavy discounts (> 0.20) exhibit a strong negative correlation with profit margins, causing negative net margin transactions.
4. **Demand Volatility**: Average Coefficient of Variation (CV) across regional categories is `1.71`, indicating moderate-to-high volatility requiring uncertainty estimation.
5. **Pareto Concentration**: Top 20% of sub-categories account for **48.9%** of total gross revenue.

## 3. Visualizations Generated
- `reports/figures/eda_sales_temporal_trends.png` (Daily, Weekly, Monthly, Yearly Trends)
- `reports/figures/eda_performance_breakdowns.png` (Category, Sub-Category & Region Performance)
- `reports/figures/eda_sales_distribution.png` (Log Sales Distribution & Skewness)
- `reports/figures/eda_discount_price_analysis.png` (Discount vs Sales & Profit Margins)
