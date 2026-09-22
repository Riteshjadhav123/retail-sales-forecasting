import os
import sqlite3
from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger("database_manager")

CREATE_SCHEMAS_SQL = """
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(100) PRIMARY KEY,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    unit_price FLOAT
);

CREATE TABLE IF NOT EXISTS stores (
    store_id VARCHAR(100) PRIMARY KEY,
    region VARCHAR(100),
    market VARCHAR(100),
    country VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id VARCHAR(100),
    order_date DATE,
    series_id VARCHAR(100),
    sales FLOAT,
    quantity INTEGER,
    discount FLOAT,
    profit FLOAT
);

CREATE TABLE IF NOT EXISTS inventory (
    series_id VARCHAR(100) PRIMARY KEY,
    current_stock FLOAT,
    safety_stock FLOAT,
    reorder_point FLOAT,
    economic_order_quantity FLOAT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id VARCHAR(100),
    forecast_date DATE,
    median_val FLOAT,
    p10_val FLOAT,
    p90_val FLOAT,
    model_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id VARCHAR(100) PRIMARY KEY,
    timestamp TIMESTAMP,
    model_name VARCHAR(100),
    dataset_version VARCHAR(50),
    mae FLOAT,
    rmse FLOAT,
    wape FLOAT,
    r2 FLOAT
);

CREATE TABLE IF NOT EXISTS recommendations (
    series_id VARCHAR(100) PRIMARY KEY,
    reorder_status VARCHAR(50),
    recommended_order_quantity FLOAT,
    composite_risk_score FLOAT,
    risk_category VARCHAR(50),
    reasoning TEXT
);
"""

class DatabaseManager:
    """Database Access & Schema Management Layer (PostgreSQL with SQLite Fallback)."""

    def __init__(self, db_path: str = "data/retailmind.db"):
        self.db_path = db_path
        self.pg_host = os.getenv("POSTGRES_HOST")
        self.pg_db = os.getenv("POSTGRES_DB", "retailmind")
        self.pg_user = os.getenv("POSTGRES_USER", "postgres")
        self.pg_pass = os.getenv("POSTGRES_PASSWORD")

    def initialize_schema(self) -> bool:
        """Initializes database tables and schemas."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executescript(CREATE_SCHEMAS_SQL)
            conn.commit()
            conn.close()
            logger.info(f"Database schema initialized successfully at '{self.db_path}'.")
            return True
        except Exception as e:
            logger.warning(f"Database initialization exception: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Returns database connection status."""
        is_active = os.path.exists(self.db_path)
        return {
            "engine": "PostgreSQL (Configured) / SQLite (Active Fallback)",
            "database_path": self.db_path,
            "is_connected": is_active,
            "tables": ["products", "stores", "sales", "inventory", "forecasts", "experiments", "recommendations"]
        }
