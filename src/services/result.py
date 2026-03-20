"""
Generic service result wrapper.
Provides a consistent return type for all service layer operations.
"""
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

T = TypeVar('T')


@dataclass
class ServiceResult(Generic[T]):
    """
    Wraps the outcome of any service operation.

    Attributes:
        success:      Whether the operation completed without errors.
        data:         The returned payload on success (None on failure).
        error:        A human-readable error message on failure (None on success).
        is_not_found: True when the operation succeeded technically but the
                      requested record does not exist. Allows callers to
                      distinguish "record missing" from a real service error
                      without relying on error message string matching.
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    is_not_found: bool = False

    # ------------------------------------------------------------------
    # Factory helpers — prefer these over constructing instances directly
    # ------------------------------------------------------------------

    @classmethod
    def ok(cls, data: Optional[T] = None) -> 'ServiceResult[T]':
        """Creates a successful result, optionally carrying a data payload."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'ServiceResult[T]':
        """Creates a failed result with a descriptive error message."""
        return cls(success=False, error=error)

    @classmethod
    def not_found(cls, message: str) -> 'ServiceResult[T]':
        """
        Creates a result that signals the requested record does not exist.
        Treated as a failure (success=False) but flagged separately so callers
        can show an informational message instead of an error dialog.
        """
        return cls(success=False, error=message, is_not_found=True)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        """Allows using the result directly in boolean expressions."""
        return self.success
