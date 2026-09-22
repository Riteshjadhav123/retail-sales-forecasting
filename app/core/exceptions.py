"""RetailMind-X Custom Exceptions."""

class RetailMindException(Exception):
    """Base exception for RetailMind-X."""
    pass

class ValidationError(RetailMindException):
    """Raised when data fails schema or domain validation."""
    pass

class ModelError(RetailMindException):
    """Raised when forecasting model training or inference fails."""
    pass

class InventoryError(RetailMindException):
    """Raised when inventory optimization fails or encounters invalid constraints."""
    pass

class SessionError(RetailMindException):
    """Raised when session state is invalid or uninitialized."""
    pass
