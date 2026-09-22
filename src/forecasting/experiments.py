import os
import json
from datetime import datetime
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger("experiment_tracker")

class ExperimentTracker:
    """Rigorous Experiment Tracking Framework for RetailMind-X."""

    def __init__(self, log_path: str = "experiments/experiment_log.json"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.experiments = self._load_experiments()

    def _load_experiments(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load experiment log: {e}")
        return []

    def log_experiment(
        self,
        experiment_id: str,
        model_name: str,
        dataset_version: str,
        features: List[str],
        hyperparameters: Dict[str, Any],
        metrics: Dict[str, float],
        validation_method: str = "Chronological_Holdout",
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """Logs a single experimental run with reproducible parameters."""
        entry = {
            "experiment_id": experiment_id,
            "timestamp": datetime.now().isoformat(),
            "model_name": model_name,
            "dataset_version": dataset_version,
            "validation_method": validation_method,
            "random_seed": random_seed,
            "feature_count": len(features),
            "features": features,
            "hyperparameters": hyperparameters,
            "metrics": metrics
        }
        self.experiments.append(entry)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.experiments, f, indent=2)
        logger.info(f"Logged experiment '{experiment_id}' ({model_name}) -> MAE={metrics.get('MAE', 0.0):.2f}, RMSE={metrics.get('RMSE', 0.0):.2f}.")
        return entry
