import pytest
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
from src.inventory.abc_analysis import ABCInventoryClassifier
from src.inventory.risk_matrix import InventoryRiskMatrixEngine
from src.inventory.sku_explorer import SKUExplorerEngine
from src.data.quality import DataQualityEngine

client = TestClient(app)

def test_data_quality_score_calculation():
    df = pd.DataFrame({
        "Order Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
        "Sales": [100.0, 150.0, 200.0, 180.0, 220.0]
    })
    engine = DataQualityEngine(df, date_col="Order Date", sales_col="Sales")
    res = engine.run_assessment()
    assert "quality_score" in res
    assert res["quality_score"] >= 85.0
    assert res["quality_status"] == "GOOD"
    assert len(res["quality_explanations"]) > 0

def test_abc_inventory_classifier():
    df = pd.DataFrame({
        "series_id": ["SKU_1", "SKU_2", "SKU_3", "SKU_4"],
        "Sales": [1000.0, 200.0, 50.0, 10.0]
    })
    classifier = ABCInventoryClassifier(df, series_col="series_id", sales_col="Sales")
    res = classifier.classify()
    assert "classes" in res
    assert "A" in res["classes"]
    assert res["total_skus"] == 4

def test_inventory_risk_matrix():
    recs = [
        {"series_id": "SKU_1", "cv": 0.9, "composite_risk_score": 85.0, "reorder_status": "REORDER_NOW"},
        {"series_id": "SKU_2", "cv": 0.2, "composite_risk_score": 20.0, "reorder_status": "NORMAL"}
    ]
    engine = InventoryRiskMatrixEngine(recs)
    res = engine.build_matrix()
    assert "quadrants" in res
    assert len(res["quadrants"]["CRITICAL"]) == 1
    assert len(res["quadrants"]["LOW"]) == 1

def test_sku_explorer_engine():
    df = pd.DataFrame({
        "Order Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        "series_id": ["SKU_TEST", "SKU_TEST", "SKU_TEST"],
        "Sales": [100.0, 120.0, 110.0]
    })
    explorer = SKUExplorerEngine(df)
    res = explorer.explore_sku("SKU_TEST", horizon_days=14)
    assert res["series_id"] == "SKU_TEST"
    assert len(res["forecast_median"]) == 14
    assert "safety_stock" in res
    assert "reorder_point" in res

def test_phase2_endpoints():
    # Setup session with sample dataset
    df_sample = pd.DataFrame({
        "Order Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "series_id": ["Central_Furniture"] * 4,
        "Sales": [100.0, 150.0, 200.0, 180.0],
        "Quantity": [2, 3, 4, 3]
    })
    csv_bytes = df_sample.to_csv(index=False).encode("utf-8")
    client.post("/api/v1/dataset/upload", files={"file": ("test_p2.csv", csv_bytes, "text/csv")})

    # 1. Data Health Endpoint
    r1 = client.get("/api/v1/data_health")
    assert r1.status_code == 200
    d1 = r1.json()
    assert "quality_score" in d1

    # 2. ABC Analysis Endpoint
    r2 = client.get("/api/v1/abc_analysis")
    assert r2.status_code == 200
    d2 = r2.json()
    assert "classes" in d2

    # 3. Risk Matrix Endpoint
    r3 = client.get("/api/v1/risk_matrix")
    assert r3.status_code == 200
    d3 = r3.json()
    assert "quadrants" in d3

    # 4. SKU Explorer Endpoint
    r4 = client.get("/api/v1/sku_explorer?series_id=Central_Furniture")
    assert r4.status_code == 200
    d4 = r4.json()
    assert "forecast_p10" in d4

    # 5. Forecast Diagnostics Endpoint
    r5 = client.get("/api/v1/forecast_diagnostics?series_id=Central_Furniture")
    assert r5.status_code == 200
    d5 = r5.json()
    assert "residuals" in d5
