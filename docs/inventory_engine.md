# Inventory Optimization Engine Documentation

## Core Mathematical Formulations

### 1. Safety Stock ($SS$)
$$SS = Z \times \sqrt{L \cdot \sigma_D^2 + D^2 \cdot \sigma_L^2}$$
- $Z$: Normal distribution inverse cumulative probability factor ($Z=1.645$ for 95% service level, $Z=2.326$ for 99% service level).
- $L$: Replenishment lead time in days.
- $\sigma_D$: Standard deviation of daily customer demand.
- $D$: Average daily customer demand.
- $\sigma_L$: Standard deviation of lead-time delays in days.

### 2. Reorder Point ($ROP$)
$$ROP = (D \cdot L) + SS$$
- Triggers replenishment order when total inventory position (on-hand + on-order) drops to or below $ROP$.

### 3. Economic Order Quantity ($EOQ$)
$$EOQ = \sqrt{\frac{2 \cdot D_{\text{annual}} \cdot S}{H}}$$
- $D_{\text{annual}}$: Projected annual demand ($D \times 365$).
- $S$: Fixed cost per order ($50.00 default).
- $H$: Annual holding cost per unit ($15\% \times \text{Unit Price}$).

---

## Assumptions & Principles
1. Demand and lead times are treated as independent random variables.
2. Holding costs are evaluated as a linear percentage of unit price.
3. Unfilled demand during stockout periods is backordered or lost according to service level goals.
