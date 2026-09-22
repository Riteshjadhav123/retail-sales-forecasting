# Digital Retail Twin Simulator Specification

## Concept & Nature
The Digital Retail Twin is a lightweight, data-driven simulation model of store-product retail supply chain dynamics. It executes day-by-day time-step iterations over a 90-day simulation horizon.

> [!NOTE]
> This simulator is a data-driven stochastic mathematical representation designed for stress-testing inventory policies, not a real-time hardware twin of an actual physical enterprise.

## Simulation Event Sequence (Daily Loop)
For each day $t \in [1, 90]$:
1. **Pipeline Order Arrivals**: Arriving supplier orders are added to current on-hand inventory.
2. **Customer Demand Realization**: Daily demand $D_t$ is observed. Realized sales $S_t = \min(I_t, D_t)$. Stockout counted if $I_t < D_t$.
3. **Inventory Position Check**: Evaluates $I_{\text{position}} = I_{\text{on-hand}} + I_{\text{pipeline}}$. If $I_{\text{position}} \le ROP$, a new order for $EOQ$ units is dispatched with arrival day $t + L$.

## Pre-Built Stress Test Scenarios
1. `DEMAND_SPIKE`: +50% demand surge.
2. `SUPPLIER_DELAY`: +7 days lead-time delay.
3. `PROMOTION_CAMPAIGN`: +40% volume surge with 15% price discount.
4. `DEMAND_DROP`: -40% demand decline.
5. `INVENTORY_SHORTAGE`: 50% initial stock reduction.
