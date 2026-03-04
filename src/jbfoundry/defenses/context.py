"""
Defense Context System for Thread-Safe Defense Execution.
"""

from contextvars import ContextVar
from typing import Any, Dict, Optional
import threading

_defense_context: ContextVar[Optional['DefenseContext']] = ContextVar('defense_context', default=None)


class DefenseContext:
    """Isolated context for each defense call."""

    def __init__(self, **kwargs):
        self._data = kwargs.copy()
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value

    def update(self, **kwargs) -> None:
        with self._lock:
            self._data.update(kwargs)

    def increment(self, key: str, delta: int = 1) -> int:
        with self._lock:
            current = self._data.get(key, 0)
            new_value = current + delta
            self._data[key] = new_value
            return new_value

    def has(self, key: str) -> bool:
        return key in self._data

    def keys(self):
        return self._data.keys()

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return self._data.copy()

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(f"Context key '{key}' not found")
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)


def get_defense_context() -> DefenseContext:
    context = _defense_context.get()
    if context is None:
        raise RuntimeError(
            "No defense context available. This method can only be called "
            "within a defense execution."
        )
    return context


def has_defense_context() -> bool:
    return _defense_context.get() is not None


def set_defense_context(context: DefenseContext) -> None:
    _defense_context.set(context)


def clear_defense_context() -> None:
    _defense_context.set(None)


def ctx_get(key: str, default: Any = None) -> Any:
    return get_defense_context().get(key, default)


def ctx_set(key: str, value: Any) -> None:
    get_defense_context().set(key, value)


def ctx_increment(key: str, delta: int = 1) -> int:
    return get_defense_context().increment(key, delta)


def ctx_has(key: str) -> bool:
    return get_defense_context().has(key)
