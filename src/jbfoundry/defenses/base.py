"""
Core defense base types and registry helpers.
"""

from typing import Dict, Type
from abc import ABC, ABCMeta, abstractmethod
from contextvars import Token

from .context import DefenseContext, _defense_context

# Registry for defense implementations
_DEFENSE_REGISTRY: Dict[str, Type["BaseDefense"]] = {}


class DefenseMetaclass(ABCMeta):
    """
    Metaclass that wraps defense methods with context management.
    """

    def __new__(mcs, name, bases, class_dict):
        cls = super().__new__(mcs, name, bases, class_dict)

        if name != "BaseDefense":
            for method_name in ("apply", "process_response"):
                if method_name in class_dict:
                    original_method = class_dict[method_name]

                    def wrapped(self, *args, _original=original_method, **kwargs):
                        context = DefenseContext(**kwargs)
                        token: Token = _defense_context.set(context)
                        try:
                            return _original(self, *args, **kwargs)
                        finally:
                            _defense_context.reset(token)

                    setattr(cls, method_name, wrapped)

        return cls


class BaseDefense(ABC, metaclass=DefenseMetaclass):
    """Base class for defense implementations."""

    name: str = "base"
    description: str = "Base defense class"
    default_config: Dict[str, any] = {}  # Default configuration for this defense

    def __init__(self, **kwargs):
        """Initialize defense with parameters."""
        self.params = kwargs

    @abstractmethod
    def apply(self, prompt: str, **kwargs) -> str:
        """
        Apply the defense to a prompt.

        Args:
            prompt: The prompt to defend
            **kwargs: Additional parameters

        Returns:
            The defended prompt
        """
        pass

    @abstractmethod
    def process_response(self, response: str, **kwargs) -> str:
        """
        Process the model's response with the defense.

        Args:
            response: The model's response
            **kwargs: Additional parameters

        Returns:
            The processed response
        """
        pass

    @classmethod
    def from_config(cls, config: dict) -> "BaseDefense":
        """Create a defense instance from a configuration dictionary."""
        return cls(**config)


def register_defense(name: str):
    """Decorator to register a new defense implementation."""
    def _register(cls):
        cls.name = name
        _DEFENSE_REGISTRY[name] = cls
        return cls
    return _register
