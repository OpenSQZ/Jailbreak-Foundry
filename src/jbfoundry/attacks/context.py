"""
Attack Context System for Thread-Safe Attack Execution.

This module provides a Flask-like context system for attacks, ensuring that
each attack generation call has isolated state even when the same attack
instance is used concurrently across multiple threads.
"""

from contextvars import ContextVar
from typing import Any, Dict, Optional
import threading


# Context variable for storing the current attack context (Python 3.7+)
_attack_context: ContextVar[Optional['AttackContext']] = ContextVar('attack_context', default=None)


class AttackContext:
    """
    Isolated context for each attack generation call.

    Similar to Flask's request context, this provides thread-local storage
    for attack-specific data that should not be shared between concurrent
    attack executions.
    """

    def __init__(self, **kwargs):
        """
        Initialize attack context with optional initial data.

        Args:
            **kwargs: Initial context data (e.g., cost_tracker, metadata, etc.)
        """
        self._data = kwargs.copy()
        self._lock = threading.Lock()  # For thread-safety within context

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context.

        Args:
            key: The key to retrieve
            default: Default value if key not found

        Returns:
            Value associated with key or default
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the context.

        Args:
            key: The key to set
            value: The value to associate with the key
        """
        with self._lock:
            self._data[key] = value

    def update(self, **kwargs) -> None:
        """
        Update multiple values in the context.

        Args:
            **kwargs: Key-value pairs to update
        """
        with self._lock:
            self._data.update(kwargs)

    def increment(self, key: str, delta: int = 1) -> int:
        """
        Atomically increment a numeric value in the context.

        Args:
            key: The key to increment
            delta: Amount to increment by (default: 1)

        Returns:
            New value after increment
        """
        with self._lock:
            current = self._data.get(key, 0)
            new_value = current + delta
            self._data[key] = new_value
            return new_value

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the context.

        Args:
            key: The key to check

        Returns:
            True if key exists, False otherwise
        """
        return key in self._data

    def keys(self):
        """Get all keys in the context."""
        return self._data.keys()

    def to_dict(self) -> Dict[str, Any]:
        """
        Get a copy of all context data as a dictionary.

        Returns:
            Dictionary copy of all context data
        """
        with self._lock:
            return self._data.copy()

    def __contains__(self, key: str) -> bool:
        """Support 'key in context' syntax."""
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        """Support context[key] syntax."""
        if key not in self._data:
            raise KeyError(f"Context key '{key}' not found")
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Support context[key] = value syntax."""
        self.set(key, value)


def get_attack_context() -> AttackContext:
    """
    Get the current attack context.

    Returns:
        Current AttackContext instance

    Raises:
        RuntimeError: If no attack context is active
    """
    context = _attack_context.get()
    if context is None:
        raise RuntimeError(
            "No attack context available. This method can only be called "
            "within an attack generation execution."
        )
    return context


def has_attack_context() -> bool:
    """
    Check if an attack context is currently active.

    Returns:
        True if context is available, False otherwise
    """
    return _attack_context.get() is not None


def set_attack_context(context: AttackContext) -> None:
    """
    Set the current attack context (internal use only).

    Args:
        context: The AttackContext to set as current
    """
    _attack_context.set(context)


def clear_attack_context() -> None:
    """Clear the current attack context (internal use only)."""
    _attack_context.set(None)


# Convenience functions for common context operations
def ctx_get(key: str, default: Any = None) -> Any:
    """Get a value from the current attack context."""
    return get_attack_context().get(key, default)


def ctx_set(key: str, value: Any) -> None:
    """Set a value in the current attack context."""
    get_attack_context().set(key, value)


def ctx_increment(key: str, delta: int = 1) -> int:
    """Atomically increment a value in the current attack context."""
    return get_attack_context().increment(key, delta)


def ctx_has(key: str) -> bool:
    """Check if a key exists in the current attack context."""
    return get_attack_context().has(key)