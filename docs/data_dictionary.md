# Data Dictionary — Global Superstore Dataset

## Real Transactional Fields (Raw & Cleaned)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `Order ID` | String | Unique transaction order identifier. |
| `Order Date` | Datetime64 | Date transaction was placed. |
| `Ship Date` | Datetime64 | Date order was dispatched. |
| `Ship Mode` | String | Shipping class (First Class, Second Class, Standard Class, Same Day). |
| `Customer ID` | String | Unique customer identifier. |
| `Segment` | String | Customer market segment (Consumer, Corporate, Home Office). |
| `City` | String | Customer location city. |
| `State` | String | Customer location state/province. |
| `Country` | String | Destination country (147 countries). |
| `Market` | String | Global retail market region (APAC, Europe, LATAM, US, Canada, EMEA). |
| `Region` | String | Geographic sub-region (13 unique regions). |
| `Category` | String | Top-level product hierarchy (Furniture, Office Supplies, Technology). |
| `Sub-Category` | String | Secondary product level (17 unique sub-categories). |
| `Product ID` | String | Individual SKU identifier. |
| `Sales` | Float64 | Gross revenue generated ($). |
| `Quantity` | Int64 | Units purchased. |
| `Discount` | Float64 | Promotional discount rate applied (0.0 to 0.80). |
| `Profit` | Float64 | Net profit/loss from transaction ($). |
| `Unit Price` | Float64 | Derived price per unit (`Sales / Quantity`). |

---

## Derived Time-Series Features

| Feature Name | Type | Formula / Description |
| :--- | :--- | :--- |
| `series_id` | String | Group key (`Region_Category`). |
| `lag_1` | Float64 | Sales at day $t-1$. |
| `lag_7` | Float64 | Sales at day $t-7$. |
| `lag_14` | Float64 | Sales at day $t-14$. |
| `lag_28` | Float64 | Sales at day $t-28$. |
| `rolling_mean_7` | Float64 | 7-day trailing average sales on shifted target. |
| `rolling_mean_28`| Float64 | 28-day trailing average sales on shifted target. |
| `rolling_std_7` | Float64 | 7-day trailing standard deviation of sales. |
| `short_term_trend`| Float64 | Ratio of `rolling_mean_7 / rolling_mean_28`. |
| `demand_volatility`| Float64 | Coefficient of Variation (`rolling_std_7 / rolling_mean_7`). |
| `sin_month` / `cos_month` | Float64 | Cyclical monthly calendar encodings. |

---

## Derived Inventory & Demand Recovery Fields

| Field Name | Type | Signal Status | Description |
| :--- | :--- | :--- | :--- |
| `is_stockout_derived` | Boolean | SIMULATED/DERIVED | Flag indicating inferred stockout event (zero sales after high demand velocity). |
| `inventory_level_proxy` | Float64 | SIMULATED/DERIVED | Inferred warehouse inventory level buffer. |
| `reconstructed_demand` | Float64 | RECONSTRUCTED | Unconstrained customer demand estimated via Tobit model during stockout periods. |
