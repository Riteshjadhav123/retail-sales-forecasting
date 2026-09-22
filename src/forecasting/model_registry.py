"""
src/forecasting/model_registry.py
Model Registry Engine for RetailMind-X
Tracks versioned forecasting models, evaluation metrics (MAPE, RMSE, MAE),
training timestamps, session linkage, and active production status.
100% session-grounded.
"""

from typing import Dict, Any, List, Optional
import datetime
import os
import json


class ModelRegistry:
    """
    Manages versioned model tracking and status.
    """
    _registry: List[Dict[str, Any]] = []

    @classmethod
    def register_model(
        cls,
        model_name: str,
        metrics: Dict[str, float],
        dataset_name: str,
        target_col: str,
        target_type: str = "units",
        is_active: bool = False,
        notes: str = ""
    ) -> Dict[str, Any]:
        version_num = len(cls._registry) + 1
        version_tag = f"v{version_num}.0.0"

        # If activating this model, deactivate previous active models for the same target
        if is_active:
            for entry in cls._registry:
                if entry.get("status") == "ACTIVE_PRODUCTION":
                    entry["status"] = "ARCHIVED"

        entry = {
            "version": version_tag,
            "model_name": model_name,
            "status": "ACTIVE_PRODUCTION" if is_active else "CANDIDATE",
            "registered_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataset_name": dataset_name,
            "target_column": target_col,
            "target_type": target_type,
            "metrics": {
                "mape": round(metrics.get("mape", 0.0), 2) if metrics.get("mape") is not None else None,
                "rmse": round(metrics.get("rmse", 0.0), 2) if metrics.get("rmse") is not None else None,
                "mae": round(metrics.get("mae", 0.0), 2) if metrics.get("mae") is not None else None,
                "r2": round(metrics.get("r2", 0.0), 3) if metrics.get("r2") is not None else None,
            },
            "notes": notes
        }

        cls._registry.append(entry)
        return entry

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        return cls._registry

    @classmethod
    def get_active_model(cls) -> Optional[Dict[str, Any]]:
        for entry in reversed(cls._registry):
            if entry.get("status") == "ACTIVE_PRODUCTION":
                return entry
        return cls._registry[-1] if cls._registry else None

    @classmethod
    def activate_model(cls, version: str) -> bool:
        found = False
        for entry in cls._registry:
            if entry.get("version") == version:
                entry["status"] = "ACTIVE_PRODUCTION"
                found = True
            else:
                if entry.get("status") == "ACTIVE_PRODUCTION":
                    entry["status"] = "ARCHIVED"
        return found

    @classmethod
    def clear(cls):
        cls._registry = []
