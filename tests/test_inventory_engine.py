import pytest
from src.inventory.engine import InventoryOptimizationEngine

def test_inventory_engine_math():
    engine = InventoryOptimizationEngine(ordering_cost=50.0, holding_cost_pct=0.15)
    
    ss = engine.calculate_safety_stock(avg_daily_demand=20.0, std_daily_demand=5.0, lead_time_days=7.0, service_level=0.95)
    rop = engine.calculate_reorder_point(avg_daily_demand=20.0, safety_stock=ss, lead_time_days=7.0)
    eoq = engine.calculate_eoq(annual_demand=7300.0, unit_price=50.0)

    assert ss > 0.0
    assert rop > ss
    assert rop == (20.0 * 7.0) + ss
    assert eoq > 0.0

def test_inventory_optimization_suite():
    engine = InventoryOptimizationEngine()
    params = engine.optimize_series_inventory("Central_Furniture", avg_daily_demand=15.0, std_daily_demand=4.0)

    assert params["series_id"] == "Central_Furniture"
    assert "safety_stock" in params
    assert "reorder_point" in params
    assert "economic_order_quantity" in params
