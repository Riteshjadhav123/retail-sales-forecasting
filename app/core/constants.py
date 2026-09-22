from enum import Enum
from typing import Dict

class ServiceLevel(float, Enum):
    STANDARD = 0.90
    CRITICAL = 0.95
    HIGH = 0.98
    MAXIMUM = 0.99

class SystemConstants:
    DEFAULT_SERVICE_LEVEL = 0.95
    DEFAULT_LEAD_TIME_DAYS = 7
    DEFAULT_HOLDING_COST_PER_UNIT = 2.00
    DEFAULT_ORDERING_COST = 50.00
    DEFAULT_HORIZONS = [7, 14, 30]
    DEFAULT_QUANTILES = [0.10, 0.50, 0.90]
    DEFAULT_RANDOM_STATE = 42

    # Standard Z-Scores for Gaussian quantiles
    Z_SCORES: Dict[float, float] = {
        0.80: 1.2816,
        0.85: 1.4395,
        0.90: 1.6449,
        0.95: 1.95996,
        0.98: 2.3263,
        0.99: 2.5758,
    }
