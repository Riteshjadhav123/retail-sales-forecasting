import os
import json
import joblib
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.utils.logger import get_logger

logger = get_logger("model_registry")

class ModelRegistry:
    """Production Model Registry for RetailMind-X."""

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

    def register_model(
        self,
        model_name: str,
        version: str,
        features: List[str],
        metrics: Dict[str, float],
        hyperparameters: Dict[str, Any],
        model_object: Optional[Any] = None,
        dataset_version: str = "v1.0"
    ) -> str:
        """Registers a model entry with full metadata and serialized artifact."""
        model_id = f"{model_name}_v{version}_{datetime.now().strftime('%Y%m%m_%H%M%S')}"
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
            "timestamp": datetime.now().isoformat(),
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
