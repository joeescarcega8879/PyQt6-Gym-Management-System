"""
Generic service result wrapper.
Provides a consistent return type for all service layer operations.
"""
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional

T = TypeVar('T')


@dataclass
class ServiceResult(Generic[T]):
    """
    Wraps the outcome of any service operation.

    Attributes:
        success: Whether the operation completed without errors.
        data:    The returned payload on success (None on failure).
        error:   A human-readable error message on failure (None on success).
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None

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

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def __bool__(self) -> bool:
        """Allows using the result directly in boolean expressions."""
        return self.success
