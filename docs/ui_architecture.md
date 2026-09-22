# RetailMind-X UI Architecture & Design System

## Design Philosophy & Personality
- **Original & Technical**: Clean dark slate theme (`#0B0F19`) inspired by mission-critical aerospace command centers.
- **Decision-First Layout**: Directs user focus to high-priority actionable decisions rather than static graphs.
- **Fast & Responsive**: Single-Page Application (SPA) architecture with asynchronous REST API polling and cached responses.

## UI Component Hierarchy

```
+-----------------------------------------------------------------------------------+
|  RETAILMIND-X  [RESEARCH ENGINE v1.0]  "From Demand Signals to Decisions." System: ● ONLINE |
+-----------------------------------------------------------------------------------+
| 1.Command Center | 2.Demand Intel | 3.Forecast Lab | ... | 9.System Health         |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +--------------+  +--------------+  +--------------+  +--------------+           |
|  | Gross Sales  |  | Horizon      |  | Inv Value    |  | Stockout Risk|           |
|  | $5,620,000   |  | 90 Days      |  | $1,420,500   |  | 4.8%         |           |
|  +--------------+  +--------------+  +--------------+  +--------------+           |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | AI ACTION FEED — WHAT NEEDS MY ATTENTION?                                   |  |
|  | [HIGH] Imminent Stockout Alert — Series Central_Furniture                     |  |
|  | [MEDIUM] Overstock Warning — Series West_Office Supplies                    |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

## Color System
- **Background**: `#0B0F19`
- **Panel / Surface**: `#111827`
- **Borders**: `#1F2937`
- **Primary Accent**: `#06B6D4` (Cyan)
- **Success / Healthy**: `#10B981` (Emerald)
- **Warning / Alert**: `#F59E0B` (Amber)
- **Danger / High Priority**: `#F43F5E` (Rose)

## 9 Primary Experiences
1. **Command Center**: Key performance metrics + AI Action Feed.
2. **Demand Intelligence**: Historical demand, forecast & prediction bounds ($p10/p50/p90$).
3. **Forecast Lab**: Interactive model workbench & metric comparison table.
4. **Inventory Brain**: Decision cards (`REORDER_NOW`, `MONITOR`, `HEALTHY`, `OVERSTOCKED`).
5. **Scenario Lab**: Interactive parameter sliders and BASELINE vs SIMULATED impact table.
6. **Digital Twin**: 90-day simulation under stress scenarios (`DEMAND_SPIKE`, `SUPPLIER_DELAY`).
7. **Explainable AI**: SHAP feature driver importances & structured rationale.
8. **Research Lab**: Academic/research ablation matrix and experiment logs.
9. **System Health**: System telemetry, dataset versions, and unit test status.
