"""
RetailMind-X: Compatibility facade for session_manager.
Re-exports from app.data.session_manager to maintain shared singleton state.
"""

from app.data.session_manager import (
    AppState,
    DatasetSession,
    SESSION,
)

__all__ = [
    "AppState",
    "DatasetSession",
    "SESSION",
]
