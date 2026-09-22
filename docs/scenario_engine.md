# Interactive What-If Scenario Lab Documentation

## Overview
The What-If Scenario Lab enables decision-makers to execute sensitivity analysis and simulate parameter shifts across 6 operational dimensions:

1. **Demand Growth Percentage**: Simulates market expansion or contraction.
2. **Promotion Campaign Boost**: Simulates volume surges from marketing campaigns.
3. **Price Adjustments**: Evaluates price elasticity impacts on revenue and holding cost.
4. **Lead-Time Disruption**: Simulates port congestion and supplier delivery delays.
5. **Target Service Level**: Evaluates trade-offs between 90%, 95%, and 99% customer availability.
6. **Starting Inventory**: Tests initial warehouse stock levels.

## Output Comparison Structure
The lab outputs a side-by-side **BASELINE vs SCENARIO** summary detailing:
- Expected daily demand
- Safety stock delta ($\Delta SS$)
- Reorder point delta ($\Delta ROP$)
- Economic order quantity delta ($\Delta EOQ$)
- Composite Risk Index delta ($\Delta \text{Risk}$)
