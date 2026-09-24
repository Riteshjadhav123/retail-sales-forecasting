# RetailMind-X — Retail Sales Forecasting & Inventory Intelligence Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Pytest Suite](https://img.shields.io/badge/pytest-61%20passed-success.svg)]()
[![Hardening](https://img.shields.io/badge/hardening-9%2F9%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Vaidsys Technologies — Data Science Internship**  
> **Project 1:** Retail Sales Forecasting & Inventory Intelligence  
> **Architecture:** Modern Data-First, Session-Isolated Full-Stack Intelligence Platform

---

## 📌 Project Overview

RetailMind-X is an enterprise-grade time-series forecasting and inventory optimization platform engineered for retail operations. Designed around a strict **Data-First architecture**, the platform contains zero hardcoded datasets. It initializes in a clean `NO_DATASET` state, automatically profiles any uploaded retail transaction dataset, constructs leak-free temporal features, trains competitive baseline and machine learning forecasting models (Ridge, Random Forest, LightGBM Quantile Regressors), and generates actionable inventory optimization strategies (Safety Stock, Reorder Point, EOQ, ABC stratification, and stockout/overstock mitigation).

### Key Objectives & Achievements
- **Adaptive Ingestion:** Automatic semantic column mapping (Order Date, Sales/Revenue, Quantity, SKU/Category).
- **Leak-Free Forecasting:** Strict chronological time-series splitting with expanding-window rolling and lag feature engineering.
- **Probabilistic Horizons:** Forecasts across 7, 14, and 30-day horizons with P10/P50/P90 prediction intervals.
- **Inventory Optimization:** Multi-echelon inventory control targeting **>=15% stockout reduction** and **>=10% overstock reduction**.
- **Interactive Command Center:** Real-time web UI dashboard with live upload progress, scenario simulator, executive reporting, and conversational AI assistant.

---

## 📂 Repository Structure

```
vaidysis/
├── app/                      # Canonical Application Core
│   ├── api/                  # FastAPI routers and route handlers
│   ├── core/                 # App configuration, logging, exceptions
│   ├── data/                 # Dynamic dataset profiler, cleaner, session manager
│   ├── features/             # Zero-lookahead time-series feature engineering
│   ├── forecasting/          # Forecasting models, temporal validator, model registry
│   ├── intelligence/         # Anomaly detection, seasonality, pricing & AI decision center
│   ├── inventory/            # Safety Stock, ROP, EOQ, ABC analysis, risk matrix
│   ├── reports/              # 30-section audit & executive report generators
│   ├── static/               # Frontend CSS, JavaScript, and assets
│   ├── templates/            # Single-page Command Center interface
│   └── main.py               # FastAPI application entrypoint
├── src/                      # Clean Compatibility Facades (pointing to app/*)
├── api/                      # Route Compatibility Layer (api.routes)
├── config/                   # System, inventory, and model YAML configurations
├── data/
│   ├── sample/               # Verified sample retail sales dataset
│   │   └── sample_retail_sales_dataset.csv
│   ├── raw/                  # Clean staging directory for runtime uploads
│   └── processed/            # Clean directory for runtime features
├── models/                   # Clean model registry storage
│   └── registry.json
├── scripts/                  # Operational Scripts
│   ├── launcher.py           # Auto-launch server and browser
│   ├── run_app.py            # Headless server launcher
│   ├── run_pipeline.py       # Headless pipeline execution
│   └── verify_hardening.py   # 9-point comprehensive hardening test suite
├── tests/                    # 61 Automated Pytest Unit & Integration Tests
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── config.yaml               # Root fallback configuration
├── LICENSE                   # Open-source MIT license
├── pyproject.toml            # Project packaging specification
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
└── run_retailmind.bat        # Windows one-click application launcher
```

---

## 🛠️ Prerequisites & Requirements

- **Operating System:** Windows 10/11, Linux, or macOS
- **Python Version:** Python 3.10 or higher
- **Browser:** Modern web browser (Chrome, Edge, Firefox, Brave)

---

## 🚀 Installation & Setup

1. **Clone or Navigate to the Repository:**
   ```bash
   cd c:\Users\HP\OneDrive\Desktop\vaidysis
   ```

2. **Create and Activate a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Running the Application

### Option 1: One-Click Launcher (Windows)
Double-click `run_retailmind.bat` or run:
```cmd
run_retailmind.bat
```
*This automatically starts the backend server and opens `http://127.0.0.1:8000` in your default browser.*

### Option 2: Python Launcher
```bash
python scripts/launcher.py
```

### Option 3: Manual Uvicorn Start
```bash
python scripts/run_app.py
# Or directly:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at: **`http://127.0.0.1:8000`**

---

## 📊 Using the Sample Dataset

RetailMind-X includes a verified 5,000-row sample retail sales dataset located at:
```
data/sample/sample_retail_sales_dataset.csv
```

### Step-by-Step Workflow:
1. Launch the platform and open `http://127.0.0.1:8000`.
2. In the **Upload Dataset** zone, upload `data/sample/sample_retail_sales_dataset.csv`.
3. The real-time progress component displays transmission speed, uploaded bytes, and ETA.
4. The system automatically profiles the schema and detects date and metric fields.
5. Confirm column mappings and click **Run Intelligence Pipeline**.
6. Explore interactive forecasts, inventory reorder recommendations, ABC matrix, scenario simulations, and export the comprehensive 30-section executive audit report .

---

## 🧪 Verification & Automated Testing

### 1. Run Complete Pytest Suite (61 Tests)
```bash
python -m pytest tests/ -v
```
All 61 unit, integration, and security tests validate:
- Session isolation & cross-dataset leak prevention
- Chronological temporal train/val/test zero-lookahead split
- Safety Stock, ROP, and EOQ mathematics
- Dynamic schema mapping and metric detection
- Fast API endpoint contracts and error handling

### 2. Run Comprehensive Hardening Audit (9 Verification Points)
```bash
python scripts/verify_hardening.py
```
Validates:
1. Multi-dataset session isolation
2. Semantic target detection across heterogeneous schemas
3. Inventory optimization formula correctness
4. Forecast metrics & Vaidsys target compliance
5. Zero-leakage temporal cross-validation
6. 30-section report generation integrity
7. Frontend state machine transitions

---

## 📑 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health status and runtime environment |
| `GET` | `/api/v1/state` | Current dataset session state (`NO_DATASET`, `ANALYSIS_COMPLETE`, etc.) |
| `POST` | `/api/v1/dataset/upload` | Multipart file upload with real-time profiling |
| `POST` | `/api/v1/dataset/map_columns`| Set semantic column mappings |
| `POST` | `/api/v1/dataset/process` | Trigger end-to-end forecasting & inventory pipeline |
| `POST` | `/api/v1/dataset/clear` | Clear current dataset session and purge memory |
| `GET` | `/api/v1/summary` | Executive summary metrics and inventory indicators |
| `GET` | `/api/v1/forecast` | Multi-horizon time-series predictions (P10/P50/P90) |
| `GET` | `/api/v1/inventory/recommendations` | SKU-level reorder flags, Safety Stock, and EOQ |
| `POST` | `/api/v1/scenario/simulate` | Interactive what-if simulation (lead time, demand shift) |
| `POST` | `/api/v1/assistant/chat` | Context-aware AI inventory assistant query |
| `GET` | `/api/v1/reports/export` | Download complete audit report |

Interactive Swagger documentation is available at: **`http://127.0.0.1:8000/docs`**

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
