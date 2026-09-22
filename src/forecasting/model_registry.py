"""
RetailMind-X: Compatibility facade for model_registry.
Re-exports ModelRegistry from app.forecasting.model_registry.
"""

from app.forecasting.model_registry import ModelRegistry

__all__ = ["ModelRegistry"]
