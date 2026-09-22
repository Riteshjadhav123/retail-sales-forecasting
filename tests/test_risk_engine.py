import pytest
from src.inventory.risk_engine import InventoryRiskEngine

def test_risk_engine_dimensions():
    engine = InventoryRiskEngine()
    
    stockout_risk = engine.compute_stockout_risk(current_stock=50.0, reorder_point=100.0)
    overstock_risk = engine.compute_overstock_risk(current_stock=300.0, reorder_point=50.0, eoq=100.0)
    volatility_risk = engine.compute_volatility_risk(coefficient_of_variation=0.8)

    assert stockout_risk == 50.0
    assert overstock_risk > 0.0
    assert volatility_risk == 40.0

def test_composite_risk_evaluation():
    engine = InventoryRiskEngine()
    risk = engine.evaluate_risk(current_stock=20.0, reorder_point=80.0, eoq=100.0, cv=0.7)

    assert "composite_risk_score" in risk
    assert "risk_category" in risk
    assert 0.0 <= risk["composite_risk_score"] <= 100.0
