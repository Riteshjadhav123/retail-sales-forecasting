import os
import yaml
from functools import lru_cache
from typing import Dict, Any

class Settings:
    """Application settings loaded from YAML configuration."""
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict
        self.app = config_dict.get("app", {})
        self.paths = config_dict.get("paths", {})
        self.logging = config_dict.get("logging", {})
        self.session = config_dict.get("session", {})

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    primary_config = os.path.join(base_dir, "config", "settings.yaml")
    fallback_config = os.path.join(base_dir, "config.yaml")

    config_path = primary_config if os.path.exists(primary_config) else fallback_config
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return Settings(data)
    return Settings({})
