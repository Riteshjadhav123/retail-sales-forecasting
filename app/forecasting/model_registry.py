"""
RetailMind-X Model Registry Engine.
Tracks versioned forecasting models, evaluation metrics (MAPE, RMSE, MAE),
training timestamps, serialized artifacts, session linkage, and active production status.
Unified implementation supporting both file-based serialization and in-memory class registry.
"""

import os
import json
import joblib
import datetime
from typing import Dict, Any, Optional, List
from app.core.logging import get_logger

logger = get_logger("model_registry")


class _RegisterModelDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return owner._register_class_model
        def _dispatch(*args, **kwargs):
            if "dataset_name" in kwargs or "target_col" in kwargs:
                return owner._register_class_model(*args, **kwargs)
            return instance._register_instance_model(*args, **kwargs)
        return _dispatch


class ModelRegistry:
    """Production Model Registry for RetailMind-X."""
    _registry: List[Dict[str, Any]] = []

    def __init__(self, registry_file: str = "models/registry.json", models_dir: str = "models"):
        self.registry_file = registry_file
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not read existing registry: {e}. Re-initializing.")
        return {"models": []}

    def _save_registry(self):
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=2)

    def _register_instance_model(
        self,
        model_name: str,
        version: str = "1.0",
        features: Optional[List[str]] = None,
        metrics: Optional[Dict[str, float]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        model_object: Optional[Any] = None,
        dataset_version: str = "v1.0"
    ) -> str:
        """Registers a model entry with full metadata and serialized artifact."""
        metrics = metrics or {}
        hyperparameters = hyperparameters or {}
        features = features or []
        model_id = f"{model_name}_v{version}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        artifact_path = os.path.join(self.models_dir, f"{model_id}.joblib")

        if model_object is not None:
            try:
                joblib.dump(model_object, artifact_path)
            except Exception as e:
                logger.warning(f"Failed to serialize model object artifact: {e}")
                artifact_path = "N/A"

        entry = {
            "model_id": model_id,
            "model_name": model_name,
            "version": version,
            "timestamp": datetime.datetime.now().isoformat(),
            "dataset_version": dataset_version,
            "features": features,
            "hyperparameters": hyperparameters,
            "metrics": metrics,
            "artifact_path": artifact_path
        }

        self.registry["models"].append(entry)
        self._save_registry()
        logger.info(f"Registered model '{model_id}' with MAE={metrics.get('MAE', 0.0):.2f}, RMSE={metrics.get('RMSE', 0.0):.2f}.")
        return model_id

    @classmethod
    def _register_class_model(
        cls,
        model_name: str,
        metrics: Optional[Dict[str, float]] = None,
        dataset_name: str = "Active Dataset",
        target_col: str = "Demand",
        target_type: str = "units",
        is_active: bool = False,
        notes: str = ""
    ) -> Dict[str, Any]:
        metrics = metrics or {}
        version_num = len(cls._registry) + 1
        version_tag = f"v{version_num}.0.0"

        if is_active:
            for entry in cls._registry:
                if entry.get("status") == "ACTIVE_PRODUCTION":
                    entry["status"] = "ARCHIVED"

        entry = {
            "version": version_tag,
            "model_name": model_name,
            "status": "ACTIVE_PRODUCTION" if is_active else "CANDIDATE",
            "metrics": metrics,
            "dataset_name": dataset_name,
            "target_col": target_col,
            "target_type": target_type,
            "registered_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notes": notes
        }

        cls._registry.append(entry)
        return entry

    register_model = _RegisterModelDescriptor()

    def get_best_model(self, metric: str = "MAE", lower_is_better: bool = True) -> Dict[str, Any]:
        """Retrieves best model entry based on specified metric."""
        models = self.registry.get("models", [])
        if not models:
            raise ValueError("No models currently registered in Model Registry.")

        sorted_models = sorted(
            models,
            key=lambda x: x["metrics"].get(metric, float("inf") if lower_is_better else float("-inf")),
            reverse=not lower_is_better
        )
        return sorted_models[0]

    def list_registered_models(self) -> List[Dict[str, Any]]:
        """Lists all registered models."""
        return self.registry.get("models", [])

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        return cls._registry

    @classmethod
    def get_active_model(cls) -> Optional[Dict[str, Any]]:
        for entry in cls._registry:
            if entry.get("status") == "ACTIVE_PRODUCTION":
                return entry
        return cls._registry[0] if cls._registry else None

    @classmethod
    def activate_model(cls, version: str) -> bool:
        target = None
        for entry in cls._registry:
            if entry.get("version") == version:
                target = entry
                break
        if not target:
            return False

        for entry in cls._registry:
            if entry.get("status") == "ACTIVE_PRODUCTION":
                entry["status"] = "ARCHIVED"

        target["status"] = "ACTIVE_PRODUCTION"
        return True

    @classmethod
    def clear(cls):
        cls._registry = []
