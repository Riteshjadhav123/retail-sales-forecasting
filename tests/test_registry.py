import pytest
import os
from src.forecasting.registry import ModelRegistry

def test_model_registry(tmp_path):
    reg_file = str(tmp_path / "registry.json")
    m_dir = str(tmp_path / "models")
    registry = ModelRegistry(registry_file=reg_file, models_dir=m_dir)

    m_id = registry.register_model(
        model_name="TestModel",
        version="1.0",
        features=["f1", "f2"],
        metrics={"MAE": 12.5, "RMSE": 20.1},
        hyperparameters={"param1": 10}
    )

    assert isinstance(m_id, str)
    best = registry.get_best_model(metric="MAE", lower_is_better=True)
    assert best["model_name"] == "TestModel"
    assert best["metrics"]["MAE"] == 12.5
