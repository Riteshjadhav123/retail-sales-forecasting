import pytest
import io
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "dataset_version" in data

def test_state_endpoint():
    response = client.get("/api/v1/state")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data

def test_data_first_session_flow():
    # 1. Clear session
    r_clear = client.post("/api/v1/dataset/clear")
    assert r_clear.status_code == 200
    
    # 2. Upload sample CSV dataset
    df_sample = pd.DataFrame({
        "Order Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "series_id": ["SKU_A", "SKU_A", "SKU_B", "SKU_B"],
        "Sales": [100.0, 150.0, 200.0, 180.0],
        "Quantity": [2, 3, 4, 3]
    })
    csv_bytes = df_sample.to_csv(index=False).encode("utf-8")
    
    files = {"file": ("test_retail.csv", csv_bytes, "text/csv")}
    r_up = client.post("/api/v1/dataset/upload", files=files)
    assert r_up.status_code == 200
    data_up = r_up.json()
    assert data_up["status"] == "SUCCESS"
    assert data_up["rows"] == 4
    
    # 3. Map columns & Quality Audit
    map_payload = {
        "mapping": {
            "Date": "Order Date",
            "Product": "series_id",
            "Sales": "Sales",
            "Quantity": "Quantity"
        }
    }
    r_map = client.post("/api/v1/dataset/map_columns", json=map_payload)
    assert r_map.status_code == 200
    data_map = r_map.json()
    assert data_map["status"] == "SUCCESS"
    
    # 4. Process Pipeline
    r_proc = client.post("/api/v1/dataset/process")
    assert r_proc.status_code == 200
    data_proc = r_proc.json()
    assert data_proc["status"] == "SUCCESS"
    assert data_proc["state"] == "ANALYSIS_COMPLETE"

