# Data Pipeline Specification

## Stage 1: Ingestion & Contracting
Raw CSV files are fetched from the remote repository and parsed. Pydantic contracts (`RawSalesContract`) validate required fields prior to processing.

## Stage 2: Quality Engine Assessment
Automated diagnostic metrics run to evaluate:
- Total row/column counts
- Column-wise missing value percentages
- Duplicate row counts
- Date boundaries and invalid date counts
- Sales distribution skewness and IQR outliers

## Stage 3: Cleaning & Preprocessing
1. **Multi-Format Datetime Parsing**: Flexibly converts strings into `datetime64[ns]`.
2. **Numeric Sanitation**: Clips negative sales values to 0.0 and computes `Unit Price`.
3. **Imputation & Deduplication**: Fills missing categorical fields and removes duplicate records.
4. **Chronological Sorting**: Sorts by `Order Date`, `Market`, `Region`, `Category`, `Sub-Category`.

## Stage 4: Feature Engineering (Zero Leakage)
1. Aggregates transactions into daily sequence observations per time-series key (`series_id`).
2. Generates date features (day, day_of_week, month, quarter, year, sin/cos cyclical terms).
3. Derives time-shifted lags (`lag_1, 7, 14, 28`) and trailing rolling statistics (`rolling_mean_7, 14, 28`, `rolling_std_7, 28`).
4. Strict `.shift(1)` rule guarantees zero lookahead leakage.

## Stage 5: Demand Recovery Analysis
Identifies stockouts (zero sales following high rolling demand) and reconstructs unconstrained demand using Tobit statistical un-censoring (`reconstructed_demand`).
