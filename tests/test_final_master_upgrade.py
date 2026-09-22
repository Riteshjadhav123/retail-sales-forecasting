"""
tests/test_final_master_upgrade.py
Comprehensive test suite for RetailMind-X Final Master Upgrade:
- 12 schema role semantic profiler & capability matrix
- Demand anomaly engine with causal attribution
- Seasonality engine (day-of-week & monthly lift)
- Promo & price elasticity engine
- Inventory cost optimizer with labeled assumptions
- AI decision center (Today's priorities & top actions)
- Data drift detector (distribution shifts & KS test)
- Model registry (versioning & activation)
- Ask RetailMind assistant (grounded natural language queries)
- REST API integration endpoints
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from src.data.profiler import DatasetProfiler
from src.data.session_manager import SESSION
from src.intelligence.anomaly_engine import DemandAnomalyEngine
from src.intelligence.seasonality_engine import SeasonalityEngine
from src.intelligence.promo_price_engine import PromotionPriceEngine
from src.inventory.cost_optimizer import InventoryCostOptimizer
from src.intelligence.decision_center import AIDecisionCenter
from src.forecasting.drift_detector import DataDriftDetector
from src.forecasting.model_registry import ModelRegistry
from src.intelligence.ask_assistant import AskRetailMindAssistant
from api.routes import router
from fastapi import FastAPI


# Setup test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def sample_retail_df():
    dates = pd.date_range("2023-01-01", periods=120, freq="D")
    np.random.seed(42)
    demand = np.random.poisson(lam=50, size=120).astype(float)
    # Add a spike and a drop
    demand[40] = 250.0
    demand[80] = 2.0
    promo = [1 if i % 10 == 0 else 0 for i in range(120)]
    price = [19.99 if p == 0 else 14.99 for p in promo]

    return pd.DataFrame({
        "order_date": dates,
        "sku": ["SKU_A" if i % 2 == 0 else "SKU_B" for i in range(120)],
        "units_sold": demand,
        "revenue": demand * np.array(price),
        "is_promotion": promo,
        "unit_price": price
    })


def test_profiler_roles_and_capabilities(sample_retail_df):
    profiler = DatasetProfiler()
    profile = profiler.profile(sample_retail_df)

    # Check 12 role identification
    semantic = profile.get("semantic_metadata", {})
    assert "order_date" in semantic
    assert semantic["order_date"]["role"] == "DATE"
    assert "sku" in semantic
    assert semantic["sku"]["role"] == "PRODUCT"

    # Check detected frequency
    assert profile.get("detected_frequency") == "Daily"

    # Check target classification
    assert profile.get("target_display") in ["Units", "Monetary ($)", "Monetary (Sales / Revenue)"]

    # Check capability matrix
    matrix = profile.get("capability_matrix", {})
    assert matrix.get("forecasting") is True
    assert matrix.get("inventory_intelligence") is True
    assert matrix.get("seasonality_intelligence") is True
    assert matrix.get("promotional_impact") is True
    assert matrix.get("price_elasticity") is True


def test_demand_anomaly_engine(sample_retail_df):
    anomalies = DemandAnomalyEngine.detect_anomalies(
        df=sample_retail_df,
        date_col="order_date",
        target_col="units_sold",
        promo_col="is_promotion"
    )

    assert len(anomalies) > 0
    # Confirm presence of spike or drop with attribution
    types = [a["type"] for a in anomalies]
    assert "SPIKE" in types or "DROP" in types
    for a in anomalies:
        assert "causal_attribution" in a
        assert a["severity"] in ["HIGH", "MEDIUM", "LOW"]


def test_seasonality_engine(sample_retail_df):
    seasonality = SeasonalityEngine.calculate_seasonality(
        df=sample_retail_df,
        date_col="order_date",
        target_col="units_sold"
    )

    assert seasonality["available"] is True
    assert len(seasonality["day_of_week"]) == 7
    assert len(seasonality["monthly"]) > 0
    # Check baseline presence
    assert seasonality["baseline_average_demand"] > 0


def test_promo_price_engine(sample_retail_df):
    res = PromotionPriceEngine.analyze(
        df=sample_retail_df,
        date_col="order_date",
        target_col="units_sold",
        promo_col="is_promotion",
        price_col="unit_price"
    )

    assert res["available"] is True
    assert "promotional_lift" in res
    assert "price_elasticity" in res
    assert res["price_elasticity"]["label"] == "Observed price sensitivity across sales transactions"


def test_promo_price_engine_missing_columns():
    empty_df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    res = PromotionPriceEngine.analyze(
        df=empty_df,
        date_col="a",
        target_col="b"
    )
    assert res["available"] is False


def test_inventory_cost_optimizer():
    optimizer = InventoryCostOptimizer(holding_rate_annual=0.20, fixed_order_cost=50.0)
    items = [
        {"sku": "SKU-001", "current_stock": 10, "safety_stock": 25, "reorder_quantity": 80, "reorder_needed": True, "stockout_risk": "CRITICAL"},
        {"sku": "SKU-002", "current_stock": 300, "safety_stock": 50, "reorder_quantity": 0, "reorder_needed": False, "stockout_risk": "LOW", "overstock_risk": True}
    ]

    res = optimizer.calculate_costs(items)
    assert res["available"] is True
    assert "assumptions" in res
    assert "current_strategy" in res
    assert "recommended_strategy" in res
    assert "projected_savings" in res
    assert res["current_strategy"]["total_cost"] >= 0


def test_ai_decision_center():
    items = [
        {"sku": "SKU-CRIT", "current_stock": 0, "safety_stock": 30, "reorder_quantity": 100, "reorder_needed": True, "stockout_risk": "CRITICAL"},
        {"sku": "SKU-OK", "current_stock": 80, "safety_stock": 20, "reorder_quantity": 0, "reorder_needed": False, "stockout_risk": "LOW"}
    ]
    anomalies = [{"type": "SPIKE", "date": "2023-02-15", "value": 250, "deviation_pct": 350.0, "severity": "HIGH", "causal_attribution": "Spike"}]

    res = AIDecisionCenter.generate_decision_dashboard(
        inventory_items=items,
        anomalies=anomalies,
        forecast_metrics={"mape": 14.5},
        target_display="units"
    )

    assert res["priorities"]["critical_stockouts"] == 1
    assert len(res["top_actions"]) > 0
    top = res["top_actions"][0]
    assert top["priority"] == "CRITICAL"
    assert "what" in top and "why" in top and "action" in top


def test_data_drift_detector(sample_retail_df):
    res = DataDriftDetector.detect_drift(
        df=sample_retail_df,
        date_col="order_date",
        target_col="units_sold"
    )

    assert res["available"] is True
    assert res["drift_status"] in ["NO_DRIFT", "MODERATE_DRIFT", "SIGNIFICANT_DRIFT"]
    assert "differences" in res
    assert "ks_p_value" in res["differences"]


def test_model_registry():
    ModelRegistry.clear()
    reg = ModelRegistry.register_model(
        model_name="AutoARIMA",
        metrics={"mape": 12.5, "rmse": 45.0, "mae": 30.0},
        dataset_name="Test Retail",
        target_col="units_sold",
        is_active=True
    )

    assert reg["version"] == "v1.0.0"
    assert reg["status"] == "ACTIVE_PRODUCTION"

    models = ModelRegistry.list_models()
    assert len(models) == 1

    active = ModelRegistry.get_active_model()
    assert active["version"] == "v1.0.0"


def test_ask_retailmind_assistant():
    summary = {"dataset_name": "Retail Store", "row_count": 500, "target_column": "Demand", "detected_frequency": "Daily", "target_display": "Units"}
    items = [{"sku": "SKU-99", "current_stock": 5, "safety_stock": 25, "reorder_quantity": 50, "reorder_needed": True, "stockout_risk": "CRITICAL"}]
    forecast_results = {"best_model": "Prophet", "mape": 8.7}

    # Test replenishment query
    ans1 = AskRetailMindAssistant.answer_query("Which items need replenishment?", summary, items, forecast_results)
    assert "SKU-99" in ans1["answer"]
    assert "Inventory Engine" in ans1["source"]

    # Test best model / accuracy query
    ans2 = AskRetailMindAssistant.answer_query("What is our best forecast model?", summary, items, forecast_results)
    assert "Prophet" in ans2["answer"]
    assert "8.7%" in ans2["answer"]

    # Test fallback query
    ans3 = AskRetailMindAssistant.answer_query("What is the weather in Paris?", summary, items, forecast_results)
    assert "don't have enough specific information" in ans3["answer"]


def test_api_endpoints_integration(sample_retail_df):
    # Set session data
    SESSION.clean_df = sample_retail_df
    SESSION.dataset_name = "Sample_Retail.csv"
    SESSION.date_column = "order_date"
    SESSION.target_column = "units_sold"
    SESSION.target_display = "Units"
    SESSION.detected_frequency = "Daily"

    # 1. Capabilities
    r_cap = client.get("/api/v1/capabilities")
    assert r_cap.status_code == 200
    assert r_cap.json()["detected_frequency"] == "Daily"

    # 2. Anomalies
    r_anom = client.get("/api/v1/anomalies")
    assert r_anom.status_code == 200
    assert "anomalies" in r_anom.json()

    # 3. Seasonality
    r_seas = client.get("/api/v1/seasonality")
    assert r_seas.status_code == 200
    assert r_seas.json()["available"] is True

    # 4. Promo / Price
    r_pp = client.get("/api/v1/promo_price")
    assert r_pp.status_code == 200

    # 5. Cost Optimization
    r_cost = client.get("/api/v1/cost_optimization")
    assert r_cost.status_code == 200
    assert r_cost.json()["available"] is True

    # 6. Decision Center
    r_dec = client.get("/api/v1/decision_center")
    assert r_dec.status_code == 200
    assert "priorities" in r_dec.json()
    assert "top_actions" in r_dec.json()

    # 7. Drift
    r_drift = client.get("/api/v1/drift")
    assert r_drift.status_code == 200
    assert r_drift.json()["available"] is True

    # 8. Model Registry & Activate & Retrain
    r_reg = client.get("/api/v1/model_registry")
    assert r_reg.status_code == 200
    assert len(r_reg.json()["models"]) > 0

    r_retrain = client.post("/api/v1/model_retrain")
    assert r_retrain.status_code == 200
    assert r_retrain.json()["status"] == "retrained_successfully"

    # 9. Ask RetailMind
    r_ask = client.post("/api/v1/ask_retailmind", json={"query": "Which items need replenishment?"})
    assert r_ask.status_code == 200
    assert "answer" in r_ask.json()