def test_summary_endpoint():
    response = client.get("/api/v1/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_sales_dollar" in data

def test_action_feed_endpoint():
    response = client.get("/api/v1/action_feed")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_demand_endpoint():
    response = client.get("/api/v1/demand?series_id=SKU_A")
    assert response.status_code == 200
    data = response.json()
    assert "historical_sales" in data
    assert "forecast_median" in data

def test_reorder_endpoint():
    response = client.get("/api/v1/reorder")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_scenario_endpoint():
    payload = {
        "base_avg_daily_demand": 20.0,
        "demand_growth_pct": 25.0,
        "scenario_lead_time_days": 10.0
    }
    response = client.post("/api/v1/scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "baseline" in data
    assert "scenario" in data

def test_digital_twin_endpoint():
    payload = {
        "series_id": "SKU_A",
        "scenario_name": "DEMAND_SPIKE"
    }
    response = client.post("/api/v1/digital_twin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "DEMAND_SPIKE"

def test_explainability_endpoint():
    response = client.get("/api/v1/explainability?series_id=SKU_A")
    assert response.status_code == 200
    data = response.json()
    assert "feature_importances" in data
    assert "explanations" in data

def test_ablation_endpoint():
    response = client.get("/api/v1/ablation")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_sales_analytics_endpoint():
    response = client.get("/api/v1/sales_analytics?timeframe=daily")
    assert response.status_code == 200
    data = response.json()
    assert "dates" in data
    assert "sales" in data

def test_project_insights_endpoint():
    response = client.get("/api/v1/project_insights")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_stores_and_categories_endpoints():
    r1 = client.get("/api/v1/stores")
    assert r1.status_code == 200
    assert isinstance(r1.json(), list)

    r2 = client.get("/api/v1/categories")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

def test_report_downloads():
    r_sec = client.get("/api/v1/reports/30_sections")
    assert r_sec.status_code == 200
    assert r_sec.json()["total_sections"] == 30

    r_html = client.get("/api/v1/reports/download/html")
    assert r_html.status_code == 200
    assert "<html" in r_html.text.lower()

    r_excel = client.get("/api/v1/reports/download/excel")
    assert r_excel.status_code == 200
    assert len(r_excel.content) > 0

    r_csv = client.get("/api/v1/reports/download/forecast_csv")
    assert r_csv.status_code == 200
    assert len(r_csv.content) > 0

def test_multi_dataset_structures_and_isolation():
    """Validates 4 structurally different dataset formats (Test A, B, C, D) and zero data leakage across session switches."""
    # Clear session first
    client.post("/api/v1/dataset/clear")
    
    # ------------------------------------
    # TEST A: Standard Date, Product, Sales, Quantity
    # ------------------------------------
    df_a = pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
        "Product": ["SKU_A1", "SKU_A1", "SKU_A1", "SKU_A1", "SKU_A1"],
        "Sales": [100.0, 120.0, 110.0, 130.0, 140.0],
        "Quantity": [10, 12, 11, 13, 14]
    })
    r_a = client.post("/api/v1/dataset/upload", files={"file": ("test_a.csv", df_a.to_csv(index=False).encode(), "text/csv")})
    assert r_a.status_code == 200
    res_a = r_a.json()
    assert res_a["auto_executed"] is True
    
    sum_a = client.get("/api/v1/summary").json()
    assert sum_a["total_sales_dollar"] == 600.0
    assert sum_a["filename"] == "test_a.csv"

    # ------------------------------------
    # TEST B: Order_Date, Product_ID, Revenue, Units_Sold, Store_ID
    # ------------------------------------
    df_b = pd.DataFrame({
        "Order_Date": ["2024-02-01", "2024-02-02", "2024-02-03", "2024-02-04", "2024-02-05"],
        "Product_ID": ["ITEM_B2", "ITEM_B2", "ITEM_B2", "ITEM_B2", "ITEM_B2"],
        "Revenue": [550.0, 600.0, 580.0, 620.0, 650.0],
        "Units_Sold": [5, 6, 5, 6, 7],
        "Store_ID": ["STORE_WEST"] * 5
    })
    r_b = client.post("/api/v1/dataset/upload", files={"file": ("test_b.csv", df_b.to_csv(index=False).encode(), "text/csv")})
    assert r_b.status_code == 200
    res_b = r_b.json()
    assert res_b["auto_executed"] is True

    sum_b = client.get("/api/v1/summary").json()
    # Confirm Test B replaced Test A completely (Total sales = 3000.0, zero contamination from Test A 600.0)
    assert sum_b["total_sales_dollar"] == 3000.0
    assert sum_b["filename"] == "test_b.csv"

    # ------------------------------------
    # TEST C: date, sku, quantity, price, store, inventory
    # ------------------------------------
    df_c = pd.DataFrame({
        "date": ["2024-03-01", "2024-03-02", "2024-03-03", "2024-03-04", "2024-03-05"],
        "sku": ["PROD_C3", "PROD_C3", "PROD_C3", "PROD_C3", "PROD_C3"],
        "quantity": [25, 30, 28, 35, 40],
        "price": [15.0, 15.0, 15.0, 15.0, 15.0],
        "store": ["BRANCH_01"] * 5,
        "inventory": [100, 75, 47, 12, 50]
    })
    r_c = client.post("/api/v1/dataset/upload", files={"file": ("test_c.csv", df_c.to_csv(index=False).encode(), "text/csv")})
    assert r_c.status_code == 200
    res_c = r_c.json()
    assert res_c["auto_executed"] is True
    
    sum_c = client.get("/api/v1/summary").json()
    assert sum_c["has_inventory_data"] is True
    assert sum_c["filename"] == "test_c.csv"

    # ------------------------------------
    # TEST D: InvoiceDate, StockCode, Quantity, UnitPrice, CustomerID
    # ------------------------------------
    df_d = pd.DataFrame({
        "InvoiceDate": ["2024-04-01", "2024-04-02", "2024-04-03", "2024-04-04", "2024-04-05"],
        "StockCode": ["85123A", "85123A", "85123A", "85123A", "85123A"],
        "Quantity": [6, 12, 4, 8, 10],
        "UnitPrice": [2.55, 2.55, 2.55, 2.55, 2.55],
        "CustomerID": [17850] * 5
    })
    r_d = client.post("/api/v1/dataset/upload", files={"file": ("test_d.csv", df_d.to_csv(index=False).encode(), "text/csv")})
    assert r_d.status_code == 200
    res_d = r_d.json()
    assert res_d["auto_executed"] is True
    
    sum_d = client.get("/api/v1/summary").json()
    assert sum_d["filename"] == "test_d.csv"

def test_invalid_dataset_required_column_validation():
    """Verifies clean error handling when uploaded dataset lacks required Date or Sales columns."""
    client.post("/api/v1/dataset/clear")
    
    df_bad = pd.DataFrame({
        "Customer_Name": ["John", "Alice", "Bob"],
        "City": ["New York", "London", "Paris"],
        "Feedback": ["Good", "Average", "Excellent"]
    })
    r_bad = client.post("/api/v1/dataset/upload", files={"file": ("invalid.csv", df_bad.to_csv(index=False).encode(), "text/csv")})
    assert r_bad.status_code == 200
    res_bad = r_bad.json()
    assert res_bad["auto_executed"] is False
    assert res_bad["profiling"]["is_valid"] is False
    assert "Analysis cannot start" in res_bad["profiling"]["error_message"]

def test_master_report_multi_format_downloads():
    """Verifies single master report download endpoint supports excel, pdf, word, html, and json formats."""
    # Excel format
    r_excel = client.get("/api/v1/reports/download/master?format=excel")
    assert r_excel.status_code == 200
    assert r_excel.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(r_excel.content) > 0

    # PDF format
    r_pdf = client.get("/api/v1/reports/download/master?format=pdf")
    assert r_pdf.status_code == 200
    assert r_pdf.headers["content-type"] == "application/pdf"
    assert len(r_pdf.content) > 0

    # Word format
    r_word = client.get("/api/v1/reports/download/master?format=word")
    assert r_word.status_code == 200
    assert r_word.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(r_word.content) > 0

    # HTML format
    r_html = client.get("/api/v1/reports/download/master?format=html")
    assert r_html.status_code == 200
    assert "text/html" in r_html.headers["content-type"]
    assert len(r_html.content) > 0

    # JSON format
    r_json = client.get("/api/v1/reports/download/master?format=json")
    assert r_json.status_code == 200
    assert "application/json" in r_json.headers["content-type"]
    assert len(r_json.content) > 0

