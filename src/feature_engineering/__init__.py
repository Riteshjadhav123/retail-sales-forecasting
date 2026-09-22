"""
Feature engineering module for Vaidsys Retail Sales Forecasting.
Engineers calendar, lag, rolling, trend, price, and promotion features with zero future data leakage.
"""

from src.feature_engineering.builder import FeatureBuilder

__all__ = ["FeatureBuilder"]
