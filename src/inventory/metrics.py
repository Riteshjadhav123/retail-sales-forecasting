import numpy as np
import pandas as pd
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger("supply_chain_metrics")

def compute_holding_cost(average_inventory_units: float, unit_price: float, holding_cost_pct: float = 0.15) -> float:
    """Computes annual holding cost: Average_Inventory * Unit_Price * Holding_Cost_Pct."""
    return float(average_inventory_units * unit_price * holding_cost_pct)

def compute_ordering_cost(number_of_orders: int, ordering_cost_per_order: float = 50.0) -> float:
    """Computes total ordering cost: Number_of_Orders * Ordering_Cost."""
    return float(number_of_orders * ordering_cost_per_order)

def compute_supply_chain_metrics(
    demand_series: np.ndarray,
    sales_series: np.ndarray,
    inventory_series: np.ndarray,
    rop_series: np.ndarray,
    unit_price: float = 50.0,
    ordering_cost_per_order: float = 50.0,
    holding_cost_pct: float = 0.15
) -> Dict[str, float]:
    """Calculates comprehensive operational and financial inventory performance metrics."""
    n_days = len(demand_series)
    total_demand = float(np.sum(demand_series))
    total_sales = float(np.sum(sales_series))

    # Fill Rate = Total Sales / Total Demand
    fill_rate_pct = (total_sales / total_demand * 100.0) if total_demand > 0 else 100.0

    # Stockout Rate = % days where stockout occurred (sales < demand or inventory == 0)
    stockout_days = np.sum((sales_series < demand_series) | (inventory_series <= 0))
    stockout_rate_pct = (stockout_days / n_days * 100.0) if n_days > 0 else 0.0

    # Service Level = 100 - Stockout Rate
    service_level_achieved = 100.0 - stockout_rate_pct

    # Overstock Rate = % days where inventory > 2 * ROP
    overstock_days = np.sum(inventory_series > (2.0 * rop_series))
    overstock_rate_pct = (overstock_days / n_days * 100.0) if n_days > 0 else 0.0

    # Financial Costs
    avg_inventory = float(np.mean(inventory_series))
    annual_holding_cost = compute_holding_cost(avg_inventory, unit_price, holding_cost_pct)
    
    # Estimate reorder frequencies
    reorder_events = np.sum(np.diff((inventory_series <= rop_series).astype(int)) > 0)
    annual_ordering_cost = compute_ordering_cost(reorder_events, ordering_cost_per_order)

    total_cost = annual_holding_cost + annual_ordering_cost

    return {
        "Fill_Rate_Pct": round(fill_rate_pct, 2),
        "Service_Level_Pct": round(service_level_achieved, 2),
        "Stockout_Rate_Pct": round(stockout_rate_pct, 2),
        "Overstock_Rate_Pct": round(overstock_rate_pct, 2),
        "Average_Inventory_Units": round(avg_inventory, 2),
        "Holding_Cost": round(annual_holding_cost, 2),
        "Ordering_Cost": round(annual_ordering_cost, 2),
        "Total_Supply_Chain_Cost": round(total_cost, 2)
    }
